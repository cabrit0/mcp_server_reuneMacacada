"""
Sistema de scraping adaptativo que escolhe automaticamente o método mais eficiente
para cada site, reduzindo o uso de recursos e melhorando a performance.
"""

import asyncio
import aiohttp
import logging
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from typing import Dict, List, Optional, Any, Union

from puppeteer_pool import puppeteer_pool
from simple_cache import simple_cache

# Cache de métodos por domínio
domain_method_cache = {}
# Formato: 'dominio.com': { 'method': 'simple|puppeteer', 'success_rate': 0.95, 'last_updated': timestamp, 'usage_count': 10 }

async def simple_scraping_method(url: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Tenta fazer scraping usando apenas requisições HTTP simples (método leve)
    
    Args:
        url: URL para fazer scraping
        timeout: Tempo limite em segundos
        
    Returns:
        Objeto com HTML e metadados ou None se falhar
    """
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            async with session.get(url, timeout=timeout, headers=headers) as response:
                if response.status != 200:
                    logging.debug(f"Método simples falhou para {url}: Status {response.status}")
                    return None
                
                html = await response.text()
                
                # Verificar se o conteúdo principal está presente
                # Isso ajuda a detectar sites que exigem JavaScript
                soup = BeautifulSoup(html, 'html.parser')
                
                has_main_content = bool(
                    soup.find('main') or 
                    soup.find(id='content') or 
                    soup.find(class_='content') or 
                    soup.find('article') or
                    len(soup.get_text()) > 1000
                )
                
                if not has_main_content:
                    logging.debug(f"Método simples não encontrou conteúdo principal em {url}")
                    return None
                
                # Extrair metadados básicos
                title = soup.title.text.strip() if soup.title else ''
                description = ''
                
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    description = meta_desc['content']
                else:
                    og_desc = soup.find('meta', attrs={'property': 'og:description'})
                    if og_desc and og_desc.get('content'):
                        description = og_desc['content']
                
                return {
                    'html': html,
                    'title': title,
                    'description': description,
                    'method': 'simple'
                }
    except Exception as e:
        logging.debug(f"Método simples falhou para {url}: {str(e)}")
        return None

async def puppeteer_scraping_method(url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """
    Faz scraping usando Puppeteer (método pesado, mas mais poderoso)
    
    Args:
        url: URL para fazer scraping
        timeout: Tempo limite em segundos
        
    Returns:
        Objeto com HTML e metadados ou None se falhar
    """
    browser = None
    
    try:
        # Obter instância do pool
        browser = await puppeteer_pool.get_browser()
        page = await browser.newPage()
        
        # Configurar interceptação de requisições para bloquear recursos desnecessários
        await page.setRequestInterception(True)
        
        # Define o manipulador de requisições
        async def request_handler(req):
            if req.resourceType in ['stylesheet', 'font', 'image']:
                await req.abort()
            else:
                await req.continue_()
                
        page.on('request', lambda req: asyncio.ensure_future(request_handler(req)))
        
        # Configurar timeout e navegação
        await page.setDefaultNavigationTimeout(timeout * 1000)
        
        # Navegar para a página
        await page.goto(url, {'waitUntil': 'domcontentloaded', 'timeout': timeout * 1000})
        
        # Aguardar um pouco para conteúdo dinâmico carregar
        await page.waitFor(1000)
        
        # Extrair conteúdo e metadados
        html = await page.content()
        
        title = await page.evaluate('() => document.title || ""')
        
        description = await page.evaluate('''
            () => {
                const metaDesc = document.querySelector('meta[name="description"]');
                const ogDesc = document.querySelector('meta[property="og:description"]');
                return (metaDesc && metaDesc.getAttribute('content')) || 
                       (ogDesc && ogDesc.getAttribute('content')) || '';
            }
        ''')
        
        await page.close()
        
        return {
            'html': html,
            'title': title,
            'description': description,
            'method': 'puppeteer'
        }
    except Exception as e:
        logging.error(f"Método Puppeteer falhou para {url}: {str(e)}")
        return None
    finally:
        # Sempre devolver o browser ao pool
        if browser:
            await puppeteer_pool.release_browser(browser)

def update_domain_cache(domain: str, method: str, success: bool) -> None:
    """
    Atualiza o cache de métodos para um domínio específico
    
    Args:
        domain: Nome do domínio
        method: Método usado ('simple' ou 'puppeteer')
        success: Se o método foi bem-sucedido
    """
    global domain_method_cache
    
    if domain not in domain_method_cache:
        # Inicializar entrada no cache
        domain_method_cache[domain] = {
            'method': method,
            'success_rate': 1.0 if success else 0.0,
            'last_updated': time.time(),
            'usage_count': 1
        }
        return
    
    cache = domain_method_cache[domain]
    cache['usage_count'] += 1
    
    if cache['method'] == method:
        # Atualizar taxa de sucesso do método atual
        cache['success_rate'] = cache['success_rate'] * 0.9 + (0.1 if success else 0)
    elif success:
        # Se o novo método teve sucesso, considerar trocar
        cache['success_rate'] = cache['success_rate'] * 0.7  # Penalizar método atual
        
        # Trocar método se a taxa de sucesso for baixa
        if cache['success_rate'] < 0.5:
            logging.info(f"Trocando método preferido para {domain} de {cache['method']} para {method}")
            cache['method'] = method
            cache['success_rate'] = 0.7  # Começar com uma taxa razoável
    
    cache['last_updated'] = time.time()

async def adaptiveScrape(url: str, options: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """
    Faz scraping de uma URL usando o método mais eficiente
    
    Args:
        url: URL para fazer scraping
        options: Opções de configuração
            - timeout: Tempo limite em segundos (padrão: 30)
            - method: Forçar um método específico ('simple' ou 'puppeteer')
            
    Returns:
        Resultado do scraping ou None se falhar
    """
    if options is None:
        options = {}
    
    timeout = options.get('timeout', 30)
    if isinstance(timeout, int) and timeout > 1000:  # Se for em milissegundos, converter para segundos
        timeout = timeout / 1000
    
    force_method = options.get('method')
    
    try:
        # Extrair domínio da URL
        domain = urlparse(url).netloc
        
        # Determinar qual método usar
        method_to_use = force_method
        
        if not method_to_use:
            # Verificar cache de domínio
            if domain in domain_method_cache and domain_method_cache[domain]['method'] and (time.time() - domain_method_cache[domain]['last_updated'] < 86400):  # Cache válido por 1 dia
                method_to_use = domain_method_cache[domain]['method']
                logging.debug(f"Usando método em cache para {domain}: {method_to_use}")
            else:
                # Padrão: tentar método simples primeiro
                method_to_use = 'simple'
        
        # Tentar o método escolhido
        result = None
        
        if method_to_use == 'simple':
            result = await simple_scraping_method(url, min(timeout, 5))
            
            # Se falhar, tentar Puppeteer
            if not result:
                logging.debug(f"Método simples falhou para {url}, tentando Puppeteer")
                result = await puppeteer_scraping_method(url, timeout)
                
                # Atualizar cache
                update_domain_cache(domain, 'puppeteer', bool(result))
            else:
                # Método simples funcionou
                update_domain_cache(domain, 'simple', True)
        else:
            # Usar Puppeteer diretamente
            result = await puppeteer_scraping_method(url, timeout)
            
            # Atualizar cache
            update_domain_cache(domain, 'puppeteer', bool(result))
        
        if not result:
            logging.warning(f"Falha ao fazer scraping de {url} com todos os métodos disponíveis")
            return None
        
        return result
    except Exception as e:
        logging.error(f"Erro no scraping adaptativo: {str(e)}")
        return None

def clearDomainMethodCache() -> int:
    """
    Limpa o cache de métodos por domínio
    
    Returns:
        Número de entradas removidas
    """
    global domain_method_cache
    count = len(domain_method_cache)
    domain_method_cache.clear()
    logging.info('Cache de métodos por domínio foi limpo')
    return count

def getDomainMethodCacheStats() -> Dict[str, Any]:
    """
    Obtém estatísticas do cache de métodos
    
    Returns:
        Estatísticas do cache
    """
    domains = list(domain_method_cache.keys())
    simple_count = sum(1 for d in domains if domain_method_cache[d]['method'] == 'simple')
    puppeteer_count = sum(1 for d in domains if domain_method_cache[d]['method'] == 'puppeteer')
    
    return {
        'totalDomains': len(domains),
        'simpleMethodCount': simple_count,
        'puppeteerMethodCount': puppeteer_count,
        'domains': [
            {
                'domain': d,
                'method': domain_method_cache[d]['method'],
                'successRate': domain_method_cache[d]['success_rate'],
                'usageCount': domain_method_cache[d]['usage_count'],
                'lastUpdated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(domain_method_cache[d]['last_updated']))
            }
            for d in domains
        ]
    }
