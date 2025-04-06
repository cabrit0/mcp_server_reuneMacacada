"""
Pool de instâncias Puppeteer para otimizar o web scraping.
"""

import asyncio
import logging
from pyppeteer import launch
from typing import Dict, List, Optional

class PuppeteerPool:
    def __init__(self, max_instances=3, max_idle_time=300):
        """
        Inicializa o pool de instâncias Puppeteer.
        
        Args:
            max_instances: Número máximo de instâncias de navegador
            max_idle_time: Tempo máximo de ociosidade em segundos
        """
        self.max_instances = max_instances
        self.max_idle_time = max_idle_time  # segundos
        self.browsers = []
        self.in_use = set()
        self.lock = asyncio.Lock()
        self.last_used = {}
        
    async def get_browser(self):
        """
        Obtém uma instância de navegador do pool.
        
        Returns:
            Instância de navegador Puppeteer
        """
        async with self.lock:
            # Tentar reutilizar um navegador existente
            for browser in self.browsers:
                if browser not in self.in_use:
                    self.in_use.add(browser)
                    self.last_used[browser] = asyncio.get_event_loop().time()
                    return browser
            
            # Criar novo navegador se não exceder o limite
            if len(self.browsers) < self.max_instances:
                browser = await launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', 
                          '--disable-dev-shm-usage', '--disable-gpu'],
                    ignoreHTTPSErrors=True
                )
                self.browsers.append(browser)
                self.in_use.add(browser)
                self.last_used[browser] = asyncio.get_event_loop().time()
                return browser
                
            # Esperar até que um navegador esteja disponível
            while True:
                await asyncio.sleep(0.5)
                for browser in self.browsers:
                    if browser not in self.in_use:
                        self.in_use.add(browser)
                        self.last_used[browser] = asyncio.get_event_loop().time()
                        return browser
    
    async def release_browser(self, browser):
        """
        Libera um navegador de volta para o pool.
        
        Args:
            browser: Instância de navegador a ser liberada
        """
        async with self.lock:
            if browser in self.in_use:
                self.in_use.remove(browser)
                self.last_used[browser] = asyncio.get_event_loop().time()
    
    async def cleanup_idle_browsers(self):
        """Fecha navegadores ociosos para liberar memória"""
        current_time = asyncio.get_event_loop().time()
        async with self.lock:
            for browser in list(self.browsers):
                if (browser not in self.in_use and 
                    current_time - self.last_used.get(browser, 0) > self.max_idle_time):
                    await browser.close()
                    self.browsers.remove(browser)
                    self.last_used.pop(browser, None)
                    logging.info("Fechou instância de navegador ociosa")
    
    async def close_all(self):
        """Fecha todos os navegadores ao encerrar o aplicativo"""
        async with self.lock:
            for browser in self.browsers:
                try:
                    await browser.close()
                except:
                    pass
            self.browsers = []
            self.in_use = set()
            self.last_used = {}

# Instância global
puppeteer_pool = PuppeteerPool()
