"""Phaser MCP Server - Main server implementation.

This module implements the MCP server for Phaser game engine documentation access.
It provides tools for reading documentation, searching content, and accessing
API references.
"""

import asyncio
import os
import sys
from typing import Any

from loguru import logger
from mcp.server.fastmcp import Context, FastMCP

from .client import PhaserDocsClient
from .parser import PhaserDocumentParser


class PhaserMCPServer:
    """Main MCP server class for Phaser documentation access."""

    def __init__(self) -> None:
        """Initialize the Phaser MCP server."""
        self._setup_logging()
        self._load_environment_variables()
        self.client = PhaserDocsClient()
        self.parser = PhaserDocumentParser()
        logger.info("Phaser MCP Server initialized")

    def _setup_logging(self) -> None:
        """Configure logging based on environment variables."""
        # Remove default logger
        logger.remove()

        # Get log level from environment variable
        log_level = os.getenv("FASTMCP_LOG_LEVEL", "INFO").upper()

        # Validate log level
        valid_levels = [
            "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
        ]
        if log_level not in valid_levels:
            log_level = "INFO"

        # Configure logger with structured output
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:"
                   "<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

        logger.info(f"Logging configured with level: {log_level}")

    def _load_environment_variables(self) -> None:
        """Load and validate environment variables."""
        # Log level (already handled in _setup_logging)
        log_level = os.getenv("FASTMCP_LOG_LEVEL", "INFO")
        logger.debug(f"Environment variable FASTMCP_LOG_LEVEL: {log_level}")

        # Request timeout configuration
        timeout_str = os.getenv("PHASER_DOCS_TIMEOUT", "30")
        try:
            timeout = int(timeout_str)
            if timeout <= 0:
                raise ValueError("Timeout must be positive")
            logger.debug(f"Request timeout set to: {timeout} seconds")
        except ValueError as e:
            logger.warning(
                f"Invalid PHASER_DOCS_TIMEOUT value '{timeout_str}': {e}. "
                "Using default value of 30 seconds."
            )

        # Max retries configuration
        retries_str = os.getenv("PHASER_DOCS_MAX_RETRIES", "3")
        try:
            retries = int(retries_str)
            if retries < 0:
                raise ValueError("Max retries must be non-negative")
            logger.debug(f"Max retries set to: {retries}")
        except ValueError as e:
            logger.warning(
                f"Invalid PHASER_DOCS_MAX_RETRIES value '{retries_str}': {e}. "
                "Using default value of 3."
            )

        # Cache TTL configuration (for future use)
        cache_ttl_str = os.getenv("PHASER_DOCS_CACHE_TTL", "3600")
        try:
            cache_ttl = int(cache_ttl_str)
            if cache_ttl < 0:
                raise ValueError("Cache TTL must be non-negative")
            logger.debug(f"Cache TTL set to: {cache_ttl} seconds")
        except ValueError as e:
            logger.warning(
                f"Invalid PHASER_DOCS_CACHE_TTL value '{cache_ttl_str}': {e}. "
                "Using default value of 3600 seconds."
            )

    async def initialize(self) -> None:
        """Initialize server components with proper error handling."""
        try:
            logger.info("Initializing server components...")

            # Initialize HTTP client
            await self.client.initialize()
            logger.debug("HTTP client initialized successfully")

            # Validate client connectivity (optional health check)
            try:
                await self.client.health_check()
                logger.debug("Client health check passed")
            except Exception as e:
                logger.warning(f"Client health check failed: {e}")
                # Continue initialization as this is not critical

            logger.info("Server components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize server components: {e}")
            # Re-raise with more context
            raise RuntimeError(
                f"Server initialization failed: {str(e)}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up server resources with comprehensive error handling."""
        logger.info("Starting server cleanup...")

        cleanup_errors = []

        # Cleanup HTTP client
        try:
            if hasattr(self, 'client') and self.client:
                await self.client.close()
                logger.debug("HTTP client closed successfully")
        except Exception as e:
            error_msg = f"Error closing HTTP client: {e}"
            logger.error(error_msg)
            cleanup_errors.append(error_msg)

        # Additional cleanup for parser if needed
        try:
            if hasattr(self, 'parser') and self.parser:
                # Parser cleanup if it has any resources to clean
                if hasattr(self.parser, 'cleanup'):
                    await self.parser.cleanup()
                logger.debug("Parser cleanup completed")
        except Exception as e:
            error_msg = f"Error during parser cleanup: {e}"
            logger.error(error_msg)
            cleanup_errors.append(error_msg)

        if cleanup_errors:
            logger.warning(
                f"Server cleanup completed with {len(cleanup_errors)} errors"
            )
        else:
            logger.info("Server cleanup completed successfully")

    def get_server_info(self) -> dict[str, Any]:
        """Get server information and status."""
        return {
            "name": "phaser-mcp-server",
            "version": "1.0.0",
            "status": "running",
            "log_level": os.getenv("FASTMCP_LOG_LEVEL", "INFO"),
            "environment_variables": {
                "FASTMCP_LOG_LEVEL": os.getenv("FASTMCP_LOG_LEVEL", "INFO"),
                "PHASER_DOCS_TIMEOUT": os.getenv("PHASER_DOCS_TIMEOUT", "30"),
                "PHASER_DOCS_MAX_RETRIES": os.getenv(
                    "PHASER_DOCS_MAX_RETRIES", "3"
                ),
                "PHASER_DOCS_CACHE_TTL": os.getenv(
                    "PHASER_DOCS_CACHE_TTL", "3600"
                ),
            }
        }


# Create FastMCP server instance with proper configuration
def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""
    try:
        # Create FastMCP server with proper name
        mcp_server = FastMCP("phaser-mcp-server")

        # Log server creation
        logger.debug("FastMCP server instance created")

        return mcp_server

    except Exception as e:
        logger.error(f"Failed to create FastMCP server: {e}")
        raise RuntimeError(f"FastMCP server creation failed: {str(e)}") from e


# Initialize server instances
mcp = create_mcp_server()
server = PhaserMCPServer()


@mcp.tool()
async def read_documentation(
    ctx: Context,
    url: str,
    max_length: int = 5000,
    start_index: int = 0,
) -> str:
    """Read Phaser documentation from a specific URL.

    Args:
        ctx: MCP context
        url: URL of the Phaser documentation page to read
        max_length: Maximum length of content to return (default: 5000)
        start_index: Starting index for pagination (default: 0)

    Returns:
        Markdown-formatted documentation content

    Raises:
        ValueError: If URL is invalid or parameters are out of range
        RuntimeError: If documentation cannot be retrieved
    """
    logger.info(f"Reading documentation from URL: {url}")

    try:
        # Validate parameters
        if max_length <= 0:
            raise ValueError("max_length must be positive")
        if start_index < 0:
            raise ValueError("start_index must be non-negative")

        # Fetch and parse documentation
        page = await server.client.get_page_content(url)
        parsed_content = server.parser.parse_html_content(page.content, url)
        markdown_content = server.parser.convert_to_markdown(parsed_content)

        # Apply pagination
        if start_index >= len(markdown_content):
            return ""

        end_index = min(start_index + max_length, len(markdown_content))
        paginated_content = markdown_content[start_index:end_index]

        logger.info(
            f"Successfully read documentation: {len(paginated_content)} characters"
        )
        return paginated_content

    except Exception as e:
        logger.error(f"Failed to read documentation from {url}: {e}")
        raise RuntimeError(f"Failed to read documentation: {str(e)}") from e


@mcp.tool()
async def search_documentation(
    ctx: Context,
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search Phaser documentation for specific content.

    Args:
        ctx: MCP context
        query: Search query string
        limit: Maximum number of results to return (default: 10)

    Returns:
        List of search results with title, URL, and snippet

    Raises:
        ValueError: If query is empty or limit is invalid
        RuntimeError: If search cannot be performed
    """
    logger.info(f"Searching documentation for query: {query}")

    try:
        # Validate parameters
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        if limit <= 0:
            raise ValueError("limit must be positive")

        # Perform search
        search_results = await server.client.search_content(query, limit)

        # Convert to dictionary format for MCP response
        results = []
        for result in search_results:
            results.append({
                "rank_order": result.rank_order,
                "url": result.url,
                "title": result.title,
                "snippet": result.snippet,
                "relevance_score": result.relevance_score,
            })

        logger.info(f"Search completed: {len(results)} results found")
        return results

    except Exception as e:
        logger.error(f"Failed to search documentation for '{query}': {e}")
        raise RuntimeError(f"Failed to search documentation: {str(e)}") from e


@mcp.tool()
async def get_api_reference(
    ctx: Context,
    class_name: str,
) -> str:
    """Get Phaser API reference for a specific class.

    Args:
        ctx: MCP context
        class_name: Name of the Phaser class to get API reference for

    Returns:
        Markdown-formatted API reference documentation

    Raises:
        ValueError: If class_name is empty
        RuntimeError: If API reference cannot be retrieved
    """
    logger.info(f"Getting API reference for class: {class_name}")

    try:
        # Validate parameters
        if not class_name.strip():
            raise ValueError("class_name cannot be empty")

        # Get API reference
        api_ref = await server.client.get_api_reference(class_name)

        # Format as markdown
        markdown_content = server.parser.format_api_reference_to_markdown(api_ref)

        logger.info(f"Successfully retrieved API reference for {class_name}")
        return markdown_content

    except Exception as e:
        logger.error(f"Failed to get API reference for '{class_name}': {e}")
        raise RuntimeError(f"Failed to get API reference: {str(e)}") from e


async def main() -> None:
    """Main entry point for the Phaser MCP server with proper lifecycle management."""
    logger.info("Starting Phaser MCP Server")

    # Track server state
    server_initialized = False

    try:
        # Log server information
        server_info = server.get_server_info()
        logger.info(f"Server info: {server_info}")

        # Initialize server components
        logger.info("Initializing server components...")
        await server.initialize()
        server_initialized = True
        logger.info("Server initialization completed successfully")

        # Log that server is ready
        logger.info("Phaser MCP Server is ready to accept connections")

        # Run the MCP server
        logger.debug("Starting FastMCP server...")
        await mcp.run()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Server error occurred: {e}")
        logger.debug("Server error details:", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup resources
        if server_initialized:
            logger.info("Performing server cleanup...")
            try:
                await server.cleanup()
                logger.info("Server cleanup completed successfully")
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
                logger.debug("Cleanup error details:", exc_info=True)
        else:
            logger.warning("Server was not fully initialized, skipping cleanup")

        logger.info("Phaser MCP Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
