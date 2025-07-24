# Phaser MCP Server

ゲームエンジン[Phaser](https://phaser.io/)を使ったゲーム開発を補助するためのModel Context Protocol (MCP)
サーバーです。このMCPサーバーは、生成AIが[Phaserの公式ドキュメント](https://docs.phaser.io/phaser/)を効率的に参照するのが役割です。

## 概要

このMCPサーバーは、AIアシスタントがPhaser公式ドキュメント、APIリファレンス、チュートリアルにアクセスして検索できるようにします。ゲーム開発者がPhaserのAPIや機能について正確で最新の情報を取得するのを支援するように設計されています。

AWS Documentation MCP
Serverのアーキテクチャをベースとし、Phaserドキュメント（<https://docs.phaser.io/>）に特化した機能を提供します。

## 機能

- **ドキュメント読み込み**: Phaserドキュメントページを取得してMarkdown形式に変換
- **ドキュメント検索**: Phaserドキュメント内でのコンテンツ検索
- **APIリファレンス**: Phaserの各クラス、メソッド、プロパティの詳細情報を取得
- **サンプルコード取得**: 特定の機能に関するサンプルコードやチュートリアルを検索
- **ページネーション**: 大きなドキュメントページの分割取得
- **エラーハンドリング**: 包括的なエラー処理とリトライ機能
- **セキュリティ**: Phaserドメインのみアクセス許可

## 対象ドキュメント

- Phaser 3 公式ドキュメント (<https://docs.phaser.io/phaser/>)
- API リファレンス (<https://docs.phaser.io/api/>)
- チュートリアル・ガイド
- サンプルコード集

## 技術仕様

### アーキテクチャ

- **言語**: Python 3.13+ (推奨: Python 3.14+)
- **フレームワーク**: FastMCP (Model Context Protocol)
- **HTTPクライアント**: httpx (非同期HTTP通信)
- **HTMLパーサー**: BeautifulSoup4
- **Markdown変換**: markdownify
- **データバリデーション**: Pydantic
- **ログ記録**: loguru

### 主要コンポーネント

- **server.py**: MCPサーバーのメイン実装とツール定義
- **client.py**: PhaserドキュメントサイトへのHTTPリクエスト処理
- **parser.py**: HTML解析とMarkdown変換ロジック
- **models.py**: データモデルとバリデーション

## 使用例

AIアシスタントとの対話例：

- "Phaserでスプライトを作成する方法を教えて"
- "Scene クラスのドキュメントを取得して"
- "物理エンジンの使い方に関するチュートリアルを検索して"
- "Tweenアニメーションのサンプルコードを見せて"
- "Phaser.GameObjectsクラスのAPIリファレンスを表示して"
- "タイルマップの作成方法について詳しく教えて"

## インストール

### 前提条件

- Python 3.13+ (推奨: Python 3.14+)
- uvパッケージマネージャー（uvxでの実行用）

uvパッケージマネージャーのインストール方法については、[公式ドキュメント](https://docs.astral.sh/uv/getting-started/installation/)を参照してください。

### uvxを使用（推奨）

最も簡単なインストール方法です：

```bash
# 最新版を実行
uvx phaser-mcp-server@latest

# 特定のバージョンを実行
uvx phaser-mcp-server@1.0.0
```

### Dockerを使用

コンテナ環境での実行：

```bash
# イメージをビルド
docker build -t phaser-mcp-server:latest .

# 最新版を実行
docker run --rm -it phaser-mcp-server:latest

# 環境変数を設定して実行
docker run --rm -it \
  -e FASTMCP_LOG_LEVEL=DEBUG \
  -e PHASER_DOCS_TIMEOUT=60 \
  phaser-mcp-server:latest

# docker-composeを使用して実行
docker-compose up

# バックグラウンドで実行
docker-compose up -d

# ヘルスチェックを実行
docker exec phaser-mcp-server docker-healthcheck.sh
```

### 開発者向けインストール

ソースコードから開発環境をセットアップする場合：

#### 前提条件（asdfを使用する場合）

asdfを使ってPythonとuvを管理する場合：

```bash
# asdfをインストール（まだインストールしていない場合）
# macOS (Homebrew)
brew install asdf

# Linux
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc
echo '. "$HOME/.asdf/completions/asdf.bash"' >> ~/.bashrc
source ~/.bashrc

# Pythonプラグインを追加
asdf plugin add python

# Python 3.14をインストール（推奨バージョン）
asdf install python 3.14.0
asdf global python 3.14.0

# uvプラグインを追加してインストール
asdf plugin add uv
asdf install uv latest
asdf global uv latest

# インストール確認
python --version  # Python 3.14.0 が表示されることを確認
uv --version      # uvのバージョンが表示されることを確認
```

#### インストール手順

```bash
# リポジトリをクローン
git clone https://github.com/phaser-mcp-server/phaser-mcp-server.git
cd phaser-mcp-server

# 開発用依存関係を含めてインストール
uv sync --dev

# 開発モードでインストール
uv pip install -e .
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
| `PHASER_DOCS_CACHE_TTL`   | `3600`       | キャッシュの有効期限（秒、将来の機能用）                   |

### コマンドラインオプション

```bash
# ヘルプを表示
phaser-mcp-server --help

# バージョン情報を表示
phaser-mcp-server --version

# サーバー情報を表示
phaser-mcp-server --info

# ヘルスチェックを実行
phaser-mcp-server --health-check

# ログレベルを設定
phaser-mcp-server --log-level DEBUG

# タイムアウト時間を設定（秒）
phaser-mcp-server --timeout 60

# 最大リトライ回数を設定
phaser-mcp-server --max-retries 5

# キャッシュTTLを設定（秒）
phaser-mcp-server --cache-ttl 7200
```

## 開発

### 前提条件

- Python 3.13+ (推奨: Python 3.14+)
- uvパッケージマネージャー

### 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/phaser-mcp-server/phaser-mcp-server.git
cd phaser-mcp-server

# 開発用依存関係を含めてインストール
uv sync --dev

# pre-commitフックをインストール
uv run pre-commit install
```

#### 開発ツール

開発環境には以下のツールが含まれます：

- **ruff**: Pythonコードのリンティングとフォーマット
- **pyright**: 型チェック
- **pytest**: テストフレームワーク
- **mdformat**: Markdownファイルのフォーマット
  - mdformat-gfm: GitHub Flavored Markdown対応
  - mdformat-frontmatter: YAMLフロントマター対応
  - mdformat-tables: テーブルフォーマット対応
- **pre-commit**: コミット前の自動チェック
- **commitizen**: 規約に従ったコミットメッセージ

### テスト

```bash
# 全テストを実行
uv run pytest

# カバレッジレポート付きでテストを実行
uv run pytest --cov=phaser_mcp_server --cov-report=html

# 特定のテストファイルを実行
uv run pytest tests/test_server.py

# ライブテスト（実際のPhaserドキュメントを使用）
uv run pytest -m live
```

### コード品質チェック

```bash
# リンティングを実行
uv run ruff check

# コードフォーマットを実行
uv run ruff format

# Markdownフォーマットを実行
uv run mdformat README.md docs/ --wrap 88

# 型チェックを実行
uv run pyright

# 全品質チェックを実行
uv run pre-commit run --all-files
```

#### Makefileを使用した場合

```bash
# Pythonコードのフォーマット
make format

# Markdownファイルのフォーマット
make format-md

# 全てのフォーマット（Python + Markdown）
make format-all

# Markdownフォーマットのチェック（変更なし）
make format-md-check

# Markdownフォーマットの差分表示
make format-md-diff

# 全品質チェック
make check

# pre-commitフックの実行
make pre-commit
```

### ビルドとパッケージング

```bash
# パッケージをビルド
uv build

# Dockerイメージをビルド
docker build -t phaser-mcp-server:latest .

# Docker Composeでビルドと実行
docker-compose build
docker-compose up

# マルチステージビルドの各ステージを確認
docker build --target builder -t phaser-mcp-server:builder .
```

## トラブルシューティング

### よくある問題

#### 接続エラー

```bash
# ヘルスチェックを実行して接続を確認
phaser-mcp-server --health-check

# デバッグログを有効にして詳細を確認
phaser-mcp-server --log-level DEBUG
```

#### タイムアウトエラー

```bash
# タイムアウト時間を延長
phaser-mcp-server --timeout 60

# または環境変数で設定
PHASER_DOCS_TIMEOUT=60 phaser-mcp-server
```

#### リトライエラー

```bash
# 最大リトライ回数を増加
phaser-mcp-server --max-retries 5

# または環境変数で設定
PHASER_DOCS_MAX_RETRIES=5 phaser-mcp-server
```

#### メモリ使用量が多い場合

```bash
# read_documentationツールでmax_lengthパラメータを小さく設定
# 例: max_length=2000 に設定して使用
```

#### MCPクライアント接続問題

```bash
# サーバー情報を確認
phaser-mcp-server --info

# MCPクライアント設定を確認
# mcp.jsonファイルの設定が正しいか確認
```

### ログの確認

```bash
# 詳細なログを出力
phaser-mcp-server --log-level DEBUG

# エラーのみを出力
phaser-mcp-server --log-level ERROR

# 環境変数でログレベルを設定
FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server
```

### デバッグのヒント

1. **接続テスト**: まず`--health-check`オプションでサーバーの基本動作を確認
1. **ログレベル**: 問題発生時は`--log-level DEBUG`で詳細ログを確認
1. **ネットワーク**: Phaserドキュメントサイト（docs.phaser.io）への接続を確認
1. **リソース**: メモリ使用量が多い場合は`max_length`パラメータを調整

## パフォーマンス

### リソース使用量

- **メモリ使用量**: 通常時約50MB、最大100MB
- **CPU使用量**: 低負荷（リクエスト処理時のみ）
- **ネットワーク**: PhaserドキュメントサイトへのHTTPS接続
- **ディスク使用量**: 最小限（ログファイルのみ）

### パフォーマンス特性

- **レスポンス時間**: 通常1-3秒（ネットワーク状況による）
- **同時接続数**: 最大10接続
- **リクエストタイムアウト**: デフォルト30秒（設定可能）
- **リトライ機能**: 指数バックオフによる自動リトライ

### 最適化のヒント

- 大きなドキュメントページでは`max_length`パラメータを適切に設定（推奨: 2000-5000文字）
- 頻繁にアクセスするページは将来のキャッシュ機能を活用予定
- ネットワーク状況に応じて`--timeout`オプションを調整
- 大量のリクエストを行う場合は`--max-retries`を適切に設定

## セキュリティ

- Phaserの公式ドメイン（docs.phaser.io）のみアクセス許可
- 入力値のサニタイゼーション実装
- レート制限によるDoS攻撃防止
- 非rootユーザーでのDocker実行
- HTTPS通信の強制
- セキュリティイベントのログ記録

## よくある質問（FAQ）

### Q: どのバージョンのPhaserに対応していますか？

A: 主にPhaser 3の公式ドキュメント（docs.phaser.io）に対応しています。Phaser 2のドキュメントは対象外です。

### Q: オフラインで使用できますか？

A: いいえ、このサーバーはPhaserの公式ドキュメントサイトにリアルタイムでアクセスするため、インターネット接続が必要です。

### Q: 他のゲームエンジンのドキュメントにも対応予定はありますか？

A: 現在はPhaserに特化していますが、将来的に他のゲームエンジンへの対応も検討しています。

### Q: キャッシュ機能はありますか？

A: 現在は基本的なキャッシュ機能のみですが、将来のバージョンでより高度なキャッシュ機能を実装予定です。

### Q: 商用利用は可能ですか？

A: はい、MITライセンスの下で商用利用が可能です。

### Q: 貢献方法を教えてください

A: GitHubリポジトリでIssueの報告やPull Requestの提出を歓迎しています。詳細は貢献セクションを参照してください。

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 貢献

1. リポジトリをフォーク
1. 機能ブランチを作成（`git checkout -b feature/amazing-feature`）
1. 変更をコミット（`git commit -m 'feat: add amazing feature'`）
1. ブランチをプッシュ（`git push origin feature/amazing-feature`）
1. プルリクエストを作成

### 開発ガイドライン

- [Conventional Commits](https://www.conventionalcommits.org/)に従ったコミットメッセージ
- テストカバレッジ90%以上を維持
- 全品質チェックをパス（ruff、pyright、pytest）
- ドキュメントの更新

## サポート

### 問題報告・質問

- **バグ報告**:
  [GitHub Issues](https://github.com/phaser-mcp-server/phaser-mcp-server/issues)
- **機能要望**:
  [GitHub Issues](https://github.com/phaser-mcp-server/phaser-mcp-server/issues)
- **質問・議論**:
  [GitHub Discussions](https://github.com/phaser-mcp-server/phaser-mcp-server/discussions)

### ドキュメント

- **プロジェクトドキュメント**: [docs/](docs/)フォルダ内
- **API仕様**: [docs/api.md](docs/api.md)
- **インストールガイド**: [docs/installation.md](docs/installation.md)
- **使用方法**: [docs/usage.md](docs/usage.md)

### 外部リソース

- **Phaser公式ドキュメント**: [docs.phaser.io](https://docs.phaser.io/)
- **Model Context Protocol**:
  [modelcontextprotocol.io](https://modelcontextprotocol.io/)
- **uvパッケージマネージャー**: [docs.astral.sh/uv](https://docs.astral.sh/uv/)

## 関連リンク

- [Phaser公式サイト](https://phaser.io/)
- [Phaser公式ドキュメント](https://docs.phaser.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [uvパッケージマネージャー](https://docs.astral.sh/uv/)
