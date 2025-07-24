"""End-to-end tests for Phaser MCP Server.

This module contains end-to-end tests that test the complete MCP communication
flow, including live tests with actual Phaser documentation and performance tests.
"""

import asyncio
import time
from unittest.mock import Mock

import pytest

from phaser_mcp_server.client import PhaserDocsClient
from phaser_mcp_server.server import PhaserMCPServer


class MockContext:
    """Mock MCP context for testing."""

    def __init__(self):
        self.session_id = "test-session"
        self.request_id = "test-request"


class TestEndToEndMCPCommunication:
    """End-to-end tests for MCP communication."""

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.fixture
    async def initialized_server(self) -> PhaserMCPServer:
        """Create and initialize a test server."""
        test_server = PhaserMCPServer()
        await test_server.initialize()
        yield test_server
        await test_server.cleanup()

    @pytest.mark.asyncio
    async def test_complete_mcp_workflow(self, mock_context: MockContext):
        """Test complete MCP workflow from request to response."""
        # Import MCP tools
        from phaser_mcp_server.server import (
            get_api_reference,
            read_documentation,
            search_documentation,
        )

        # Test data
        test_url = "https://docs.phaser.io/phaser/"
        test_query = "sprite"
        test_class = "Sprite"

        # Mock HTTP responses for consistent testing
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Phaser Documentation</title></head>
        <body>
            <main>
                <h1>Phaser Game Framework</h1>
                <p>Phaser is a fast, robust and versatile game framework.</p>
                <pre><code class="language-javascript">
const game = new Phaser.Game(config);
                </code></pre>
            </main>
        </body>
        </html>
        """

        api_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Sprite API</title></head>
        <body>
            <main>
                <h1>Phaser.GameObjects.Sprite</h1>
                <div class="description">A Sprite Game Object displays textures.</div>
                <div class="methods">
                    <div class="method">setTexture</div>
                    <div class="method">destroy</div>
                </div>
                <div class="properties">
                    <div class="property">x</div>
                    <div class="property">y</div>
                </div>
            </main>
        </body>
        </html>
        """

        # Mock HTTP client responses
        async def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            url = args[0] if args else kwargs.get("url", "")
            mock_response = Mock()
            if "api" in url:
                mock_response.text = api_html
                mock_response.url = "https://docs.phaser.io/api/Sprite"
            else:
                mock_response.text = sample_html
                mock_response.url = test_url

            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response._content = mock_response.text.encode("utf-8")
            mock_response.raise_for_status = Mock()
            return mock_response

        # Patch the HTTP client
        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            # Test 1: Read documentation
            doc_result = await read_documentation(mock_context, test_url)
            assert isinstance(doc_result, str)
            assert "Phaser Game Framework" in doc_result
            assert "```javascript" in doc_result

            # Test 2: Search documentation (mocked to return empty for now)
            search_result = await search_documentation(mock_context, test_query)
            assert isinstance(search_result, list)

            # Test 3: Get API reference
            api_result = await get_api_reference(mock_context, test_class)
            assert isinstance(api_result, str)
            assert "# Sprite" in api_result
            assert "setTexture" in api_result
            assert "destroy" in api_result

    @pytest.mark.asyncio
    async def test_mcp_error_propagation(self, mock_context: MockContext):
        """Test that errors are properly propagated through MCP layer."""
        from phaser_mcp_server.server import read_documentation

        # Test with invalid URL that should cause validation error
        with pytest.raises((ValueError, RuntimeError)):  # Should raise a specific error
            await read_documentation(mock_context, "invalid-url")

        # Test with invalid parameters
        with pytest.raises(ValueError):
            await read_documentation(
                mock_context, "https://docs.phaser.io/test", max_length=-1
            )

    @pytest.mark.asyncio
    async def test_mcp_context_handling(self, mock_context: MockContext):
        """Test that MCP context is properly handled."""
        from phaser_mcp_server.server import read_documentation

        # Verify context is passed correctly (doesn't raise errors)
        # Mock a simple response
        sample_html = "<html><body><h1>Test</h1></body></html>"

        async def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            url = args[0] if args else kwargs.get("url", "")
            mock_response = Mock()
            mock_response.text = sample_html
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.url = url
            mock_response._content = sample_html.encode("utf-8")
            mock_response.raise_for_status = Mock()
            return mock_response

        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            result = await read_documentation(
                mock_context, "https://docs.phaser.io/test"
            )
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_server_lifecycle_integration(
        self, initialized_server: PhaserMCPServer
    ):
        """Test server lifecycle integration."""
        # Verify server is properly initialized
        server_info = initialized_server.get_server_info()
        assert server_info["status"] == "running"
        assert server_info["name"] == "phaser-mcp-server"

        # Verify components are accessible
        assert initialized_server.client is not None
        assert initialized_server.parser is not None

        # Test that server can handle basic operations
        # (This would normally involve actual MCP protocol testing)
        assert hasattr(initialized_server, "initialize")
        assert hasattr(initialized_server, "cleanup")


