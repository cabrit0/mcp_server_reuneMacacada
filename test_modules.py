import asyncio
import json
from typing import List

import content_sourcing
import path_generator
from schemas import Resource, MCP


async def test_content_sourcing(topic: str = "Python programming") -> List[Resource]:
    """Test the content_sourcing module by finding resources for a topic."""
    print(f"Finding resources for topic: {topic}")
    resources = await content_sourcing.find_resources(topic, max_results=5)

    print(f"Found {len(resources)} resources:")
    for i, resource in enumerate(resources, 1):
        print(f"{i}. {resource.title} ({resource.type}): {resource.url}")

    return resources


def test_path_generator(resources: List[Resource], topic: str = "Python programming") -> MCP:
    """Test the path_generator module by generating a learning path."""
    print(f"\nGenerating learning path for topic: {topic}")

    try:
        # Test resource grouping first
        print("Testing resource grouping...")
        resource_groups = path_generator.group_resources(topic, resources)
        print(f"Resource groups created: {list(resource_groups.keys())}")

        # Now test the full path generation
        print("Generating full learning path...")
        mcp = path_generator.generate_learning_path(topic, resources)

        print(f"Generated MCP with ID: {mcp.id}")
        print(f"Title: {mcp.title}")
        print(f"Description: {mcp.description}")
        print(f"Root Node ID: {mcp.rootNodeId}")
        print(f"Number of nodes: {len(mcp.nodes)}")

        print("\nNodes:")
        for node_id, node in mcp.nodes.items():
            print(f"- {node.title} ({node.type}): {len(node.resources)} resources")

        return mcp
    except Exception as e:
        import traceback
        print(f"Error in path_generator: {str(e)}")
        print(traceback.format_exc())
        return None


async def main():
    """Run the tests."""
    topic = "Python programming"

    try:
        # Test content_sourcing
        resources = await test_content_sourcing(topic)

        if resources:
            # Test path_generator
            mcp = test_path_generator(resources, topic)

            # Convert to JSON and pretty print
            mcp_json = mcp.model_dump_json(indent=2)
            print("\nMCP JSON (truncated):")
            print(mcp_json[:500] + "...")

            # Save to file for inspection
            with open("test_mcp.json", "w") as f:
                f.write(mcp_json)
            print("\nFull MCP saved to test_mcp.json")
        else:
            print("No resources found, cannot test path_generator")

    except Exception as e:
        print(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
