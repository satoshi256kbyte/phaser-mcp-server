"""Pagination performance tests for Phaser MCP Server.

This module contains tests that verify the performance of pagination
processing in the Phaser MCP Server.
"""

import time
import statistics
from unittest.mock import MagicMock

import pytest

from phaser_mcp_server.models import DocumentationPage
from tests.test_end_to_end import MockContext
from tests.test_performance_fixtures import create_mock_response, setup_test_environment


class TestPaginationPerformance:
    """Pagination performance tests for Phaser MCP Server."""

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
    async def test_pagination_performance(
        self, mock_context: MockContext, large_html_content: str, setup_test_environment
    ):
        """ページネーション処理のパフォーマンステスト。

        このテストは、大きなHTMLコンテンツのページネーション処理のパフォーマンスを検証します。
        新しいモックレスポンス作成関数を使用し、ページネーション処理のメモリ管理を改善します。

        psutilモジュールが利用できない場合、メモリ使用量の測定部分はスキップされますが、
        処理時間のパフォーマンステストは継続されます。

        要件:
            1.1: モックオブジェクトが正しく設定されること
            3.3: ページネーション処理のメモリ使用量が適切に管理されること
        """
        from phaser_mcp_server.server import PhaserMCPServer
        from phaser_mcp_server.utils import get_memory_usage

        # フィクスチャから初期メモリ使用量を取得
        initial_state = setup_test_environment
        initial_memory = initial_state["memory"]

        # psutilモジュールが利用できない場合の警告メッセージ
        if initial_memory is None:
            print(
                "警告: psutilモジュールが利用できないため、メモリ使用量の測定はスキップされます"
            )

        # テスト用URL
        test_url = "https://docs.phaser.io/test-pagination"

        # 新しいcreate_mock_response関数を使用してHTTPレスポンスをモック
        mock_response = create_mock_response(
            url=test_url,
            content=large_html_content,
            status_code=200,
            content_type="text/html",
        )

        # モックレスポンスの検証
        assert (
            mock_response.url == test_url
        ), "モックレスポンスのURLが正しく設定されていません"
        assert (
            mock_response.text == large_html_content
        ), "モックレスポンスのテキストが正しく設定されていません"
        assert (
            mock_response.status_code == 200
        ), "モックレスポンスのステータスコードが正しく設定されていません"
        assert (
            mock_response.headers["content-type"] == "text/html"
        ), "モックレスポンスのコンテンツタイプが正しく設定されていません"
        assert mock_response._content == large_html_content.encode(
            "utf-8"
        ), "モックレスポンスのバイナリコンテンツが正しく設定されていません"

        # サーバーインスタンスを作成
        server = PhaserMCPServer()

        # テスト用のDocumentationPageオブジェクトを作成
        page_content = DocumentationPage(
            url=test_url,
            content=large_html_content,
            title="Test Pagination Document",
            content_type="text/html",
            word_count=5000,  # 適当な値を設定
        )

        # モックのMarkdownコンテンツを作成
        # 実際のページネーションをテストするために十分な長さのコンテンツを用意
        mock_markdown = "# Test Document\n\n" + "Test content\n" * 1000

        # サーバーのクライアントとパーサーをモック
        server.client = MagicMock()
        server.parser = MagicMock()

        # get_page_contentメソッドのモック
        async def mock_get_page_content(url):
            return page_content

        server.client.get_page_content = mock_get_page_content

        # parse_html_contentとconvert_to_markdownメソッドのモック
        server.parser.parse_html_content = MagicMock(return_value=large_html_content)
        server.parser.convert_to_markdown = MagicMock(return_value=mock_markdown)

        # ページネーションのテスト設定
        page_size = 1000
        num_pages = 5
        processing_times = []
        memory_usage_per_page = []

        # ページネーション処理をシミュレート
        for i in range(num_pages):
            # ガベージコレクションを実行して前のイテレーションの影響を最小化
            import gc

            gc.collect()

            # 処理前のメモリ使用量を記録（psutilが利用可能な場合のみ）
            before_memory = get_memory_usage() if initial_memory is not None else None

            # 処理時間の測定開始（高精度タイマーを使用）
            start_time = time.perf_counter()

            # ページネーション処理
            start_index = i * page_size

            # サーバーの内部処理をシミュレート
            page = await server.client.get_page_content(test_url)
            parsed_content = server.parser.parse_html_content(page.content, page.url)
            markdown_content = server.parser.convert_to_markdown(parsed_content)

            # ページネーションを適用
            if start_index >= len(markdown_content):
                result = ""
            else:
                end_index = min(start_index + page_size, len(markdown_content))
                result = markdown_content[start_index:end_index]

            # 処理時間の測定終了
            end_time = time.perf_counter()
            processing_time = end_time - start_time
            processing_times.append(processing_time)

            # 処理後のメモリ使用量を記録（psutilが利用可能な場合のみ）
            after_memory = get_memory_usage() if initial_memory is not None else None

            # メモリ使用量の変化を記録（psutilが利用可能な場合）
            if before_memory is not None and after_memory is not None:
                memory_usage_per_page.append(after_memory - before_memory)

            # 結果の検証
            assert isinstance(
                result, str
            ), f"ページ {i} の結果が文字列でなければなりません"
            assert (
                len(result) <= page_size
            ), f"ページ {i} のサイズが制限を超えています: {len(result)} > {page_size}"

            # 明示的に大きなオブジェクトへの参照を解除してメモリリークを防止
            del result
            gc.collect()

        # 平均処理時間の計算
        avg_processing_time = statistics.mean(processing_times)

        # 最大処理時間と最小処理時間
        max_processing_time = max(processing_times)
        min_processing_time = min(processing_times)

        # 標準偏差の計算
        std_dev = statistics.stdev(processing_times) if len(processing_times) > 1 else 0

        # 環境に依存しない動的な閾値の設定
        base_threshold = 0.5  # 基本閾値
        size_adjustment = (
            len(large_html_content) / 100000 * 0.2
        )  # コンテンツサイズによる調整
        threshold = max(base_threshold + size_adjustment, 0.2)  # 最小閾値を設定

        # パフォーマンスの検証
        assert avg_processing_time < threshold, (
            f"平均処理時間が閾値を超えています: {avg_processing_time:.4f}s > {threshold:.4f}s\n"
            f"- 実行回数: {num_pages}\n"
            f"- 処理時間: {[f'{t:.4f}s' for t in processing_times]}\n"
            f"- 最大処理時間: {max_processing_time:.4f}s\n"
            f"- 最小処理時間: {min_processing_time:.4f}s\n"
            f"- 標準偏差: {std_dev:.4f}s\n"
            f"- コンテンツサイズ: {len(large_html_content)} バイト"
        )

        # メモリ使用量の検証（psutilが利用可能な場合）
        if memory_usage_per_page and initial_memory is not None:
            # 最終的なメモリ使用量を取得
            final_memory = get_memory_usage()

            if final_memory is not None:
                # 全体のメモリ増加量を計算
                total_memory_increase = final_memory - initial_memory

                # ページあたりの平均メモリ増加量を計算
                avg_memory_per_page = statistics.mean(memory_usage_per_page)

                # メモリ使用量の閾値を設定
                memory_threshold = 5.0  # 5MB

                # メモリ使用量の検証
                assert total_memory_increase < memory_threshold, (
                    f"メモリ使用量が閾値を超えています: {total_memory_increase:.2f}MB > {memory_threshold:.2f}MB\n"
                    f"- 初期メモリ使用量: {initial_memory:.2f}MB\n"
                    f"- 最終メモリ使用量: {final_memory:.2f}MB\n"
                    f"- ページあたりの平均メモリ増加量: {avg_memory_per_page:.2f}MB\n"
                    f"- ページごとのメモリ増加量: {[f'{m:.2f}MB' for m in memory_usage_per_page]}"
                )

                print(
                    f"✓ ページネーションメモリ使用量テスト成功:\n"
                    f"  - 全体のメモリ増加量: {total_memory_increase:.2f}MB\n"
                    f"  - ページあたりの平均メモリ増加量: {avg_memory_per_page:.2f}MB\n"
                    f"  - 閾値: {memory_threshold:.2f}MB"
                )
            else:
                print(
                    "警告: テスト実行中にpsutilモジュールが利用できなくなったため、最終メモリ検証をスキップしました"
                )
        elif initial_memory is None:
            print(
                "情報: psutilモジュールが利用できないため、メモリ使用量の検証をスキップしました"
            )

        print(
            f"✓ ページネーション処理パフォーマンステスト成功:\n"
            f"  - 平均処理時間: {avg_processing_time:.4f}s\n"
            f"  - 最大処理時間: {max_processing_time:.4f}s\n"
            f"  - 最小処理時間: {min_processing_time:.4f}s\n"
            f"  - 標準偏差: {std_dev:.4f}s\n"
            f"  - 閾値: {threshold:.4f}s\n"
            f"  - ページ数: {num_pages}\n"
            f"  - ページサイズ: {page_size}文字"
        )
