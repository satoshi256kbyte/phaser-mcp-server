# Phaser MCP Server

Phaserゲームエンジンのドキュメントへのアクセスを提供するModel Context Protocol (MCP) サーバーです。AIアシスタントがPhaser関連の質問やタスクで開発者を支援できるようにします。

## 概要

このMCPサーバーは、AIアシスタントがPhaser公式ドキュメント、APIリファレンス、チュートリアルにアクセスして検索できるようにします。ゲーム開発者がPhaserのAPIや機能について正確で最新の情報を取得するのを支援するように設計されています。

## 機能

- **ドキュメント読み込み**: PhaserドキュメントページをMarkdown形式で取得・変換
- **ドキュメント検索**: Phaserドキュメント内でのコンテンツ検索
- **APIリファレンス**: Phaserクラス、メソッド、プロパティの詳細情報へのアクセス
- **コード例**: 特定の機能に関するサンプルコードやチュートリアルの取得

## インストール

### uvxを使用（推奨）

```bash
uvx phaser-mcp-server@latest
```

### Dockerを使用

```bash
docker run --rm -it phaser-mcp-server:latest
```

## MCPクライアント設定

MCPクライアント設定に以下を追加してください：

### uvxインストール

```json
{
  "mcpServers": {
    "phaser-mcp-server": {
      "command": "uvx",
      "args": ["phaser-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Dockerインストール

```json
{
  "mcpServers": {
    "phaser-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--interactive",
        "--env",
        "FASTMCP_LOG_LEVEL=ERROR",
        "phaser-mcp-server:latest"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## 利用可能なツール

- `read_documentation`: Phaserドキュメントページの取得と変換
- `search_documentation`: Phaserドキュメント内の検索
- `get_api_reference`: 詳細なAPIリファレンス情報の取得

## 開発

### 前提条件

- Python 3.14+
- uvパッケージマネージャー

### セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd phaser-mcp-server

# 依存関係をインストール
uv sync --dev

# pre-commitフックをインストール
pre-commit install
```

### テスト

```bash
# テストを実行
uv run pytest

# カバレッジ付きでテストを実行
uv run pytest --cov=phaser_mcp_server
```

### コード品質

```bash
# リンティングを実行
uv run ruff check

# フォーマットを実行
uv run ruff format

# 型チェックを実行
uv run pyright
```

## ライセンス

MIT License - 詳細はLICENSEファイルを参照してください。

## 貢献

1. リポジトリをフォーク
2. 機能ブランチを作成
3. 変更を実装
4. テストと品質チェックを実行
5. プルリクエストを提出

## サポート

問題や質問については、GitHubのissue trackerをご利用ください。
