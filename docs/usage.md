# 使用ガイド

Phaser MCP Serverの具体的な使用方法とベストプラクティスについて説明します。

## 基本的な使用方法

### サーバーの起動

```bash
# 基本起動
phaser-mcp-server

# デバッグモードで起動
FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server

# カスタム設定で起動
PHASER_DOCS_TIMEOUT=60 FASTMCP_LOG_LEVEL=INFO phaser-mcp-server
```

### MCP クライアントでの使用

Claude Desktop や他のMCPクライアントから以下のツールを使用できます。

## ツール別使用例

### 1. read_documentation - ドキュメント読み込み

#### 基本的な使用

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/getting-started"
  }
}
```

**結果例:**

```markdown
# Getting Started with Phaser

Phaser is a fun, free and fast 2D game framework for making HTML5 games...

## Installation

You can install Phaser via npm:

```bash
npm install phaser
```

## Your First Game

Create a new HTML file and add the following code:

```javascript
const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    scene: {
        preload: preload,
        create: create
    }
};

const game = new Phaser.Game(config);
```

```

#### 長いドキュメントのページネーション

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/scenes",
    "max_length": 2000,
    "start_index": 0
  }
}
```

続きを読む場合：

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/scenes",
    "max_length": 2000,
    "start_index": 2000
  }
}
```

### 2. search_documentation - ドキュメント検索

#### 基本的な検索

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "sprite animation"
  }
}
```

**結果例:**

```json
[
  {
    "rank_order": 1,
    "url": "https://docs.phaser.io/phaser/animations",
    "title": "Animations - Phaser Documentation",
    "snippet": "Learn how to create sprite animations in Phaser using the Animation Manager...",
    "relevance_score": 0.95
  },
  {
    "rank_order": 2,
    "url": "https://docs.phaser.io/phaser/sprites",
    "title": "Sprites - Phaser Documentation", 
    "snippet": "Sprites are the most important display objects in Phaser...",
    "relevance_score": 0.87
  }
]
```

#### 特定のトピックを検索

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "physics collision detection",
    "limit": 5
  }
}
```

#### 複数キーワードでの検索

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "tween easing functions",
    "limit": 3
  }
}
```

### 3. get_api_reference - API リファレンス取得

#### Scene クラスの情報取得

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.Scene"
  }
}
```

**結果例:**

```markdown
# Phaser.Scene

A Scene is a self-contained game world that can contain its own game objects, cameras, physics systems, and more.

## Constructor

```javascript
new Phaser.Scene(config)
```

### Parameters

- `config` (string | Phaser.Types.Scenes.SettingsConfig) - The scene key or configuration object.

## Methods

### add

```javascript
add: Phaser.GameObjects.GameObjectFactory
```

A reference to the GameObject Factory which can be used to add new objects to this Scene.

### physics

```javascript
physics: Phaser.Physics.Arcade.ArcadePhysics
```

A reference to the Arcade Physics system for this Scene.

## Examples

```javascript
class GameScene extends Phaser.Scene {
    constructor() {
        super({ key: 'GameScene' });
    }
    
    create() {
        this.add.text(400, 300, 'Hello Phaser!', {
            fontSize: '32px',
            fill: '#000'
        });
    }
}
```

```

#### 特定のゲームオブジェクトの情報取得

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.GameObjects.Sprite"
  }
}
```

## 実践的な使用例

### 1. ゲーム開発の学習

#### スプライトの作成方法を学ぶ

1. **検索でトピックを見つける**

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "create sprite",
    "limit": 3
  }
}
```

2. **詳細なドキュメントを読む**

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/sprites"
  }
}
```

3. **API リファレンスで詳細を確認**

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.GameObjects.Sprite"
  }
}
```

### 2. 特定の機能の実装

#### 物理エンジンの実装

1. **物理エンジンについて検索**

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "arcade physics setup",
    "limit": 5
  }
}
```

2. **設定方法のドキュメントを読む**

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/physics/arcade-physics"
  }
}
```

3. **Physics クラスの API を確認**

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.Physics.Arcade.ArcadePhysics"
  }
}
```

### 3. トラブルシューティング

#### エラーの解決

1. **エラーメッセージで検索**

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "texture not found error",
    "limit": 5
  }
}
```

2. **関連するドキュメントを読む**

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/textures"
  }
}
```

## ベストプラクティス

### 1. 効率的な検索

#### 良い検索クエリの例

