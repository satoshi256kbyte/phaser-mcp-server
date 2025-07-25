"""Utility functions for Phaser MCP Server.

This module provides utility functions for the Phaser MCP Server, including
performance measurement and testing utilities.
"""

from typing import Optional


def get_memory_usage() -> Optional[float]:
    """現在のプロセスのメモリ使用量を取得する。

    このユーティリティ関数は、現在実行中のPythonプロセスのメモリ使用量を
    メガバイト単位で返します。psutilモジュールが利用できない場合は、
    Noneを返します。

    Returns:
        メモリ使用量（MB）またはNone（psutilが利用できない場合）
    """
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        # RSS (Resident Set Size) - 実際に使用されている物理メモリ量
        return process.memory_info().rss / 1024 / 1024  # MB単位に変換
    except (ImportError, AttributeError):
        # psutilモジュールが利用できない場合や、
        # 予期しない属性エラーが発生した場合はNoneを返す
        return None
