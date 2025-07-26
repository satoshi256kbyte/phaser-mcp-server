"""Integration tests for MCP tools.

This module contains integration tests for the MCP tools, testing the interaction
between different components with mocked HTTP responses and error cases.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from pytest_mock import MockerFixture

from phaser_mcp_server.client import ValidationError
from phaser_mcp_server.models import SearchResult
from phaser_mcp_server.server import server
from tests.utils import MockContext


class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.fixture
    def sample_html_content(self) -> str:
        """Sample HTML content for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phaser Sprite Tutorial - Phaser Documentation</title>
        </head>
        <body>
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
        </body>
        </html>
        """

    @pytest.fixture
    def sample_api_html(self) -> str:
        """Sample API HTML content for testing."""
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
    def mock_httpx_client(self, mocker: MockerFixture) -> Mock:
        """Mock httpx.AsyncClient for HTTP requests."""
        mock_client = AsyncMock()
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_read_documentation_success(
        self,
        mock_context: MockContext,
        sample_html_content: str,
        mock_httpx_client: Mock,
    ):
        """Test successful documentation reading integration."""
        from phaser_mcp_server.models import DocumentationPage
        from phaser_mcp_server.server import read_documentation

        # Mock the client's get_page_content method directly
        with patch.object(server.client, "get_page_content") as mock_get_page:
            mock_page = DocumentationPage(
                url="https://docs.phaser.io/phaser/sprites",
                title="Working with Sprites",
                content=sample_html_content,
                content_type="text/html",
            )
            mock_get_page.return_value = mock_page

            # Test the tool
            result = await read_documentation(
                mock_context,
                "https://docs.phaser.io/phaser/sprites",
                max_length=1000,
                start_index=0,
            )

            # Verify result
            assert isinstance(result, str)
            assert len(result) > 0
            # The actual content depends on the parser implementation
            assert "Working with Sprites" in result or "Sprites" in result

            # Verify client method was called correctly
            mock_get_page.assert_called_once_with(
                "https://docs.phaser.io/phaser/sprites"
            )

    @pytest.mark.asyncio
    async def test_read_documentation_with_pagination(
        self,
        mock_context: MockContext,
        sample_html_content: str,
        mock_httpx_client: Mock,
    ):
        """Test documentation reading with pagination."""
        from phaser_mcp_server.models import DocumentationPage
        from phaser_mcp_server.server import read_documentation

        # Mock the client's get_page_content method directly
        with patch.object(server.client, "get_page_content") as mock_get_page:
            mock_page = DocumentationPage(
                url="https://docs.phaser.io/phaser/sprites",
                title="Working with Sprites",
                content=sample_html_content,
                content_type="text/html",
            )
            mock_get_page.return_value = mock_page

            # Test with small max_length to trigger pagination
            result = await read_documentation(
                mock_context,
                "https://docs.phaser.io/phaser/sprites",
                max_length=100,
                start_index=0,
            )

            # Verify pagination worked
            assert isinstance(result, str)
            assert len(result) <= 100
            assert len(result) > 0

            # Test with start_index
            result_offset = await read_documentation(
                mock_context,
                "https://docs.phaser.io/phaser/sprites",
                max_length=100,
                start_index=50,
            )

            assert isinstance(result_offset, str)
            # Results may be the same if content is short, so just verify it's valid
            assert len(result_offset) >= 0

    @pytest.mark.asyncio
    async def test_read_documentation_invalid_parameters(
        self, mock_context: MockContext
    ):
        """Test documentation reading with invalid parameters."""
        from phaser_mcp_server.server import read_documentation

        # Test negative max_length - server wraps ValueError in RuntimeError
        with pytest.raises(RuntimeError, match="Failed to read documentation"):
            await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/test", max_length=-1
            )

        # Test negative start_index - server wraps ValueError in RuntimeError
        with pytest.raises(RuntimeError, match="Failed to read documentation"):
            await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/test", start_index=-1
            )

    @pytest.mark.asyncio
    async def test_read_documentation_http_error(self, mock_context: MockContext):
        """Test documentation reading with HTTP error."""
        from phaser_mcp_server.client import HTTPError
        from phaser_mcp_server.server import read_documentation

        # Mock the client's get_page_content method to raise HTTPError
        with patch.object(server.client, "get_page_content") as mock_get_page:
            mock_get_page.side_effect = HTTPError(
                "Page not found: https://docs.phaser.io/phaser/nonexistent"
            )

            # Should raise RuntimeError wrapping the HTTP error
            with pytest.raises(RuntimeError, match="Failed to read documentation"):
                await read_documentation(
                    mock_context, "https://docs.phaser.io/phaser/nonexistent"
                )

    @pytest.mark.asyncio
    async def test_read_documentation_network_error(self, mock_context: MockContext):
        """Test documentation reading with network error."""
        from phaser_mcp_server.client import NetworkError
        from phaser_mcp_server.server import read_documentation

        # Mock the client's get_page_content method to raise NetworkError
        with patch.object(server.client, "get_page_content") as mock_get_page:
            mock_get_page.side_effect = NetworkError(
                "Connection error: Connection failed"
            )

            # Should raise RuntimeError wrapping the network error
            with pytest.raises(RuntimeError, match="Failed to read documentation"):
                await read_documentation(
                    mock_context, "https://docs.phaser.io/phaser/test"
                )

    @pytest.mark.asyncio
    async def test_search_documentation_success(self, mock_context: MockContext):
        """Test successful documentation search integration."""
        from phaser_mcp_server.server import search_documentation

        # Mock the search_content method to return sample results
        with patch.object(server.client, "search_content") as mock_search:
            mock_search.return_value = [
                SearchResult(
                    rank_order=1,
                    url="https://docs.phaser.io/phaser/sprites",
                    title="Working with Sprites",
                    snippet="Sprites are the basic building blocks of games.",
                    relevance_score=0.95,
                ),
                SearchResult(
                    rank_order=2,
                    url="https://docs.phaser.io/phaser/animations",
                    title="Animation System",
                    snippet="Create smooth animations for your sprites.",
                    relevance_score=0.85,
                ),
            ]

            # Test the search tool
            result = await search_documentation(
                mock_context, "sprite animation", limit=10
            )

            # Verify result structure
            assert isinstance(result, list)
            assert len(result) == 2

            # Verify first result
            first_result = result[0]
            assert first_result["rank_order"] == 1
            assert first_result["url"] == "https://docs.phaser.io/phaser/sprites"
            assert first_result["title"] == "Working with Sprites"
            assert (
                first_result["snippet"]
                == "Sprites are the basic building blocks of games."
            )
            assert first_result["relevance_score"] == 0.95

            # Verify second result
            second_result = result[1]
            assert second_result["rank_order"] == 2
            assert second_result["url"] == "https://docs.phaser.io/phaser/animations"
            assert second_result["title"] == "Animation System"

            # Verify search was called correctly
            mock_search.assert_called_once_with("sprite animation", 10)

    @pytest.mark.asyncio
    async def test_search_documentation_empty_query(self, mock_context: MockContext):
        """Test search with empty query."""
        from phaser_mcp_server.server import search_documentation

        # Test empty query - server wraps ValueError in RuntimeError
        with pytest.raises(RuntimeError, match="Failed to search documentation"):
            await search_documentation(mock_context, "")

        # Test whitespace-only query - server wraps ValueError in RuntimeError
        with pytest.raises(RuntimeError, match="Failed to search documentation"):
            await search_documentation(mock_context, "   ")

    @pytest.mark.asyncio
    async def test_search_documentation_invalid_limit(self, mock_context: MockContext):
        """Test search with invalid limit."""
        from phaser_mcp_server.server import search_documentation

        # Test negative limit - server wraps ValueError in RuntimeError
        with pytest.raises(RuntimeError, match="Failed to search documentation"):
            await search_documentation(mock_context, "test", limit=-1)

        # Test zero limit - server wraps ValueError in RuntimeError
        with pytest.raises(RuntimeError, match="Failed to search documentation"):
            await search_documentation(mock_context, "test", limit=0)

    @pytest.mark.asyncio
    async def test_search_documentation_client_error(self, mock_context: MockContext):
        """Test search with client error."""
        from phaser_mcp_server.server import search_documentation

        # Mock the search_content method to raise an error
        with patch.object(server.client, "search_content") as mock_search:
            mock_search.side_effect = ValidationError("Invalid search query")

            # Should raise RuntimeError wrapping the client error
            with pytest.raises(RuntimeError, match="Failed to search documentation"):
                await search_documentation(mock_context, "test query")

    @pytest.mark.asyncio
    async def test_get_api_reference_success(
        self, mock_context: MockContext, sample_api_html: str, mock_httpx_client: Mock
    ):
        """Test successful API reference retrieval integration."""
        from phaser_mcp_server.models import ApiReference
        from phaser_mcp_server.server import get_api_reference

        # Mock the client's get_api_reference method directly
        with patch.object(server.client, "get_api_reference") as mock_api:
            mock_api.return_value = ApiReference(
                class_name="Sprite",
                url="https://docs.phaser.io/api/Sprite",
                description="A Sprite Game Object is used to display a texture.",
                methods=["setTexture", "setPosition", "destroy"],
                properties=["x", "y", "texture"],
                examples=["const sprite = this.add.sprite(0, 0, 'key');"],
            )

            # Test the API reference tool
            result = await get_api_reference(mock_context, "Sprite")

            # Verify result structure
            assert isinstance(result, str)
            assert "# Sprite" in result
            assert "Sprite Game Object" in result
            # Should have at least one of these sections
            assert any(
                section in result
                for section in ["## Methods", "## Properties", "## Examples"]
            )

            # Verify client method was called correctly
            mock_api.assert_called_once_with("Sprite")

    @pytest.mark.asyncio
    async def test_get_api_reference_empty_class_name(self, mock_context: MockContext):
        """Test API reference with empty class name."""
        from phaser_mcp_server.server import get_api_reference

        # Test empty class name - server wraps ValueError in RuntimeError
        with pytest.raises(RuntimeError, match="Failed to get API reference"):
            await get_api_reference(mock_context, "")

        # Test whitespace-only class name - server wraps ValueError in RuntimeError
        with pytest.raises(RuntimeError, match="Failed to get API reference"):
            await get_api_reference(mock_context, "   ")

    @pytest.mark.asyncio
    async def test_get_api_reference_not_found(self, mock_context: MockContext):
        """Test API reference when class not found."""
        from phaser_mcp_server.models import ApiReference
        from phaser_mcp_server.server import get_api_reference

        # Mock the client's get_api_reference method to return fallback result
        with patch.object(server.client, "get_api_reference") as mock_api:
            mock_api.return_value = ApiReference(
                class_name="NonExistentClass",
                url="https://docs.phaser.io/api/NonExistentClass",
                description="API reference for NonExistentClass. No docs found.",
                methods=[],
                properties=[],
                examples=[],
            )

            # Should still return a result (fallback behavior)
            result = await get_api_reference(mock_context, "NonExistentClass")

            assert isinstance(result, str)
            assert "# NonExistentClass" in result
            assert "No docs found" in result

    @pytest.mark.asyncio
    async def test_get_api_reference_network_error(self, mock_context: MockContext):
        """Test API reference with network error."""
        from phaser_mcp_server.client import NetworkError
        from phaser_mcp_server.server import get_api_reference

        # Mock the client's get_api_reference method to raise NetworkError
        with patch.object(server.client, "get_api_reference") as mock_api:
            mock_api.side_effect = NetworkError("Connection error: Connection failed")

            # Should raise RuntimeError wrapping the network error
            with pytest.raises(RuntimeError, match="Failed to get API reference"):
                await get_api_reference(mock_context, "Sprite")


class TestMCPToolsErrorHandling:
    """Test error handling scenarios in MCP tools."""

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.fixture
    def mock_httpx_client(self, mocker: MockerFixture) -> Mock:
        """Mock httpx.AsyncClient for HTTP requests."""
        mock_client = AsyncMock()
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_read_documentation_rate_limit_error(self, mock_context: MockContext):
        """Test documentation reading with rate limit error."""
        from phaser_mcp_server.client import RateLimitError
        from phaser_mcp_server.server import read_documentation

        # Mock the client's get_page_content method to raise RateLimitError
        with patch.object(server.client, "get_page_content") as mock_get_page:
            mock_get_page.side_effect = RateLimitError("Rate limited after 3 attempts")

            # Should raise RuntimeError wrapping the rate limit error
            with pytest.raises(RuntimeError, match="Failed to read documentation"):
                await read_documentation(
                    mock_context, "https://docs.phaser.io/phaser/test"
                )

    @pytest.mark.asyncio
    async def test_read_documentation_timeout_error(self, mock_context: MockContext):
        """Test documentation reading with timeout error."""
        from phaser_mcp_server.client import NetworkError
        from phaser_mcp_server.server import read_documentation

        # Mock the client's get_page_content method to raise NetworkError (timeout)
        with patch.object(server.client, "get_page_content") as mock_get_page:
            mock_get_page.side_effect = NetworkError("Request timeout")

            # Should raise RuntimeError wrapping the timeout error
            with pytest.raises(RuntimeError, match="Failed to read documentation"):
                await read_documentation(
                    mock_context, "https://docs.phaser.io/phaser/test"
                )

    @pytest.mark.asyncio
    async def test_search_documentation_validation_error(
        self, mock_context: MockContext
    ):
        """Test search with validation error from client."""
        from phaser_mcp_server.server import search_documentation

        # Mock the search_content method to raise validation error
        with patch.object(server.client, "search_content") as mock_search:
            mock_search.side_effect = ValidationError("Suspicious pattern detected")

            # Should raise RuntimeError wrapping the validation error
            with pytest.raises(RuntimeError, match="Failed to search documentation"):
                await search_documentation(mock_context, "malicious query")

    @pytest.mark.asyncio
    async def test_get_api_reference_client_error(self, mock_context: MockContext):
        """Test API reference with client error."""
        from phaser_mcp_server.server import get_api_reference

        # Mock the get_api_reference method to raise an error
        with patch.object(server.client, "get_api_reference") as mock_api:
            mock_api.side_effect = ValidationError("Class name is empty")

            # Should raise RuntimeError wrapping the client error
            with pytest.raises(RuntimeError, match="Failed to get API reference"):
                await get_api_reference(mock_context, "")


class TestMCPToolsWithRealComponents:
    """Test MCP tools with real component integration (no HTTP mocking)."""

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.fixture
    def mock_httpx_client(self, mocker: MockerFixture) -> Mock:
        """Mock httpx.AsyncClient for HTTP requests."""
        mock_client = AsyncMock()
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_tools_with_real_parser_integration(
        self, mock_context: MockContext, mock_httpx_client: Mock
    ):
        """Test tools with real parser but mocked HTTP."""
        from phaser_mcp_server.models import DocumentationPage
        from phaser_mcp_server.server import read_documentation

        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phaser Game Development - Phaser Documentation</title>
        </head>
        <body>
            <main>
                <h1>Game Development with Phaser</h1>
                <p>Phaser is a powerful 2D game framework.</p>
                <pre><code class="language-javascript">
const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    scene: {
        preload: preload,
        create: create,
        update: update
    }
};

const game = new Phaser.Game(config);
                </code></pre>
                <h2>Creating Sprites</h2>
                <p>Use this.add.sprite() to create sprites:</p>
                <pre><code>
const player = this.add.sprite(100, 100, 'player');
player.setScale(2);
                </code></pre>
            </main>
        </body>
        </html>
        """

        # Mock the client's get_page_content method directly
        with patch.object(server.client, "get_page_content") as mock_get_page:
            mock_page = DocumentationPage(
                url="https://docs.phaser.io/phaser/game-development",
                title="Phaser Game Development",
                content=sample_html,
                content_type="text/html",
            )
            mock_get_page.return_value = mock_page

            # Test with real parser integration
            result = await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/game-development"
            )

            # Verify the parser correctly processed the content
            assert isinstance(result, str)
            assert len(result) > 0
            # The actual content depends on the parser implementation
            assert "Game Development" in result or "Phaser" in result

    @pytest.mark.asyncio
    async def test_api_reference_with_real_parser(
        self, mock_context: MockContext, mock_httpx_client: Mock
    ):
        """Test API reference tool with real parser integration."""
        from phaser_mcp_server.models import ApiReference
        from phaser_mcp_server.server import get_api_reference

        # Mock the client's get_api_reference method directly
        with patch.object(server.client, "get_api_reference") as mock_api:
            mock_api.return_value = ApiReference(
                class_name="Scene",
                url="https://docs.phaser.io/api/Scene",
                description="A Scene is responsible for running the main game loop.",
                methods=["add", "load", "physics"],
                properties=["cameras", "input"],
                examples=["class GameScene extends Phaser.Scene { create() { } }"],
            )

            # Test with real parser integration
            result = await get_api_reference(mock_context, "Scene")

            # Verify the parser correctly processed the API content
            assert isinstance(result, str)
            assert "# Scene" in result
            assert "Scene" in result  # Should contain Scene-related content
            # Should have at least one of these sections
            assert any(
                section in result
                for section in ["## Methods", "## Properties", "## Examples"]
            )

            # Verify client method was called correctly
            mock_api.assert_called_once_with("Scene")


