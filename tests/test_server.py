"""Unit tests for the MCP server module.

This module contains comprehensive tests for the MCP server functionality
including tool functions, initialization, and error handling.
"""

import os
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
    async def test_read_documentation_with_zero_max_length(self, mock_context):
        """Test read_documentation with zero max_length."""
        with pytest.raises(RuntimeError, match="max_length must be positive"):
            await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/test", max_length=0
            )

    @pytest.mark.asyncio
    async def test_read_documentation_with_large_max_length(self, mock_context):
        """Test read_documentation with very large max_length."""
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
                    return_value="Short content",
                ):
                    result = await read_documentation(
                        mock_context,
                        "https://docs.phaser.io/phaser/test",
                        max_length=1000000,
                    )

                    # Should return full content
                    assert result == "Short content"

    @pytest.mark.asyncio
    async def test_read_documentation_with_exact_length_match(self, mock_context):
        """Test read_documentation when content length exactly matches max_length."""
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
                    return_value="12345",  # Exactly 5 characters
                ):
                    result = await read_documentation(
                        mock_context,
                        "https://docs.phaser.io/phaser/test",
                        max_length=5,
                    )

                    assert result == "12345"

    @pytest.mark.asyncio
    async def test_read_documentation_empty_content(self, mock_context):
        """Test read_documentation with empty content."""
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="",
        )

        with patch.object(server.client, "get_page_content", return_value=mock_page):
            with patch.object(server.parser, "parse_html_content"):
                with patch.object(
                    server.parser,
                    "convert_to_markdown",
                    return_value="",
                ):
                    result = await read_documentation(
                        mock_context, "https://docs.phaser.io/phaser/test"
                    )

                    assert result == ""

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
    async def test_read_documentation_client_error(self, mock_context):
        """Test read_documentation with client error."""
        with patch.object(
            server.client, "get_page_content", side_effect=Exception("Network error")
        ):
            with pytest.raises(RuntimeError, match="Failed to read documentation"):
                await read_documentation(
                    mock_context, "https://docs.phaser.io/phaser/test"
                )

    @pytest.mark.asyncio
    async def test_read_documentation_parser_error(self, mock_context):
        """Test read_documentation with parser error."""
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<h1>Test</h1><p>Test content</p>",
        )

        with patch.object(server.client, "get_page_content", return_value=mock_page):
            with patch.object(
                server.parser,
                "parse_html_content",
                side_effect=Exception("Parse error"),
            ):
                with pytest.raises(RuntimeError, match="Failed to read documentation"):
                    await read_documentation(
                        mock_context, "https://docs.phaser.io/phaser/test"
                    )

    @pytest.mark.asyncio
    async def test_read_documentation_markdown_conversion_error(self, mock_context):
        """Test read_documentation with markdown conversion error."""
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
                    side_effect=Exception("Conversion error"),
                ):
                    with pytest.raises(
                        RuntimeError, match="Failed to read documentation"
                    ):
                        await read_documentation(
                            mock_context, "https://docs.phaser.io/phaser/test"
                        )

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
            assert result[0]["snippet"] == "Learn about sprites"
            assert result[0]["relevance_score"] == 0.95
            mock_search.assert_called_once_with("sprites", 10)

    @pytest.mark.asyncio
    async def test_search_documentation_multiple_results(self, mock_context):
        """Test search_documentation with multiple results."""
        mock_results = [
            SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/sprites",
                title="Sprites",
                snippet="Learn about sprites",
                relevance_score=0.95,
            ),
            SearchResult(
                rank_order=2,
                url="https://docs.phaser.io/phaser/textures",
                title="Textures",
                snippet="Learn about textures",
                relevance_score=0.85,
            ),
        ]

        with patch.object(
            server.client, "search_content", return_value=mock_results
        ) as mock_search:
            result = await search_documentation(mock_context, "graphics")

            assert len(result) == 2
            assert result[0]["rank_order"] == 1
            assert result[1]["rank_order"] == 2
            assert result[0]["relevance_score"] == 0.95
            assert result[1]["relevance_score"] == 0.85
            mock_search.assert_called_once_with("graphics", 10)

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
    async def test_search_documentation_with_limit_one(self, mock_context):
        """Test search_documentation with limit of 1."""
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
            result = await search_documentation(mock_context, "sprites", limit=1)

            assert len(result) == 1
            mock_search.assert_called_once_with("sprites", 1)

    @pytest.mark.asyncio
    async def test_search_documentation_with_large_limit(self, mock_context):
        """Test search_documentation with very large limit."""
        mock_results = []

        with patch.object(
            server.client, "search_content", return_value=mock_results
        ) as mock_search:
            result = await search_documentation(mock_context, "test", limit=1000)

            assert result == []
            mock_search.assert_called_once_with("test", 1000)

    @pytest.mark.asyncio
    async def test_search_documentation_empty_query(self, mock_context):
        """Test search_documentation with empty query."""
        with pytest.raises(RuntimeError, match="query cannot be empty"):
            await search_documentation(mock_context, "")

    @pytest.mark.asyncio
    async def test_search_documentation_whitespace_only_query(self, mock_context):
        """Test search_documentation with whitespace-only query."""
        with pytest.raises(RuntimeError, match="query cannot be empty"):
            await search_documentation(mock_context, "   ")

    @pytest.mark.asyncio
    async def test_search_documentation_zero_limit(self, mock_context):
        """Test search_documentation with zero limit."""
        with pytest.raises(RuntimeError, match="limit must be positive"):
            await search_documentation(mock_context, "test", limit=0)

    @pytest.mark.asyncio
    async def test_search_documentation_negative_limit(self, mock_context):
        """Test search_documentation with negative limit."""
        with pytest.raises(RuntimeError, match="limit must be positive"):
            await search_documentation(mock_context, "test", limit=-1)

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
    async def test_search_documentation_client_error(self, mock_context):
        """Test search_documentation with client error."""
        with patch.object(
            server.client, "search_content", side_effect=Exception("Search error")
        ):
            with pytest.raises(RuntimeError, match="Failed to search documentation"):
                await search_documentation(mock_context, "test")

    @pytest.mark.asyncio
    async def test_search_documentation_network_error(self, mock_context):
        """Test search_documentation with network error."""
        with patch.object(
            server.client, "search_content", side_effect=Exception("Network timeout")
        ):
            with pytest.raises(RuntimeError, match="Failed to search documentation"):
                await search_documentation(mock_context, "sprites")

    @pytest.mark.asyncio
    async def test_search_documentation_empty_results(self, mock_context):
        """Test search_documentation with empty results."""
        with patch.object(server.client, "search_content", return_value=[]):
            result = await search_documentation(mock_context, "nonexistent")

            assert result == []

    @pytest.mark.asyncio
    async def test_search_documentation_special_characters(self, mock_context):
        """Test search_documentation with special characters in query."""
        mock_results = []

        with patch.object(
            server.client, "search_content", return_value=mock_results
        ) as mock_search:
            result = await search_documentation(mock_context, "test & special chars!")

            assert result == []
            mock_search.assert_called_once_with("test & special chars!", 10)

    @pytest.mark.asyncio
    async def test_search_documentation_unicode_query(self, mock_context):
        """Test search_documentation with unicode characters in query."""
        mock_results = []

        with patch.object(
            server.client, "search_content", return_value=mock_results
        ) as mock_search:
            result = await search_documentation(mock_context, "テスト")

            assert result == []
            mock_search.assert_called_once_with("テスト", 10)

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
    async def test_get_api_reference_complex_class_name(self, mock_context):
        """Test get_api_reference with complex class name."""
        mock_api_ref = ApiReference(
            class_name="Phaser.GameObjects.Components.Transform",
            url="https://docs.phaser.io/api/Transform",
            description="Transform component",
            methods=["setPosition", "setRotation"],
            properties=["x", "y", "rotation"],
            examples=["transform.setPosition(100, 200);"],
        )

        with patch.object(
            server.client, "get_api_reference", return_value=mock_api_ref
        ) as mock_get_api:
            with patch.object(
                server.parser,
                "format_api_reference_to_markdown",
                return_value="# Transform\n\nTransform component",
            ) as mock_format:
                result = await get_api_reference(
                    mock_context, "Phaser.GameObjects.Components.Transform"
                )

                assert result == "# Transform\n\nTransform component"
                mock_get_api.assert_called_once_with(
                    "Phaser.GameObjects.Components.Transform"
                )
                mock_format.assert_called_once_with(mock_api_ref)

    @pytest.mark.asyncio
    async def test_get_api_reference_minimal_data(self, mock_context):
        """Test get_api_reference with minimal API reference data."""
        mock_api_ref = ApiReference(
            class_name="TestClass",
            url="https://docs.phaser.io/api/TestClass",
            description="Test class",
        )

        with patch.object(
            server.client, "get_api_reference", return_value=mock_api_ref
        ) as mock_get_api:
            with patch.object(
                server.parser,
                "format_api_reference_to_markdown",
                return_value="# TestClass\n\nTest class",
            ) as mock_format:
                result = await get_api_reference(mock_context, "TestClass")

                assert result == "# TestClass\n\nTest class"
                mock_get_api.assert_called_once_with("TestClass")
                mock_format.assert_called_once_with(mock_api_ref)

    @pytest.mark.asyncio
    async def test_get_api_reference_with_special_characters(self, mock_context):
        """Test get_api_reference with special characters in class name."""
        mock_api_ref = ApiReference(
            class_name="Test$Class",
            url="https://docs.phaser.io/api/TestClass",
            description="Test class with special chars",
        )

        with patch.object(
            server.client, "get_api_reference", return_value=mock_api_ref
        ) as mock_get_api:
            with patch.object(
                server.parser,
                "format_api_reference_to_markdown",
                return_value="# Test$Class\n\nTest class with special chars",
            ) as mock_format:
                result = await get_api_reference(mock_context, "Test$Class")

                assert result == "# Test$Class\n\nTest class with special chars"
                mock_get_api.assert_called_once_with("Test$Class")
                mock_format.assert_called_once_with(mock_api_ref)

    @pytest.mark.asyncio
    async def test_get_api_reference_empty_class_name(self, mock_context):
        """Test get_api_reference with empty class_name."""
        with pytest.raises(RuntimeError, match="class_name cannot be empty"):
            await get_api_reference(mock_context, "")

    @pytest.mark.asyncio
    async def test_get_api_reference_whitespace_only_class_name(self, mock_context):
        """Test get_api_reference with whitespace-only class_name."""
        with pytest.raises(RuntimeError, match="class_name cannot be empty"):
            await get_api_reference(mock_context, "   ")

    @pytest.mark.asyncio
    async def test_get_api_reference_tabs_and_newlines_class_name(self, mock_context):
        """Test get_api_reference with tabs and newlines in class_name."""
        with pytest.raises(RuntimeError, match="class_name cannot be empty"):
            await get_api_reference(mock_context, "\t\n  \r")

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
    async def test_get_api_reference_client_error(self, mock_context):
        """Test get_api_reference with client error."""
        with patch.object(
            server.client, "get_api_reference", side_effect=Exception("API error")
        ):
            with pytest.raises(RuntimeError, match="Failed to get API reference"):
                await get_api_reference(mock_context, "TestClass")

    @pytest.mark.asyncio
    async def test_get_api_reference_network_error(self, mock_context):
        """Test get_api_reference with network error."""
        with patch.object(
            server.client, "get_api_reference", side_effect=Exception("Network timeout")
        ):
            with pytest.raises(RuntimeError, match="Failed to get API reference"):
                await get_api_reference(mock_context, "Sprite")

    @pytest.mark.asyncio
    async def test_get_api_reference_formatting_error(self, mock_context):
        """Test get_api_reference with formatting error."""
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

    @pytest.mark.asyncio
    async def test_get_api_reference_class_not_found(self, mock_context):
        """Test get_api_reference when class is not found."""
        with patch.object(
            server.client, "get_api_reference", side_effect=Exception("Class not found")
        ):
            with pytest.raises(RuntimeError, match="Failed to get API reference"):
                await get_api_reference(mock_context, "NonExistentClass")

    @pytest.mark.asyncio
    async def test_get_api_reference_error_handling(self, mock_context):
        """Test get_api_reference error handling."""
        with patch.object(
            server.client, "get_api_reference", side_effect=Exception("API error")
        ):
            with pytest.raises(RuntimeError, match="Failed to get API reference"):
                await get_api_reference(mock_context, "TestClass")


