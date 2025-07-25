# CAPTCHA/Cloudflare保護の対応手順

Phaser公式ドキュメントサイト（docs.phaser.io）はCloudflareによる保護が有効になっており、自動化されたアクセスを検出すると人間であることの確認を求める場合があります。

## 問題の症状

- `403 Forbidden` エラーが発生する
- `Access forbidden` メッセージが表示される
- ブラウザでアクセスすると「人間であることを確認」画面が表示される

## 基本的な対応手順

### 1. ブラウザでの事前認証

最も簡単で推奨される方法です：

1. **ブラウザでPhaserドキュメントにアクセス**

   ```
   https://docs.phaser.io/
   ```

2. **CAPTCHA認証を完了**
   - 「人間であることを確認」画面が表示された場合は、指示に従って認証を完了
   - チェックボックスをクリックしたり、画像選択を行う
   - 認証完了後、ページが正常に表示されることを確認

3. **同じネットワーク環境でMCPサーバーを実行**
   - 認証後、同じIPアドレス・ネットワーク環境からMCPサーバーを実行
   - 通常、認証は数時間から24時間程度有効

### 2. 待機時間の調整

頻繁なアクセスを避けるため、リクエスト間隔を調整：

```bash
# タイムアウト時間を長めに設定
PHASER_DOCS_TIMEOUT=60 phaser-mcp-server

# リトライ回数を減らす
PHASER_DOCS_MAX_RETRIES=1 phaser-mcp-server
```

## 高度な対応手順（開発者向け）

### セッションCookieの手動設定

**注意**: この方法は技術的な知識が必要で、Cookieの有効期限があります。

1. **ブラウザでCookieを取得**
   - ブラウザで<https://docs.phaser.io/にアクセス>
   - F12キーで開発者ツールを開く
   - `Application`タブ → `Cookies` → `https://docs.phaser.io`を選択
   - 以下のCookieをメモ：
     - `cf_clearance` (Cloudflare認証トークン)
     - `__cfduid` (Cloudflare UID)
     - その他のセッション関連Cookie

2. **プログラムでCookieを設定**

   ```python
   from phaser_mcp_server.client import PhaserDocsClient
   
   client = PhaserDocsClient()
   
   # 取得したCookieを設定
   client.set_session_cookies({
       "cf_clearance": "your_clearance_token_here",
       "__cfduid": "your_cfduid_here"
   })
   
   await client.initialize()
   ```

3. **Cookie有効期限の管理**
   - Cloudflare Cookieは通常24時間程度で期限切れ
   - 定期的にブラウザで再認証が必要
   - 自動化する場合は適切な間隔でCookieを更新

## トラブルシューティング

### よくあるエラーと対処法

#### `403 Forbidden`が継続する場合

1. **IPアドレスの確認**

   ```bash
   # 現在のIPアドレスを確認
   curl ifconfig.me
   ```

2. **ブラウザとサーバーが同じネットワークか確認**
   - VPNやプロキシの設定を確認
   - 同じWiFi/有線接続を使用

3. **User-Agentの確認**
   - 現在のUser-Agentが適切に設定されているか確認
   - 必要に応じてより新しいブラウザのUser-Agentに更新

#### Cookie設定が効かない場合

1. **Cookieの形式確認**

   ```python
   # 現在のCookieを確認
   cookies = client.get_session_cookies()
   print(cookies)
   ```

2. **ドメイン設定の確認**
   - Cookieが正しいドメイン（docs.phaser.io）に設定されているか確認

3. **Cookie有効期限の確認**
   - ブラウザの開発者ツールでCookieの有効期限を確認
   - 期限切れの場合は再認証が必要

### デバッグ方法

1. **詳細ログの有効化**

   ```bash
   FASTMCP_LOG_LEVEL=DEBUG phaser-mcp-server
   ```

2. **ヘルスチェックの実行**

   ```bash
   phaser-mcp-server --health-check
   ```

3. **手動テスト**

   ```python
   import asyncio
   from phaser_mcp_server.client import PhaserDocsClient
   
   async def test():
       client = PhaserDocsClient()
       try:
           await client.initialize()
           page = await client.get_page_content('https://docs.phaser.io/')
           print("Success!")
       except Exception as e:
           print(f"Error: {e}")
       finally:
           await client.close()
   
   asyncio.run(test())
   ```

## 予防策

### 1. アクセス頻度の制限

```python
import asyncio

# リクエスト間に適切な間隔を設ける
await asyncio.sleep(2)  # 2秒待機
```

### 2. 適切なUser-Agentの使用

現在のクライアントは以下のUser-Agentを使用：

```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

### 3. セッション管理

- 長時間の使用時は定期的にセッションを更新
- Cookie有効期限の監視
- 必要に応じて再認証の実行

## 注意事項

1. **利用規約の遵守**
   - Phaserドキュメントサイトの利用規約を遵守
   - 過度なアクセスは避ける

2. **セキュリティ**
   - Cookieは機密情報として扱う
   - 共有や公開は避ける

3. **自動化の制限**
   - 完全な自動化は困難
   - 人間による定期的な介入が必要

4. **法的考慮事項**
   - ウェブスクレイピングの法的制限を理解
   - 適切な使用頻度を維持

## 将来の改善予定

- 自動Cookie更新機能
- より高度なセッション管理
- プロキシローテーション対応
- レート制限の自動調整

この対応により、Phaser MCPサーバーをより安定して使用できるようになります。
