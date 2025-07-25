# テストスキップロジック実装

## 概要

タスク9「テストのスキップロジックを実装する」では、必要な依存関係（特に`psutil`モジュール）が利用できない場合にテストを適切にスキップするロジックを実装しました。

## 実装内容

### 1. `get_memory_usage()` 関数の改善

`phaser_mcp_server/utils.py`の`get_memory_usage()`関数は既に適切な例外処理を実装しており、`psutil`が利用できない場合は`None`を返します。

```python
def get_memory_usage() -> Optional[float]:
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB単位に変換
    except (ImportError, AttributeError):
        # psutilモジュールが利用できない場合や、
        # 予期しない属性エラーが発生した場合はNoneを返す
        return None
```

### 2. `setup_test_environment` フィクスチャの更新

`tests/test_performance_fixtures.py`と`tests/utils.py`の両方で、`setup_test_environment`フィクスチャを更新し、`psutil`が利用できない場合の処理を明確にしました。

```python
@pytest.fixture
def setup_test_environment() -> Dict[str, Optional[float]]:
    """テスト環境をセットアップし、テスト前後の状態を管理する。

    psutilモジュールが利用できない場合、メモリ使用量はNoneとして記録されます。
    この場合、メモリ使用量に依存するテストは適切にスキップされる必要があります。
    """
    # ガベージコレクションを強制実行して初期状態をクリーンにする
    gc.collect()

    # テスト前の状態を記録
    # psutilが利用できない場合、get_memory_usage()はNoneを返す
    initial_state = {"memory": get_memory_usage()}

    yield initial_state

    # テスト後のクリーンアップ
    gc.collect()
```

### 3. メモリ使用量テストのスキップロジック

`tests/test_memory_usage.py`では、既に適切なスキップロジックが実装されていました：

```python
# psutilモジュールが利用できない場合はテストをスキップ
if initial_memory is None:
    pytest.skip(
        "メモリ使用量テストをスキップします: psutilモジュールが利用できません"
    )
```

### 4. ページネーションテストの改善

`tests/test_pagination_performance.py`では、`psutil`が利用できない場合でも処理時間のテストは継続し、メモリ関連の測定のみをスキップするように改善しました：

```python
# psutilモジュールが利用できない場合の警告メッセージ
if initial_memory is None:
    print("警告: psutilモジュールが利用できないため、メモリ使用量の測定はスキップされます")

# 処理前のメモリ使用量を記録（psutilが利用可能な場合のみ）
before_memory = get_memory_usage() if initial_memory is not None else None

# メモリ使用量の検証（psutilが利用可能な場合）
if memory_usage_per_page and initial_memory is not None:
    # メモリ検証ロジック
elif initial_memory is None:
    print("情報: psutilモジュールが利用できないため、メモリ使用量の検証をスキップしました")
```

## スキップロジックの種類

### 1. 完全スキップ

メモリ使用量が必須のテストでは、`psutil`が利用できない場合にテスト全体をスキップします：

```python
if initial_memory is None:
    pytest.skip("psutilモジュールが利用できないため、メモリテストをスキップします")
```

### 2. 部分スキップ

処理時間とメモリ使用量の両方をテストする場合、メモリ部分のみをスキップし、処理時間のテストは継続します：

```python
if initial_memory is None:
    print("警告: psutilモジュールが利用できないため、メモリ使用量の測定はスキップされます")
# 処理時間のテストは継続
```

### 3. 実行時スキップ

テスト実行中に`psutil`が利用できなくなった場合のスキップ：

```python
final_memory = get_memory_usage()
if final_memory is None:
    pytest.skip("テスト実行中にpsutilモジュールが利用できなくなりました")
```

## テスト結果

実装したスキップロジックは以下のテストで検証されています：

1. `tests/test_utils.py::TestMemoryUsage::test_get_memory_usage_without_psutil` - `psutil`が利用できない場合の動作をテスト
2. `tests/test_memory_usage.py::TestMemoryUsage::test_memory_usage_performance` - メモリテストのスキップロジックをテスト
3. `tests/test_pagination_performance.py::TestPaginationPerformance::test_pagination_performance` - 部分スキップロジックをテスト

すべてのテストが正常に動作し、適切なスキップメッセージが表示されることを確認しました。

## 要件への対応

- ✅ **必要な依存関係が利用できない場合にテストをスキップするロジックを追加する**
- ✅ **スキップ理由を明確に表示するようにする**
- ✅ **要件2.2への対応**: `psutil`が利用できない場合のテストスキップ

## 使用方法

テストを実行する際、`psutil`が利用できない環境では自動的に適切なスキップメッセージが表示されます：

```bash
# 通常の実行（psutil利用可能）
python -m pytest tests/test_memory_usage.py -v

# psutilが利用できない場合は自動的にスキップされる
```

スキップされたテストは pytest の出力で `SKIPPED` として表示され、スキップ理由も明確に示されます。
