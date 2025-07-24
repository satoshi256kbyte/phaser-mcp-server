"""Integration tests for MCP tools.

This module contains integration tests for the MCP tools, testing the interaction
between different components of the Phaser MCP Server, including the server,
client, and parser modules.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from phaser_mcp_server.client import PhaserDocsClient
from phaser_mcp_server.models import ApiReference, DocumentationPage, SearchResult
from phaser_mcp_server.parser import PhaserDocumentParser
from phaser_mcp_server.server import (
    get_api_reference,
    read_documentation,
    search_documentation,
)


class MockContext:
    """Mock MCP context for testing."""

    def __init__(self) -> None:
        """Initialize mock context with test values."""
        self.session_id = "test-session"
        self.request_id = "test-request"
        self.user_id = "test-user"


class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.fixture
    def sample_html(self) -> str:
        """Sample HTML content for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phaser Sprite Tutorial - Phaser Documentation</title>
        </head>
        <body>
            <nav class="navigation">Navigation content</nav>
            <main class="content">
                <h1>Working with Sprites</h1>
                <p>Sprites are the basic building blocks of Phaser games.</p>
                <h2>Creating a Sprite</h2>
                <p>To create a sprite, use the following code:</p>
                <pre><code class="language-javascript">
const sprite = this.add.sprite(100, 100, 'player');
sprite.setScale(2);
                </code></pre>
                <h3>Sprite Properties</h3>
                <ul>
                    <li>x: X position</li>
                    <li>y: Y position</li>
                    <li>texture: Sprite texture</li>
                </ul>
            </main>
            <footer class="footer">Footer content</footer>
        </body>
        </html>
        """

    @pytest.fixture
    def api_html(self) -> str:
        """Sample API documentation HTML."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phaser.GameObjects.Sprite - API Reference</title>
        </head>
        <body>
            <main class="api-content">
                <h1 class="class-name">Phaser.GameObjects.Sprite</h1>
                <div class="description">
                    A Sprite Game Object is used to display a texture on screen.
                </div>
                <div class="methods">
                    <div class="method">setTexture</div>
                    <div class="method">setPosition</div>
                    <div class="method">destroy</div>
                </div>
                <div class="properties">
                    <div class="property">x</div>
                    <div class="property">y</div>
                    <div class="property">texture</div>
                </div>
                <div class="examples">
                    <div class="example">
                        const sprite = this.add.sprite(0, 0, 'key');
                    </div>
                </div>
            </main>
        </body>
        </html>
        """

    @pytest.fixture
    def search_results_html(self) -> str:
        """Sample search results HTML."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Search Results - Phaser Documentation</title>
        </head>
        <body>
            <main class="search-results">
                <h1>Search Results for "sprite"</h1>
                <div class="result">
                    <h3><a href="/phaser/sprites">Working with Sprites</a></h3>
                    <p>Sprites are the basic building blocks of Phaser games...</p>
                </div>
                <div class="result">
                    <h3><a href="/api/Phaser.GameObjects.Sprite">Phaser.Sprite</a></h3>
                    <p>A Sprite Game Object is used to display a texture...</p>
                </div>
                <div class="result">
                    <h3><a href="/phaser/animations">Sprite Animations</a></h3>
                    <p>Learn how to animate sprites in your Phaser games...</p>
                </div>
            </main>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_read_documentation_integration(
        self, mock_context: MockContext, sample_html: str
    ):
        """Test read_documentation tool integration."""
        # Mock the HTTP client to return sample HTML
        with patch("httpx.AsyncClient.get") as mock_get:
            # Setup mock response
            mock_response = Mock()
            mock_response.text = sample_html
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.url = "https://docs.phaser.io/phaser/sprites"
            mock_response._content = sample_html.encode("utf-8")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Call the MCP tool
            result = await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/sprites"
            )

            # Verify the result
            assert isinstance(result, str)
            assert "# Working with Sprites" in result
            assert "Sprites are the basic building blocks" in result
            assert "```javascript" in result
            assert "const sprite = this.add.sprite" in result
            assert "## Creating a Sprite" in result
            assert "### Sprite Properties" in result
            assert "- x: X position" in result or "* x: X position" in result

            # Verify HTTP client was called correctly
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert "https://docs.phaser.io/phaser/sprites" in args or kwargs.get(
                "url", ""
            )

    @pytest.mark.asyncio
    async def test_read_documentation_with_pagination(
        self, mock_context: MockContext, sample_html: str
    ):
        """Test read_documentation tool with pagination parameters."""
        # Mock the HTTP client to return sample HTML
        with patch("httpx.AsyncClient.get") as mock_get:
            # Setup mock response
            mock_response = Mock()
            mock_response.text = sample_html
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.url = "https://docs.phaser.io/phaser/sprites"
            mock_response._content = sample_html.encode("utf-8")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Call the MCP tool with pagination parameters
            result = await read_documentation(
                mock_context,
                "https://docs.phaser.io/phaser/sprites",
                max_length=50,
                start_index=10,
            )

            # Verify the result
            assert isinstance(result, str)
            assert len(result) <= 50

            # Verify HTTP client was called correctly
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_documentation_error_handling(self, mock_context: MockContext):
        """Test read_documentation tool error handling."""
        # Mock the HTTP client to raise an exception
        with patch("httpx.AsyncClient.get") as mock_get:
            # Setup mock to raise HTTP error
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.url = "https://docs.phaser.io/nonexistent"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response

            # Call the MCP tool and expect an exception
            with pytest.raises(RuntimeError) as exc_info:
                await read_documentation(
                    mock_context, "https://docs.phaser.io/nonexistent"
                )

            # Verify the error message
            assert "Failed to read documentation" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_documentation_integration(
        self, mock_context: MockContext, search_results_html: str
    ):
        """Test search_documentation tool integration."""
        # Mock the client's search_content method
        with patch(
            "phaser_mcp_server.client.PhaserDocsClient.search_content"
        ) as mock_search:
            # Setup mock search results
            mock_results = [
                SearchResult(
                    rank_order=1,
                    url="https://docs.phaser.io/phaser/sprites",
                    title="Working with Sprites",
                    snippet="Sprites are the basic building blocks of Phaser games...",
                    relevance_score=0.95,
                ),
                SearchResult(
                    rank_order=2,
                    url="https://docs.phaser.io/api/Phaser.GameObjects.Sprite",
                    title="Phaser.GameObjects.Sprite",
                    snippet="A Sprite Game Object is used to display a texture...",
                    relevance_score=0.85,
                ),
                SearchResult(
                    rank_order=3,
                    url="https://docs.phaser.io/phaser/animations",
                    title="Sprite Animations",
                    snippet="Learn how to animate sprites in your Phaser games...",
                    relevance_score=0.75,
                ),
            ]
            mock_search.return_value = mock_results

            # Call the MCP tool
            result = await search_documentation(mock_context, "sprite", limit=5)

            # Verify the result
            assert isinstance(result, list)
            assert len(result) == 3

            # Check first result
            assert result[0]["rank_order"] == 1
            assert result[0]["url"] == "https://docs.phaser.io/phaser/sprites"
            assert result[0]["title"] == "Working with Sprites"
            assert "building blocks" in result[0]["snippet"]
            assert result[0]["relevance_score"] == 0.95

            # Verify search was called correctly
            mock_search.assert_called_once_with("sprite", 5)

    @pytest.mark.asyncio
    async def test_search_documentation_empty_results(self, mock_context: MockContext):
        """Test search_documentation tool with empty results."""
        # Mock the client's search_content method to return empty results
        with patch(
            "phaser_mcp_server.client.PhaserDocsClient.search_content"
        ) as mock_search:
            mock_search.return_value = []

            # Call the MCP tool
            result = await search_documentation(mock_context, "nonexistent", limit=5)

            # Verify the result
            assert isinstance(result, list)
            assert len(result) == 0

            # Verify search was called correctly
            mock_search.assert_called_once_with("nonexistent", 5)

    @pytest.mark.asyncio
    async def test_search_documentation_error_handling(self, mock_context: MockContext):
        """Test search_documentation tool error handling."""
        # Mock the client's search_content method to raise an exception
        with patch(
            "phaser_mcp_server.client.PhaserDocsClient.search_content"
        ) as mock_search:
            mock_search.side_effect = ValueError("Invalid search query")

            # Call the MCP tool and expect an exception
            with pytest.raises(RuntimeError) as exc_info:
                await search_documentation(mock_context, "", limit=5)

            # Verify the error message
            assert "Failed to search documentation" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_api_reference_integration(
        self, mock_context: MockContext, api_html: str
    ):
        """Test get_api_reference tool integration."""
        # Mock the HTTP client to return API HTML
        with patch("httpx.AsyncClient.get") as mock_get:
            # Setup mock response
            mock_response = Mock()
            mock_response.text = api_html
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.url = "https://docs.phaser.io/api/Phaser.GameObjects.Sprite"
            mock_response._content = api_html.encode("utf-8")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Call the MCP tool
            result = await get_api_reference(mock_context, "Sprite")

            # Verify the result
            assert isinstance(result, str)
            assert "# Sprite" in result or "# Phaser.GameObjects.Sprite" in result
            assert (
                "A Sprite Game Object is used to display a texture on screen" in result
            )
            assert "## Methods" in result
            assert "- setTexture" in result or "* setTexture" in result
            assert "- setPosition" in result or "* setPosition" in result
            assert "- destroy" in result or "* destroy" in result
            assert "## Properties" in result
            assert "- x" in result or "* x" in result
            assert "- y" in result or "* y" in result
            assert "- texture" in result or "* texture" in result
            # Examples section might not be present in all API references
            if "## Examples" in result:
                assert "```javascript" in result
                assert "this.add.sprite" in result

            # Verify HTTP client was called correctly
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_api_reference_error_handling(self, mock_context: MockContext):
        """Test get_api_reference tool error handling."""
        # Mock the HTTP client to raise an exception
        with patch("httpx.AsyncClient.get") as mock_get:
            # Setup mock to raise HTTP error
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.url = "https://docs.phaser.io/api/NonExistentClass"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response

            # Call the MCP tool and expect an exception
            with pytest.raises(RuntimeError) as exc_info:
                await get_api_reference(mock_context, "NonExistentClass")

            # Verify the error message
            assert "Failed to get API reference" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_mcp_tools_parameter_validation(self, mock_context: MockContext):
        """Test parameter validation in MCP tools."""
        # Test read_documentation with invalid parameters
        with pytest.raises(RuntimeError):
            await read_documentation(mock_context, "", max_length=100)

        with pytest.raises(RuntimeError):
            await read_documentation(
                mock_context, "https://docs.phaser.io/test", max_length=-1
            )

        with pytest.raises(RuntimeError):
            await read_documentation(
                mock_context, "https://docs.phaser.io/test", start_index=-1
            )

        # Test search_documentation with invalid parameters
        with pytest.raises(RuntimeError):
            await search_documentation(mock_context, "", limit=5)

        with pytest.raises(RuntimeError):
            await search_documentation(mock_context, "test", limit=0)

        with pytest.raises(RuntimeError):
            await search_documentation(mock_context, "test", limit=-1)

        # Test get_api_reference with invalid parameters
        with pytest.raises(RuntimeError):
            await get_api_reference(mock_context, "")


