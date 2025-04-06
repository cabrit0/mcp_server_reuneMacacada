# MCP Server

A server that generates Master Content Plans (MCPs) based on topics. The server aggregates resources from the web and organizes them into structured learning paths.

## Features

- Generate learning paths for any topic (not just technology topics)
- Find relevant resources using web search and scraping
- Organize resources into a logical sequence with customizable number of nodes
- Support for multiple languages with focus on Portuguese
- Performance optimizations for Render's free tier
- Caching system for faster responses
- Return a standardized JSON structure for consumption by client applications
- **NEW**: TF-IDF based resource relevance filtering to ensure resources match the requested topic
- **NEW**: Strategic quiz distribution across learning trees for balanced learning experiences
- **NEW**: YouTube integration to include relevant videos in learning paths
- **NEW**: Category system to generate more specific content for different types of topics
- **NEW**: Asynchronous task system with real-time progress feedback to improve user experience and avoid timeouts
- **NEW**: Enhanced caching system for improved performance and faster response times
- **NEW**: Optimized web scraping techniques for better resource utilization

## Tech Stack

- Python 3.9+
- FastAPI
- Pyppeteer for JavaScript-heavy web scraping
- DuckDuckGo Search API
- BeautifulSoup for HTML parsing
- scikit-learn for TF-IDF based resource relevance filtering
- yt-dlp for YouTube video search and metadata extraction
- Redis (optional) for distributed caching
- msgpack for efficient data serialization

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/mcp_server.git
   cd mcp_server
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Install Chrome/Chromium for Pyppeteer (if not already installed)

## Usage

### Running Locally

1. Start the server using the provided batch file (Windows):

   ```
   run_local.bat
   ```

   Or manually with uvicorn:

   ```
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Access the API at `http://localhost:8000`

3. Generate an MCP by making a GET request to:

   ```
   GET /generate_mcp?topic=your_topic
   ```

4. Check the API documentation at `http://localhost:8000/docs`

### Production URL

The production server is available at:

```
https://reunemacacada.onrender.com
```

All endpoints documented in this README are available at both the local and production URLs.

### Testing the Caching System

1. Make a first request to generate an MCP (this will populate the cache):

   ```
   GET /generate_mcp?topic=python&num_nodes=15&language=pt
   ```

2. Make a second request with the same parameters (this should use the cache):

   ```
   GET /generate_mcp?topic=python&num_nodes=15&language=pt
   ```

   The second request should be significantly faster as the result will be retrieved from the cache.

## Documentation

Detailed documentation is available in the `docs` folder:

- [API Reference](docs/api_reference.md) - Detailed API documentation
- [Endpoints Reference](docs/endpoints_reference.md) - Complete reference of all endpoints
- [Flutter Integration](docs/flutter_integration.md) - Guide for integrating with Flutter apps
- [Async Tasks System](docs/async_tasks_system.md) - Documentation for the asynchronous task system
- [Performance Improvements](docs/performance_improvements.md) - Overview of performance optimizations
- [Caching System](docs/caching_system.md) - Documentation for the caching system
- [Web Scraping Optimization](docs/web_scraping_optimization.md) - Details on web scraping optimizations

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /generate_mcp?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&min_width={min_width}&max_width={max_width}&min_height={min_height}&max_height={max_height}&language={language}&category={category}` - Generate an MCP for the specified topic synchronously
  - `topic` (required): The topic to generate an MCP for (minimum 3 characters)
  - `max_resources` (optional): Maximum number of resources to include (default: 15, min: 5, max: 30)
  - `num_nodes` (optional): Number of nodes to include in the learning path (default: 15, min: 10, max: 30)
  - `min_width` (optional): Minimum width of the tree (nodes at first level) (default: 3, min: 2, max: 10)
  - `max_width` (optional): Maximum width at any level of the tree (default: 5, min: 3, max: 15)
  - `min_height` (optional): Minimum height of the tree (depth) (default: 3, min: 2, max: 8)
  - `max_height` (optional): Maximum height of the tree (depth) (default: 7, min: 3, max: 12)
  - `language` (optional): Language for resources (default: "pt")
  - `category` (optional): Category for the topic (e.g., "technology", "finance", "health"). If not provided, it will be detected automatically.
- `POST /generate_mcp_async?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&min_width={min_width}&max_width={max_width}&min_height={min_height}&max_height={max_height}&language={language}&category={category}` - Start asynchronous generation of an MCP
- `GET /status/{task_id}` - Check the status of an asynchronous task
- `GET /tasks` - List all tasks
- `POST /clear_cache?pattern={pattern}` - Clear the cache based on a pattern (e.g., "mcp:_" for all MCPs, "_" for all)

## Examples

### Basic usage (Portuguese)

```
GET /generate_mcp?topic=python
```

### Custom number of nodes

```
GET /generate_mcp?topic=machine+learning&num_nodes=20
```

### English language

```
GET /generate_mcp?topic=javascript&language=en
```

### Specify category manually

```
GET /generate_mcp?topic=python&category=technology
```

### Full customization

```
GET /generate_mcp?topic=história+do+brasil&max_resources=20&num_nodes=25&min_width=4&max_width=8&min_height=4&max_height=8&language=pt
```

### Control tree structure

```
GET /generate_mcp?topic=machine+learning&min_width=2&max_width=4&min_height=5&max_height=10
```

### Asynchronous generation

```
POST /generate_mcp_async?topic=inteligência+artificial&category=technology
```

### Check task status

```
GET /status/550e8400-e29b-41d4-a716-446655440000
```

### Clear cache

```
POST /clear_cache
```

### Clear specific cache

```
POST /clear_cache?pattern=mcp:*
```

## Deployment

The server can be deployed to various platforms:

### Using Docker

```
docker build -t mcp-server .
docker run -p 8080:8080 mcp-server
```

### Deploying to Render, Fly.io, or other platforms

Follow the platform-specific instructions for deploying a Docker container or a Python application.

## License

**Proprietary Software - All Rights Reserved**

This software is proprietary and confidential. Unauthorized copying, distribution, modification, public display, or public performance of this software is strictly prohibited. This software is intended for use under a paid subscription model only.

© 2024 ReuneMacacada. All rights reserved.

Last commit: v1.0.7 - Versão estável com sistema de cache otimizado, documentação de otimizações de performance e melhorias no web scraping