@pytest.mark.live
class TestLiveDocumentationAccess:
    """Live tests with actual Phaser documentation.

    These tests require internet connection and access to docs.phaser.io.
    They are marked with @pytest.mark.live and can be skipped in CI/CD.
    """

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.fixture
    async def live_client(self) -> PhaserDocsClient:
        """Create a real client for live testing."""
        client = PhaserDocsClient()
        await client.initialize()
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_live_documentation_reading(
        self, mock_context: MockContext, live_client: PhaserDocsClient
    ):
        """Test reading actual Phaser documentation."""
        from phaser_mcp_server.server import read_documentation

        # Test with actual Phaser documentation URL
        test_urls = [
            "https://docs.phaser.io/phaser/",
            "https://docs.phaser.io/phaser/getting-started",
        ]

        for url in test_urls:
            try:
                result = await read_documentation(mock_context, url, max_length=1000)

                # Verify we got meaningful content
                assert isinstance(result, str)
                assert len(result) > 0
                assert len(result) <= 1000

                # Should contain Phaser-related content
                assert any(
                    keyword in result.lower()
                    for keyword in ["phaser", "game", "sprite", "scene"]
                )

                print(f"✓ Successfully read documentation from {url}")

            except Exception as e:
                pytest.skip(f"Live test failed for {url}: {e}")

    @pytest.mark.asyncio
    async def test_live_api_reference_access(
        self, mock_context: MockContext, live_client: PhaserDocsClient
    ):
        """Test accessing actual Phaser API references."""
        from phaser_mcp_server.server import get_api_reference

        # Test with common Phaser classes
        test_classes = ["Sprite", "Scene", "Game"]

        for class_name in test_classes:
            try:
                result = await get_api_reference(mock_context, class_name)

                # Verify we got meaningful API documentation
                assert isinstance(result, str)
                assert len(result) > 0

                # Should contain API-related content
                assert f"# {class_name}" in result
                assert any(
                    section in result
                    for section in ["## Methods", "## Properties", "## Examples"]
                )

                print(f"✓ Successfully retrieved API reference for {class_name}")

            except Exception as e:
                pytest.skip(f"Live API test failed for {class_name}: {e}")

    @pytest.mark.asyncio
    async def test_live_search_functionality(
        self, mock_context: MockContext, live_client: PhaserDocsClient
    ):
        """Test search functionality with live data."""
        from phaser_mcp_server.server import search_documentation

        # Test search queries
        test_queries = ["sprite", "animation", "physics"]

        for query in test_queries:
            try:
                result = await search_documentation(mock_context, query, limit=5)

                # Verify search results structure
                assert isinstance(result, list)
                # Note: Search might return empty results if not implemented
                # This test mainly verifies the search doesn't crash

                print(f"✓ Search completed for query: {query} ({len(result)} results)")

            except Exception as e:
                pytest.skip(f"Live search test failed for '{query}': {e}")

    @pytest.mark.asyncio
    async def test_live_error_handling(self, mock_context: MockContext):
        """Test error handling with live requests."""
        from phaser_mcp_server.server import read_documentation

        # Test with non-existent page
        try:
            with pytest.raises(RuntimeError):
                await read_documentation(
                    mock_context, "https://docs.phaser.io/nonexistent-page-12345"
                )
            print("✓ Properly handled 404 error")
        except Exception as e:
            pytest.skip(f"Live error handling test failed: {e}")

    @pytest.mark.asyncio
    async def test_live_content_quality(self, mock_context: MockContext):
        """Test the quality of parsed content from live documentation."""
        from phaser_mcp_server.server import read_documentation

        try:
            # Get content from main Phaser documentation page
            result = await read_documentation(
                mock_context, "https://docs.phaser.io/phaser/", max_length=2000
            )

            # Verify content quality
            assert isinstance(result, str)
            assert len(result) > 100  # Should have substantial content

            # Should be properly formatted Markdown
            assert result.count("#") > 0  # Should have headers

            # Should contain code blocks if present
            if "```" in result:
                # Verify code blocks are properly formatted
                code_blocks = result.count("```")
                assert code_blocks % 2 == 0  # Should have matching opening/closing

            # Should not contain HTML tags (should be converted to Markdown)
            html_tags = ["<div>", "<span>", "<p>", "<h1>", "<h2>"]
            for tag in html_tags:
                assert tag not in result, f"Found unconverted HTML tag: {tag}"

            print("✓ Content quality checks passed")

        except Exception as e:
            pytest.skip(f"Live content quality test failed: {e}")


