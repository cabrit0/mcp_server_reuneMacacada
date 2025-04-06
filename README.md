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

## Tech Stack

- Python 3.9+
- FastAPI
- Pyppeteer for JavaScript-heavy web scraping
- DuckDuckGo Search API
- BeautifulSoup for HTML parsing
- scikit-learn for TF-IDF based resource relevance filtering
- yt-dlp for YouTube video search and metadata extraction

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

1. Start the server:

   ```
   uvicorn main:app --reload
   ```

2. Access the API at `http://localhost:8000`

3. Generate an MCP by making a GET request to:

   ```
   GET /generate_mcp?topic=your_topic
   ```

4. Check the API documentation at `http://localhost:8000/docs`

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /generate_mcp?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&language={language}&category={category}` - Generate an MCP for the specified topic
  - `topic` (required): The topic to generate an MCP for (minimum 3 characters)
  - `max_resources` (optional): Maximum number of resources to include (default: 15, min: 5, max: 30)
  - `num_nodes` (optional): Number of nodes to include in the learning path (default: 15, min: 10, max: 30)
  - `language` (optional): Language for resources (default: "pt")
  - `category` (optional): Category for the topic (e.g., "technology", "finance", "health"). If not provided, it will be detected automatically.

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
GET /generate_mcp?topic=história+do+brasil&max_resources=20&num_nodes=25&language=pt
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

Last commit: v1.0.0 - Versão estável com integração YouTube e sistema de categorias