class TestMCPToolsComponentIntegration:
    """Integration tests for MCP tools with component interactions."""

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.mark.asyncio
    async def test_read_documentation_component_integration(
        self, mock_context: MockContext
    ):
        """Test read_documentation integration with client and parser components."""
        # Create mock components
        mock_client = AsyncMock(spec=PhaserDocsClient)
        mock_parser = Mock(spec=PhaserDocumentParser)

        # Setup mock client response
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<html><body><h1>Test</h1></body></html>",
        )
        mock_client.get_page_content.return_value = mock_page

        # Setup mock parser response
        mock_parser.parse_html_content.return_value = {
            "title": "Test Page",
            "content": Mock(),  # BeautifulSoup object
            "text_content": "Test content",
            "code_blocks": [],
        }
        mock_parser.convert_to_markdown.return_value = "# Test Page\n\nTest content"

        # Patch the server components
        with patch("phaser_mcp_server.server.server") as mock_server:
            mock_server.client = mock_client
            mock_server.parser = mock_parser

            # Call the MCP tool
            result = await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/test"
            )

            # Verify the result
            assert result == "# Test Page\n\nTest content"

            # Verify component interactions
            mock_client.get_page_content.assert_called_once_with(
                "https://docs.phaser.io/phaser/test"
            )
            mock_parser.parse_html_content.assert_called_once_with(
                mock_page.content, "https://docs.phaser.io/phaser/test"
            )
            mock_parser.convert_to_markdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_documentation_component_integration(
        self, mock_context: MockContext
    ):
        """Test search_documentation integration with client component."""
        # Create mock client
        mock_client = AsyncMock(spec=PhaserDocsClient)

        # Setup mock search results
        mock_results = [
            SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test Page",
                snippet="Test snippet",
                relevance_score=0.9,
            )
        ]
        mock_client.search_content.return_value = mock_results

        # Patch the server components
        with patch("phaser_mcp_server.server.server") as mock_server:
            mock_server.client = mock_client

            # Call the MCP tool
            result = await search_documentation(mock_context, "test", limit=5)

            # Verify the result
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["rank_order"] == 1
            assert result[0]["url"] == "https://docs.phaser.io/phaser/test"
            assert result[0]["title"] == "Test Page"
            assert result[0]["snippet"] == "Test snippet"
            assert result[0]["relevance_score"] == 0.9

            # Verify component interactions
            mock_client.search_content.assert_called_once_with("test", 5)

    @pytest.mark.asyncio
    async def test_get_api_reference_component_integration(
        self, mock_context: MockContext
    ):
        """Test get_api_reference integration with client and parser components."""
        # Create mock components
        mock_client = AsyncMock(spec=PhaserDocsClient)
        mock_parser = Mock(spec=PhaserDocumentParser)

        # Setup mock client response
        mock_api_ref = ApiReference(
            class_name="TestClass",
            url="https://docs.phaser.io/api/TestClass",
            description="Test class description",
            methods=["method1", "method2"],
            properties=["prop1", "prop2"],
            examples=["const test = new TestClass();"],
        )
        mock_client.get_api_reference.return_value = mock_api_ref

        # Setup mock parser response
        mock_parser.format_api_reference_to_markdown.return_value = (
            "# TestClass\n\nTest class description\n\n"
            "## Methods\n- method1\n- method2\n\n"
            "## Properties\n- prop1\n- prop2\n\n"
            "## Examples\n```javascript\nconst test = new TestClass();\n```"
        )

        # Patch the server components
        with patch("phaser_mcp_server.server.server") as mock_server:
            mock_server.client = mock_client
            mock_server.parser = mock_parser

            # Call the MCP tool
            result = await get_api_reference(mock_context, "TestClass")

            # Verify the result
            assert "# TestClass" in result
            assert "Test class description" in result
            assert "## Methods" in result
            assert "- method1" in result or "* method1" in result
            assert "## Properties" in result
            assert "## Examples" in result
            assert "```javascript" in result

            # Verify component interactions
            mock_client.get_api_reference.assert_called_once_with("TestClass")
            mock_parser.format_api_reference_to_markdown.assert_called_once_with(
                mock_api_ref
            )


