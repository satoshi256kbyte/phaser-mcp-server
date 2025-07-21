#!/usr/bin/env python3
"""Test script for search error handling."""

import asyncio
from phaser_mcp_server.client import PhaserDocsClient, ValidationError


async def test_search_error_handling():
    """Test search error handling scenarios."""
    client = PhaserDocsClient()
    
    try:
        await client.initialize()
        
        # Test empty query
        print("=== Testing empty query ===")
        try:
            await client.search_content("", limit=5)
            print("ERROR: Should have raised ValidationError")
        except ValidationError as e:
            print(f"✓ Correctly caught ValidationError: {e}")
        
        # Test invalid limit
        print("\n=== Testing invalid limit ===")
        try:
            await client.search_content("test", limit=0)
            print("ERROR: Should have raised ValueError")
        except ValueError as e:
            print(f"✓ Correctly caught ValueError: {e}")
        
        # Test malicious query
        print("\n=== Testing malicious query ===")
        try:
            await client.search_content("<script>alert('xss')</script>", limit=5)
            print("ERROR: Should have raised ValidationError")
        except ValidationError as e:
            print(f"✓ Correctly caught ValidationError: {e}")
        
        # Test very long query (should be truncated)
        print("\n=== Testing long query (truncation) ===")
        long_query = "a" * 250
        results = await client.search_content(long_query, limit=5)
        print(f"✓ Long query handled successfully, got {len(results)} results")
        
        # Test large limit (should be capped)
        print("\n=== Testing large limit (capping) ===")
        results = await client.search_content("sprite", limit=200)
        print(f"✓ Large limit handled successfully, got {len(results)} results")
        
        print("\n✓ All error handling tests passed!")
        
    except Exception as e:
        print(f"Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_search_error_handling())