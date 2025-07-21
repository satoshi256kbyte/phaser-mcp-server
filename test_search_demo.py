#!/usr/bin/env python3
"""Demo script to test the search functionality."""

import asyncio
from phaser_mcp_server.client import PhaserDocsClient


async def test_search():
    """Test the search functionality."""
    client = PhaserDocsClient()
    
    try:
        await client.initialize()
        
        # Test search with a simple query
        print("Testing search for 'sprite'...")
        results = await client.search_content("sprite", limit=3)
        
        print(f"Found {len(results)} results:")
        for result in results:
            print(f"  {result.rank_order}. {result.title}")
            print(f"     URL: {result.url}")
            print(f"     Score: {result.relevance_score}")
            if result.snippet:
                print(f"     Snippet: {result.snippet[:100]}...")
            print()
            
    except Exception as e:
        print(f"Search test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_search())