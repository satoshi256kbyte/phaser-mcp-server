"""Unit tests for the MCP server module.

This module contains comprehensive tests for the MCP server functionality
including tool functions, initialization, and error handling.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from phaser_mcp_server.models import ApiReference, DocumentationPage, SearchResult
from phaser_mcp_server.server import (
    get_api_reference,
    read_documentation,
    search_documentation,
    server,
)
from tests.utils import MockContext


class TestServerConfiguration:
    """Test server configuration and initialization."""

    def test_server_exists(self):
        """Test that server object exists."""
        from phaser_mcp_server.server import server

        assert server is not None

    def test_mcp_server_exists(self):
        """Test that mcp server object exists."""
        from phaser_mcp_server.server import mcp

        assert mcp is not None


class TestReadDocumentationTool:
    """Test the read_documentation MCP tool."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        return MockContext()

    @pytest.mark.asyncio
    async def test_read_documentation_success(self, mock_context):
        """Test successful documentation reading."""
        # Mock the client and parser
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<h1>Test</h1><p>Test content</p>",
        )

        with patch.object(
            server.client, "get_page_content", return_value=mock_page
        ) as mock_get_page:
            with patch.object(server.parser, "parse_html_content") as mock_parse:
                with patch.object(
                    server.parser,
                    "convert_to_markdown",
                    return_value="# Test\n\nTest content",
                ) as mock_convert:
                    mock_parse.return_value = {
                        "title": "Test",
                        "content": "<h1>Test</h1><p>Test content</p>",
                        "text_content": "Test content",
                    }

                    result = await read_documentation(
                        mock_context, "https://docs.phaser.io/phaser/test"
                    )

                    assert result == "# Test\n\nTest content"
                    mock_get_page.assert_called_once_with(
                        "https://docs.phaser.io/phaser/test"
                    )
                    mock_parse.assert_called_once()
                    mock_convert.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_documentation_with_pagination(self, mock_context):
        """Test documentation reading with pagination parameters."""
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<h1>Test</h1><p>Test content</p>",
        )

        with patch.object(server.client, "get_page_content", return_value=mock_page):
            with patch.object(server.parser, "parse_html_content"):
                with patch.object(
                    server.parser,
                    "convert_to_markdown",
                    return_value="This is a long test content for pagination",
                ):
                    result = await read_documentation(
                        mock_context,
                        "https://docs.phaser.io/phaser/test",
                        max_length=10,
                        start_index=5,
                    )

                    # Should return paginated content
                    assert len(result) <= 10
                    assert result.strip() == "is a long"

    @pytest.mark.asyncio
    async def test_read_documentation_invalid_parameters(self, mock_context):
        """Test read_documentation with invalid parameters."""
        # Test negative max_length
        with pytest.raises(RuntimeError, match="max_length must be positive"):
            await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/test", max_length=-1
            )

        # Test negative start_index
        with pytest.raises(RuntimeError, match="start_index must be non-negative"):
            await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/test", start_index=-1
            )

    @pytest.mark.asyncio
    async def test_read_documentation_start_index_beyond_content(self, mock_context):
        """Test read_documentation when start_index is beyond content length."""
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<h1>Test</h1><p>Test content</p>",
        )

        with patch.object(server.client, "get_page_content", return_value=mock_page):
            with patch.object(server.parser, "parse_html_content"):
                with patch.object(
                    server.parser, "convert_to_markdown", return_value="Short content"
                ):
                    result = await read_documentation(
                        mock_context,
                        "https://docs.phaser.io/phaser/test",
                        start_index=100,
                    )

                    # Should return empty string
                    assert result == ""

    @pytest.mark.asyncio
    async def test_read_documentation_error_handling(self, mock_context):
        """Test read_documentation error handling."""
        with patch.object(
            server.client, "get_page_content", side_effect=Exception("Network error")
        ):
            with pytest.raises(RuntimeError, match="Failed to read documentation"):
                await read_documentation(
                    mock_context, "https://docs.phaser.io/phaser/test"
                )


