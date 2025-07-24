# API リファレンス

Phaser MCP
Serverが提供するMCPツールの詳細なAPIリファレンスです。このドキュメントでは、各ツールの機能、パラメータ、戻り値、使用例、およびベストプラクティスについて説明します。

## 概要

このサーバーは3つの主要なMCPツールを提供します：

- [`read_documentation`](#read_documentation) - Phaserドキュメントページの読み込み
- [`search_documentation`](#search_documentation) - ドキュメント内検索
- [`get_api_reference`](#get_api_reference) - APIリファレンス取得

各ツールは、Phaserゲームエンジンのドキュメントに効率的にアクセスするための特定の機能を提供します。これらのツールを組み合わせることで、開発者はPhaserの機能、APIリファレンス、チュートリアル、サンプルコードに関する情報を簡単に取得できます。

## read_documentation

`read_documentation`ツールは、指定されたURLからPhaserドキュメントページを取得し、Markdown形式に変換します。このツールは、チュートリアル、ガイド、リファレンスなど、Phaserドキュメントの任意のページにアクセスするために使用できます。

### シグネチャ

```python
async def read_documentation(
    ctx: Context,
    url: str,
    max_length: int = 5000,
    start_index: int = 0,
) -> str
```

### パラメータ

| パラメータ    | 型        | 必須 | デフォルト | 説明                                                                                                                                                           |
| ------------- | --------- | ---- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`         | `string`  | ✓    | -          | 取得するPhaserドキュメントのURL。相対パス（例：`/phaser/getting-started`）または絶対URL（例：`https://docs.phaser.io/phaser/getting-started`）を指定できます。 |
| `max_length`  | `integer` | -    | `5000`     | 返すコンテンツの最大文字数。大きなドキュメントを分割して取得する場合に便利です。                                                                               |
| `start_index` | `integer` | -    | `0`        | ページネーション用の開始インデックス。`max_length`と組み合わせて大きなドキュメントを分割して取得できます。                                                     |

### 戻り値

**型**: `string`

Markdown形式に変換されたドキュメントコンテンツを返します。変換されたMarkdownには以下の特徴があります：

- 見出し構造が保持されます（`#`、`##`、`###`など）
- コードブロックは言語指定付きで保持されます（\`\`\`javascript など）
- 画像参照は絶対URLに変換されます
- リンクは絶対URLに変換されます
- テーブルやリストなどの書式も保持されます

### 使用例

#### 基本的な使用

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/getting-started"
  }
}
```

#### ページネーション付き

大きなドキュメントを分割して取得する例：

```json
// 最初の3000文字を取得
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/scenes",
    "max_length": 3000,
    "start_index": 0
  }
}

// 続きの3000文字を取得
{
  "name": "read_documentation",
  "arguments": {
    "url": "https://docs.phaser.io/phaser/scenes",
    "max_length": 3000,
    "start_index": 3000
  }
}
```

#### 相対パスの使用

```json
{
  "name": "read_documentation",
  "arguments": {
    "url": "/phaser/physics/arcade"
  }
}
```

### エラー

| エラータイプ   | 条件                     | メッセージ例                                                 |
| -------------- | ------------------------ | ------------------------------------------------------------ |
| `ValueError`   | `max_length` が0以下     | "max_length must be positive"                                |
| `ValueError`   | `start_index` が負の値   | "start_index must be non-negative"                           |
| `RuntimeError` | 無効なURL                | "Failed to read documentation: Invalid URL"                  |
| `RuntimeError` | 許可されていないドメイン | "Failed to read documentation: URL not from allowed domains" |
| `RuntimeError` | ネットワークエラー       | "Failed to read documentation: Connection timeout"           |
| `RuntimeError` | ページが見つからない     | "Failed to read documentation: Page not found (404)"         |

### ベストプラクティス

1. **大きなページの処理**: 長いドキュメントページでは`max_length`を適切に設定し、メモリ使用量を制御してください。一般的に2000〜5000文字が適切です。
1. **ページネーション**: 大きなコンテンツは`start_index`を使って分割して取得してください。各部分を順番に処理することで、全体を効率的に取得できます。
1. **URL検証**: Phaserの公式ドメイン（docs.phaser.io）のURLのみ使用してください。他のドメインへのアクセスは拒否されます。
1. **相対パスの使用**:
   完全なURLを指定する代わりに、相対パス（例：`/phaser/getting-started`）を使用できます。これはベースURL（`https://docs.phaser.io`）に自動的に追加されます。
1. **エラー処理**:
   ネットワークエラーや無効なURLに対して適切なエラー処理を実装してください。サーバーは自動的にリトライを行いますが、クライアント側でもエラーハンドリングを実装することをお勧めします。

## search_documentation

`search_documentation`ツールは、Phaserドキュメント内でコンテンツを検索し、関連する結果を返します。このツールを使用すると、特定のトピック、機能、またはAPIに関する情報を効率的に見つけることができます。

### シグネチャ

```python
async def search_documentation(
    ctx: Context,
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]
```

### パラメータ

| パラメータ | 型        | 必須 | デフォルト | 説明                                                                                                                   |
| ---------- | --------- | ---- | ---------- | ---------------------------------------------------------------------------------------------------------------------- |
| `query`    | `string`  | ✓    | -          | 検索クエリ文字列。スペースで区切られた複数のキーワードを指定できます。英語のキーワードを使用することを強く推奨します。 |
| `limit`    | `integer` | -    | `10`       | 返す結果の最大数。1〜100の範囲で指定できます。                                                                         |

### 戻り値

**型**: `list[dict[str, Any]]`

検索結果のリストを返します。各結果は以下の構造を持つ辞書（JSONオブジェクト）です：

```json
{
  "rank_order": 1,
  "url": "https://docs.phaser.io/phaser/sprites",
  "title": "Sprites - Phaser Documentation",
  "snippet": "Learn how to create and manage sprites in Phaser...",
  "relevance_score": 0.95
}
```

#### 結果オブジェクトのフィールド

| フィールド        | 型                 | 説明                                                                                                     |
| ----------------- | ------------------ | -------------------------------------------------------------------------------------------------------- |
| `rank_order`      | `integer`          | 検索結果の順位（1から開始）。関連性の高い順にソートされます。                                            |
| `url`             | `string`           | ドキュメントページのURL。このURLは`read_documentation`ツールに直接渡すことができます。                   |
| `title`           | `string`           | ページのタイトル。検索結果を識別するのに役立ちます。                                                     |
| `snippet`         | `string` \| `null` | コンテンツの抜粋。検索クエリに関連する部分が含まれます。利用できない場合は`null`になります。             |
| `relevance_score` | `float` \| `null`  | 関連度スコア（0.0〜1.0）。値が大きいほど関連性が高いことを示します。利用できない場合は`null`になります。 |

### 使用例

#### 基本的な検索

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "sprite animation"
  }
}
```

#### 結果数を制限

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "physics collision",
    "limit": 5
  }
}
```

#### 複数キーワードでの検索

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "tween easing functions"
  }
}
```

#### 特定の機能に関する検索

```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "camera follow player"
  }
}
```

### エラー

| エラータイプ   | 条件                  | メッセージ例                                                 |
| -------------- | --------------------- | ------------------------------------------------------------ |
| `ValueError`   | 空のクエリ            | "Search query cannot be empty"                               |
| `ValueError`   | `limit` が0以下       | "limit must be positive"                                     |
| `ValueError`   | `limit` が100を超える | "limit cannot exceed 100"                                    |
| `RuntimeError` | 検索エラー            | "Failed to search documentation: Search service unavailable" |
| `RuntimeError` | ネットワークエラー    | "Failed to search documentation: Connection timeout"         |

### ベストプラクティス

1. **具体的なクエリ**: より具体的な検索語を使用すると、関連性の高い結果が得られます。例えば、「game」よりも「sprite
   animation」のような具体的なクエリの方が良い結果を得られます。
1. **複数キーワード**: スペース区切りで複数のキーワードを指定できます。これにより、検索範囲を絞り込むことができます。
1. **英語のキーワード**: 検索は英語のキーワードで最も効果的です。日本語などの他の言語では結果が限られる場合があります。
1. **結果の制限**: 必要な結果数に応じて`limit`を調整してください。デフォルトの10が多くの場合に適切ですが、より広範囲の結果が必要な場合は増やすことができます。
1. **検索結果の活用**: 検索結果から得られたURLを`read_documentation`ツールに渡して、詳細な情報を取得できます。
1. **検索戦略**: 最初に広い検索語で始め、結果が多すぎる場合は具体的なキーワードを追加して絞り込むことをお勧めします。

## get_api_reference

`get_api_reference`ツールは、特定のPhaserクラスのAPIリファレンス情報を取得します。このツールを使用すると、クラスの詳細、メソッド、プロパティ、使用例などの情報を取得できます。

### シグネチャ

```python
async def get_api_reference(
    ctx: Context,
    class_name: str,
) -> str
```

### パラメータ

| パラメータ   | 型       | 必須 | デフォルト | 説明                                                                                                                    |
| ------------ | -------- | ---- | ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| `class_name` | `string` | ✓    | -          | 取得するPhaserクラス名。名前空間を含む完全なクラス名（例：`Phaser.GameObjects.Sprite`）を指定することを強く推奨します。 |

### 戻り値

**型**: `string`

Markdown形式でフォーマットされたAPIリファレンス情報を返します。以下の情報が含まれます：

- クラスの概要と説明
- コンストラクタ情報とパラメータ
- メソッド一覧とシグネチャ
- プロパティ一覧と型情報
- 使用例（利用可能な場合）
- 継承関係（親クラスなど）

返されるMarkdownは構造化されており、見出しレベルで情報が整理されています：

````markdown
# Phaser.GameObjects.Sprite

A Sprite Game Object is used for the display of both static and animated images in your game.

## Constructor

```javascript
new Phaser.GameObjects.Sprite(scene, x, y, texture, frame)
````

