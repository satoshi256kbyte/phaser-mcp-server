"""Test utilities for Phaser MCP Server tests.

This module provides utility functions for testing the Phaser MCP Server.
"""

import gc
from typing import Dict, Optional
from unittest.mock import Mock

import pytest

from phaser_mcp_server.utils import get_memory_usage


def create_mock_response(
    url: str, content: str, status_code: int = 200, content_type: str = "text/html"
) -> Mock:
    """Create a standardized mock response object for testing.

    This function creates a mock response object that simulates an HTTP response
    with the specified properties. It properly sets up all necessary attributes
    and methods, including the `raise_for_status` method that behaves correctly
    based on the status code.

    Args:
        url: The URL for the mock response
        content: The content of the response (as a string)
        status_code: HTTP status code (default: 200)
        content_type: Content type header value (default: "text/html")

    Returns:
        A configured mock response object
    """
    mock_response = Mock()
    mock_response.text = content
    mock_response.status_code = status_code
    mock_response.headers = {"content-type": content_type}
    mock_response.url = url

    # Set binary content properly - both _content and content properties
    content_bytes = content.encode("utf-8")
    mock_response._content = content_bytes

    # Create a mock content object that supports len()
    mock_content = Mock()
    mock_content.__len__ = Mock(return_value=len(content_bytes))
    mock_content.__bytes__ = Mock(return_value=content_bytes)
    mock_content.__str__ = Mock(return_value=content)
    mock_response.content = mock_content

    # Implement raise_for_status method based on status code
    def raise_for_status() -> None:
        if status_code >= 400:
            from httpx import HTTPStatusError

            raise HTTPStatusError(
                f"HTTP Error: {status_code}", request=None, response=mock_response
            )

    mock_response.raise_for_status = raise_for_status

    return mock_response


@pytest.fixture
def setup_test_environment() -> Dict[str, Optional[float]]:
    """テスト環境をセットアップし、テスト前後の状態を管理する。

    このフィクスチャは、テスト実行前にガベージコレクションを強制実行して
    一貫した初期状態を確保し、テスト前のメモリ使用量を記録します。
    テスト完了後も同様にガベージコレクションを実行してリソースを解放します。

    psutilモジュールが利用できない場合、メモリ使用量はNoneとして記録されます。
    この場合、メモリ使用量に依存するテストは適切にスキップされる必要があります。

    Returns:
        テスト前の状態を含む辞書（メモリ使用量など）

    Example:
        ```python
        def test_memory_usage(setup_test_environment):
            initial_state = setup_test_environment
            if initial_state["memory"] is None:
                pytest.skip("psutilモジュールが利用できないため、メモリテストをスキップします")
            # テストコード
            assert get_memory_usage() - initial_state["memory"] < 10  # 10MB以内の増加
        ```
    """
    # ガベージコレクションを強制実行して初期状態をクリーンにする
    gc.collect()

    # テスト前の状態を記録
    # psutilが利用できない場合、get_memory_usage()はNoneを返す
    initial_state = {"memory": get_memory_usage()}

    yield initial_state

    # テスト後のクリーンアップ
    gc.collect()
