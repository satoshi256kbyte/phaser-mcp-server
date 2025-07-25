"""Phaser MCP Server - Model Context Protocol server for Phaser game engine docs.

This package provides MCP tools for accessing Phaser documentation, API references,
and tutorials to assist game developers using AI assistants.
"""

__version__ = "1.0.0"
__author__ = "Phaser MCP Server Team"
__description__ = "MCP Server for Phaser Game Engine Documentation"

# Import utility functions
from phaser_mcp_server.utils import get_memory_usage

# Package metadata
__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "get_memory_usage",
]
