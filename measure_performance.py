"""
Script to measure MCP generation performance.
"""

import asyncio
import time
import json
import sys
import requests
from typing import Dict, Any, Optional


async def measure_mcp_generation(topic: str = "python", language: str = "en") -> None:
    """
    Measure the time it takes to generate an MCP.

    Args:
        topic: Topic to generate MCP for
        language: Language to use
    """
    print(f"Measuring MCP generation time for topic: {topic}, language: {language}")

    # Start timer
    start_time = time.time()

    # Generate MCP
    response = requests.post(f"http://localhost:8000/generate_mcp_async?topic={topic}&language={language}")
    if response.status_code != 200:
        print(f"Error generating MCP: {response.text}")
        return

    # Get task ID
    task_id = response.json().get("task_id")
    if not task_id:
        print("No task ID returned")
        print(f"Response: {response.text}")
        return

    print(f"Task ID: {task_id}")

    # Poll for completion
    completed = False
    result = None
    error = None

    while not completed:
        # Wait a bit
        await asyncio.sleep(2)

        # Check status
        status_response = requests.get(f"http://localhost:8000/status/{task_id}")
        if status_response.status_code != 200:
            print(f"Error checking status: {status_response.text}")
            continue

        # Parse response
        status_data = status_response.json()
        status = status_data.get("status")
        progress = status_data.get("progress", 0)

        # Print progress
        print(f"Status: {status}, Progress: {progress}%")

        # Check if completed
        if status == "completed":
            completed = True
            result = status_data.get("result")
        elif status == "failed":
            completed = True
            error = status_data.get("error")

        # Print latest message
        messages = status_data.get("messages", [])
        if messages:
            latest_message = messages[-1].get("message", "")
            print(f"Latest message: {latest_message}")

    # End timer
    end_time = time.time()
    total_time = end_time - start_time

    # Print results
    print("\n=== MCP Generation Complete ===")
    print(f"Total time: {total_time:.2f} seconds")

    if error:
        print(f"Error: {error}")
    elif result:
        # Print MCP stats
        try:
            # Check if result is already a dict
            if isinstance(result, dict):
                mcp = result
            elif isinstance(result, str):
                mcp = json.loads(result)
            else:
                print(f"Unexpected result type: {type(result)}")
                print(f"Result: {result}")
                return total_time

            # Check if nodes is a list or dict
            nodes = mcp.get("nodes", {})
            if isinstance(nodes, dict):
                nodes = list(nodes.values())
            resources = sum(1 for node in nodes if node.get("resources") and len(node.get("resources", [])) > 0)
            quizzes = sum(1 for node in nodes if node.get("quiz"))

            print(f"MCP Stats:")
            print(f"- Nodes: {len(nodes)}")
            print(f"- Nodes with resources: {resources}")
            print(f"- Nodes with quizzes: {quizzes}")
        except Exception as e:
            print(f"Error parsing MCP: {str(e)}")
            print(f"Result type: {type(result)}")
            print(f"Result: {result[:100]}..." if isinstance(result, str) and len(result) > 100 else f"Result: {result}")

    # Return total time
    return total_time


async def main() -> None:
    """Main function."""
    # Get topic from command line
    topic = sys.argv[1] if len(sys.argv) > 1 else "python"
    language = sys.argv[2] if len(sys.argv) > 2 else "en"

    # Measure MCP generation time
    await measure_mcp_generation(topic, language)


if __name__ == "__main__":
    asyncio.run(main())