### Parameters

- `scene` (Phaser.Scene) - The Scene to which this Sprite belongs
- `x` (number) - The horizontal position of this Game Object in the world
- `y` (number) - The vertical position of this Game Object in the world
- `texture` (string | Phaser.Textures.Texture) - The key, or instance of the Texture
  this Game Object will use
- `frame` (string | number) - The initial frame to display

## Methods

- `setTexture(key, frame)` - Sets the texture and frame this Sprite will use for
  rendering
- `play(key, ignoreIfPlaying)` - Starts playing the given animation
- `setPosition(x, y)` - Sets the position of this Game Object

## Properties

- `x` (number) - The horizontal position of this Game Object in the world
- `y` (number) - The vertical position of this Game Object in the world
- `visible` (boolean) - The visible state of the Game Object

## Examples

```javascript
const sprite = this.add.sprite(400, 300, 'player');
sprite.setScale(2);
sprite.play('walk');
```

````

### 使用例

#### Sceneクラスの情報取得

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.Scene"
  }
}
````

#### Spriteクラスの情報取得

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.GameObjects.Sprite"
  }
}
```

#### 物理エンジンクラスの情報取得

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.Physics.Arcade.Body"
  }
}
```

#### 入力関連クラスの情報取得

```json
{
  "name": "get_api_reference",
  "arguments": {
    "class_name": "Phaser.Input.InputPlugin"
  }
}
```