class TestMCPToolsErrorCases:
    """Test error cases for MCP tools."""

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.mark.asyncio
    async def test_read_documentation_client_error(self, mock_context: MockContext):
        """Test read_documentation with client error."""
        # Patch the client to raise an exception
        with patch(
            "phaser_mcp_server.client.PhaserDocsClient.get_page_content"
        ) as mock_get_page:
            mock_get_page.side_effect = ValueError("Invalid URL")

            # Call the MCP tool and expect an exception
            with pytest.raises(RuntimeError) as exc_info:
                await read_documentation(mock_context, "https://docs.phaser.io/test")

            # Verify the error message
            assert "Failed to read documentation" in str(exc_info.value)
            assert "Invalid URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_read_documentation_parser_error(self, mock_context: MockContext):
        """Test read_documentation with parser error."""
        # Create mock components
        mock_client = AsyncMock(spec=PhaserDocsClient)
        mock_parser = Mock(spec=PhaserDocumentParser)

        # Setup mock client response
        mock_page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="<html><body><h1>Test</h1></body></html>",
        )
        mock_client.get_page_content.return_value = mock_page

        # Setup mock parser to raise an exception
        mock_parser.parse_html_content.side_effect = ValueError("Parsing error")

        # Patch the server components
        with patch("phaser_mcp_server.server.server") as mock_server:
            mock_server.client = mock_client
            mock_server.parser = mock_parser

            # Call the MCP tool and expect an exception
            with pytest.raises(RuntimeError) as exc_info:
                await read_documentation(
                    mock_context, "https://docs.phaser.io/phaser/test"
                )

            # Verify the error message
            assert "Failed to read documentation" in str(exc_info.value)
            assert "Parsing error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_documentation_validation_error(
        self, mock_context: MockContext
    ):
        """Test search_documentation with validation error."""
        # Patch the client to raise a validation error
        with patch(
            "phaser_mcp_server.client.PhaserDocsClient.search_content"
        ) as mock_search:
            mock_search.side_effect = ValueError("Invalid search query")

            # Call the MCP tool and expect an exception
            with pytest.raises(RuntimeError) as exc_info:
                await search_documentation(mock_context, "test<script>", limit=5)

            # Verify the error message
            assert "Failed to search documentation" in str(exc_info.value)
            assert "Invalid search query" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_api_reference_not_found(self, mock_context: MockContext):
        """Test get_api_reference with class not found."""
        # Patch the client to return a minimal API reference for not found case
        with patch(
            "phaser_mcp_server.client.PhaserDocsClient.get_api_reference"
        ) as mock_get_api:
            mock_api_ref = ApiReference(
                class_name="NonExistentClass",
                url="https://docs.phaser.io/api/NonExistentClass",
                description="No specific documentation page found for this class.",
            )
            mock_get_api.return_value = mock_api_ref

            # Call the MCP tool
            result = await get_api_reference(mock_context, "NonExistentClass")

            # Verify the result indicates not found
            assert "# NonExistentClass" in result
            assert "No specific documentation page found" in result

            # Verify component interactions
            mock_get_api.assert_called_once_with("NonExistentClass")
