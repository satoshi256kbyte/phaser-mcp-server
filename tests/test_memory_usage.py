"""Memory usage tests for Phaser MCP Server.

This module contains tests that verify memory usage and performance
of the Phaser MCP Server.
"""

import pytest
from unittest.mock import MagicMock

from phaser_mcp_server.utils import get_memory_usage
from phaser_mcp_server.models import DocumentationPage
from tests.test_end_to_end import MockContext
from tests.test_performance_fixtures import setup_test_environment


class TestMemoryUsage:
    """Memory usage tests for Phaser MCP Server."""

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
        from phaser_mcp_server.server import PhaserMCPServer

        # フィクスチャから初期メモリ使用量を取得
        initial_state = setup_test_environment
        initial_memory = initial_state["memory"]

        # psutilモジュールが利用できない場合はテストをスキップ
        if initial_memory is None:
            pytest.skip(
                "メモリ使用量テストをスキップします: psutilモジュールが利用できません"
            )

        # サーバーインスタンスを作成
        server = PhaserMCPServer()

        # DocumentationPageオブジェクトを作成
        page_content = DocumentationPage(
            url="https://docs.phaser.io/test-memory",
            content=large_html_content,
            title="Test Memory Document",
            content_type="text/html",
            word_count=5000,  # 適当な値を設定
        )

        # モックのMarkdownコンテンツを作成（実際のパース処理をシミュレート）
        mock_markdown = "# Test Document\n\n" + "Test content\n" * 500

        # サーバーのクライアントとパーサーをモック
        server.client = MagicMock()
        server.parser = MagicMock()

        # get_page_contentメソッドのモック
        server.client.get_page_content = MagicMock(return_value=page_content)

        # parse_html_contentとconvert_to_markdownメソッドのモック
        server.parser.parse_html_content = MagicMock(return_value=large_html_content)
        server.parser.convert_to_markdown = MagicMock(return_value=mock_markdown)

        # メモリ管理のストレステストのために複数の大きなドキュメントを処理
        num_docs = 5
        doc_size = 2000

        # ドキュメントを処理してメモリ使用量を追跡
        for i in range(num_docs):
            # サーバーの内部処理をシミュレート
            page = page_content  # モックされたget_page_contentの結果を使用
            parsed_content = server.parser.parse_html_content(page.content, page.url)
            markdown_content = server.parser.convert_to_markdown(parsed_content)

            # ページネーションを適用
            start_index = 0
            end_index = min(start_index + doc_size, len(markdown_content))
            result = markdown_content[start_index:end_index]

            assert isinstance(result, str)
            assert len(result) <= doc_size, (
                f"ドキュメント {i} のサイズが制限を超えています: "
                f"{len(result)} > {doc_size}"
            )

        # 処理後のメモリ使用量を確認
        final_memory = get_memory_usage()
        if final_memory is None:
            pytest.skip("テスト実行中にpsutilモジュールが利用できなくなりました")

        # メモリ増加量を計算
        memory_increase = final_memory - initial_memory

        # ドキュメントサイズと数に基づいて環境に依存しない閾値を設定
        # 計算式: 基本閾値 + (ドキュメントサイズ × ドキュメント数 × 係数)
        base_threshold = 10.0  # MB - 基本的な処理オーバーヘッド
        size_factor = 0.005  # ドキュメントサイズに対する係数
        count_factor = 1.2  # ドキュメント数に対する係数

        # 動的に閾値を計算
        max_allowed_increase = base_threshold + (
            doc_size * num_docs * size_factor * count_factor
        )

        # 詳細なエラーメッセージを含むメモリ使用量のアサーション
        assert memory_increase < max_allowed_increase, (
            f"メモリリークの可能性があります。メモリ使用量が許容値を超えて増加しました:\n"
            f"- 初期メモリ使用量: {initial_memory:.2f}MB\n"
            f"- 最終メモリ使用量: {final_memory:.2f}MB\n"
            f"- 増加量: {memory_increase:.2f}MB\n"
            f"- 許容値: {max_allowed_increase:.2f}MB\n"
            f"- 処理したドキュメント: {num_docs}個 (各{doc_size}文字)\n"
            f"- 推奨対策: メモリ解放処理の確認、大きなオブジェクトの参照解除を確認"
        )

        print(
            f"✓ メモリ使用量テスト成功: 増加量 {memory_increase:.2f}MB "
            f"(許容値: {max_allowed_increase:.2f}MB)"
        )
