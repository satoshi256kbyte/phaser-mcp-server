# テストカバレッジガイド

このドキュメントでは、Phaser MCP Serverのテストカバレッジ設定と使用方法について説明します。

## 概要

プロジェクトでは以下のカバレッジ目標を設定しています：

- **全体カバレッジ**: 86%以上（ブランチカバレッジ含む）
- **モジュール別カバレッジ**:
  - `models.py`: 98%以上
  - `parser.py`: 90%以上
  - `client.py`: 90%以上
  - `server.py`: 90%以上
  - `utils.py`: 100%

## カバレッジの実行方法

### 基本的なカバレッジレポート

```bash
# 基本的なカバレッジレポートを生成
make test-cov

# カバレッジ閾値チェック付きでテスト実行
make test-cov-check
```

### 詳細なカバレッジ分析

```bash
# モジュール別カバレッジチェック
uv run python scripts/check_coverage.py

# CI用テスト（カバレッジ閾値チェック付き）
make ci-test
```

### HTMLレポートの確認

テスト実行後、`htmlcov/index.html`を開いてブラウザで詳細なカバレッジレポートを確認できます。

```bash
# macOSの場合
open htmlcov/index.html

# Linuxの場合
xdg-open htmlcov/index.html
```

## カバレッジ設定

### pytest設定

`pyproject.toml`でのpytest設定：

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=phaser_mcp_server",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=86",
]
```

### coverage設定

```toml
[tool.coverage.run]
source = ["phaser_mcp_server"]
branch = true
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*",
    "phaser_mcp_server/stubs/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
sort = "Cover"
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "pass",
    "raise ImportError",
]
```

## GitHub Actions CI

`.github/workflows/test-coverage.yml`でCI/CDパイプラインが設定されています：

- プルリクエストとmainブランチへのマージ時に実行
- Python 3.13と3.14でのマトリックステスト
- カバレッジレポートの生成とアップロード
- モジュール別カバレッジ閾値チェック

## カバレッジレポートの読み方

### ターミナル出力

```bash
Name                          Stmts   Miss Branch BrPart   Cover   Missing
--------------------------------------------------------------------------
phaser_mcp_server/client.py     516     70    226     31  83.96%   210, 212, 214, ...
phaser_mcp_server/parser.py     511     52    280     44  85.84%   167, 279-283, ...
phaser_mcp_server/server.py     256     31     50     10  86.60%   52, 80, 82-83, ...
phaser_mcp_server/models.py     120      3     48      4  95.83%   79, 196, 329, ...
--------------------------------------------------------------------------
TOTAL                          1416    156    604     89  86.19%
```

- **Stmts**: 実行可能な文の総数
- **Miss**: カバーされていない文の数
- **Branch**: 分岐の総数
- **BrPart**: 部分的にカバーされた分岐の数
- **Cover**: カバレッジ率
- **Missing**: カバーされていない行番号

### モジュール別レポート

`scripts/check_coverage.py`の出力：

```bash
📊 Module Coverage Report
==================================================
✅ phaser_mcp_server/models.py
   Coverage: 100.00% (threshold: 98%)
   Lines: 120/120 covered, 0 missing

❌ phaser_mcp_server/client.py
   Coverage: 83.96% (threshold: 90%)
   Lines: 516/520 covered, 4 missing
   Missing lines: [210, 212, 214, 1479]
```

## カバレッジ向上のヒント

### 1. 未カバー行の特定

```bash
# HTMLレポートで詳細確認
open htmlcov/index.html

# ターミナルで未カバー行を確認
uv run pytest --cov=phaser_mcp_server --cov-report=term-missing
```

### 2. ブランチカバレッジの改善

- 条件分岐（if/else）の両方のパスをテスト
- 例外処理のテストケースを追加
- エッジケースのテストを実装

### 3. テストマーカーの活用

```python
@pytest.mark.unit
def test_function():
    pass

@pytest.mark.integration
def test_integration():
    pass
```

特定のマーカーのみ実行：

```bash
# ユニットテストのみ実行
uv run pytest -m unit

# 統合テストを除外
uv run pytest -m "not integration"
```

## トラブルシューティング

### カバレッジデータが見つからない

```bash
# テストを実行してカバレッジデータを生成
uv run pytest --cov=phaser_mcp_server --cov-report=xml

# その後でカバレッジチェックを実行
uv run python scripts/check_coverage.py
```

### 閾値を満たさない場合

1. HTMLレポートで未カバー行を確認
2. 該当箇所のテストケースを追加
3. エッジケースや例外処理のテストを実装
4. 必要に応じて`pragma: no cover`でカバレッジ対象外に指定

### CI/CDでの失敗

GitHub Actionsでカバレッジチェックが失敗した場合：

1. ローカルで`make test-cov-check`を実行
2. 失敗したモジュールのテストを追加
3. プルリクエストを更新

## 参考資料

- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [GitHub Actions workflow](.github/workflows/test-coverage.yml)
- [カバレッジチェックスクリプト](scripts/check_coverage.py)