class TestSearchDocumentationTool:
    """Test the search_documentation MCP tool."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        return MockContext()

    @pytest.mark.asyncio
    async def test_search_documentation_success(self, mock_context):
        """Test successful documentation search."""
        mock_results = [
            SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/sprites",
                title="Sprites",
                snippet="Learn about sprites",
                relevance_score=0.95,
            )
        ]

        with patch.object(
            server.client, "search_content", return_value=mock_results
        ) as mock_search:
            result = await search_documentation(mock_context, "sprites")

            assert len(result) == 1
            assert result[0]["rank_order"] == 1
            assert result[0]["url"] == "https://docs.phaser.io/phaser/sprites"
            assert result[0]["title"] == "Sprites"
            mock_search.assert_called_once_with("sprites", 10)

    @pytest.mark.asyncio
    async def test_search_documentation_with_limit(self, mock_context):
        """Test search_documentation with custom limit."""
        mock_results = []

        with patch.object(
            server.client, "search_content", return_value=mock_results
        ) as mock_search:
            result = await search_documentation(mock_context, "test", limit=5)

            assert result == []
            mock_search.assert_called_once_with("test", 5)

    @pytest.mark.asyncio
    async def test_search_documentation_invalid_parameters(self, mock_context):
        """Test search_documentation with invalid parameters."""
        # Test empty query
        with pytest.raises(RuntimeError, match="query cannot be empty"):
            await search_documentation(mock_context, "")

        # Test negative limit
        with pytest.raises(RuntimeError, match="limit must be positive"):
            await search_documentation(mock_context, "test", limit=-1)

    @pytest.mark.asyncio
    async def test_search_documentation_error_handling(self, mock_context):
        """Test search_documentation error handling."""
        with patch.object(
            server.client, "search_content", side_effect=Exception("Search error")
        ):
            with pytest.raises(RuntimeError, match="Failed to search documentation"):
                await search_documentation(mock_context, "test")


class TestGetApiReferenceTool:
    """Test the get_api_reference MCP tool."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        return MockContext()

    @pytest.mark.asyncio
    async def test_get_api_reference_success(self, mock_context):
        """Test successful API reference retrieval."""
        mock_api_ref = ApiReference(
            class_name="Phaser.GameObjects.Sprite",
            url="https://docs.phaser.io/api/Sprite",
            description="A sprite game object",
            methods=["setTexture", "destroy"],
            properties=["x", "y"],
            examples=["const sprite = this.add.sprite(0, 0, 'key');"],
        )

        with patch.object(
            server.client, "get_api_reference", return_value=mock_api_ref
        ) as mock_get_api:
            with patch.object(
                server.parser,
                "format_api_reference_to_markdown",
                return_value="# Sprite\n\nA sprite game object",
            ) as mock_format:
                result = await get_api_reference(mock_context, "Sprite")

                assert result == "# Sprite\n\nA sprite game object"
                mock_get_api.assert_called_once_with("Sprite")
                mock_format.assert_called_once_with(mock_api_ref)

    @pytest.mark.asyncio
    async def test_get_api_reference_invalid_parameters(self, mock_context):
        """Test get_api_reference with invalid parameters."""
        # Test empty class_name
        with pytest.raises(RuntimeError, match="class_name cannot be empty"):
            await get_api_reference(mock_context, "")

        # Test whitespace-only class_name
        with pytest.raises(RuntimeError, match="class_name cannot be empty"):
            await get_api_reference(mock_context, "   ")

    @pytest.mark.asyncio
    async def test_get_api_reference_error_handling(self, mock_context):
        """Test get_api_reference error handling."""
        with patch.object(
            server.client, "get_api_reference", side_effect=Exception("API error")
        ):
            with pytest.raises(RuntimeError, match="Failed to get API reference"):
                await get_api_reference(mock_context, "TestClass")


