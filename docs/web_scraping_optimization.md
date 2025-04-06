# Otimização de Web Scraping no MCP Server

Este documento descreve as técnicas e estratégias de otimização de web scraping implementadas e planejadas para o MCP Server.

## Visão Geral

O MCP Server depende fortemente de web scraping para coletar recursos educacionais da web. A otimização do processo de scraping é crucial para melhorar a performance, reduzir o tempo de resposta e minimizar o uso de recursos.

## Desafios Atuais

O processo de web scraping no MCP Server enfrenta os seguintes desafios:

1. **Alto Consumo de Recursos**: O uso do Puppeteer (via Pyppeteer) para scraping consome muita memória e CPU, pois cada instância carrega um navegador Chrome headless completo.

2. **Tempo de Resposta Lento**: O scraping de múltiplas páginas sequencialmente leva a tempos de resposta longos.

3. **Limitações do Render**: O plano gratuito do Render tem recursos limitados, o que pode levar a timeouts e falhas durante o scraping.

4. **Diversidade de Sites**: Diferentes sites requerem diferentes técnicas de scraping, alguns necessitando de JavaScript e outros não.

## Otimizações Implementadas

### 1. Sistema de Cache

Implementamos um sistema de cache que armazena o conteúdo de páginas web e metadados extraídos, reduzindo a necessidade de fazer scraping repetidamente da mesma página.

```python
# Verificar o cache antes de fazer scraping
cache_key = f"page:{url}"
cached_content = simple_cache.get(cache_key)
if cached_content:
    return cached_content

# Fazer scraping e armazenar no cache
content = await scrape_url(url)
simple_cache.setex(cache_key, 604800, content)  # 1 semana
```

## Otimizações Planejadas

### 1. Pool de Instâncias Puppeteer

**Descrição**: Implementar um pool de instâncias Puppeteer para reutilização, reduzindo o overhead de criar e destruir instâncias de navegador.

**Implementação**:

```python
class PuppeteerPool:
    def __init__(self, max_instances=3):
        self.max_instances = max_instances
        self.browsers = []
        self.in_use = set()
        self.lock = asyncio.Lock()
        
    async def get_browser(self):
        async with self.lock:
            # Tentar reutilizar um browser existente
            for browser in self.browsers:
                if browser not in self.in_use:
                    self.in_use.add(browser)
                    return browser
            
            # Criar novo browser se não exceder o limite
            if len(self.browsers) < self.max_instances:
                browser = await launch(headless=True, args=['--no-sandbox'])
                self.browsers.append(browser)
                self.in_use.add(browser)
                return browser
                
            # Esperar até que um browser esteja disponível
            while True:
                await asyncio.sleep(0.5)
                for browser in self.browsers:
                    if browser not in self.in_use:
                        self.in_use.add(browser)
                        return browser
    
    async def release_browser(self, browser):
        async with self.lock:
            if browser in self.in_use:
                self.in_use.remove(browser)
```

### 2. Scraping Adaptativo

**Descrição**: Implementar um sistema que escolhe o método de scraping mais eficiente para cada site.

**Implementação**:

```python
async def scrape_url(url: str, timeout: int = 30) -> Optional[str]:
    """
    Scrape a URL using the most efficient method available.
    """
    domain = urlparse(url).netloc
    
    # Decide qual método usar baseado no domínio
    if domain in JS_REQUIRED_DOMAINS:
        return await scrape_with_puppeteer(url, timeout)
    else:
        # Tentar primeiro com requests
        try:
            content = await scrape_with_requests(url, timeout)
            # Verificar se o conteúdo parece completo
            if content and len(content) > 1000:
                return content
        except Exception:
            pass
        
        # Fallback para Puppeteer se requests falhar
        return await scrape_with_puppeteer(url, timeout)
```

### 3. Otimização do Puppeteer

**Descrição**: Otimizar o uso do Puppeteer para reduzir o consumo de recursos.

**Implementação**:

```python
async def scrape_with_puppeteer(url: str, timeout: int = 30) -> Optional[str]:
    """Scrape a URL using Puppeteer."""
    browser = await puppeteer_pool.get_browser()
    try:
        page = await browser.newPage()
        
        # Bloquear recursos desnecessários
        await page.setRequestInterception(True)
        page.on('request', lambda req: asyncio.ensure_future(
            req.abort() if req.resourceType in ['stylesheet', 'font', 'image'] 
            else req.continue_()
        ))
        
        # Definir timeout
        await page.setDefaultNavigationTimeout(timeout * 1000)
        
        # Navegar para a página
        await page.goto(url, {'waitUntil': 'domcontentloaded'})
        
        # Obter o conteúdo
        content = await page.content()
        
        # Fechar a página
        await page.close()
        
        return content
    finally:
        await puppeteer_pool.release_browser(browser)
```

### 4. Paralelização com Controle de Concorrência

**Descrição**: Implementar scraping paralelo com controle de concorrência para otimizar o uso de recursos.

**Implementação**:

```python
class ParallelScraper:
    def __init__(self, max_concurrent=10, max_per_domain=3):
        self.max_concurrent = max_concurrent
        self.max_per_domain = max_per_domain
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.domain_semaphores = {}
        
    async def get_domain_semaphore(self, domain):
        if domain not in self.domain_semaphores:
            self.domain_semaphores[domain] = asyncio.Semaphore(self.max_per_domain)
        return self.domain_semaphores[domain]
    
    async def scrape_urls(self, urls: List[str]) -> Dict[str, str]:
        tasks = []
        for url in urls:
            task = asyncio.create_task(self._scrape_with_limits(url))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return dict(results)
    
    async def _scrape_with_limits(self, url: str) -> Tuple[str, str]:
        domain = urlparse(url).netloc
        domain_semaphore = await self.get_domain_semaphore(domain)
        
        # Adquirir ambos os semáforos
        async with self.semaphore:
            async with domain_semaphore:
                content = await scrape_url(url)
                return url, content
```

## Benefícios Esperados

A implementação dessas otimizações trará os seguintes benefícios:

1. **Redução no Uso de Memória**: O pool de instâncias Puppeteer reduzirá significativamente o uso de memória ao reutilizar instâncias de navegador.

2. **Melhoria no Tempo de Resposta**: A paralelização e o scraping adaptativo reduzirão o tempo total de scraping.

3. **Maior Confiabilidade**: O controle de concorrência e as técnicas adaptativas aumentarão a confiabilidade do processo de scraping.

4. **Melhor Utilização de Recursos**: A otimização do Puppeteer e o bloqueio de recursos desnecessários reduzirão o uso de CPU e memória.

## Métricas de Performance

Para medir o impacto das otimizações, monitoraremos as seguintes métricas:

1. **Tempo de Scraping**: Tempo médio para fazer scraping de uma página
2. **Uso de Memória**: Consumo de memória durante o scraping
3. **Uso de CPU**: Utilização de CPU durante o scraping
4. **Taxa de Sucesso**: Porcentagem de páginas scrapadas com sucesso
5. **Tempo Total de Geração**: Tempo total para gerar um MCP

## Conclusão

A otimização do web scraping é uma parte crucial da melhoria de performance do MCP Server. As técnicas e estratégias descritas neste documento permitirão reduzir significativamente o tempo de resposta e o uso de recursos, melhorando a experiência do usuário e permitindo que o servidor funcione de forma eficiente no plano gratuito do Render.
