import logging
from typing import Optional, List

from fastapi import FastAPI, Query, HTTPException, Path, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

import content_sourcing
import path_generator
from schemas import MCP, TaskInfo, TaskCreationResponse
from task_manager import task_manager
from simple_cache import simple_cache
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp_server")

# Usando o cache distribuído em vez do cache simples em memória

# Create FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Server that generates Master Content Plans (MCPs) based on topics",
    version="1.1.0"
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
    max_resources: Optional[int] = Query(15, ge=5, le=30, description="Maximum number of resources to include"),
    num_nodes: Optional[int] = Query(15, ge=10, le=30, description="Number of nodes to include in the learning path"),
    min_width: Optional[int] = Query(3, ge=2, le=10, description="Minimum width of the tree (nodes at first level)"),
    max_width: Optional[int] = Query(5, ge=3, le=15, description="Maximum width at any level of the tree"),
    min_height: Optional[int] = Query(3, ge=2, le=8, description="Minimum height of the tree (depth)"),
    max_height: Optional[int] = Query(7, ge=3, le=12, description="Maximum height of the tree (depth)"),
    language: Optional[str] = Query("pt", description="Language for resources (e.g., 'pt', 'en', 'es')"),
    category: Optional[str] = Query(None, description="Category for the topic (e.g., 'technology', 'finance', 'health'). If not provided, it will be detected automatically.")
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

        # Check cache first
        cache_key = f"mcp:{topic}_{max_resources}_{num_nodes}_{language}_{category}"
        cached_mcp = simple_cache.get(cache_key)
        if cached_mcp:
            logger.info(f"Returning cached MCP for topic: {topic}")
            return MCP(**cached_mcp)

        # Find resources
        logger.info(f"Finding resources for topic: {topic} in language: {language}")
        resources = await content_sourcing.find_resources(topic, max_results=max_resources, language=language, category=category)

        if not resources:
            logger.warning(f"No resources found for topic: {topic}")
            raise HTTPException(status_code=404, detail=f"No resources found for topic: {topic}")

        logger.info(f"Found {len(resources)} resources for topic: {topic}")

        # Generate learning path
        logger.info(f"Generating learning path for topic: {topic} with {num_nodes} nodes")
        try:
            mcp = await path_generator.generate_learning_path(
                topic, resources,
                min_nodes=num_nodes, max_nodes=num_nodes+10,
                min_width=min_width, max_width=max_width,
                min_height=min_height, max_height=max_height,
                category=category, language=language
            )

            # Cache the result
            simple_cache.setex(cache_key, 2592000, mcp.model_dump())  # 30 dias
        except ValueError as ve:
            logger.warning(f"Could not generate enough nodes: {str(ve)}")
            raise HTTPException(status_code=400, detail=str(ve))

        logger.info(f"Successfully generated MCP for topic: {topic}")
        return mcp

    except Exception as e:
        logger.error(f"Error generating MCP for topic {topic}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating MCP: {str(e)}")


@app.post("/generate_mcp_async", response_model=TaskCreationResponse)
async def generate_mcp_async_endpoint(
    background_tasks: BackgroundTasks,
    topic: str = Query(..., min_length=3, description="The topic to generate an MCP for"),
    max_resources: Optional[int] = Query(15, ge=5, le=30, description="Maximum number of resources to include"),
    num_nodes: Optional[int] = Query(15, ge=10, le=30, description="Number of nodes to include in the learning path"),
    min_width: Optional[int] = Query(3, ge=2, le=10, description="Minimum width of the tree (nodes at first level)"),
    max_width: Optional[int] = Query(5, ge=3, le=15, description="Maximum width at any level of the tree"),
    min_height: Optional[int] = Query(3, ge=2, le=8, description="Minimum height of the tree (depth)"),
    max_height: Optional[int] = Query(7, ge=3, le=12, description="Maximum height of the tree (depth)"),
    language: Optional[str] = Query("pt", description="Language for resources (e.g., 'pt', 'en', 'es')"),
    category: Optional[str] = Query(None, description="Category for the topic (e.g., 'technology', 'finance', 'health'). If not provided, it will be detected automatically.")
):
    """
    Generate a Master Content Plan (MCP) for a given topic asynchronously.

    This endpoint:
    1. Creates a background task to generate the MCP
    2. Returns immediately with a task ID
    3. The client can check the task status using the /status/{task_id} endpoint
    """
    logger.info(f"Received async request for topic: {topic}")

    # Check cache first
    cache_key = f"mcp:{topic}_{max_resources}_{num_nodes}_{min_width}_{max_width}_{min_height}_{max_height}_{language}_{category}"
    cached_mcp = simple_cache.get(cache_key)
    if cached_mcp:
        logger.info(f"Found cached MCP for topic: {topic}")
        # Create a completed task with the cached result
        task = task_manager.create_task(f"Generate MCP for topic: {topic}")
        # Usar o resultado do cache diretamente
        task.mark_as_completed(cached_mcp)
        return TaskCreationResponse(task_id=task.id, message="Task completed immediately (cached result)")

    # Create a new task
    task = task_manager.create_task(f"Generate MCP for topic: {topic}")

    # Add the task to background tasks
    background_tasks.add_task(
        process_mcp_generation,
        task_id=task.id,
        topic=topic,
        max_resources=max_resources,
        num_nodes=num_nodes,
        min_width=min_width,
        max_width=max_width,
        min_height=min_height,
        max_height=max_height,
        language=language,
        category=category
    )

    return TaskCreationResponse(task_id=task.id)


