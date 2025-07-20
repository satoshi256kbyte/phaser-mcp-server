# Project Organization & Structure

## プロジェクト構造

```
phaser-mcp-server/
├── pyproject.toml              # プロジェクト設定・依存関係
├── README.md                   # プロジェクト説明・使用方法
├── LICENSE                     # ライセンス
├── .gitignore                  # Git除外設定
├── .pre-commit-config.yaml     # Pre-commitフック設定
├── phaser_mcp_server/          # メインパッケージ
│   ├── __init__.py
│   ├── server.py               # MCPサーバーメイン実装
│   ├── client.py               # Phaserドキュメント取得クライアント
│   ├── parser.py               # HTMLパーサー・Markdown変換
│   └── models.py               # Pydanticモデル定義
├── tests/                      # テストファイル
│   ├── __init__.py
│   ├── test_server.py
│   ├── test_client.py
│   └── test_parser.py
└── docs/                       # ドキュメント
    ├── installation.md
    ├── usage.md
    └── api.md
```

## パッケージ構成

- **phaser_mcp_server/**: メインパッケージディレクトリ
  - `server.py`: MCP サーバーの実装、ツール定義
  - `client.py`: Phaser ドキュメントサイトへのHTTPリクエスト処理
  - `parser.py`: HTML解析とMarkdown変換ロジック
  - `models.py`: データモデルとバリデーション

## 設定ファイル

- `pyproject.toml`: プロジェクト設定、依存関係、ビルド設定
- `.pre-commit-config.yaml`: コード品質チェック設定
- `.gitignore`: Git管理除外ファイル設定

## 開発・テスト

- `tests/`: 単体テスト・統合テスト
- `docs/`: プロジェクトドキュメント
