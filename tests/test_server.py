"""Unit tests for the MCP server module.

This module contains comprehensive tests for the MCP server functionality
including tool functions, initialization, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from mcp import Context

from phaser_mcp_server.server import (
    read_documentation,
    search_documentation,
    get_api_reference,
    main,
    server,
)
from phaser_mcp_server.models import DocumentationPage, SearchResult, ApiReference


class MockContext:
    """Mock MCP context for testing."""
    pass


class TestServerInitialization:
    """Test server initialization and configuration."""

    def test_server_initialization(self):
        """Test that server is properly initialized."""
        assert server is not None
        assert hasattr(server, 'client')
        assert hasattr(server, 'parser')

    def test_server_components_initialization(self):
        """Test that server components are properly initialized."""
        # Check that client and parser are initialized
        assert server.client is not None
        assert server.parser is not None


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
            content="<h1>Test</h1><p>Test content</p>"
        )
        
        with patch.object(server.client, 'get_page_content', return_value=mock_page) as mock_get_page:
            with patch.object(server.parser, 'parse_html_content') as mock_parse:
                with patch.object(server.parser, 'convert_to_markdown', return_value="# Test\n\nTest content") as mock_convert:
                    mock_parse.return_value = {
                        "title": "Test",
                        "content": "<h1>Test</h1><p>Test content</p>",
                        "text_content": "Test content"
                    }
                    
                    result = await read_documentation(
                        mock_context, 
                        "https://docs.phaser.io/phaser/test"
                    )
                    
                    assert result == "# Test\n\nTest content"
                    mock_get_page.assert_called_once_with("https://docs.phaser.io/phaser/test")
                    mock_parse.assert_called_once()
                    mock_convert.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_documentation_with_pagination(self, mock_context):
        """Test documentation reading with pagination parameters."""
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<h1>Test</h1><p>Test content</p>"
        )
        
        with patch.object(server.client, 'get_page_content', return_value=mock_page):
            with patch.object(server.parser, 'parse_html_content'):
                with patch.object(server.parser, 'convert_to_markdown', return_value="This is a long test content for pagination"):
                    result = await read_documentation(
                        mock_context,
                        "https://docs.phaser.io/phaser/test",
                        max_length=10,
                        start_index=5
                    )
                    
                    # Should return paginated content
                    assert len(result) <= 10
                    assert result == "is a long"

    @pytest.mark.asyncio
    async def test_read_documentation_invalid_parameters(self, mock_context):
        """Test read_documentation with invalid parameters."""
        # Test negative max_length
        with pytest.raises(RuntimeError, match="max_length must be positive"):
            await read_documentation(
                mock_context,
                "https://docs.phaser.io/phaser/test",
                max_length=-1
            )
        
        # Test negative start_index
        with pytest.raises(RuntimeError, match="start_index must be non-negative"):
            await read_documentation(
                mock_context,
                "https://docs.phaser.io/phaser/test",
                start_index=-1
            )

    @pytest.mark.asyncio
    async def test_read_documentation_start_index_beyond_content(self, mock_context):
        """Test read_documentation when start_index is beyond content length."""
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<h1>Test</h1><p>Test content</p>"
        )
        
        with patch.object(server.client, 'get_page_content', return_value=mock_page):
            with patch.object(server.parser, 'parse_html_content'):
                with patch.object(server.parser, 'convert_to_markdown', return_value="Short content"):
                    result = await read_documentation(
                        mock_context,
                        "https://docs.phaser.io/phaser/test",
                        start_index=100
                    )
                    
                    # Should return empty string
                    assert result == ""

    @pytest.mark.asyncio
    async def test_read_documentation_error_handling(self, mock_context):
        """Test read_documentation error handling."""
        with patch.object(server.client, 'get_page_content', side_effect=Exception("Network error")):
            with pytest.raises(RuntimeError, match="Failed to read documentation"):
                await read_documentation(
                    mock_context,
                    "https://docs.phaser.io/phaser/test"
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
                relevance_score=0.95
            )
        ]
        
        with patch.object(server.client, 'search_content', return_value=mock_results) as mock_search:
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
        
        with patch.object(server.client, 'search_content', return_value=mock_results) as mock_search:
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
        with patch.object(server.client, 'search_content', side_effect=Exception("Search error")):
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
            examples=["const sprite = this.add.sprite(0, 0, 'key');"]
        )
        
        with patch.object(server.client, 'get_api_reference', return_value=mock_api_ref) as mock_get_api:
            with patch.object(server.parser, 'format_api_reference_to_markdown', return_value="# Sprite\n\nA sprite game object") as mock_format:
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
        with patch.object(server.client, 'get_api_reference', side_effect=Exception("API error")):
            with pytest.raises(RuntimeError, match="Failed to get API reference"):
                await get_api_reference(mock_context, "TestClass")


class TestMainFunction:
    """Test the main function and CLI entry point."""

    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        assert callable(main)

    @patch('phaser_mcp_server.server.mcp')
    def test_main_function_calls_mcp_run(self, mock_mcp):
        """Test that main function calls mcp.run()."""
        # Mock the mcp.run method
        mock_mcp.run.return_value = None
        
        # Call main function
        main()
        
        # Verify mcp.run was called
        mock_mcp.run.assert_called_once()


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
            content="<h1>Test</h1><p>Test content</p>"
        )
        
        with patch.object(server.client, 'get_page_content', return_value=mock_page):
            with patch.object(server.parser, 'parse_html_content'):
                with patch.object(server.parser, 'convert_to_markdown', return_value="This is a test content with multiple words"):
                    result = await read_documentation(
                        mock_context,
                        "https://docs.phaser.io/phaser/test",
                        max_length=20,
                        start_index=0
                    )
                    
                    # Should cut at word boundary
                    assert not result.endswith(" ")
                    assert len(result) <= 20

    @pytest.mark.asyncio
    async def test_empty_search_results(self, mock_context):
        """Test handling of empty search results."""
        with patch.object(server.client, 'search_content', return_value=[]):
            result = await search_documentation(mock_context, "nonexistent")
            
            assert result == []

    @pytest.mark.asyncio
    async def test_api_reference_formatting_error(self, mock_context):
        """Test handling of API reference formatting errors."""
        mock_api_ref = ApiReference(
            class_name="TestClass",
            url="https://docs.phaser.io/api/TestClass",
            description="Test class"
        )
        
        with patch.object(server.client, 'get_api_reference', return_value=mock_api_ref):
            with patch.object(server.parser, 'format_api_reference_to_markdown', side_effect=Exception("Format error")):
                with pytest.raises(RuntimeError, match="Failed to get API reference"):
                    await get_api_reference(mock_context, "TestClass")