class TestMCPToolErrorHandling:
    """Test MCP tool error handling scenarios."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        return MockContext()

    @pytest.mark.asyncio
    async def test_read_documentation_tool_logging(self, mock_context):
        """Test that read_documentation tool logs appropriately."""
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<h1>Test</h1><p>Test content</p>",
        )

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch.object(
                server.client, "get_page_content", return_value=mock_page
            ):
                with patch.object(server.parser, "parse_html_content"):
                    with patch.object(
                        server.parser,
                        "convert_to_markdown",
                        return_value="# Test\n\nTest content",
                    ):
                        await read_documentation(
                            mock_context, "https://docs.phaser.io/phaser/test"
                        )

                        # Should log info about reading documentation
                        info_calls = [
                            call
                            for call in mock_logger.info.call_args_list
                            if "Reading documentation" in str(call)
                        ]
                        assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_search_documentation_tool_logging(self, mock_context):
        """Test that search_documentation tool logs appropriately."""
        mock_results = []

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch.object(
                server.client, "search_content", return_value=mock_results
            ):
                await search_documentation(mock_context, "test query")

                # Should log info about searching
                info_calls = [
                    call
                    for call in mock_logger.info.call_args_list
                    if "Searching documentation" in str(call)
                ]
                assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_get_api_reference_tool_logging(self, mock_context):
        """Test that get_api_reference tool logs appropriately."""
        mock_api_ref = ApiReference(
            class_name="TestClass",
            url="https://docs.phaser.io/api/TestClass",
            description="Test class",
        )

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch.object(
                server.client, "get_api_reference", return_value=mock_api_ref
            ):
                with patch.object(
                    server.parser,
                    "format_api_reference_to_markdown",
                    return_value="# TestClass\n\nTest class",
                ):
                    await get_api_reference(mock_context, "TestClass")

                    # Should log info about getting API reference
                    info_calls = [
                        call
                        for call in mock_logger.info.call_args_list
                        if "Getting API reference" in str(call)
                    ]
                    assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_read_documentation_error_logging(self, mock_context):
        """Test that read_documentation logs errors appropriately."""
        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch.object(
                server.client,
                "get_page_content",
                side_effect=Exception("Network error"),
            ):
                with pytest.raises(RuntimeError):
                    await read_documentation(
                        mock_context, "https://docs.phaser.io/phaser/test"
                    )

                # Should log error
                error_calls = [
                    call
                    for call in mock_logger.error.call_args_list
                    if "Failed to read documentation" in str(call)
                ]
                assert len(error_calls) >= 1

    @pytest.mark.asyncio
    async def test_search_documentation_error_logging(self, mock_context):
        """Test that search_documentation logs errors appropriately."""
        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch.object(
                server.client, "search_content", side_effect=Exception("Search error")
            ):
                with pytest.raises(RuntimeError):
                    await search_documentation(mock_context, "test")

                # Should log error
                error_calls = [
                    call
                    for call in mock_logger.error.call_args_list
                    if "Failed to search documentation" in str(call)
                ]
                assert len(error_calls) >= 1

    @pytest.mark.asyncio
    async def test_get_api_reference_error_logging(self, mock_context):
        """Test that get_api_reference logs errors appropriately."""
        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch.object(
                server.client, "get_api_reference", side_effect=Exception("API error")
            ):
                with pytest.raises(RuntimeError):
                    await get_api_reference(mock_context, "TestClass")

                # Should log error
                error_calls = [
                    call
                    for call in mock_logger.error.call_args_list
                    if "Failed to get API reference" in str(call)
                ]
                assert len(error_calls) >= 1

    @pytest.mark.asyncio
    async def test_tool_context_handling(self, mock_context):
        """Test that tools handle MCP context properly."""
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
                    return_value="# Test\n\nTest content",
                ):
                    # Should accept context without issues
                    result = await read_documentation(
                        mock_context, "https://docs.phaser.io/phaser/test"
                    )
                    assert result == "# Test\n\nTest content"

    @pytest.mark.asyncio
    async def test_tool_parameter_validation_order(self, mock_context):
        """Test that tool parameter validation happens in correct order."""
        # Test that parameter validation happens before client calls
        with patch.object(server.client, "get_page_content") as mock_get_page:
            with pytest.raises(RuntimeError, match="max_length must be positive"):
                await read_documentation(
                    mock_context, "https://docs.phaser.io/phaser/test", max_length=-1
                )

            # Client should not be called if validation fails
            mock_get_page.assert_not_called()


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
                    with patch.object(
                        server, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
                        with patch.object(server, "get_server_info") as mock_info:
                            mock_info.return_value = {
                                "name": "test",
                                "version": "1.0.0",
                            }

                            await main()

                            mock_init.assert_called_once()
                            mock_run.assert_called_once()
                            mock_cleanup.assert_called_once()

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
                    with patch.object(
                        server, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
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
                            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_server_error(self):
        """Test main function with server error."""
        from phaser_mcp_server.server import main, mcp, server

        # Mock command line arguments
        with patch("sys.argv", ["phaser-mcp-server"]):
            with patch.object(mcp, "run", new_callable=AsyncMock) as mock_run:
                with patch.object(
                    server, "initialize", new_callable=AsyncMock
                ) as mock_init:
                    with patch.object(
                        server, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
                        with patch.object(server, "get_server_info") as mock_info:
                            mock_info.return_value = {
                                "name": "test",
                                "version": "1.0.0",
                            }
                            mock_run.side_effect = Exception("Server error")

                            # Should handle exception and exit
                            with pytest.raises(SystemExit) as exc_info:
                                await main()

                            assert exc_info.value.code == 1
                            mock_init.assert_called_once()
                            mock_run.assert_called_once()
                            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_initialization_failure(self):
        """Test main function with initialization failure."""
        from phaser_mcp_server.server import main, mcp, server

        # Mock command line arguments
        with patch("sys.argv", ["phaser-mcp-server"]):
            with patch.object(mcp, "run", new_callable=AsyncMock) as mock_run:
                with patch.object(
                    server, "initialize", new_callable=AsyncMock
                ) as mock_init:
                    with patch.object(
                        server, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
                        with patch.object(server, "get_server_info") as mock_info:
                            mock_info.return_value = {
                                "name": "test",
                                "version": "1.0.0",
                            }
                            mock_init.side_effect = Exception("Init failed")

                            # Should handle exception and exit
                            with pytest.raises(SystemExit) as exc_info:
                                await main()

                            assert exc_info.value.code == 1
                            mock_init.assert_called_once()
                            mock_run.assert_not_called()
                            # Cleanup should not be called if initialization failed
                            mock_cleanup.assert_not_called()

    @pytest.mark.asyncio
    async def test_main_function_cleanup_error(self):
        """Test main function with cleanup error."""
        from phaser_mcp_server.server import main, mcp, server

        # Mock command line arguments
        with patch("sys.argv", ["phaser-mcp-server"]):
            with patch.object(mcp, "run", new_callable=AsyncMock) as mock_run:
                with patch.object(
                    server, "initialize", new_callable=AsyncMock
                ) as mock_init:
                    with patch.object(
                        server, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
                        with patch.object(server, "get_server_info") as mock_info:
                            with patch(
                                "phaser_mcp_server.server.logger"
                            ) as mock_logger:
                                mock_info.return_value = {
                                    "name": "test",
                                    "version": "1.0.0",
                                }
                                mock_cleanup.side_effect = Exception("Cleanup failed")

                                # Should handle cleanup error gracefully
                                await main()

                                mock_init.assert_called_once()
                                mock_run.assert_called_once()
                                mock_cleanup.assert_called_once()

                                # Should log cleanup error
                                error_calls = [
                                    call
                                    for call in mock_logger.error.call_args_list
                                    if "Error during cleanup" in str(call)
                                ]
                                assert len(error_calls) >= 1

    @pytest.mark.asyncio
    async def test_main_function_no_initialization_no_cleanup(self):
        """Test main function when server was not initialized."""
        from phaser_mcp_server.server import main, mcp, server

        # Mock command line arguments
        with patch("sys.argv", ["phaser-mcp-server"]):
            with patch.object(mcp, "run", new_callable=AsyncMock) as mock_run:
                with patch.object(
                    server, "initialize", new_callable=AsyncMock
                ) as mock_init:
                    with patch.object(
                        server, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
                        with patch.object(server, "get_server_info") as mock_info:
                            with patch(
                                "phaser_mcp_server.server.logger"
                            ) as mock_logger:
                                mock_info.side_effect = Exception("Info failed")

                                # Should handle exception and exit
                                with pytest.raises(SystemExit) as exc_info:
                                    await main()

                                assert exc_info.value.code == 1
                                mock_init.assert_not_called()
                                mock_run.assert_not_called()
                                mock_cleanup.assert_not_called()

                                # Should log warning about not being initialized
                                warning_calls = [
                                    call
                                    for call in mock_logger.warning.call_args_list
                                    if "not fully initialized" in str(call)
                                ]
                                assert len(warning_calls) >= 1

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

    def test_server_instance_creation(self):
        """Test PhaserMCPServer instance creation."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch(
                "phaser_mcp_server.server.PhaserDocumentParser"
            ) as mock_parser_class:
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        server_instance = PhaserMCPServer()

                        assert server_instance is not None
                        mock_client_class.assert_called_once()
                        mock_parser_class.assert_called_once()

    def test_server_logging_setup(self, monkeypatch):
        """Test server logging configuration."""
        from phaser_mcp_server.server import PhaserMCPServer

        # Test with default log level
        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        PhaserMCPServer()

                        # Should configure logger
                        mock_logger.remove.assert_called()
                        mock_logger.add.assert_called()

    def test_server_logging_setup_with_custom_level(self, monkeypatch):
        """Test server logging configuration with custom log level."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("FASTMCP_LOG_LEVEL", "DEBUG")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        PhaserMCPServer()

                        # Should configure logger with DEBUG level
                        mock_logger.add.assert_called()
                        call_args = mock_logger.add.call_args
                        assert call_args[1]["level"] == "DEBUG"

    def test_server_logging_setup_with_invalid_level(self, monkeypatch):
        """Test server logging configuration with invalid log level."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("FASTMCP_LOG_LEVEL", "INVALID")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        PhaserMCPServer()

                        # Should fall back to INFO level
                        call_args = mock_logger.add.call_args
                        assert call_args[1]["level"] == "INFO"

    def test_server_environment_variables_loading(self, monkeypatch):
        """Test server environment variables loading."""
        from phaser_mcp_server.server import PhaserMCPServer

        # Set test environment variables
        monkeypatch.setenv("FASTMCP_LOG_LEVEL", "WARNING")
        monkeypatch.setenv("PHASER_DOCS_TIMEOUT", "45")
        monkeypatch.setenv("PHASER_DOCS_MAX_RETRIES", "5")
        monkeypatch.setenv("PHASER_DOCS_CACHE_TTL", "7200")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_setup_logging"):
                        PhaserMCPServer()

                        # Should log environment variable values
                        debug_calls = [
                            call
                            for call in mock_logger.debug.call_args_list
                            if "Environment variable" in str(call)
                        ]
                        assert len(debug_calls) >= 1

    def test_server_environment_variables_invalid_timeout(self, monkeypatch):
        """Test server environment variables with invalid timeout."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("PHASER_DOCS_TIMEOUT", "invalid")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_setup_logging"):
                        PhaserMCPServer()

                        # Should log warning about invalid value
                        warning_calls = [
                            call
                            for call in mock_logger.warning.call_args_list
                            if "Invalid PHASER_DOCS_TIMEOUT" in str(call)
                        ]
                        assert len(warning_calls) >= 1

    def test_server_environment_variables_negative_timeout(self, monkeypatch):
        """Test server environment variables with negative timeout."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("PHASER_DOCS_TIMEOUT", "-10")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_setup_logging"):
                        PhaserMCPServer()

                        # Should log warning about invalid value
                        warning_calls = [
                            call
                            for call in mock_logger.warning.call_args_list
                            if "Invalid PHASER_DOCS_TIMEOUT" in str(call)
                        ]
                        assert len(warning_calls) >= 1

    def test_server_environment_variables_invalid_retries(self, monkeypatch):
        """Test server environment variables with invalid max retries."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("PHASER_DOCS_MAX_RETRIES", "invalid")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_setup_logging"):
                        PhaserMCPServer()

                        # Should log warning about invalid value
                        warning_calls = [
                            call
                            for call in mock_logger.warning.call_args_list
                            if "Invalid PHASER_DOCS_MAX_RETRIES" in str(call)
                        ]
                        assert len(warning_calls) >= 1

    def test_server_environment_variables_negative_retries(self, monkeypatch):
        """Test server environment variables with negative max retries."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("PHASER_DOCS_MAX_RETRIES", "-1")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_setup_logging"):
                        PhaserMCPServer()

                        # Should log warning about invalid value
                        warning_calls = [
                            call
                            for call in mock_logger.warning.call_args_list
                            if "Invalid PHASER_DOCS_MAX_RETRIES" in str(call)
                        ]
                        assert len(warning_calls) >= 1

    def test_server_environment_variables_invalid_cache_ttl(self, monkeypatch):
        """Test server environment variables with invalid cache TTL."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("PHASER_DOCS_CACHE_TTL", "invalid")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_setup_logging"):
                        PhaserMCPServer()

                        # Should log warning about invalid value
                        warning_calls = [
                            call
                            for call in mock_logger.warning.call_args_list
                            if "Invalid PHASER_DOCS_CACHE_TTL" in str(call)
                        ]
                        assert len(warning_calls) >= 1

    def test_server_environment_variables_negative_cache_ttl(self, monkeypatch):
        """Test server environment variables with negative cache TTL."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("PHASER_DOCS_CACHE_TTL", "-100")

        with patch("phaser_mcp_server.server.logger") as mock_logger:
            with patch("phaser_mcp_server.server.PhaserDocsClient"):
                with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                    with patch.object(PhaserMCPServer, "_setup_logging"):
                        PhaserMCPServer()

                        # Should log warning about invalid value
                        warning_calls = [
                            call
                            for call in mock_logger.warning.call_args_list
                            if "Invalid PHASER_DOCS_CACHE_TTL" in str(call)
                        ]
                        assert len(warning_calls) >= 1

    def test_client_initialization(self):
        """Test client initialization during server creation."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        server_instance = PhaserMCPServer()

                        # Should create client instance
                        mock_client_class.assert_called_once()
                        assert hasattr(server_instance, "client")

    def test_parser_initialization(self):
        """Test parser initialization during server creation."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient"):
            with patch(
                "phaser_mcp_server.server.PhaserDocumentParser"
            ) as mock_parser_class:
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        server_instance = PhaserMCPServer()

                        # Should create parser instance
                        mock_parser_class.assert_called_once()
                        assert hasattr(server_instance, "parser")

    @pytest.mark.asyncio
    async def test_server_async_initialization(self):
        """Test server async initialization."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        mock_client = AsyncMock()
                        mock_client_class.return_value = mock_client

                        server_instance = PhaserMCPServer()
                        await server_instance.initialize()

                        # Should initialize client
                        mock_client.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_async_initialization_with_health_check(self):
        """Test server async initialization with successful health check."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        mock_client = AsyncMock()
                        mock_client_class.return_value = mock_client

                        server_instance = PhaserMCPServer()
                        await server_instance.initialize()

                        # Should perform health check
                        mock_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_async_initialization_health_check_failure(self):
        """Test server async initialization with failed health check."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client.health_check.side_effect = Exception(
                                "Health check failed"
                            )
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()
                            # Should not raise exception, just log warning
                            await server_instance.initialize()

                            # Should log warning about health check failure
                            warning_calls = [
                                call
                                for call in mock_logger.warning.call_args_list
                                if "health check failed" in str(call)
                            ]
                            assert len(warning_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_async_initialization_failure(self):
        """Test server async initialization failure."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        mock_client = AsyncMock()
                        mock_client.initialize.side_effect = Exception("Init failed")
                        mock_client_class.return_value = mock_client

                        server_instance = PhaserMCPServer()

                        with pytest.raises(
                            RuntimeError, match="Server initialization failed"
                        ):
                            await server_instance.initialize()

    def test_get_server_info(self):
        """Test get_server_info method."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient"):
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        server_instance = PhaserMCPServer()
                        info = server_instance.get_server_info()

                        assert isinstance(info, dict)
                        assert "name" in info
                        assert "version" in info
                        assert "status" in info
                        assert "log_level" in info
                        assert "environment_variables" in info
                        assert info["name"] == "phaser-mcp-server"
                        assert info["version"] == "1.0.0"
                        assert info["status"] == "running"

    def test_get_server_info_with_environment_variables(self, monkeypatch):
        """Test get_server_info with custom environment variables."""
        from phaser_mcp_server.server import PhaserMCPServer

        monkeypatch.setenv("FASTMCP_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("PHASER_DOCS_TIMEOUT", "60")

        with patch("phaser_mcp_server.server.PhaserDocsClient"):
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        server_instance = PhaserMCPServer()
                        info = server_instance.get_server_info()

                        assert info["log_level"] == "DEBUG"
                        assert (
                            info["environment_variables"]["FASTMCP_LOG_LEVEL"]
                            == "DEBUG"
                        )
                        assert (
                            info["environment_variables"]["PHASER_DOCS_TIMEOUT"] == "60"
                        )

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
            assert args.log_level is None
            assert args.timeout is None
            assert args.max_retries is None
            assert args.cache_ttl is None
            assert args.info is False
            assert args.health_check is False

    def test_parse_arguments_version(self):
        """Test parsing version argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--version"]):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_arguments_help(self):
        """Test parsing help argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--help"]):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_arguments_log_level_debug(self):
        """Test parsing log level DEBUG argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--log-level", "DEBUG"]):
            args = parse_arguments()
            assert args.log_level == "DEBUG"

    def test_parse_arguments_log_level_info(self):
        """Test parsing log level INFO argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--log-level", "INFO"]):
            args = parse_arguments()
            assert args.log_level == "INFO"

    def test_parse_arguments_log_level_error(self):
        """Test parsing log level ERROR argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--log-level", "ERROR"]):
            args = parse_arguments()
            assert args.log_level == "ERROR"

    def test_parse_arguments_log_level_critical(self):
        """Test parsing log level CRITICAL argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--log-level", "CRITICAL"]):
            args = parse_arguments()
            assert args.log_level == "CRITICAL"

    def test_parse_arguments_invalid_log_level(self):
        """Test parsing invalid log level argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--log-level", "INVALID"]):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_arguments_timeout(self):
        """Test parsing timeout argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--timeout", "45"]):
            args = parse_arguments()
            assert args.timeout == 45

    def test_parse_arguments_timeout_zero(self):
        """Test parsing timeout argument with zero value."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--timeout", "0"]):
            args = parse_arguments()
            assert args.timeout == 0

    def test_parse_arguments_timeout_negative(self):
        """Test parsing timeout argument with negative value."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--timeout", "-10"]):
            args = parse_arguments()
            assert args.timeout == -10

    def test_parse_arguments_timeout_invalid(self):
        """Test parsing invalid timeout argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--timeout", "invalid"]):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_arguments_max_retries(self):
        """Test parsing max retries argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--max-retries", "5"]):
            args = parse_arguments()
            assert args.max_retries == 5

    def test_parse_arguments_max_retries_zero(self):
        """Test parsing max retries argument with zero value."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--max-retries", "0"]):
            args = parse_arguments()
            assert args.max_retries == 0

    def test_parse_arguments_max_retries_negative(self):
        """Test parsing max retries argument with negative value."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--max-retries", "-1"]):
            args = parse_arguments()
            assert args.max_retries == -1

    def test_parse_arguments_max_retries_invalid(self):
        """Test parsing invalid max retries argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--max-retries", "invalid"]):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_arguments_cache_ttl(self):
        """Test parsing cache TTL argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--cache-ttl", "7200"]):
            args = parse_arguments()
            assert args.cache_ttl == 7200

    def test_parse_arguments_cache_ttl_zero(self):
        """Test parsing cache TTL argument with zero value."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--cache-ttl", "0"]):
            args = parse_arguments()
            assert args.cache_ttl == 0

    def test_parse_arguments_cache_ttl_negative(self):
        """Test parsing cache TTL argument with negative value."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--cache-ttl", "-100"]):
            args = parse_arguments()
            assert args.cache_ttl == -100

    def test_parse_arguments_cache_ttl_invalid(self):
        """Test parsing invalid cache TTL argument."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--cache-ttl", "invalid"]):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_arguments_info_flag(self):
        """Test parsing info flag."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--info"]):
            args = parse_arguments()
            assert args.info is True

    def test_parse_arguments_health_check_flag(self):
        """Test parsing health check flag."""
        from phaser_mcp_server.server import parse_arguments

        with patch("sys.argv", ["phaser-mcp-server", "--health-check"]):
            args = parse_arguments()
            assert args.health_check is True

    def test_parse_arguments_multiple_options(self):
        """Test parsing multiple arguments."""
        from phaser_mcp_server.server import parse_arguments

        with patch(
            "sys.argv",
            [
                "phaser-mcp-server",
                "--log-level",
                "DEBUG",
                "--timeout",
                "60",
                "--max-retries",
                "3",
                "--cache-ttl",
                "3600",
            ],
        ):
            args = parse_arguments()
            assert args.log_level == "DEBUG"
            assert args.timeout == 60
            assert args.max_retries == 3
            assert args.cache_ttl == 3600

    def test_parse_arguments_with_options(self):
        """Test parsing arguments with options."""
        from phaser_mcp_server.server import parse_arguments

        with patch(
            "sys.argv", ["phaser-mcp-server", "--log-level", "DEBUG", "--timeout", "60"]
        ):
            args = parse_arguments()
            assert args.log_level == "DEBUG"
            assert args.timeout == 60

    def test_apply_cli_arguments_all_options(self):
        """Test applying all CLI arguments to environment."""
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

    def test_apply_cli_arguments_partial_options(self):
        """Test applying partial CLI arguments to environment."""
        from phaser_mcp_server.server import apply_cli_arguments

        # Mock arguments with only some options set
        args = Mock()
        args.log_level = "WARNING"
        args.timeout = None
        args.max_retries = None
        args.cache_ttl = None

        # Apply arguments
        apply_cli_arguments(args)

        # Check only log level was set
        assert os.environ.get("FASTMCP_LOG_LEVEL") == "WARNING"

    def test_apply_cli_arguments_none_options(self):
        """Test applying CLI arguments when all are None."""
        from phaser_mcp_server.server import apply_cli_arguments

        # Mock arguments with all None
        args = Mock()
        args.log_level = None
        args.timeout = None
        args.max_retries = None
        args.cache_ttl = None

        # Store original environment
        original_log_level = os.environ.get("FASTMCP_LOG_LEVEL")

        # Apply arguments
        apply_cli_arguments(args)

        # Environment should remain unchanged
        assert os.environ.get("FASTMCP_LOG_LEVEL") == original_log_level

    def test_apply_cli_arguments_invalid_timeout(self):
        """Test applying CLI arguments with invalid timeout."""
        from phaser_mcp_server.server import apply_cli_arguments

        # Mock arguments with invalid timeout
        args = Mock()
        args.log_level = None
        args.timeout = -10
        args.max_retries = None
        args.cache_ttl = None

        with pytest.raises(SystemExit) as exc_info:
            apply_cli_arguments(args)

        assert exc_info.value.code == 1

    def test_apply_cli_arguments_invalid_max_retries(self):
        """Test applying CLI arguments with invalid max retries."""
        from phaser_mcp_server.server import apply_cli_arguments

        # Mock arguments with invalid max retries
        args = Mock()
        args.log_level = None
        args.timeout = None
        args.max_retries = -5
        args.cache_ttl = None

        with pytest.raises(SystemExit) as exc_info:
            apply_cli_arguments(args)

        assert exc_info.value.code == 1

    def test_apply_cli_arguments_invalid_cache_ttl(self):
        """Test applying CLI arguments with invalid cache TTL."""
        from phaser_mcp_server.server import apply_cli_arguments

        # Mock arguments with invalid cache TTL
        args = Mock()
        args.log_level = None
        args.timeout = None
        args.max_retries = None
        args.cache_ttl = -100

        with pytest.raises(SystemExit) as exc_info:
            apply_cli_arguments(args)

        assert exc_info.value.code == 1

    def test_apply_cli_arguments_zero_values(self):
        """Test applying CLI arguments with zero values."""
        from phaser_mcp_server.server import apply_cli_arguments

        # Mock arguments with zero values (should be valid for retries and cache_ttl)
        args = Mock()
        args.log_level = None
        args.timeout = 30  # Positive timeout
        args.max_retries = 0  # Zero retries should be valid
        args.cache_ttl = 0  # Zero cache TTL should be valid

        # Apply arguments - should not raise exception
        apply_cli_arguments(args)

        # Check environment variables were set
        assert os.environ.get("PHASER_DOCS_TIMEOUT") == "30"
        assert os.environ.get("PHASER_DOCS_MAX_RETRIES") == "0"
        assert os.environ.get("PHASER_DOCS_CACHE_TTL") == "0"

    def test_apply_cli_arguments(self):
        """Test applying CLI arguments to environment."""
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


class TestServerCleanup:
    """Test server cleanup functionality."""

    @pytest.mark.asyncio
    async def test_server_cleanup_success(self):
        """Test successful server cleanup."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()
                            await server_instance.cleanup()

                            # Should close client
                            mock_client.close.assert_called_once()

                            # Should log successful cleanup
                            info_calls = [
                                call
                                for call in mock_logger.info.call_args_list
                                if "cleanup completed successfully" in str(call)
                            ]
                            assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_client_error(self):
        """Test server cleanup with client error."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client.close.side_effect = Exception("Close failed")
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()
                            # Should not raise exception
                            await server_instance.cleanup()

                            # Should log error
                            error_calls = [
                                call
                                for call in mock_logger.error.call_args_list
                                if "Error closing HTTP client" in str(call)
                            ]
                            assert len(error_calls) >= 1

                            # Should log warning about cleanup errors
                            warning_calls = [
                                call
                                for call in mock_logger.warning.call_args_list
                                if "cleanup completed with" in str(call)
                            ]
                            assert len(warning_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_missing_client(self):
        """Test server cleanup when client is missing."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient"):
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            server_instance = PhaserMCPServer()
                            # Remove client attribute
                            delattr(server_instance, "client")

                            # Should not raise exception
                            await server_instance.cleanup()

                            # Should log successful cleanup
                            info_calls = [
                                call
                                for call in mock_logger.info.call_args_list
                                if "cleanup completed successfully" in str(call)
                            ]
                            assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_none_client(self):
        """Test server cleanup when client is None."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient"):
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            server_instance = PhaserMCPServer()
                            server_instance.client = None

                            # Should not raise exception
                            await server_instance.cleanup()

                            # Should log successful cleanup
                            info_calls = [
                                call
                                for call in mock_logger.info.call_args_list
                                if "cleanup completed successfully" in str(call)
                            ]
                            assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_parser_handling(self):
        """Test server cleanup handles parser properly."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()
                            await server_instance.cleanup()

                            # Should log parser cleanup
                            debug_calls = [
                                call
                                for call in mock_logger.debug.call_args_list
                                if "Parser cleanup completed" in str(call)
                            ]
                            assert len(debug_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_missing_parser(self):
        """Test server cleanup when parser is missing."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()
                            # Remove parser attribute
                            delattr(server_instance, "parser")

                            # Should not raise exception
                            await server_instance.cleanup()

                            # Should still complete successfully
                            info_calls = [
                                call
                                for call in mock_logger.info.call_args_list
                                if "cleanup completed successfully" in str(call)
                            ]
                            assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_none_parser(self):
        """Test server cleanup when parser is None."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()
                            server_instance.parser = None

                            # Should not raise exception
                            await server_instance.cleanup()

                            # Should still complete successfully
                            info_calls = [
                                call
                                for call in mock_logger.info.call_args_list
                                if "cleanup completed successfully" in str(call)
                            ]
                            assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_multiple_errors(self):
        """Test server cleanup with multiple errors."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client.close.side_effect = Exception("Client error")
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()

                            # Mock parser to also have an error (hypothetical future case)
                            with patch.object(server_instance, "parser") as mock_parser:
                                # Simulate parser cleanup error
                                def side_effect():
                                    raise Exception("Parser error")

                                # Should not raise exception
                                await server_instance.cleanup()

                                # Should log multiple errors
                                error_calls = [
                                    call
                                    for call in mock_logger.error.call_args_list
                                    if "Error closing HTTP client" in str(call)
                                ]
                                assert len(error_calls) >= 1

                                # Should log warning about cleanup errors
                                warning_calls = [
                                    call
                                    for call in mock_logger.warning.call_args_list
                                    if "cleanup completed with" in str(call)
                                ]
                                assert len(warning_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_logging_messages(self):
        """Test server cleanup logging messages."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()
                            await server_instance.cleanup()

                            # Should log starting cleanup
                            info_calls = [
                                call
                                for call in mock_logger.info.call_args_list
                                if "Starting server cleanup" in str(call)
                            ]
                            assert len(info_calls) >= 1

                            # Should log client closed
                            debug_calls = [
                                call
                                for call in mock_logger.debug.call_args_list
                                if "HTTP client closed successfully" in str(call)
                            ]
                            assert len(debug_calls) >= 1

                            # Should log completion
                            info_calls = [
                                call
                                for call in mock_logger.info.call_args_list
                                if "cleanup completed successfully" in str(call)
                            ]
                            assert len(info_calls) >= 1

    @pytest.mark.asyncio
    async def test_server_cleanup_exception_during_cleanup(self):
        """Test server cleanup when exception occurs during cleanup process."""
        from phaser_mcp_server.server import PhaserMCPServer

        with patch("phaser_mcp_server.server.PhaserDocsClient") as mock_client_class:
            with patch("phaser_mcp_server.server.PhaserDocumentParser"):
                with patch.object(PhaserMCPServer, "_setup_logging"):
                    with patch.object(PhaserMCPServer, "_load_environment_variables"):
                        with patch("phaser_mcp_server.server.logger") as mock_logger:
                            mock_client = AsyncMock()
                            mock_client.close.side_effect = RuntimeError(
                                "Unexpected error"
                            )
                            mock_client_class.return_value = mock_client

                            server_instance = PhaserMCPServer()

                            # Should handle exception gracefully
                            await server_instance.cleanup()

                            # Should log the error
                            error_calls = [
                                call
                                for call in mock_logger.error.call_args_list
                                if "Error closing HTTP client" in str(call)
                            ]
                            assert len(error_calls) >= 1


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
