"""
Default configuration settings for the MCP Server.
"""

import os
from typing import Dict, Any

# Base URL of the server
# In production: https://reunemacacada.onrender.com
# In development: http://localhost:8000
BASE_URL = os.environ.get('MCP_BASE_URL', 'https://reunemacacada.onrender.com')

# Server port
# In production: defined by Render via PORT environment variable
# In development: 8000 (default)
PORT = int(os.environ.get('PORT', 8000))

# Debug mode
# In production: False
# In development: True
DEBUG = os.environ.get('MCP_DEBUG', 'False').lower() == 'true'

# Cache settings
CACHE = {
    'type': 'memory',  # 'memory' or 'redis'
    'max_size': 1000,
    'ttl': {
        'search_results': 86400,    # 1 day
        'page_content': 604800,     # 1 week
        'mcp_results': 2592000,     # 30 days
        'default': 86400            # 1 day (default)
    }
}

# Logging settings
LOGGING = {
    'level': os.environ.get('LOG_LEVEL', 'INFO'),
    'log_file': os.environ.get('LOG_FILE', None),
    'max_bytes': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5
}

# Search settings
SEARCH = {
    'default_engine': 'fallback',  # Changed from 'duckduckgo' to 'fallback' to use both engines
    'max_results_default': int(os.environ.get('MAX_RESOURCES_DEFAULT', 15)),
    'min_results': 5,
    'max_results': 30,
    'timeout': 15,  # seconds
    'rate_limit': {
        'requests_per_minute': 10
    },
    'brave_api_key': os.environ.get('BRAVE_API_KEY', None)  # Added Brave Search API key
}

# Scraping settings
SCRAPING = {
    'timeout_default': 8,  # seconds
    'max_concurrent_tasks': 5,
    'user_agent': 'MCPBot/1.0 (+https://mcp-server.example.com/bot-info)',
    'puppeteer': {
        'max_instances': 3,
        'timeout': 30,  # seconds
        'stealth': True,
        'executable_path': os.environ.get('CHROME_EXECUTABLE_PATH', None),
        'download_chromium': os.environ.get('PUPPETEER_DOWNLOAD_CHROMIUM', 'False').lower() == 'true'
    }
}

# YouTube settings
YOUTUBE = {
    'max_results': int(os.environ.get('YOUTUBE_MAX_RESULTS', 5)),
    'timeout': 15,  # seconds
    'api_key': os.environ.get('YOUTUBE_API_KEY', None)
}

# MCP generation settings
MCP = {
    'min_nodes_default': int(os.environ.get('MIN_NODES_DEFAULT', 15)),
    'min_nodes': 10,
    'max_nodes': 30,
    'default_language': os.environ.get('DEFAULT_LANGUAGE', 'pt')
}

# Task manager settings
TASK_MANAGER = {
    'max_tasks': 100,
    'task_timeout': 300,  # seconds
    'cleanup_interval': 3600  # seconds
}

# API settings
API = {
    'rate_limit': {
        'requests_per_minute': 60
    },
    'cors': {
        'allow_origins': ['*'],  # In production, replace with specific origins
        'allow_methods': ['*'],
        'allow_headers': ['*']
    }
}
