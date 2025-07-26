# 開発者ガイド

Phaser MCP Serverの開発に貢献していただき、ありがとうございます。このドキュメントでは、開発環境のセットアップ、コーディング規約、テスト方法、デプロイメントプロセスについて説明します。

## 開発環境のセットアップ

### 前提条件

- **Python**: 3.13以上（推奨: 3.14以上）
- **uv**: パッケージマネージャー
- **Git**: バージョン管理
- **Docker**: コンテナ実行

### 開発環境の構築

```bash
# 1. リポジトリをクローン
git clone https://github.com/satoshi256kbyte/phaser-mcp-server.git
cd phaser-mcp-server

# 2. 仮想環境を作成して依存関係をインストール
uv sync

# 3. 開発用依存関係も含めてインストール
uv sync --dev

# 4. 開発モードでインストール
uv pip install -e .

# 5. pre-commit フックをインストール
uv run pre-commit install
```

### 実行方法

#### 開発環境での実行

```bash
# 直接実行
uv run phaser-mcp-server

# または仮想環境をアクティベートして実行
source .venv/bin/activate  # Linux/macOS
# または .venv\Scripts\activate  # Windows
phaser-mcp-server
```

#### Docker環境での実行

```bash
# Dockerイメージをビルド
docker build -t phaser-mcp-server:dev .

# 実行
docker run --rm -it phaser-mcp-server:dev
```

## プロジェクト構造

```
phaser-mcp-server/
├── pyproject.toml              # プロジェクト設定・依存関係
├── README.md                   # 利用者向けドキュメント
├── CONTRIBUTING.md             # 開発者向けドキュメント
├── LICENSE                     # ライセンス
├── .gitignore                  # Git除外設定
├── .pre-commit-config.yaml     # Pre-commitフック設定
├── Dockerfile                  # Docker設定
├── Makefile                    # 開発タスク
├── phaser_mcp_server/          # メインパッケージ
│   ├── __init__.py
│   ├── server.py               # MCPサーバーメイン実装
│   ├── client.py               # Phaserドキュメント取得クライアント
│   ├── parser.py               # HTMLパーサー・Markdown変換
│   ├── models.py               # Pydanticモデル定義
│   ├── utils.py                # ユーティリティ関数
│   └── stubs/                  # 型スタブファイル
├── tests/                      # テストファイル
│   ├── __init__.py
│   ├── test_server.py
│   ├── test_client.py
│   ├── test_parser.py
│   ├── test_models.py
│   ├── test_utils.py
│   ├── test_integration.py
│   ├── test_end_to_end.py
│   └── fixtures/               # テスト用データ
└── docs/                       # APIドキュメント
    └── api.md
```

## 技術仕様

### アーキテクチャ

- **言語**: Python 3.13+ (推奨: Python 3.14+)
- **フレームワーク**: FastMCP (Model Context Protocol)
- **パッケージマネージャー**: uv
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
- **utils.py**: ユーティリティ関数

## 開発ワークフロー

### 1. 機能開発

```bash
# 新しいブランチを作成
git checkout -b feature/new-feature

# 開発作業を実行
# ...

# テストを実行
make test

# コード品質チェック
make lint

# 変更をコミット
git add .
git commit -m "feat: add new feature"

# プッシュしてプルリクエストを作成
git push origin feature/new-feature
```

### 2. テスト駆動開発

```bash
# テストを先に書く
# tests/test_new_feature.py

# テストを実行（失敗することを確認）
uv run pytest tests/test_new_feature.py -v

# 機能を実装
# phaser_mcp_server/new_feature.py

# テストを再実行（成功することを確認）
uv run pytest tests/test_new_feature.py -v
```

## テスト

### テスト実行

```bash
# 全テストを実行
make test

# または直接実行
uv run pytest

# カバレッジ付きでテスト実行
uv run pytest --cov=phaser_mcp_server --cov-report=html --cov-report=term-missing

# 特定のテストファイルを実行
uv run pytest tests/test_client.py -v

# 特定のテストメソッドを実行
uv run pytest tests/test_client.py::TestPhaserDocsClient::test_fetch_page_success -v
```

### テスト構成

