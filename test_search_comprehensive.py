#!/usr/bin/env python3
"""Comprehensive test script for search functionality."""

import asyncio

from phaser_mcp_server.client import PhaserDocsClient


async def test_search_queries():
    """Test various search queries."""
    client = PhaserDocsClient()

    test_queries = [
        "sprite",
        "physics",
        "input keyboard",
        "animation tween",
        "getting started",
        "camera zoom",
        "nonexistent term",
    ]

    try:
        await client.initialize()

        for query in test_queries:
            print(f"\n=== Testing search for: '{query}' ===")
            results = await client.search_content(query, limit=3)

            if results:
                print(f"Found {len(results)} results:")
                for result in results:
                    print(f"  {result.rank_order}. {result.title}")
                    print(f"     Score: {result.relevance_score}")
                    print(f"     Snippet: {result.snippet}")
            else:
                print("No results found.")

    except Exception as e:
        print(f"Search test failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_search_queries())