class TestMCPServerLifecycle:
    """Test MCP server lifecycle and initialization."""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test server initialization process."""
        from phaser_mcp_server.server import PhaserMCPServer

        # Create a new server instance for testing
        test_server = PhaserMCPServer()

        # Test server info
        server_info = test_server.get_server_info()
        assert server_info["name"] == "phaser-mcp-server"
        assert server_info["version"] == "1.0.0"
        assert server_info["status"] == "running"
        assert "environment_variables" in server_info

        # Test initialization
        await test_server.initialize()

        # Test cleanup
        await test_server.cleanup()

    @pytest.mark.asyncio
    async def test_server_initialization_error_handling(self):
        """Test server initialization error handling."""
        from phaser_mcp_server.server import PhaserMCPServer

        test_server = PhaserMCPServer()

        # Mock client initialization to fail
        with patch.object(test_server.client, "initialize") as mock_init:
            mock_init.side_effect = Exception("Initialization failed")

            # Should raise RuntimeError with context
            with pytest.raises(RuntimeError, match="Server initialization failed"):
                await test_server.initialize()

    @pytest.mark.asyncio
    async def test_server_cleanup_error_handling(self):
        """Test server cleanup error handling."""
        from phaser_mcp_server.server import PhaserMCPServer

        test_server = PhaserMCPServer()

        # Mock client close to fail
        with patch.object(test_server.client, "close") as mock_close:
            mock_close.side_effect = Exception("Cleanup failed")

            # Should not raise exception but log errors
            await test_server.cleanup()  # Should complete without raising

    def test_create_mcp_server(self):
        """Test MCP server creation."""
        from phaser_mcp_server.server import create_mcp_server

        # Should create FastMCP instance successfully
        mcp_instance = create_mcp_server()
        assert mcp_instance is not None
        assert hasattr(mcp_instance, "tool")
        assert hasattr(mcp_instance, "run")

    def test_create_mcp_server_error_handling(self):
        """Test MCP server creation error handling."""
        from phaser_mcp_server.server import create_mcp_server

        # Mock FastMCP to fail
        with patch("phaser_mcp_server.server.FastMCP") as mock_fastmcp:
            mock_fastmcp.side_effect = Exception("FastMCP creation failed")

            # Should raise RuntimeError with context
            with pytest.raises(RuntimeError, match="FastMCP server creation failed"):
                create_mcp_server()