### エラー

| エラータイプ   | 条件                 | メッセージ例                                           |
| -------------- | -------------------- | ------------------------------------------------------ |
| `ValueError`   | 空のクラス名         | "class_name cannot be empty"                           |
| `RuntimeError` | クラスが見つからない | "Failed to get API reference: Class not found"         |
| `RuntimeError` | APIアクセスエラー    | "Failed to get API reference: API service unavailable" |
| `RuntimeError` | ネットワークエラー   | "Failed to get API reference: Connection timeout"      |

### ベストプラクティス

1. **完全なクラス名**: 名前空間を含む完全なクラス名を使用してください（例:
   `Phaser.GameObjects.Sprite`）。単に`Sprite`だけでは、正確なクラスを特定できない場合があります。
1. **大文字小文字**:
   クラス名の大文字小文字は正確に指定してください。Phaserは大文字小文字を区別します（例：`Phaser.Game`は正しいが、`phaser.game`は間違い）。
1. **階層の理解**:
   Phaserのクラス階層を理解することで、必要なクラスを正確に指定できます。例えば、`Sprite`は`Phaser.GameObjects`名前空間に属しています。
1. **関連クラスの探索**: あるクラスのAPIリファレンスを取得した後、関連するクラスやコンポーネントのAPIも確認すると、より包括的な理解が得られます。
1. **検索との組み合わせ**:
   クラス名が不明な場合は、まず`search_documentation`ツールを使用して関連するクラスを検索し、その後`get_api_reference`で詳細情報を取得するという流れが効果的です。

### 一般的なPhaserクラス

以下は、よく使用されるPhaserクラスの一覧です：

- **コア**: `Phaser.Game`, `Phaser.Scene`, `Phaser.GameObjects.GameObject`
- **表示オブジェクト**: `Phaser.GameObjects.Sprite`, `Phaser.GameObjects.Image`,
  `Phaser.GameObjects.Text`
