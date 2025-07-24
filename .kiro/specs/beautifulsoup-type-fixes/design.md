# 設計ドキュメント

## 概要

このドキュメントでは、Phaser MCP Serverプロジェクトにおける、BeautifulSoupとmarkdownifyライブラリの型チェック問題を解決するための設計を詳述します。主な目標は、コードの機能を変更せずに、Pyrightの型チェックエラーを解消することです。

## アーキテクチャ

現在のコードアーキテクチャを維持しながら、型アノテーションを追加または修正します。主に以下のコンポーネントに対して型の修正を行います：

1. **parser.py** - BeautifulSoupとmarkdownifyを使用してHTMLを解析しMarkdownに変換するモジュール
2. **型スタブファイル** - 必要に応じて、サードパーティライブラリの型定義を提供するファイル

## 型チェック問題の分析

Pyrightの出力から、以下の主要な問題が特定されました：

1. **BeautifulSoup関連の型問題**:
   - `Tag`と`BeautifulSoup`型の互換性の問題
   - `PageElement`、`Tag`、`NavigableString`の型階層の問題
   - BeautifulSoupオブジェクトのメソッドとプロパティへのアクセスに関する型の問題

2. **markdownify関連の型問題**:
   - `md`関数の型が部分的に不明
   - 戻り値の型が不明確

3. **リスト操作の型問題**:
   - 文字列に対する`append`メソッドの使用
   - リストの型が部分的に不明

4. **その他の型問題**:
   - 正規表現マッチオブジェクトの型が不明
   - 不必要な`isinstance`チェックの警告

## 解決策

### 1. 型スタブの作成と使用

BeautifulSoupとmarkdownifyの型スタブが公式に提供されていないため、プロジェクト内でカスタム型スタブを作成します。

```
phaser_mcp_server/
└── stubs/
    ├── bs4.pyi         # BeautifulSoup型定義
    └── markdownify.pyi # markdownify型定義
```

### 2. 型アノテーションの改善

parser.pyファイル内の型アノテーションを改善し、以下の点に対応します：

1. **適切な型インポート**:

   ```python
   from typing import Any, Dict, List, Optional, Pattern, Union, cast, TypeVar, Iterable, Match
   from bs4 import BeautifulSoup, Tag, NavigableString, PageElement, ResultSet
   ```

2. **型変数の定義**:

   ```python
   T = TypeVar('T')
   TagOrElement = Union[Tag, PageElement, NavigableString]
   ```

3. **キャスト演算子の使用**:

   ```python
   soup_content = cast(Tag, main_content)
   ```

4. **ジェネリック型の使用**:

   ```python
   code_blocks: List[Dict[str, Any]] = []
   ```

### 3. 正規表現マッチオブジェクトの型付け

正規表現のマッチオブジェクトに適切な型アノテーションを追加します：

```python
def _fix_links(self, match: Match[str]) -> str:
    text = match.group(1)
    url = match.group(2).strip()
    url = url.replace("&amp;", "&")
    return f"[{text}]({url})"
```

### 4. リスト操作の型修正

リスト操作に関する型の問題を修正します：

```python
# 修正前
phaser_content["game_objects"].append(block)

# 修正後
if isinstance(phaser_content["game_objects"], list):
    phaser_content["game_objects"].append(block)
```

### 5. 不必要なisinstanceチェックの修正

型チェッカーが警告する不必要なisinstanceチェックを修正します：

```python
# 修正前
if isinstance(content_input, str):
    # ...

# 修正後
if isinstance(content_input, str):  # type: ignore
    # ...
```

## データモデル

既存のデータモデルは変更せず、型アノテーションのみを追加または修正します。

## エラーハンドリング

エラーハンドリングのロジックは変更せず、型アノテーションのみを追加または修正します。

## テスト戦略

1. **単体テスト**:
   - 型修正後も既存のテストが全て通ることを確認
   - 型アノテーションの変更がランタイム動作に影響を与えないことを確認

2. **型チェックテスト**:
   - Pyrightを使用して型チェックエラーが解消されたことを確認
   - 新たな型エラーが発生していないことを確認

## 実装計画

1. カスタム型スタブファイルの作成
2. parser.pyの型アノテーション修正
3. 型チェックエラーの検証と修正
4. テストの実行と確認

## 技術的な決定事項

1. **カスタム型スタブの使用**: 公式の型スタブが利用できないため、プロジェクト固有のカスタム型スタブを作成します。
2. **Union型の活用**: BeautifulSoupの複雑な型階層に対応するため、Union型を活用します。
3. **型無視コメントの限定的使用**: 必要な場合のみ`# type: ignore`コメントを使用し、過度の使用は避けます。
4. **キャスト演算子の使用**: 型チェッカーが推論できない場合に限り、キャスト演算子を使用します。

## 将来の拡張性

1. 将来的に公式の型スタブが利用可能になった場合、カスタム型スタブから移行できるようにします。
2. Python 3.14+の新しい型機能に対応できるよう、型アノテーションを最新の標準に準拠させます。