class TestServerErrorHandling:
    """Test server-wide error handling and edge cases."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        return MockContext()

    @pytest.mark.asyncio
    async def test_word_boundary_pagination(self, mock_context):
        """Test that pagination respects word boundaries."""
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<h1>Test</h1><p>Test content</p>",
        )

        with patch.object(server.client, "get_page_content", return_value=mock_page):
            with patch.object(server.parser, "parse_html_content"):
                with patch.object(
                    server.parser,
                    "convert_to_markdown",
                    return_value="This is a test content with multiple words",
                ):
                    result = await read_documentation(
                        mock_context,
                        "https://docs.phaser.io/phaser/test",
                        max_length=20,
                        start_index=0,
                    )

                    # Should cut at word boundary
                    assert not result.endswith(" ")
                    assert len(result) <= 20

    @pytest.mark.asyncio
    async def test_empty_search_results(self, mock_context):
        """Test handling of empty search results."""
        with patch.object(server.client, "search_content", return_value=[]):
            result = await search_documentation(mock_context, "nonexistent")

            assert result == []

    @pytest.mark.asyncio
    async def test_api_reference_formatting_error(self, mock_context):
        """Test handling of API reference formatting errors."""
        mock_api_ref = ApiReference(
            class_name="TestClass",
            url="https://docs.phaser.io/api/TestClass",
            description="Test class",
        )

        with patch.object(
            server.client, "get_api_reference", return_value=mock_api_ref
        ):
            with patch.object(
                server.parser,
                "format_api_reference_to_markdown",
                side_effect=Exception("Format error"),
            ):
                with pytest.raises(RuntimeError, match="Failed to get API reference"):
                    await get_api_reference(mock_context, "TestClass")


class TestMainFunction:
    """Test main function and CLI entry point."""

    @pytest.mark.asyncio
    async def test_main_function(self):
        """Test main function initialization."""
        from phaser_mcp_server.server import main, mcp, server

        # Mock command line arguments
        with patch("sys.argv", ["phaser-mcp-server"]):
            with patch.object(mcp, "run", new_callable=AsyncMock) as mock_run:
                with patch.object(
                    server, "initialize", new_callable=AsyncMock
                ) as mock_init:
                    with patch.object(server, "cleanup", new_callable=AsyncMock):
                        with patch.object(server, "get_server_info") as mock_info:
                            mock_info.return_value = {
                                "name": "test",
                                "version": "1.0.0",
                            }

                            await main()

                            mock_init.assert_called_once()
                            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_keyboard_interrupt(self):
        """Test main function with KeyboardInterrupt."""
        from phaser_mcp_server.server import main, mcp, server

        # Mock command line arguments
        with patch("sys.argv", ["phaser-mcp-server"]):
            with patch.object(mcp, "run", new_callable=AsyncMock) as mock_run:
                with patch.object(
                    server, "initialize", new_callable=AsyncMock
                ) as mock_init:
                    with patch.object(server, "cleanup", new_callable=AsyncMock):
                        with patch.object(server, "get_server_info") as mock_info:
                            mock_info.return_value = {
                                "name": "test",
                                "version": "1.0.0",
                            }
                            mock_run.side_effect = KeyboardInterrupt()

                            # Should handle KeyboardInterrupt gracefully
                            await main()

                            mock_init.assert_called_once()
                            mock_run.assert_called_once()

    def test_cli_main_keyboard_interrupt(self):
        """Test cli_main handles KeyboardInterrupt gracefully."""
        from phaser_mcp_server.server import cli_main

        with patch("asyncio.run") as mock_run:
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit) as exc_info:
                cli_main()

            assert exc_info.value.code == 0

    def test_cli_main_exception(self):
        """Test cli_main handles exceptions gracefully."""
        from phaser_mcp_server.server import cli_main

        with patch("asyncio.run") as mock_run:
            mock_run.side_effect = Exception("Test error")

            with pytest.raises(SystemExit) as exc_info:
                cli_main()

            assert exc_info.value.code == 1

    def test_cli_main_success(self):
        """Test cli_main runs successfully."""
        from phaser_mcp_server.server import cli_main

        with patch("asyncio.run") as mock_run:
            mock_run.return_value = None

            # Should not raise any exception
            cli_main()
            mock_run.assert_called_once()


class TestServerInitialization:
    """Test server initialization and cleanup."""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test server initialization."""
        from phaser_mcp_server.server import server

        # Test server info
        info = server.get_server_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "version" in info

    @pytest.mark.asyncio
    async def test_server_cleanup(self):
        """Test server cleanup."""
        from phaser_mcp_server.server import server

        # Should not raise an error
        await server.cleanup()


class TestToolParameterValidation:
    """Test parameter validation for MCP tools."""

    @pytest.mark.asyncio
    async def test_read_documentation_negative_max_length(self):
        """Test read_documentation with negative max_length."""
        mock_context = Mock()

        with pytest.raises(RuntimeError, match="Failed to read documentation"):
            await read_documentation(
                mock_context, "https://docs.phaser.io/test", max_length=-1
            )

    @pytest.mark.asyncio
    async def test_read_documentation_negative_start_index(self):
        """Test read_documentation with negative start_index."""
        mock_context = Mock()

        with pytest.raises(RuntimeError, match="Failed to read documentation"):
            await read_documentation(
                mock_context, "https://docs.phaser.io/test", start_index=-1
            )

    @pytest.mark.asyncio
    async def test_search_documentation_negative_limit(self):
        """Test search_documentation with negative limit."""
        mock_context = Mock()

        with pytest.raises(RuntimeError, match="Failed to search documentation"):
            await search_documentation(mock_context, "test query", limit=-1)

    @pytest.mark.asyncio
    async def test_search_documentation_empty_query(self):
        """Test search_documentation with empty query."""
        mock_context = Mock()

        with pytest.raises(RuntimeError, match="Failed to search documentation"):
            await search_documentation(mock_context, "", limit=10)

    @pytest.mark.asyncio
    async def test_get_api_reference_empty_class_name(self):
        """Test get_api_reference with empty class_name."""
        mock_context = Mock()

        with pytest.raises(RuntimeError, match="Failed to get API reference"):
            await get_api_reference(mock_context, "")


