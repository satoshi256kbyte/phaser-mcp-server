"""Phaser MCP Server - Main server implementation.

This module implements the MCP server for Phaser game engine documentation access.
It provides tools for reading documentation, searching content, and accessing
API references.
"""

import argparse
import asyncio
import os
import sys
from typing import Any

from loguru import logger
from mcp.server.fastmcp import Context, FastMCP

from . import __version__
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
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
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
            raise RuntimeError(f"Server initialization failed: {str(e)}") from e

    async def cleanup(self) -> None:
        """Clean up server resources with comprehensive error handling."""
        logger.info("Starting server cleanup...")

        cleanup_errors: list[str] = []

        # Cleanup HTTP client
        try:
            if hasattr(self, "client") and self.client:
                await self.client.close()
                logger.debug("HTTP client closed successfully")
        except Exception as e:
            error_msg = f"Error closing HTTP client: {e}"
            logger.error(error_msg)
            cleanup_errors.append(error_msg)

        # Additional cleanup for parser if needed
        try:
            if hasattr(self, "parser") and self.parser:
                # Parser cleanup if it has any resources to clean
                # Note: Currently parser doesn't have cleanup method,
                # but we keep this for future compatibility
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
                "PHASER_DOCS_MAX_RETRIES": os.getenv("PHASER_DOCS_MAX_RETRIES", "3"),
                "PHASER_DOCS_CACHE_TTL": os.getenv("PHASER_DOCS_CACHE_TTL", "3600"),
            },
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
    ctx: Context[Any, Any, Any],
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
    ctx: Context[Any, Any, Any],
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
        results: list[dict[str, str | int | float | None]] = []
        for result in search_results:
            results.append(
                {
                    "rank_order": result.rank_order,
                    "url": result.url,
                    "title": result.title,
                    "snippet": result.snippet,
                    "relevance_score": result.relevance_score,
                }
            )

        logger.info(f"Search completed: {len(results)} results found")
        return results

    except Exception as e:
        logger.error(f"Failed to search documentation for '{query}': {e}")
        raise RuntimeError(f"Failed to search documentation: {str(e)}") from e


@mcp.tool()
async def get_api_reference(
    ctx: Context[Any, Any, Any],
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


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        prog="phaser-mcp-server",
        description="MCP Server for Phaser Game Engine Documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  FASTMCP_LOG_LEVEL      Set logging level (DEBUG, INFO, WARNING, ERROR)
  PHASER_DOCS_TIMEOUT    Request timeout in seconds (default: 30)
  PHASER_DOCS_MAX_RETRIES Maximum number of retries (default: 3)
  PHASER_DOCS_CACHE_TTL  Cache TTL in seconds (default: 3600)

Examples:
  phaser-mcp-server                    # Start server with default settings
  phaser-mcp-server --log-level DEBUG # Start with debug logging
  phaser-mcp-server --version         # Show version information
  phaser-mcp-server --help            # Show this help message
        """,
    )

    # Version argument
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version information and exit",
    )

    # Logging configuration
    parser.add_argument(
        "--log-level",
        choices=["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Set logging level (overrides FASTMCP_LOG_LEVEL environment variable)",
    )

    # Server configuration
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        metavar="SECONDS",
        help=(
            "Request timeout in seconds "
            "(overrides PHASER_DOCS_TIMEOUT environment variable)"
        ),
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        metavar="COUNT",
        help=(
            "Maximum number of retries "
            "(overrides PHASER_DOCS_MAX_RETRIES environment variable)"
        ),
    )

    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=None,
        metavar="SECONDS",
        help=(
            "Cache TTL in seconds "
            "(overrides PHASER_DOCS_CACHE_TTL environment variable)"
        ),
    )

    # Development and debugging options
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show server information and exit",
    )

    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform health check and exit",
    )

    return parser.parse_args()


def apply_cli_arguments(args: argparse.Namespace) -> None:
    """Apply command-line arguments to environment variables.

    Args:
        args: Parsed command-line arguments
    """
    # Apply log level if specified
    if args.log_level:
        os.environ["FASTMCP_LOG_LEVEL"] = args.log_level
        logger.debug(f"Log level set from CLI: {args.log_level}")

    # Apply timeout if specified
    if args.timeout is not None:
        if args.timeout <= 0:
            logger.error("Timeout must be positive")
            sys.exit(1)
        os.environ["PHASER_DOCS_TIMEOUT"] = str(args.timeout)
        logger.debug(f"Timeout set from CLI: {args.timeout}")

    # Apply max retries if specified
    if args.max_retries is not None:
        if args.max_retries < 0:
            logger.error("Max retries must be non-negative")
            sys.exit(1)
        os.environ["PHASER_DOCS_MAX_RETRIES"] = str(args.max_retries)
        logger.debug(f"Max retries set from CLI: {args.max_retries}")

    # Apply cache TTL if specified
    if args.cache_ttl is not None:
        if args.cache_ttl < 0:
            logger.error("Cache TTL must be non-negative")
            sys.exit(1)
        os.environ["PHASER_DOCS_CACHE_TTL"] = str(args.cache_ttl)
        logger.debug(f"Cache TTL set from CLI: {args.cache_ttl}")


async def handle_info_command() -> None:
    """Handle the --info command to show server information."""
    print(f"Phaser MCP Server v{__version__}")
    print("=" * 50)

    # Create temporary server instance to get info
    temp_server = PhaserMCPServer()
    server_info = temp_server.get_server_info()

    print(f"Name: {server_info['name']}")
    print(f"Version: {server_info['version']}")
    print(f"Status: {server_info['status']}")
    print(f"Log Level: {server_info['log_level']}")
    print()
    print("Environment Variables:")
    for key, value in server_info["environment_variables"].items():
        print(f"  {key}: {value}")
    print()
    print("Available MCP Tools:")
    print("  - read_documentation: Read Phaser documentation pages")
    print("  - search_documentation: Search Phaser documentation")
    print("  - get_api_reference: Get API reference for Phaser classes")


async def handle_health_check() -> None:
    """Handle the --health-check command to perform health check."""
    print("Performing health check...")

    try:
        # Create temporary server instance
        temp_server = PhaserMCPServer()
        await temp_server.initialize()

        # Perform health check
        await temp_server.client.health_check()

        print("✓ Health check passed")
        print("✓ Server components initialized successfully")
        print("✓ HTTP client connectivity verified")

        # Cleanup
        await temp_server.cleanup()

    except Exception as e:
        print(f"✗ Health check failed: {e}")
        sys.exit(1)


async def main() -> None:
    """Main entry point for the Phaser MCP server with CLI argument processing."""
    # Parse command-line arguments
    args = parse_arguments()

    # Handle special commands that don't start the server
    if args.info:
        await handle_info_command()
        return

    if args.health_check:
        await handle_health_check()
        return

    # Apply CLI arguments to environment variables
    apply_cli_arguments(args)

    logger.info(f"Starting Phaser MCP Server v{__version__}")

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


def cli_main() -> None:
    """CLI entry point that handles asyncio properly."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nServer shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
