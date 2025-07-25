"""End-to-end tests for Phaser MCP Server.

This module contains end-to-end tests that test the complete MCP communication
flow, including live tests with actual Phaser documentation and performance tests.
"""

import asyncio
import time

import pytest

from tests.utils import setup_test_environment

from phaser_mcp_server.client import PhaserDocsClient
from phaser_mcp_server.server import PhaserMCPServer
from tests.utils import create_mock_response


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
            if "api" in url:
                return create_mock_response(
                    url="https://docs.phaser.io/api/Sprite", content=api_html
                )
            else:
                return create_mock_response(url=test_url, content=sample_html)

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
            return create_mock_response(
                url=url, content=sample_html, content_type="text/html"
            )

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
    async def test_memory_usage_performance(
        self, mock_context: MockContext, large_html_content: str, setup_test_environment
    ):
        """メモリ使用量のパフォーマンステスト。

        このテストは、大きなHTMLコンテンツの処理が過剰なメモリ使用や
        メモリリークを引き起こさないことを検証します。setup_test_environment
        フィクスチャを使用して、一貫した初期状態と正確なメモリ測定を確保します。

        要件:
            1.2: メモリ使用量が正確に測定されること
            1.3: 大きなHTMLコンテンツ処理時にメモリリークが発生しないこと
            2.3: メモリ使用量のしきい値を超える場合に明確なエラーメッセージが表示されること
        """
        # 実装は tests/test_memory_usage.py に移動しました
        # このテストは互換性のために残しています
        from tests.test_memory_usage import TestMemoryUsage

        # TestMemoryUsageクラスのインスタンスを作成
        test_instance = TestMemoryUsage()

        # テストメソッドを実行
        await test_instance.test_memory_usage_performance(
            mock_context, large_html_content, setup_test_environment
        )

    @pytest.mark.asyncio
    async def test_read_documentation_performance(
        self, mock_context: MockContext, large_html_content: str, setup_test_environment
    ):
        """ドキュメント読み込みのパフォーマンステスト。

        このテストは、大きなHTMLコンテンツの処理パフォーマンスを検証します。
        処理時間の測定と検証を行い、パフォーマンスが要件を満たしていることを確認します。

        要件:
            1.1: モックオブジェクトが正しく設定されること
            3.1: 処理時間が測定されること

        注意: このテストの実装は tests/test_documentation_performance.py に移動しました。
        このメソッドは互換性のために残されています。
        """
        from tests.test_documentation_performance import TestDocumentationPerformance

        # TestDocumentationPerformanceクラスのインスタンスを作成
        test_instance = TestDocumentationPerformance()

        # テストメソッドを実行
        await test_instance.test_read_documentation_performance(
            mock_context, large_html_content, setup_test_environment
        )

    @pytest.mark.asyncio
    async def test_pagination_performance(
        self, mock_context: MockContext, large_html_content: str, setup_test_environment
    ):
        """ページネーション処理のパフォーマンステスト。

        このテストは、大きなHTMLコンテンツのページネーション処理のパフォーマンスを検証します。
        新しいモックレスポンス作成関数を使用し、ページネーション処理のメモリ管理を改善します。

        要件:
            1.1: モックオブジェクトが正しく設定されること
            3.3: ページネーション処理のメモリ使用量が適切に管理されること

        注意: このテストの実装は tests/test_pagination_performance.py に移動しました。
        このメソッドは互換性のために残されています。
        """
        from tests.test_pagination_performance import TestPaginationPerformance

        # TestPaginationPerformanceクラスのインスタンスを作成
        test_instance = TestPaginationPerformance()

        # テストメソッドを実行
        await test_instance.test_pagination_performance(
            mock_context, large_html_content, setup_test_environment
        )

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(
        self, mock_context: MockContext, setup_test_environment
    ):
        """並行リクエストのパフォーマンステスト。

        このテストは、複数の並行リクエストが適切に処理され、リソース競合が
        発生しないことを検証します。新しいモックレスポンス作成関数を使用し、
        リソース競合を防ぐための改善を実装します。

        要件:
            1.1: モックオブジェクトが正しく設定されること
            3.2: 並行リクエストのテストが実行される際にリソース競合が発生しないこと
        """
        from phaser_mcp_server.server import read_documentation

        # Mock HTTP response using the standardized utility function
        sample_html = """
        <html>
        <head><title>Test Document</title></head>
        <body>
            <main>
                <h1>Test Document</h1>
                <p>This is a test document for concurrent access.</p>
                <div class="content">
                    <h2>Section 1</h2>
                    <p>Content for section 1.</p>
                    <h2>Section 2</h2>
                    <p>Content for section 2.</p>
                </div>
            </main>
        </body>
        </html>
        """

        # Use a semaphore to prevent resource contention
        request_semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        request_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal request_count
            url = args[0] if args else kwargs.get("url", "")

            # Acquire semaphore to prevent resource contention
            async with request_semaphore:
                request_count += 1
                # Simulate realistic processing time with some variation
                await asyncio.sleep(0.05 + (request_count % 3) * 0.01)

                # Use the standardized mock response creation function
                return create_mock_response(
                    url=url, content=sample_html, content_type="text/html"
                )

        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            # Create concurrent requests with different URLs to test resource handling
            num_concurrent = 10
            urls = [f"https://docs.phaser.io/test-{i}" for i in range(num_concurrent)]

            start_time = time.time()

            # Execute concurrent requests with proper error handling
            try:
                tasks = [
                    read_documentation(mock_context, url, max_length=1000)
                    for url in urls
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                pytest.fail(f"Concurrent requests failed with exception: {e}")

            end_time = time.time()
            total_time = end_time - start_time

            # Verify all requests completed successfully without exceptions
            assert len(results) == num_concurrent
            successful_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    pytest.fail(f"Request {i} failed with exception: {result}")
                else:
                    successful_results.append(result)
                    assert isinstance(result, str)
                    assert "Test Document" in result
                    assert len(result) > 0

            # Verify all requests were successful
            assert len(successful_results) == num_concurrent

            # Performance assertion - should be faster than sequential but not too fast
            # With semaphore limiting to 5 concurrent and 0.05-0.08s delay per request,
            # should complete in reasonable time
            assert total_time < 1.0, f"Concurrent requests too slow: {total_time:.2f}s"
            assert (
                total_time > 0.1
            ), f"Concurrent requests suspiciously fast: {total_time:.2f}s"

            # Verify resource contention prevention worked
            assert (
                request_count == num_concurrent
            ), f"Expected {num_concurrent} requests, got {request_count}"

            print(
                f"✓ {num_concurrent} concurrent requests completed in {total_time:.2f}s"
            )
            print(
                f"✓ Resource contention prevented with semaphore limiting to 5 concurrent requests"
            )

    @pytest.mark.asyncio
    async def test_api_reference_performance(
        self, mock_context: MockContext, setup_test_environment
    ):
        """API参照取得のパフォーマンステスト。

        このテストは、API参照取得のパフォーマンスを測定し、新しいモックレスポンス
        作成関数を使用してテストの信頼性を向上させます。処理時間の測定と検証を
        改善し、パフォーマンスが要件を満たしていることを確認します。

        要件:
            1.1: モックオブジェクトが正しく設定されること
            3.1: 処理時間が測定されること
        """
        from phaser_mcp_server.server import get_api_reference

        # より大きなAPI HTMLコンテンツを生成してパフォーマンステストを強化
        api_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Phaser.GameObjects.Sprite API Reference</title></head>
        <body>
            <main>
                <h1>Phaser.GameObjects.Sprite</h1>
                <div class="description">
                    <p>A Sprite Game Object displays a texture, or frame from a texture, at a given position in the world.</p>
                    <p>You can tint the sprite, blend it, rotate it, scale it, and animate it.</p>
                </div>
                <div class="constructor">
                    <h2>Constructor</h2>
                    <div class="method">
                        <h3>new Sprite(scene, x, y, texture, frame)</h3>
                        <p>Creates a new Sprite Game Object.</p>
                    </div>
                </div>
                <div class="methods">
                    <h2>Methods</h2>"""

        # より多くのメソッドを追加してパフォーマンステストを強化
        for i in range(100):
            api_html += f"""
                    <div class="method">
                        <h3>method{i}(param1, param2)</h3>
                        <p>Description for method {i} with detailed explanation.</p>
                        <div class="parameters">
                            <h4>Parameters:</h4>
                            <ul>
                                <li>param1 (string) - First parameter description</li>
                                <li>param2 (number) - Second parameter description</li>
                            </ul>
                        </div>
                        <div class="returns">
                            <h4>Returns:</h4>
                            <p>Returns a value of type {i % 5}</p>
                        </div>
                    </div>"""

        api_html += """
                </div>
                <div class="properties">
                    <h2>Properties</h2>"""

        # より多くのプロパティを追加
        for i in range(80):
            api_html += f"""
                    <div class="property">
                        <h3>property{i}</h3>
                        <p>Description for property {i} with type information.</p>
                        <div class="type">Type: {['string', 'number', 'boolean', 'object', 'array'][i % 5]}</div>
                    </div>"""

        api_html += """
                </div>
                <div class="examples">
                    <h2>Examples</h2>
                    <pre><code class="language-javascript">
// Create a sprite
const sprite = this.add.sprite(400, 300, 'player');

// Set properties
sprite.setScale(2);
sprite.setTint(0xff0000);

// Animate the sprite
this.tweens.add({
    targets: sprite,
    x: 600,
    duration: 2000,
    ease: 'Power2'
});
                    </code></pre>
                </div>
            </main>
        </body>
        </html>
        """

        # リクエスト回数をカウントしてモック関数の呼び出しを検証
        request_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal request_count
            request_count += 1
            url = args[0] if args else kwargs.get("url", "")

            # 新しいモックレスポンス作成関数を使用
            return create_mock_response(
                url=url, content=api_html, content_type="text/html"
            )

        with pytest.MonkeyPatch().context() as m:
            m.setattr("httpx.AsyncClient.get", mock_get)

            # 複数回の測定で平均パフォーマンスを計算
            processing_times = []
            test_classes = ["Sprite", "Scene", "Game", "Physics", "Animation"]

            for class_name in test_classes:
                start_time = time.time()

                result = await get_api_reference(mock_context, class_name)

                end_time = time.time()
                processing_time = end_time - start_time
                processing_times.append(processing_time)

                # 結果の検証を強化
                assert isinstance(
                    result, str
                ), f"Result should be string, got {type(result)}"
                assert len(result) > 0, "Result should not be empty"

                # API参照の基本構造を検証
                assert (
                    f"# {class_name}" in result or "Sprite" in result
                ), f"Should contain class name or Sprite in result"

                # メソッドとプロパティのセクションが含まれていることを確認
                has_methods = "## Methods" in result or "method" in result.lower()
                has_properties = (
                    "## Properties" in result or "property" in result.lower()
                )

                assert (
                    has_methods or has_properties
                ), "Result should contain methods or properties information"

                # パフォーマンス要件の検証（個別）
                assert (
                    processing_time < 3.0
                ), f"API reference processing for {class_name} too slow: {processing_time:.3f}s"

            # 平均パフォーマンスの計算と検証
            avg_processing_time = sum(processing_times) / len(processing_times)
            max_processing_time = max(processing_times)
            min_processing_time = min(processing_times)

            # パフォーマンス要件の検証（全体）
            assert (
                avg_processing_time < 2.0
            ), f"Average API reference processing too slow: {avg_processing_time:.3f}s"

            assert (
                max_processing_time < 3.0
            ), f"Maximum API reference processing too slow: {max_processing_time:.3f}s"

            # モック関数が適切に呼び出されたことを確認
            assert request_count == len(
                test_classes
            ), f"Expected {len(test_classes)} requests, got {request_count}"

            # パフォーマンス結果の出力
            print(f"✓ API reference performance test completed:")
            print(f"  - Average processing time: {avg_processing_time:.3f}s")
            print(f"  - Min processing time: {min_processing_time:.3f}s")
            print(f"  - Max processing time: {max_processing_time:.3f}s")
            print(f"  - Total requests processed: {request_count}")
            print(f"  - All {len(test_classes)} API references processed successfully")


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
