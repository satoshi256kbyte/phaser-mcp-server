#!/usr/bin/env python3
"""Test script for MCP search tool integration."""

import asyncio
from unittest.mock import Mock
from phaser_mcp_server.server import search_documentation


async def test_mcp_search():
    """Test the MCP search_documentation tool."""
    # Create a mock context
    mock_context = Mock()
    
    try:
        print("Testing MCP search_documentation tool...")
        
        # Test search for 'sprite'
        print("\n=== Testing search for 'sprite' ===")
        results = await search_documentation(mock_context, "sprite", limit=3)
        
        print(f"Results type: {type(results)}")
        print(f"Number of results: {len(results)}")
        
        for result in results:
            print(f"Result: {result}")
            
        # Test search with no results
        print("\n=== Testing search for 'nonexistent' ===")
        results = await search_documentation(mock_context, "nonexistent", limit=3)
        print(f"Number of results: {len(results)}")
        
        # Test invalid parameters
        print("\n=== Testing invalid parameters ===")
        try:
            await search_documentation(mock_context, "", limit=3)
            print("ERROR: Should have raised ValueError for empty query")
        except RuntimeError as e:
            print(f"Correctly caught error: {e}")
            
    except Exception as e:
        print(f"MCP search test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_search())