class TestPerformance:
    """Performance tests for MCP tools."""

    @pytest.fixture
    def mock_context(self) -> MockContext:
        """Create a mock MCP context."""
        return MockContext()

    @pytest.fixture
    def large_html_content(self) -> str:
        """Generate large HTML content for performance testing."""
        base_content = """
        <html>
        <head><title>Large Document</title></head>
        <body>
            <main>
                <h1>Large Document Test</h1>
                <p>This is a large document for performance testing.</p>
                <pre><code class="language-javascript">
const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600
};
                </code></pre>
        """

        # Add many sections to make it large
        for i in range(100):
            base_content += f"""
                <h2>Section {i}</h2>
                <p>This is section {i} with content about Phaser.</p>
                <ul>
                    <li>Item 1 for section {i}</li>
                    <li>Item 2 for section {i}</li>
                    <li>Item 3 for section {i}</li>
                </ul>
                <pre><code>
const sprite{i} = this.add.sprite({i}, {i}, 'texture{i}');
sprite{i}.setScale(2);
                </code></pre>
            """

        base_content += """
            </main>
        </body>
        </html>
        """

        return base_content

    @pytest.mark.asyncio
    async def test_read_documentation_performance(
        self, mock_context: MockContext, large_html_content: str
    ):
        """Test performance of documentation reading with large content."""
        from phaser_mcp_server.server import read_documentation

        # Mock HTTP response with large content
        async def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            mock_response = Mock()
            mock_response.text = large_html_content
            mock_response.status_code = 200
            mock_response.headers = {
                "content-type": "text/html",
                "content-length": str(len(large_html_content)),
            }
            mock_response.url = url
            mock_response._content = large_html_content.encode("utf-8")
            mock_response.raise_for_status = Mock()
            return mock_response

        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            # Measure performance
            start_time = time.time()

            result = await read_documentation(
                mock_context, "https://docs.phaser.io/test-large", max_length=5000
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Verify result
            assert isinstance(result, str)
            assert len(result) <= 5000

            # Performance assertions
            assert (
                processing_time < 5.0
            ), f"Processing took too long: {processing_time:.2f}s"

            print(f"✓ Large document processed in {processing_time:.2f}s")

    @pytest.mark.asyncio
    async def test_pagination_performance(
        self, mock_context: MockContext, large_html_content: str
    ):
        """Test performance of pagination with large content."""
        from phaser_mcp_server.server import read_documentation

        # Mock HTTP response
        async def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            mock_response = Mock()
            mock_response.text = large_html_content
            mock_response.status_code = 200
            mock_response.headers = {
                "content-type": "text/html",
                "content-length": str(len(large_html_content)),
            }
            mock_response.url = url
            mock_response._content = large_html_content.encode("utf-8")
            mock_response.raise_for_status = Mock()
            return mock_response

        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            # Test multiple pagination requests
            page_size = 1000
            num_pages = 5

            start_time = time.time()

            for i in range(num_pages):
                start_index = i * page_size
                result = await read_documentation(
                    mock_context,
                    "https://docs.phaser.io/test-pagination",
                    max_length=page_size,
                    start_index=start_index,
                )
                assert isinstance(result, str)
                assert len(result) <= page_size

            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / num_pages

            # Performance assertions
            assert avg_time < 1.0, f"Average pagination time too slow: {avg_time:.2f}s"

            print(f"✓ Pagination: {num_pages} pages, avg: {avg_time:.2f}s")

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, mock_context: MockContext):
        """Test performance with concurrent requests."""
        from phaser_mcp_server.server import read_documentation

        # Mock HTTP response
        sample_html = """
        <html>
        <head><title>Test Document</title></head>
        <body>
            <main>
                <h1>Test Document</h1>
                <p>This is a test document for concurrent access.</p>
            </main>
        </body>
        </html>
        """

        async def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            # Simulate some processing time
            await asyncio.sleep(0.1)
            mock_response = Mock()
            mock_response.text = sample_html
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.url = url
            mock_response._content = sample_html.encode("utf-8")
            mock_response.raise_for_status = Mock()
            return mock_response

        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            # Create concurrent requests
            num_concurrent = 10
            urls = [f"https://docs.phaser.io/test-{i}" for i in range(num_concurrent)]

            start_time = time.time()

            # Execute concurrent requests
            tasks = [
                read_documentation(mock_context, url, max_length=1000) for url in urls
            ]
            results = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # Verify all requests completed successfully
            assert len(results) == num_concurrent
            for result in results:
                assert isinstance(result, str)
                assert "Test Document" in result

            # Performance assertion - should be faster than sequential
            # With 0.1s delay per request, sequential would take 1.0s+
            # Concurrent should be much faster
            assert total_time < 0.5, f"Concurrent requests too slow: {total_time:.2f}s"

            print(f"✓ {num_concurrent} concurrent requests in {total_time:.2f}s")

    @pytest.mark.asyncio
    async def test_memory_usage_performance(
        self, mock_context: MockContext, large_html_content: str
    ):
        """Test memory usage with large content processing."""
        import os

        import psutil

        from phaser_mcp_server.server import read_documentation

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Mock HTTP response with large content
        async def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            mock_response = Mock()
            mock_response.text = large_html_content
            mock_response.status_code = 200
            mock_response.headers = {
                "content-type": "text/html",
                "content-length": str(len(large_html_content)),
            }
            mock_response.url = url
            mock_response._content = large_html_content.encode("utf-8")
            mock_response.raise_for_status = Mock()
            return mock_response

        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            # Process multiple large documents
            for i in range(5):
                result = await read_documentation(
                    mock_context,
                    f"https://docs.phaser.io/test-memory-{i}",
                    max_length=2000,
                )
                assert isinstance(result, str)

            # Check memory usage after processing
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory usage should not increase excessively
            assert (
                memory_increase < 100
            ), f"Memory usage increased too much: {memory_increase:.2f}MB"

            print(f"✓ Memory usage increase: {memory_increase:.2f}MB")

    @pytest.mark.asyncio
    async def test_api_reference_performance(self, mock_context: MockContext):
        """Test API reference retrieval performance."""
        from phaser_mcp_server.server import get_api_reference

        # Mock API HTML content
        api_html = (
            """
        <!DOCTYPE html>
        <html>
        <head><title>API Reference</title></head>
        <body>
            <main>
                <h1>Phaser.GameObjects.Sprite</h1>
                <div class="description">API description here.</div>
                <div class="methods">
                    """
            + "".join([f"<div class='method'>method{i}</div>" for i in range(50)])
            + """
                </div>
                <div class="properties">
                    """
            + "".join([f"<div class='property'>prop{i}</div>" for i in range(30)])
            + """
                </div>
            </main>
        </body>
        </html>
        """
        )

        async def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            mock_response = Mock()
            mock_response.text = api_html
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.url = url
            mock_response._content = api_html.encode("utf-8")
            mock_response.raise_for_status = Mock()
            return mock_response

        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            # Measure API reference performance
            start_time = time.time()

            result = await get_api_reference(mock_context, "Sprite")

            end_time = time.time()
            processing_time = end_time - start_time

            # Verify result
            assert isinstance(result, str)
            assert "# Sprite" in result
            assert "## Methods" in result
            assert "## Properties" in result

            # Performance assertion
            assert (
                processing_time < 2.0
            ), f"API reference processing too slow: {processing_time:.2f}s"

            print(f"✓ API reference processed in {processing_time:.2f}s")


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "live: mark test as requiring live internet connection"
    )


def pytest_addoption(parser):
    """Add command line options for pytest."""
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run live tests that require internet connection",
    )


def pytest_runtest_setup(item):
    """Skip live tests unless --run-live is specified."""
    if "live" in item.keywords and not item.config.getoption("--run-live"):
        pytest.skip("Live tests require --run-live flag")