- `"sprite animation"` - 具体的なトピック
- `"physics collision"` - 関連する概念を組み合わせ
- `"tween easing"` - 機能と詳細を指定

#### 避けるべき検索クエリ

- `"game"` - 一般的すぎる
- `"how to"` - 曖昧すぎる
- `"問題"` - 日本語（英語推奨）

### 2. ドキュメント読み込みの最適化

#### 大きなページの処理

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/complete-guide",
    "max_length": 3000,
    "start_index": 0
  }
}
```

#### 必要な部分のみ取得

- 最初に `max_length: 1000` で概要を確認
- 必要に応じて `start_index` を調整して続きを読む
- 全体を読む必要がない場合は適切な長さに制限

### 3. API リファレンスの活用

#### 完全なクラス名を使用

```json
// 良い例
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.GameObjects.Sprite"
  }
}

// 悪い例
{
  "name": "get_api_reference", 
  "arguments": {
    "class_name": "Sprite"  // 名前空間が不完全
  }
}
```

## 高度な使用例

### 1. 複数ツールの組み合わせ

#### 包括的な学習フロー

```javascript
// 1. トピックを検索
const searchResults = await mcp.call_tool("search_documentation", {
  query: "game state management",
  limit: 3
});

// 2. 最も関連性の高いドキュメントを読む
const documentation = await mcp.call_tool("read_documentation", {
  url: searchResults[0].url,
  max_length: 2000
});

// 3. 関連するクラスのAPI情報を取得
const apiReference = await mcp.call_tool("get_api_reference", {
  class_name: "Phaser.Scenes.SceneManager"
});
```

### 2. 段階的な学習

#### 初心者向けの学習パス

1. **基本概念の理解**

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "getting started tutorial",
    "limit": 1
  }
}
```

2. **基本的なゲームオブジェクト**

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.GameObjects.GameObject"
  }
}
```

3. **シーンの管理**

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/scenes"
  }
}
```

## パフォーマンス最適化

### 1. リクエストの最適化

#### 適切なページサイズ設定

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/large-document",
    "max_length": 2000,  // メモリ使用量を制御
    "start_index": 0
  }
}
```

#### 検索結果数の制限

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "animation",
    "limit": 5  // 必要な数に制限
  }
}
```

### 2. エラー処理

#### リトライ戦略

```javascript
async function robustDocumentationRead(url, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await mcp.call_tool("read_documentation", { url });
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. 検索結果が見つからない

**問題**: 検索クエリに対して結果が返されない

**解決方法**:

- より一般的なキーワードを使用
- 英語のキーワードを使用
- スペルミスがないか確認

```json
// 改善前
{
  "name": "search_documentation",
  "arguments": {
    "query": "スプライト アニメーション"  // 日本語
  }
}

// 改善後
{
  "name": "search_documentation",
  "arguments": {
    "query": "sprite animation"  // 英語
  }
}
```

#### 2. API リファレンスが見つからない

**問題**: クラス名でAPIリファレンスが取得できない

**解決方法**:

- 完全な名前空間を含むクラス名を使用
- 大文字小文字を正確に指定
- Phaser 3の最新ドキュメントでクラス名を確認

```json
// 改善前
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "sprite"  // 不完全
  }
}

// 改善後
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.GameObjects.Sprite"  // 完全な名前空間
  }
}
```

#### 3. タイムアウトエラー

**問題**: リクエストがタイムアウトする

**解決方法**:

- タイムアウト時間を延長
- より小さなページサイズを使用
- ネットワーク接続を確認

```bash
# タイムアウト時間を延長
export PHASER_DOCS_TIMEOUT=60
phaser-mcp-server
```

### デバッグ方法

#### 詳細ログの有効化

```bash
# デバッグログを有効にして問題を特定
FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server
```

#### ヘルスチェック

```bash
# サーバーの状態を確認
phaser-mcp-server --health-check
```

## 参考リンク

- [Phaser 公式サイト](https://phaser.io/)
- [Phaser 公式ドキュメント](https://docs.phaser.io/)
- [Phaser API リファレンス](https://docs.phaser.io/api/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## サポート

使用方法について質問がある場合は、以下のリソースを活用してください：

- [GitHub Issues](https://github.com/phaser-mcp-server/phaser-mcp-server/issues) - バグ報告や機能要望
- [GitHub Discussions](https://github.com/phaser-mcp-server/phaser-mcp-server/discussions) - 使用方法の質問や議論
- [Phaser コミュニティ](https://phaser.io/community) - Phaser 全般の質問
