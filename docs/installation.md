# インストールガイド

Phaser MCP Serverのインストール方法について詳しく説明します。

## システム要件

### 最小要件

- **Python**: 3.13以上（推奨: 3.14以上）
- **メモリ**: 最小512MB、推奨1GB以上
- **ディスク容量**: 100MB以上の空き容量
- **ネットワーク**: インターネット接続（Phaserドキュメントアクセス用）

### サポートOS

- **Linux**: Ubuntu 20.04+, CentOS 8+, Debian 11+
- **macOS**: 10.15 (Catalina) 以上
- **Windows**: Windows 10/11 (WSL2推奨)

## インストール方法

### 方法1: uvx を使用（推奨）

最も簡単で推奨される方法です。

#### 前提条件

uvパッケージマネージャーがインストールされている必要があります：

```bash
# macOS (Homebrew)
brew install uv

# Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### インストールと実行

```bash
# 最新版を直接実行
uvx phaser-mcp-server@latest

# 特定のバージョンを実行
uvx phaser-mcp-server@1.0.0

# バージョン確認
uvx phaser-mcp-server@latest --version
```

### 方法2: Docker を使用

コンテナ環境での実行に適しています。

#### 前提条件

Docker がインストールされている必要があります：

```bash
# Docker のインストール確認
docker --version
```

#### 実行方法

```bash
# 基本実行
docker run --rm -it phaser-mcp-server:latest

# 環境変数を設定して実行
docker run --rm -it \
  -e FASTMCP_LOG_LEVEL=DEBUG \
  -e PHASER_DOCS_TIMEOUT=60 \
  phaser-mcp-server:latest

# バックグラウンドで実行
docker run -d --name phaser-mcp \
  -e FASTMCP_LOG_LEVEL=ERROR \
  phaser-mcp-server:latest
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  phaser-mcp-server:
    image: phaser-mcp-server:latest
    environment:
      - FASTMCP_LOG_LEVEL=ERROR
      - PHASER_DOCS_TIMEOUT=30
    restart: unless-stopped
```

```bash
# 実行
docker-compose up -d
```

### 方法3: ソースからインストール（開発者向け）

開発やカスタマイズが必要な場合に使用します。

#### 前提条件

```bash
# 必要なツールのインストール
# Git
git --version

# Python 3.13+
python3 --version

# uv パッケージマネージャー
uv --version
```

#### インストール手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/phaser-mcp-server/phaser-mcp-server.git
cd phaser-mcp-server

# 2. 仮想環境を作成して依存関係をインストール
uv sync

# 3. 開発用依存関係も含めてインストール
uv sync --dev

# 4. 開発モードでインストール
uv pip install -e .

# 5. pre-commit フックをインストール（開発者向け）
uv run pre-commit install
```

#### 実行

```bash
# 直接実行
uv run phaser-mcp-server

# または仮想環境をアクティベートして実行
source .venv/bin/activate  # Linux/macOS
# または .venv\Scripts\activate  # Windows
phaser-mcp-server
```

## MCP クライアント設定

### Claude Desktop

Claude Desktop の設定ファイルに以下を追加：

#### uvx インストールの場合

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

#### Docker インストールの場合

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

### その他のMCPクライアント

他のMCPクライアントでも同様の設定で使用できます。詳細は各クライアントのドキュメントを参照してください。

## 設定ファイルの場所

### Claude Desktop

| OS      | 設定ファイルの場所                                                |
| ------- | ----------------------------------------------------------------- |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`                     |
| Linux   | `~/.config/Claude/claude_desktop_config.json`                     |

## 環境変数設定

### 基本設定

```bash
# ログレベル設定
export FASTMCP_LOG_LEVEL=ERROR

# タイムアウト設定（秒）
export PHASER_DOCS_TIMEOUT=30

# 最大リトライ回数
export PHASER_DOCS_MAX_RETRIES=3

# キャッシュTTL（秒、将来の機能用）
export PHASER_DOCS_CACHE_TTL=3600
```

### 永続的な設定

#### Linux/macOS

```bash
# ~/.bashrc または ~/.zshrc に追加
echo 'export FASTMCP_LOG_LEVEL=ERROR' >> ~/.bashrc
echo 'export PHASER_DOCS_TIMEOUT=30' >> ~/.bashrc
source ~/.bashrc
```

#### Windows

```powershell
# PowerShell で永続的に設定
[Environment]::SetEnvironmentVariable("FASTMCP_LOG_LEVEL", "ERROR", "User")
[Environment]::SetEnvironmentVariable("PHASER_DOCS_TIMEOUT", "30", "User")
```

## インストール確認

### 基本動作確認

```bash
# バージョン確認
phaser-mcp-server --version

# サーバー情報表示
phaser-mcp-server --info

# ヘルスチェック実行
phaser-mcp-server --health-check
```

### 詳細テスト

```bash
# デバッグモードで起動
FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server

# 別のターミナルでMCPクライアントからテスト
# （具体的なテスト方法はクライアントによって異なります）
```

## トラブルシューティング

### よくある問題

#### 1. Python バージョンエラー

```bash
# エラー例
ERROR: Python 3.12 is not supported

# 解決方法
# Python 3.13+ をインストール
pyenv install 3.14.0
pyenv global 3.14.0
```

#### 2. uv が見つからない

```bash
# エラー例
command not found: uv

# 解決方法
# uv をインストール
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

#### 3. Docker イメージが見つからない

```bash
# エラー例
Unable to find image 'phaser-mcp-server:latest'

# 解決方法
# イメージをビルドまたはプル
docker build -t phaser-mcp-server:latest .
# または
docker pull phaser-mcp-server:latest
```

#### 4. 権限エラー

```bash
# エラー例
Permission denied

# 解決方法（Linux/macOS）
sudo chown -R $USER:$USER ~/.local/share/uv
# または
sudo usermod -aG docker $USER
newgrp docker
```

#### 5. ネットワーク接続エラー

```bash
# エラー例
Failed to connect to docs.phaser.io

# 解決方法
# プロキシ設定（必要に応じて）
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# DNS設定確認
nslookup docs.phaser.io
```

### ログの確認

```bash
# 詳細ログを有効にして問題を特定
FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server 2>&1 | tee debug.log

# ログファイルを確認
less debug.log
```

### サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. OS とバージョン
1. Python バージョン
1. インストール方法
1. エラーメッセージの全文
1. 実行したコマンド
1. 環境変数の設定

## アップデート

### uvx インストールの場合

```bash
# 最新版に自動更新（次回実行時）
uvx phaser-mcp-server@latest

# 特定バージョンに更新
uvx phaser-mcp-server@1.1.0
```

### Docker インストールの場合

```bash
# 最新イメージをプル
docker pull phaser-mcp-server:latest

# 古いコンテナを停止・削除
docker stop phaser-mcp
docker rm phaser-mcp

# 新しいコンテナを起動
docker run -d --name phaser-mcp phaser-mcp-server:latest
```

### ソースインストールの場合

```bash
# リポジトリを更新
git pull origin main

# 依存関係を更新
uv sync

# 再インストール
uv pip install -e .
```

## アンインストール

### uvx インストールの場合

uvx は実行時にダウンロードするため、特別なアンインストール手順は不要です。

### Docker インストールの場合

```bash
# コンテナを停止・削除
docker stop phaser-mcp
docker rm phaser-mcp

# イメージを削除
docker rmi phaser-mcp-server:latest
```

### ソースインストールの場合

```bash
# 仮想環境を削除
rm -rf .venv

# リポジトリディレクトリを削除
cd ..
rm -rf phaser-mcp-server
```