- **物理エンジン**: `Phaser.Physics.Arcade.ArcadePhysics`, `Phaser.Physics.Arcade.Body`,
  `Phaser.Physics.Matter.MatterPhysics`
- **入力**: `Phaser.Input.InputPlugin`, `Phaser.Input.Keyboard.KeyboardPlugin`,
  `Phaser.Input.Pointer`
- **アニメーション**: `Phaser.Animations.AnimationManager`, `Phaser.Tweens.TweenManager`
- **カメラ**: `Phaser.Cameras.Scene2D.Camera`, `Phaser.Cameras.Scene2D.CameraManager`
- **サウンド**: `Phaser.Sound.SoundManager`, `Phaser.Sound.WebAudioSound`
- **タイルマップ**: `Phaser.Tilemaps.Tilemap`, `Phaser.Tilemaps.TilemapLayer`

## 共通のエラーハンドリング

すべてのMCPツールは、一貫したエラーハンドリング戦略を実装しています。これにより、エラーが発生した場合でも、明確なエラーメッセージと適切な対応が可能になります。

### ネットワークエラー

すべてのツールは以下のネットワークエラーを適切に処理します：

- **接続タイムアウト**: `PHASER_DOCS_TIMEOUT`環境変数で設定可能（デフォルト: 30秒）
- **接続失敗**: 自動リトライ機能（`PHASER_DOCS_MAX_RETRIES`で設定可能、デフォルト: 3回）
- **レート制限**: 適切な待機時間を設けて再試行（指数バックオフ戦略を使用）
- **サーバーエラー**: 一時的なサーバーエラー（5xx）の場合は自動的に再試行

### セキュリティ制限

セキュリティを確保するために、以下の制限が実装されています：

- **ドメイン制限**: Phaserの公式ドメイン（docs.phaser.io, phaser.io）のみアクセス可能
- **URL検証**: 不正なURLは事前に検証され、拒否されます
- **入力サニタイゼーション**: すべての入力値は適切にサニタイズされ、インジェクション攻撃を防止
- **コンテンツサイズ制限**: 大きすぎるレスポンスは拒否され、DoS攻撃を防止（最大1MB）
- **コンテンツタイプ検証**: 許可されたコンテンツタイプ（HTML、テキスト）のみ処理

### エラーメッセージの形式

エラーが発生した場合、以下の形式のエラーメッセージが返されます：

```
Failed to [operation]: [specific error message]
```

例：

- "Failed to read documentation: Connection timeout"
- "Failed to search documentation: Search query cannot be empty"
- "Failed to get API reference: Class not found"

## パフォーマンス考慮事項

### レスポンス時間

各ツールの一般的なレスポンス時間は以下の通りです：

- **read_documentation**:

  - 通常のリクエスト: 1-3秒
  - 大きなドキュメント: 3-10秒
  - キャッシュされたコンテンツ: \<1秒（将来の機能）

- **search_documentation**:

  - 基本的な検索: 2-5秒
  - 複雑な検索クエリ: 5-8秒

- **get_api_reference**:

  - 一般的なクラス: 1-3秒
  - 複雑なクラス階層: 3-7秒

### リソース使用量

- **メモリ**: リクエストあたり最大10MB
- **同時接続**: 最大10接続
- **キャッシュ**: 将来のバージョンでキャッシュ機能を実装予定

### 最適化のヒント

1. **適切なページサイズ**: `max_length`を適切に設定してメモリ使用量を制御
1. **効率的な検索**: 具体的な検索クエリを使用して関連性の高い結果を取得
1. **バッチ処理**: 複数のAPIリファレンスが必要な場合は、個別にリクエスト
1. **結果のキャッシュ**: クライアント側で結果をキャッシュすることで、同じリクエストの繰り返しを避ける
1. **エラー時のバックオフ**: エラーが発生した場合は、一定時間待機してから再試行

## 統合例

### Claude Desktop での使用

Claude
Desktopの設定ファイル（`.kiro/settings/mcp.json`または`~/.kiro/settings/mcp.json`）に以下の設定を追加します：

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

### プログラマティックな使用

```python
# MCP クライアントでの使用例
async def get_phaser_sprite_info():
    # APIリファレンスを取得
    sprite_api = await mcp_client.call_tool(
        "get_api_reference",
        {"class_name": "Phaser.GameObjects.Sprite"}
    )
    
    # 関連ドキュメントを検索
    sprite_docs = await mcp_client.call_tool(
        "search_documentation",
        {"query": "sprite creation tutorial", "limit": 3}
    )
    
    # 最も関連性の高いドキュメントを取得
    if sprite_docs:
        top_doc = await mcp_client.call_tool(
            "read_documentation",
            {"url": sprite_docs[0]["url"]}
        )
    
    return sprite_api, sprite_docs, top_doc
```

