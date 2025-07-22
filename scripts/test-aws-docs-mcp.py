"""
Test script for the AWS Documentation MCP server.

This script demonstrates how to use the AWS Documentation MCP server to search for
and read AWS documentation.
"""

import asyncio
import json
from mcp.client import MCPClient

async def main():
    # Create an MCP client
    client = MCPClient()
    
    # Connect to the AWS Documentation MCP server
    process = await client.connect_to_server(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"],
        env={"FASTMCP_LOG_LEVEL": "ERROR", "AWS_DOCUMENTATION_PARTITION": "aws"}
    )
    
    try:
        # Wait for the server to start
        print("Waiting for server to start...")
        await asyncio.sleep(2)
        
        # Get the available tools
        tools = await client.list_tools()
        print(f"Available tools: {json.dumps(tools, indent=2)}")
        
        # Search for documentation about S3 buckets
        print("\nSearching for documentation about S3 buckets...")
        search_results = await client.call_tool(
            "search_documentation",
            {"search_phrase": "S3 bucket creation", "limit": 5}
        )
        print(f"Search results: {json.dumps(search_results, indent=2)}")
        
        # Read documentation from the first search result
        if search_results:
            first_result = search_results[0]
            print(f"\nReading documentation from: {first_result['title']}")
            doc_content = await client.call_tool(
                "read_documentation",
                {"url": first_result['url']}
            )
            print(f"Documentation content (first 500 chars): {doc_content[:500]}...")
            
            # Get recommendations for this document
            print(f"\nGetting recommendations for: {first_result['title']}")
            recommendations = await client.call_tool(
                "recommend",
                {"url": first_result['url']}
            )
            print(f"Recommendations: {json.dumps(recommendations, indent=2)}")
    
    finally:
        # Disconnect from the server
        print("\nDisconnecting from server...")
        await client.disconnect()
        process.terminate()
        await process.wait()
        print("Server terminated.")

if __name__ == "__main__":
    asyncio.run(main())