@app.get("/status/{task_id}", response_model=TaskInfo)
async def get_task_status(task_id: str = Path(..., description="The ID of the task to check")):
    """
    Get the status of a task.

    Args:
        task_id: The ID of the task to check

    Returns:
        Information about the task
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

    return task.to_dict()


@app.get("/tasks", response_model=List[TaskInfo])
async def list_tasks():
    """
    List all tasks.

    Returns:
        List of all tasks
    """
    return [task.to_dict() for task in task_manager.tasks.values()]


@app.get("/cache_stats")
async def get_cache_stats():
    """
    Get cache statistics.

    This endpoint returns statistics about the cache, including the number of items in the cache
    and information about the domain method cache that stores which scraping method works best for each domain.

    Returns:
        Dictionary with cache statistics.
    """
    try:
        # Obter estatísticas do cache principal
        cache_info = simple_cache.info()
        cache_keys = simple_cache.keys("*")

        # Obter estatísticas do cache de métodos por domínio
        from content_scraper import get_domain_method_cache_stats
        domain_cache_stats = get_domain_method_cache_stats()

        return {
            "status": "success",
            "cache": {
                "total_keys": len(cache_keys),
                "info": cache_info
            },
            "domain_method_cache": domain_cache_stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting cache stats: {str(e)}"
        }


@app.post("/clear_cache")
async def clear_cache(pattern: Optional[str] = Query("*", description="Pattern to match cache keys (e.g., 'mcp:*' for all MCPs, 'search:*' for all search results, '*' for all)"), clear_domain_cache: bool = Query(False, description="Whether to also clear the domain method cache")):
    """
    Clear the cache.

    This endpoint allows clearing the cache based on a pattern. Use with caution as it will remove cached data.

    Args:
        pattern: Pattern to match cache keys. Default is "*" which clears all cache.
                Examples: "mcp:*" for all MCPs, "search:*" for all search results.
        clear_domain_cache: Whether to also clear the domain method cache that stores which scraping method works best for each domain.

    Returns:
        Dictionary with count of items cleared and message.
    """
    try:
        # Limpar o cache principal
        count = simple_cache.clear(pattern)
        logger.info(f"Cleared {count} items from cache matching pattern: {pattern}")

        # Limpar o cache de métodos por domínio se solicitado
        domain_cache_cleared = 0
        if clear_domain_cache:
            from content_scraper import clear_domain_method_cache
            domain_cache_cleared = clear_domain_method_cache()
            logger.info(f"Cleared domain method cache")

        return {
            "status": "success",
            "message": f"Cleared {count} items from cache" + (", including domain method cache" if clear_domain_cache else ""),
            "pattern": pattern,
            "count": count,
            "domain_cache_cleared": domain_cache_cleared
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return {
            "status": "error",
            "message": f"Error clearing cache: {str(e)}"
        }


async def process_mcp_generation(
    task_id: str,
    topic: str,
    max_resources: int,
    num_nodes: int,
    min_width: int,
    max_width: int,
    min_height: int,
    max_height: int,
    language: str,
    category: Optional[str] = None
):
    """
    Process MCP generation in the background.

    Args:
        task_id: The ID of the task
        topic: The topic to generate an MCP for
        max_resources: Maximum number of resources to include
        num_nodes: Number of nodes to include in the learning path
        language: Language for resources
        category: Category for the topic
    """
    task = task_manager.get_task(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return

    try:
        # Update task status
        task.mark_as_running()
        task.update_progress(10, "Iniciando busca de recursos")

        # Find resources
        resources = await content_sourcing.find_resources(
            topic, max_results=max_resources, language=language, category=category
        )

        if not resources:
            task.mark_as_failed(f"No resources found for topic: {topic}")
            return

        task.update_progress(40, f"Encontrados {len(resources)} recursos para o tópico: {topic}")

        # Generate learning path
        task.update_progress(50, "Gerando árvore de aprendizagem")
        try:
            mcp = await path_generator.generate_learning_path(
                topic, resources,
                min_nodes=num_nodes, max_nodes=num_nodes+10,
                min_width=min_width, max_width=max_width,
                min_height=min_height, max_height=max_height,
                category=category, language=language
            )

            # Cache the result
            cache_key = f"mcp:{topic}_{max_resources}_{num_nodes}_{min_width}_{max_width}_{min_height}_{max_height}_{language}_{category}"
            simple_cache.setex(cache_key, 2592000, mcp.model_dump())  # 30 dias

            task.update_progress(90, "Finalizando geração do MCP")

            # Mark task as completed with the MCP as result
            # Usar model_dump() para compatibilidade com versões mais recentes do Pydantic
            task.mark_as_completed(mcp.model_dump())
            logger.info(f"Task {task_id} completed successfully")

        except ValueError as ve:
            task.mark_as_failed(f"Could not generate enough nodes: {str(ve)}")
            logger.warning(f"Task {task_id} failed: {str(ve)}")

    except Exception as e:
        task.mark_as_failed(f"Error generating MCP: {str(e)}")
        logger.error(f"Task {task_id} failed with error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Use configurações do arquivo config.py
    port = config.PORT
    debug = config.DEBUG

    print(f"Iniciando MCP Server na porta {port}")
    print(f"URL base: {config.BASE_URL}")
    print(f"Modo de depuração: {'Ativado' if debug else 'Desativado'}")
    print("")
    print("O servidor estará disponível em:")
    print(f"  - Local: http://localhost:{port}")
    print(f"  - Rede: http://0.0.0.0:{port}")
    print("")
    print("Pressione Ctrl+C para encerrar o servidor")

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)
