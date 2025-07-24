# Docker 設定

Phaser MCP Serverは、Dockerコンテナとして実行することができます。このドキュメントでは、Dockerを使用してサーバーをビルド、実行、管理する方法について説明します。

## 前提条件

- Docker がインストールされていること
- Docker Compose がインストールされていること（オプション、推奨）

## Dockerイメージのビルド

プロジェクトのルートディレクトリで以下のコマンドを実行して、Dockerイメージをビルドします：

```bash
docker build -t phaser-mcp-server:latest .
```

## コンテナの実行

### Docker CLIを使用する場合

```bash
docker run -d --name phaser-mcp-server \
  -e FASTMCP_LOG_LEVEL=INFO \
  -e PHASER_DOCS_TIMEOUT=30 \
  -e PHASER_DOCS_MAX_RETRIES=3 \
  -p 8000:8000 \
  phaser-mcp-server:latest
```

### Docker Composeを使用する場合

プロジェクトに含まれる`docker-compose.yml`ファイルを使用して、コンテナを起動できます：

```bash
docker-compose up -d
```

## 環境変数

Dockerコンテナは以下の環境変数をサポートしています：

| 環境変数 | 説明 | デフォルト値 |
|----------|------|------------|
| `FASTMCP_LOG_LEVEL` | ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL） | ERROR |
| `PHASER_DOCS_TIMEOUT` | HTTPリクエストのタイムアウト（秒） | 30 |
| `PHASER_DOCS_MAX_RETRIES` | 失敗したリクエストの最大再試行回数 | 3 |

## ヘルスチェック

コンテナには組み込みのヘルスチェック機能があり、サーバープロセスが正常に動作しているかを定期的に確認します。ヘルスステータスは以下のコマンドで確認できます：

```bash
docker inspect --format='{{.State.Health.Status}}' phaser-mcp-server
```

## MCP クライアント設定

Dockerコンテナを使用する場合のMCPクライアント設定例：

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

## トラブルシューティング

### ログの確認

コンテナのログを確認するには：

```bash
docker logs phaser-mcp-server
```

### コンテナ内でのコマンド実行

コンテナ内でコマンドを実行するには：

```bash
docker exec -it phaser-mcp-server /bin/bash
```

### ヘルスチェックの失敗

ヘルスチェックが失敗する場合は、以下を確認してください：

1. サーバープロセスが実行されているか
2. 必要なポートが公開されているか
3. 環境変数が正しく設定されているか
