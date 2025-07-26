# Phaser MCP Server

ゲームエンジン[Phaser](https://phaser.io/)を使ったゲーム開発を補助するためのModel Context Protocol (MCP)サーバーです。このMCPサーバーは、生成AIが[Phaserの公式ドキュメント](https://docs.phaser.io/phaser/)を効率的に参照できるようにします。

## 概要

このMCPサーバーは、AIアシスタントがPhaser公式ドキュメント、APIリファレンス、チュートリアルにアクセスして検索できるようにします。ゲーム開発者がPhaserのAPIや機能について正確で最新の情報を取得するのを支援します。

## 機能

- **ドキュメント読み込み**: Phaserドキュメントページを取得してMarkdown形式に変換
- **ドキュメント検索**: Phaserドキュメント内でのコンテンツ検索
- **APIリファレンス**: Phaserの各クラス、メソッド、プロパティの詳細情報を取得
- **ページネーション**: 大きなドキュメントページの分割取得
- **エラーハンドリング**: 包括的なエラー処理とリトライ機能
- **セキュリティ**: Phaserドメインのみアクセス許可

## 対象ドキュメント

- Phaser 3 公式ドキュメント (<https://docs.phaser.io/phaser/>)
- API リファレンス (<https://docs.phaser.io/api/>)
- チュートリアル・ガイド
- サンプルコード集

## 使用例

AIアシスタントとの対話例：

- "Phaserでスプライトを作成する方法を教えて"
- "Scene クラスのドキュメントを取得して"
- "物理エンジンの使い方に関するチュートリアルを検索して"
- "Tweenアニメーションのサンプルコードを見せて"
- "Phaser.GameObjectsクラスのAPIリファレンスを表示して"
- "タイルマップの作成方法について詳しく教えて"

## インストールと実行

### 前提条件

Docker がインストールされている必要があります：

```bash
# Docker のインストール確認
docker --version
```

### セットアップ手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/satoshi256kbyte/phaser-mcp-server.git
cd phaser-mcp-server

# 2. Dockerイメージをビルド
docker build -t phaser-mcp-server .

# 3. 動作確認（オプション）
docker run --rm phaser-mcp-server --version
```

### MCP クライアント設定

Amazon Q Developer の設定ファイル（`.amazonq/mcp.json`）に以下を追加：

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
        "--env",
        "PHASER_DOCS_TIMEOUT=30",
        "phaser-mcp-server"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

設定完了後、Amazon Q Developerを再起動してMCPサーバーが利用可能になります。

## 利用可能なMCPツール

### `read_documentation`

Phaserドキュメントページを取得してMarkdown形式に変換します。

**パラメータ:**

- `url` (string, 必須): 取得するPhaserドキュメントのURL
- `max_length` (integer, オプション): 返すコンテンツの最大文字数（デフォルト: 5000）
- `start_index` (integer, オプション): ページネーション用の開始インデックス（デフォルト: 0）

**使用例:**

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/getting-started",
    "max_length": 3000
  }
}
```

### `search_documentation`

Phaserドキュメント内でコンテンツを検索します。

**パラメータ:**

- `query` (string, 必須): 検索クエリ
- `limit` (integer, オプション): 返す結果の最大数（デフォルト: 10）

**使用例:**

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "sprite animation",
    "limit": 5
  }
}
```

### `get_api_reference`

特定のPhaserクラスのAPIリファレンス情報を取得します。

**パラメータ:**

- `class_name` (string, 必須): 取得するPhaserクラス名

**使用例:**

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.Scene"
  }
}
```

## 設定オプション

### 環境変数

以下の環境変数でサーバーの動作をカスタマイズできます：

| 環境変数                  | デフォルト値 | 説明                                                       |
| ------------------------- | ------------ | ---------------------------------------------------------- |
| `FASTMCP_LOG_LEVEL`       | `ERROR`      | ログレベル（TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL） |
| `PHASER_DOCS_TIMEOUT`     | `30`         | HTTPリクエストのタイムアウト（秒）                         |
| `PHASER_DOCS_MAX_RETRIES` | `3`          | 最大リトライ回数                                           |

### コマンドラインオプション

```bash
# ヘルプを表示
docker run --rm phaser-mcp-server --help

# バージョン情報を表示
docker run --rm phaser-mcp-server --version

# サーバー情報を表示
docker run --rm phaser-mcp-server --info

# ヘルスチェックを実行
docker run --rm phaser-mcp-server --health-check

# ログレベルを設定
docker run --rm -e FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server

# タイムアウト時間を設定（秒）
docker run --rm -e PHASER_DOCS_TIMEOUT=60 phaser-mcp-server
```

## トラブルシューティング

### よくある問題

#### CAPTCHA/Cloudflare保護による403 Forbiddenエラー

Phaser公式ドキュメントサイト（docs.phaser.io）はCloudflareによる保護が有効になっており、ボットアクセスを検出すると人間であることの確認（CAPTCHA）を求める場合があります。

**解決方法:**

1. **ブラウザでCAPTCHAを突破**:
   - ブラウザで <https://docs.phaser.io/> にアクセス
   - CAPTCHAまたは「人間であることを確認」画面が表示された場合は、指示に従って認証を完了
   - 認証完了後、ページが正常に表示されることを確認

2. **待機時間の調整**:

   ```bash
   # タイムアウト時間を延長
   docker run --rm -e PHASER_DOCS_TIMEOUT=60 phaser-mcp-server
   
   # リトライ回数を減らす
   docker run --rm -e PHASER_DOCS_MAX_RETRIES=1 phaser-mcp-server
   ```

#### 接続エラー

```bash
# ヘルスチェックを実行して接続を確認
docker run --rm phaser-mcp-server --health-check

# デバッグログを有効にして詳細を確認
# .amazonq/mcp.jsonでFASTMCP_LOG_LEVELをDEBUGに変更
```

#### タイムアウトエラー

```bash
# .amazonq/mcp.jsonでPHASER_DOCS_TIMEOUTを60に変更
# または一時的にテスト実行
docker run --rm -e PHASER_DOCS_TIMEOUT=60 phaser-mcp-server --health-check
```

### ログの確認

```bash
# Amazon Q Developerのログを確認するか、一時的にデバッグ実行
docker run --rm -e FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server --health-check
```

### Dockerイメージの管理

```bash
# ビルドしたイメージを確認
docker images phaser-mcp-server

# イメージを削除（再ビルドが必要な場合）
docker rmi phaser-mcp-server
```

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 貢献

プロジェクトへの貢献については、[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

## サポート

### 問題報告・質問

- **バグ報告**: [GitHub Issues](https://github.com/satoshi256kbyte/phaser-mcp-server/issues)
- **機能要望**: [GitHub Issues](https://github.com/satoshi256kbyte/phaser-mcp-server/issues)

### 関連リンク

- [Phaser公式サイト](https://phaser.io/)
- [Phaser公式ドキュメント](https://docs.phaser.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Docker公式サイト](https://www.docker.com/)