class TestCommandLineInterface:
    """Test command line interface functionality."""

    def test_parse_arguments_default(self):
        """Test parsing default arguments."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server"]):
            args = parse_arguments()
            assert args is not None

    def test_parse_arguments_with_options(self):
        """Test parsing arguments with options."""
        from phaser_mcp_server.server import parse_arguments

        with patch(
            "sys.argv", ["phaser-mcp-server", "--log-level", "DEBUG", "--timeout", "60"]
        ):
            args = parse_arguments()
            assert args.log_level == "DEBUG"
            assert args.timeout == 60

    def test_apply_cli_arguments(self):
        """Test applying CLI arguments to environment."""
        import os

        from phaser_mcp_server.server import apply_cli_arguments

        # Mock arguments
        args = Mock()
        args.log_level = "DEBUG"
        args.timeout = 60
        args.max_retries = 5
        args.cache_ttl = 7200

        # Apply arguments
        apply_cli_arguments(args)

        # Check environment variables were set
        assert os.environ.get("FASTMCP_LOG_LEVEL") == "DEBUG"
        assert os.environ.get("PHASER_DOCS_TIMEOUT") == "60"
        assert os.environ.get("PHASER_DOCS_MAX_RETRIES") == "5"
        assert os.environ.get("PHASER_DOCS_CACHE_TTL") == "7200"


class TestHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_handle_health_check(self):
        """Test health check handler."""
        from phaser_mcp_server.server import handle_health_check

        # Health check may exit with status code
        with pytest.raises(SystemExit):
            await handle_health_check()

    @pytest.mark.asyncio
    async def test_main_with_health_check(self):
        """Test main function with health check argument."""
        from phaser_mcp_server.server import main

        with patch("sys.argv", ["phaser-mcp-server", "--health-check"]):
            with patch("phaser_mcp_server.server.handle_health_check") as mock_health:
                mock_health.return_value = AsyncMock()

                await main()

                mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_with_info(self):
        """Test main function with info argument."""
        from phaser_mcp_server.server import main

        with patch("sys.argv", ["phaser-mcp-server", "--info"]):
            with patch("phaser_mcp_server.server.handle_info_command") as mock_info:
                mock_info.return_value = AsyncMock()

                await main()

                mock_info.assert_called_once()


class TestInfoHandler:
    """Test info handler functionality."""

    @pytest.mark.asyncio
    async def test_handle_info_command(self):
        """Test info command handler."""
        from phaser_mcp_server.server import handle_info_command

        # Should not raise an exception
        await handle_info_command()


class TestServerErrorScenarios:
    """Test server error scenarios."""

    @pytest.mark.asyncio
    async def test_server_initialization_failure(self):
        """Test server initialization failure."""
        from phaser_mcp_server.server import server

        # Mock initialization to fail
        with patch.object(
            server.client, "initialize", side_effect=Exception("Init failed")
        ):
            with pytest.raises(RuntimeError, match="Init failed"):
                await server.initialize()

    @pytest.mark.asyncio
    async def test_server_cleanup_failure(self):
        """Test server cleanup failure."""
        from phaser_mcp_server.server import server

        # Mock cleanup to fail
        with patch.object(
            server.client, "close", side_effect=Exception("Cleanup failed")
        ):
            # Should not raise exception, just log error
            await server.cleanup()


class TestEnvironmentVariableHandling:
    """Test environment variable handling."""

    def test_environment_variable_parsing(self, monkeypatch):
        """Test parsing of environment variables."""
        # Test with valid values
        monkeypatch.setenv("PHASER_DOCS_TIMEOUT", "45")
        monkeypatch.setenv("PHASER_DOCS_MAX_RETRIES", "5")

        # Import to trigger parsing
        import importlib

        import phaser_mcp_server.server

        importlib.reload(phaser_mcp_server.server)

        # Should not raise any errors
        assert phaser_mcp_server.server.server is not None
