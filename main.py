import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

import content_sourcing
import path_generator
from schemas import MCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp_server")

# Create FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Server that generates Master Content Plans (MCPs) based on topics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify the server is running."""
    return {"status": "ok"}


@app.get("/generate_mcp", response_model=MCP)
async def generate_mcp_endpoint(
    topic: str = Query(..., min_length=3, description="The topic to generate an MCP for"),
    max_resources: Optional[int] = Query(15, ge=5, le=30, description="Maximum number of resources to include")
):
    """
    Generate a Master Content Plan (MCP) for a given topic.
    
    This endpoint:
    1. Searches for relevant resources on the web
    2. Organizes them into a structured learning path
    3. Returns a complete MCP in JSON format
    """
    try:
        logger.info(f"Received request for topic: {topic}")
        
        # Find resources
        logger.info(f"Finding resources for topic: {topic}")
        resources = await content_sourcing.find_resources(topic, max_results=max_resources)
        
        if not resources:
            logger.warning(f"No resources found for topic: {topic}")
            raise HTTPException(status_code=404, detail=f"No resources found for topic: {topic}")
        
        logger.info(f"Found {len(resources)} resources for topic: {topic}")
        
        # Generate learning path
        logger.info(f"Generating learning path for topic: {topic}")
        mcp = path_generator.generate_learning_path(topic, resources)
        
        logger.info(f"Successfully generated MCP for topic: {topic}")
        return mcp
    
    except Exception as e:
        logger.error(f"Error generating MCP for topic {topic}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating MCP: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
