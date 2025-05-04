# This file is part of the MCP Server package.

from services.search.search_service import SearchService
from services.search.search_factory import SearchFactory

# Create a global search instance
search: SearchService = SearchFactory.create_search("default")

__all__ = ["search", "SearchService", "SearchFactory"]