### 複合的な使用例

```python
# 特定のトピックに関する包括的な情報を取得
async def get_comprehensive_info(topic):
    results = []
    
    # 1. トピックを検索
    search_results = await mcp_client.call_tool(
        "search_documentation",
        {"query": topic, "limit": 5}
    )
    results.append({"type": "search", "data": search_results})
    
    # 2. 関連するAPIクラスを特定
    api_classes = extract_api_classes_from_search(search_results)
    
    # 3. 各APIクラスの詳細を取得
    api_details = []
    for class_name in api_classes:
        api_ref = await mcp_client.call_tool(
            "get_api_reference",
            {"class_name": class_name}
        )
        api_details.append({"class": class_name, "reference": api_ref})
    
    results.append({"type": "api_references", "data": api_details})
    
    # 4. 最も関連性の高いドキュメントを取得
    if search_results:
        top_doc = await mcp_client.call_tool(
            "read_documentation",
            {"url": search_results[0]["url"]}
        )
        results.append({"type": "documentation", "data": top_doc})
    
    return results
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. タイムアウトエラー

**問題**: リクエストがタイムアウトする

**解決方法**:

```bash
# タイムアウト時間を延長
export PHASER_DOCS_TIMEOUT=60
```

**プログラムでの対応**:

```python
# リトライロジックの実装
async def robust_api_call(max_retries=3):
    for attempt in range(max_retries):
        try:
            return await mcp_client.call_tool(
                "get_api_reference",
                {"class_name": "Phaser.GameObjects.Sprite"}
            )
        except Exception as e:
            if "timeout" in str(e).lower() and attempt < max_retries - 1:
                # 指数バックオフで待機
                await asyncio.sleep(2 ** attempt)
                continue
            raise
```

#### 2. 検索結果が見つからない

**問題**: 検索クエリに対して結果が返されない

**解決方法**:

- より一般的な検索語を使用
- スペルミスがないか確認
- 英語のキーワードを使用

**例**:

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

#### 3. APIリファレンスが見つからない

**問題**: クラス名でAPIリファレンスが取得できない

**解決方法**:

- 完全な名前空間を含むクラス名を使用
- 大文字小文字を正確に指定
- Phaser 3の最新ドキュメントでクラス名を確認

**例**:

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

### デバッグ方法

詳細なデバッグ情報を取得するには、ログレベルを変更します：

```bash
# デバッグログを有効にして詳細情報を確認
export FASTMCP_LOG_LEVEL=DEBUG
phaser-mcp-server
```

サーバーの状態を確認するには：

```bash
# サーバー情報を表示
phaser-mcp-server --info

# ヘルスチェックを実行
phaser-mcp-server --health-check
```

## 更新履歴

### v1.0.0

- 初回リリース
- 基本的なドキュメント読み込み機能
- 検索機能
- APIリファレンス取得機能
- Docker サポート
- 包括的なエラーハンドリング

## Docker環境での使用

### Docker環境変数

Docker環境では、以下の環境変数を使用してサーバーの動作をカスタマイズできます：

| 環境変数                  | デフォルト値 | 説明                                                       |
| ------------------------- | ------------ | ---------------------------------------------------------- |
| `FASTMCP_LOG_LEVEL`       | `ERROR`      | ログレベル（TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL） |
| `PHASER_DOCS_TIMEOUT`     | `30`         | HTTPリクエストのタイムアウト（秒）                         |
| `PHASER_DOCS_MAX_RETRIES` | `3`          | 最大リトライ回数                                           |
| `PHASER_DOCS_CACHE_TTL`   | `3600`       | キャッシュTTL（秒、将来の機能用）                          |

### Docker実行例

```bash
# 基本的な実行
docker run -d --name phaser-mcp-server phaser-mcp-server:latest

# 環境変数を設定して実行
docker run -d --name phaser-mcp-server \
  -e FASTMCP_LOG_LEVEL=DEBUG \
  -e PHASER_DOCS_TIMEOUT=60 \
  -e PHASER_DOCS_MAX_RETRIES=5 \
  phaser-mcp-server:latest

# ヘルスチェックの実行
docker exec phaser-mcp-server docker-healthcheck.sh

