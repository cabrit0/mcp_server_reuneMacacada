"""
Configurações do MCP Server.
"""

import os

# URL base do servidor
# Em produção: https://reunemacacada.onrender.com
# Em desenvolvimento: http://localhost:8000
BASE_URL = os.environ.get('MCP_BASE_URL', 'https://reunemacacada.onrender.com')

# Porta do servidor
# Em produção: definida pelo Render via variável de ambiente PORT
# Em desenvolvimento: 8000 (padrão)
PORT = int(os.environ.get('PORT', 8000))

# Modo de depuração
# Em produção: False
# Em desenvolvimento: True
DEBUG = os.environ.get('MCP_DEBUG', 'False').lower() == 'true'

# Configurações de cache
CACHE_TTL = {
    'search_results': 86400,    # 1 dia
    'page_content': 604800,     # 1 semana
    'mcp_results': 2592000,     # 30 dias
    'default': 86400            # 1 dia (padrão)
}

# Configurações de scraping
MAX_CONCURRENT_REQUESTS = 10
MAX_REQUESTS_PER_DOMAIN = 3
MAX_PUPPETEER_INSTANCES = 3
