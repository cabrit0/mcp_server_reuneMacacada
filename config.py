"""
Configurações do MCP Server.

Este arquivo importa configurações do sistema modular em infrastructure/config/settings.py
para manter compatibilidade com código existente.
"""

from infrastructure.config import config

# Importar configurações do sistema modular
BASE_URL = config.get('BASE_URL')
PORT = config.get('PORT')
DEBUG = config.get('DEBUG')

# Configurações de cache
CACHE_TTL = config.get('CACHE', {}).get('ttl', {})

# Configurações de scraping
MAX_CONCURRENT_REQUESTS = config.get('SCRAPING', {}).get('max_concurrent_tasks', 10)
MAX_REQUESTS_PER_DOMAIN = 3  # Manter valor original se não existir no sistema modular
MAX_PUPPETEER_INSTANCES = config.get('SCRAPING', {}).get('puppeteer', {}).get('max_instances', 3)