# ログの確認
docker logs phaser-mcp-server
```

### Docker Compose設定例

```yaml
version: '3.8'

services:
  phaser-mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
    image: phaser-mcp-server:latest
    container_name: phaser-mcp-server
    environment:
      - FASTMCP_LOG_LEVEL=INFO
      - PHASER_DOCS_TIMEOUT=30
      - PHASER_DOCS_MAX_RETRIES=3
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "docker-healthcheck.sh"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped
```

### MCPクライアント設定（Docker）

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

## 高度な使用例

### 1. ゲーム開発の学習フロー

```python
async def learn_phaser_game_development():
    # 1. 基本概念を検索
    basics = await mcp_client.call_tool(
        "search_documentation",
        {"query": "getting started tutorial", "limit": 3}
    )
    
    # 2. 基本チュートリアルを読む
    if basics:
        tutorial = await mcp_client.call_tool(
            "read_documentation",
            {"url": basics[0]["url"]}
        )
        
    # 3. ゲームオブジェクトについて学ぶ
    game_objects = await mcp_client.call_tool(
        "get_api_reference",
        {"class_name": "Phaser.GameObjects.GameObject"}
    )
    
    # 4. シーン管理について学ぶ
    scenes = await mcp_client.call_tool(
        "search_documentation",
        {"query": "scene management", "limit": 2}
    )
    
    if scenes:
        scene_docs = await mcp_client.call_tool(
            "read_documentation",
            {"url": scenes[0]["url"]}
        )
        
    # 5. 物理エンジンについて学ぶ
    physics = await mcp_client.call_tool(
        "get_api_reference",
        {"class_name": "Phaser.Physics.Arcade.ArcadePhysics"}
    )
    
    return {
        "basics": basics,
        "tutorial": tutorial,
        "game_objects": game_objects,
        "scenes": scenes,
        "scene_docs": scene_docs,
        "physics": physics
    }
```

### 2. 特定の機能の実装支援

```python
async def implement_sprite_animation():
    # 1. アニメーションについて検索
    animation_search = await mcp_client.call_tool(
        "search_documentation",
        {"query": "sprite animation sheet", "limit": 3}
    )
    
    # 2. アニメーションマネージャーのAPIを取得
    animation_api = await mcp_client.call_tool(
        "get_api_reference",
        {"class_name": "Phaser.Animations.AnimationManager"}
    )
    
    # 3. スプライトのAPIを取得
    sprite_api = await mcp_client.call_tool(
        "get_api_reference",
        {"class_name": "Phaser.GameObjects.Sprite"}
    )
    
    # 4. 具体的な実装例を検索
    examples = await mcp_client.call_tool(
        "search_documentation",
        {"query": "sprite animation example code", "limit": 2}
    )
    
    # 5. 最も関連性の高い例を取得
    if examples:
        example_doc = await mcp_client.call_tool(
            "read_documentation",
            {"url": examples[0]["url"]}
        )
    
    return {
        "search_results": animation_search,
        "animation_api": animation_api,
        "sprite_api": sprite_api,
        "examples": examples,
        "example_doc": example_doc
    }
```

### 3. トラブルシューティング支援

```python
async def troubleshoot_phaser_issue(error_message):
    # 1. エラーメッセージで検索
    error_search = await mcp_client.call_tool(
        "search_documentation",
        {"query": error_message, "limit": 5}
    )
    
    # 2. 関連するAPIリファレンスを特定
    api_classes = extract_potential_classes_from_error(error_message)
    api_refs = []
    
    for class_name in api_classes:
        try:
            api_ref = await mcp_client.call_tool(
                "get_api_reference",
                {"class_name": class_name}
            )
            api_refs.append({"class": class_name, "reference": api_ref})
        except Exception:
            continue
    
    # 3. 一般的なトラブルシューティングガイドを検索
    troubleshooting = await mcp_client.call_tool(
        "search_documentation",
        {"query": "troubleshooting common issues", "limit": 3}
    )
    
    return {
        "error_search": error_search,
        "api_references": api_refs,
        "troubleshooting_guides": troubleshooting
    }
```

## 関連リソース

- [Phaser 公式サイト](https://phaser.io/)
- [Phaser 公式ドキュメント](https://docs.phaser.io/)
- [Phaser API リファレンス](https://docs.phaser.io/api/)
- [Phaser GitHub リポジトリ](https://github.com/photonstorm/phaser)
- [Phaser 例集](https://phaser.io/examples)
