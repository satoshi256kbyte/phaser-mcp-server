#!/usr/bin/env python3
"""Test script to check real Phaser documentation URLs."""

import asyncio

import httpx


async def test_urls():
    """Test various Phaser documentation URLs."""
    urls_to_test = [
        "https://docs.phaser.io/",
        "https://docs.phaser.io/phaser/",
        "https://docs.phaser.io/api/",
        "https://phaser.io/tutorials/",
        "https://phaser.io/examples/",
    ]

    async with httpx.AsyncClient() as client:
        for url in urls_to_test:
            try:
                response = await client.head(url, timeout=10)
                print(f"✓ {url} - Status: {response.status_code}")
            except Exception as e:
                print(f"✗ {url} - Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_urls())