- **単体テスト**: 各モジュールの個別機能をテスト
- **統合テスト**: モジュール間の連携をテスト
- **エンドツーエンドテスト**: 完全なワークフローをテスト
- **パフォーマンステスト**: メモリ使用量と処理時間をテスト

### テストカバレッジ

現在のテストカバレッジ: **88.65%**

- models.py: 98% coverage
- parser.py: 89% coverage
- client.py: 86% coverage
- server.py: 87% coverage
- utils.py: 100% coverage

### テスト作成のガイドライン

1. **AAA パターン**を使用: Arrange, Act, Assert
2. **モック**を適切に使用してHTTPリクエストをシミュレート
3. **エラーケース**も含めて包括的にテスト
4. **非同期テスト**には`@pytest.mark.asyncio`を使用

## コード品質

### リンティングとフォーマット

```bash
# コードフォーマット
make format

# または個別実行
uv run ruff format
uv run ruff check --fix

# 型チェック
make typecheck

# または直接実行
uv run pyright
```

### コーディング規約

- **PEP 8**: Pythonコーディング規約に準拠
- **型ヒント**: すべての関数とメソッドに型ヒントを追加
- **ドキュメント文字列**: Google形式のdocstringを使用
- **行長**: 88文字以内
- **インポート**: isortによる自動整理

### Pre-commitフック

コミット前に自動的に以下がチェックされます：

- コードフォーマット（ruff）
- リンティング（ruff）
- 型チェック（pyright）
- テスト実行（pytest）

## Docker開発

### Dockerイメージのビルド

```bash
# イメージをビルド
docker build -t phaser-mcp-server:dev .

# 開発用にビルド（キャッシュ無効化）
docker build --no-cache -t phaser-mcp-server:dev .
```

### Docker環境での実行

```bash
# 基本実行
docker run --rm -it phaser-mcp-server:dev

# 環境変数を設定して実行
docker run --rm -it \
  -e FASTMCP_LOG_LEVEL=DEBUG \
  -e PHASER_DOCS_TIMEOUT=60 \
  phaser-mcp-server:dev

# ボリュームマウントで開発
docker run --rm -it \
  -v $(pwd):/app \
  -w /app \
  python:3.13-slim \
  bash
```

### Docker環境変数

| 環境変数                  | 説明                                                | デフォルト値 |
| ------------------------- | --------------------------------------------------- | ------------ |
| `FASTMCP_LOG_LEVEL`       | ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL） | ERROR        |
| `PHASER_DOCS_TIMEOUT`     | HTTPリクエストのタイムアウト（秒）                  | 30           |
| `PHASER_DOCS_MAX_RETRIES` | 失敗したリクエストの最大再試行回数                  | 3            |

## デバッグ

### ログレベルの設定

```bash
# デバッグログを有効にして実行
FASTMCP_LOG_LEVEL=DEBUG uv run phaser-mcp-server

# 特定のモジュールのログを確認
FASTMCP_LOG_LEVEL=DEBUG uv run phaser-mcp-server 2>&1 | grep "client.py"
```

### 対話的デバッグ

```python
# コード内にブレークポイントを設置
import pdb; pdb.set_trace()

# または
breakpoint()
```

### テストデバッグ

```bash
# テスト実行時にpdbを有効化
uv run pytest --pdb

# 失敗時のみpdbを起動
uv run pytest --pdb-trace
```

## 高度なトラブルシューティング

### CAPTCHA/Cloudflare保護の対応

Phaser公式ドキュメントサイトはCloudflareによる保護が有効になっています。

#### 開発時の対応

1. **ブラウザでの事前認証**:
   ```bash
   # ブラウザで https://docs.phaser.io/ にアクセスしてCAPTCHAを突破
   open https://docs.phaser.io/
   ```

2. **セッションCookieの取得と設定**:
   ```python
   # 開発用のCookie設定例
   from phaser_mcp_server.client import PhaserDocsClient
   
   client = PhaserDocsClient()
   client.set_session_cookies({
       "cf_clearance": "your_clearance_token_here",
       "__cfduid": "your_cfduid_here"
   })
   ```

3. **リクエスト頻度の調整**:
   ```bash
   # タイムアウトを長めに設定
   PHASER_DOCS_TIMEOUT=60 uv run phaser-mcp-server
   
   # リトライ回数を減らす
   PHASER_DOCS_MAX_RETRIES=1 uv run phaser-mcp-server
   ```

