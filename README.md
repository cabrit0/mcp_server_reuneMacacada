# MCP Server

A server that generates Master Content Plans (MCPs) based on topics. The server aggregates resources from the web and organizes them into structured learning paths.

## Features

- Generate learning paths for any topic
- Find relevant resources using web search and scraping
- Organize resources into a logical sequence
- Return a standardized JSON structure for consumption by client applications

## Tech Stack

- Python 3.9+
- FastAPI
- Pyppeteer for JavaScript-heavy web scraping
- DuckDuckGo Search API
- BeautifulSoup for HTML parsing

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
- `GET /generate_mcp?topic={topic}` - Generate an MCP for the specified topic

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

privada