#### テスト時の対応

```python
# テストでのモック使用例
@pytest.fixture
def mock_phaser_response():
    with httpx_mock.HTTPXMock() as m:
        m.add_response(
            url="https://docs.phaser.io/phaser/getting-started",
            html="<html><body>Mock content</body></html>"
        )
        yield m
```

### パフォーマンス最適化

#### メモリ使用量の監視

```python
# メモリ使用量の測定
from phaser_mcp_server.utils import get_memory_usage

initial_memory = get_memory_usage()
# 処理実行
final_memory = get_memory_usage()
print(f"Memory usage: {final_memory - initial_memory:.2f} MB")
```

#### 処理時間の測定

```python
import time

start_time = time.time()
# 処理実行
end_time = time.time()
print(f"Processing time: {end_time - start_time:.2f} seconds")
```

## MCP クライアント設定（開発・テスト用）

### Amazon Q Developer設定

開発中のサーバーをテストするための設定（`.amazonq/mcp.json`）：

```json
{
  "mcpServers": {
    "phaser-mcp-server-dev": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--interactive",
        "--env",
        "FASTMCP_LOG_LEVEL=DEBUG",
        "--env",
        "PHASER_DOCS_TIMEOUT=60",
        "phaser-mcp-server:dev"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### ローカル開発用設定

```json
{
  "mcpServers": {
    "phaser-mcp-server-local": {
      "command": "uv",
      "args": ["run", "phaser-mcp-server"],
      "cwd": "/path/to/phaser-mcp-server",
      "env": {
        "FASTMCP_LOG_LEVEL": "DEBUG",
        "PHASER_DOCS_TIMEOUT": "60"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## リリースプロセス

### バージョン管理

```bash
# バージョンを確認
uv run phaser-mcp-server --version

# pyproject.tomlでバージョンを更新
# version = "1.1.0"
```

### リリース手順

1. **テストの実行**:
   ```bash
   make test
   make lint
   make typecheck
   ```

2. **バージョンの更新**:
   ```bash
   # pyproject.tomlのversionを更新
   vim pyproject.toml
   ```

3. **Dockerイメージのビルド**:
   ```bash
   docker build -t phaser-mcp-server:1.1.0 .
   docker build -t phaser-mcp-server:latest .
   ```

4. **コミットとタグ**:
   ```bash
   git add .
   git commit -m "chore: bump version to 1.1.0"
   git tag v1.1.0
   git push origin main --tags
   ```

5. **Dockerイメージの公開**（必要に応じて）:
   ```bash
   # Docker Hubまたはプライベートレジストリに公開
   docker push your-registry/phaser-mcp-server:1.1.0
   docker push your-registry/phaser-mcp-server:latest
   ```

## 貢献のガイドライン

### プルリクエスト

1. **ブランチ命名規則**:
   - `feature/description` - 新機能
   - `fix/description` - バグ修正
   - `docs/description` - ドキュメント更新
   - `refactor/description` - リファクタリング

2. **コミットメッセージ**:
   - Conventional Commits形式を使用
   - `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`

3. **プルリクエストの要件**:
   - すべてのテストが通ること
   - コードカバレッジが維持されること
   - リンティングエラーがないこと
   - 適切なドキュメントが含まれること

### コードレビュー

- **機能性**: コードが意図した通りに動作するか
- **可読性**: コードが理解しやすいか
- **保守性**: 将来の変更に対応しやすいか
- **パフォーマンス**: 効率的な実装になっているか
- **セキュリティ**: セキュリティ上の問題がないか

## サポート

### 開発に関する質問

- **GitHub Issues**: バグ報告や機能要望
- **コードレビュー**: プルリクエストでのフィードバック

### 関連リソース

- [Python公式ドキュメント](https://docs.python.org/3/)
- [FastMCPドキュメント](https://github.com/jlowin/fastmcp)
- [Pydanticドキュメント](https://docs.pydantic.dev/)
- [pytestドキュメント](https://docs.pytest.org/)
- [uvドキュメント](https://docs.astral.sh/uv/)
- [Docker公式ドキュメント](https://docs.docker.com/)

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。
