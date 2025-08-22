# テストコード作成ガイド

## 概要

本ドキュメントでは、**ckanext-feedback**のテストコード作成における基本的な手順と方法について説明します。特に、`conftest.py`で定義されたフィクスチャの使用方法と、データベーステストの実行方法に焦点を当てています。  
テストコードを実行するには、[README テスト](../../README.md#テスト)を参照してください。

## 目次

1. [テスト環境の準備](#テスト環境の準備)
2. [フィクスチャの使用方法](#フィクスチャの使用方法)
3. [データベーステストの実行](#データベーステストの実行)
4. [テストコードの記述パターン](#テストコードの記述パターン)
5. [よくある使用例](#よくある使用例)

## テスト環境の準備

### 必要な依存関係

テストを実行するには、以下の依存関係が必要です：

- pytest
- pytest-freezegun（時間固定テスト用）
- CKANのテストヘルパー

### テストディレクトリ構造

```
ckanext-feedback/
├── ckanext/feedback/tests/
│   ├── conftest.py                    # 共通フィクスチャ定義
│   ├── services/
│   │   └── admin/
│   │       └── test_utilization.py    # テストファイル例
│   └── ...
```

## フィクスチャの使用方法

### 基本的なフィクスチャ

`conftest.py`では、以下のようなフィクスチャが定義されています：

- `user`: テスト用ユーザー
- `sysadmin`: システム管理者ユーザー
- `organization`: テスト用組織
- `dataset`: テスト用データセット
- `resource`: テスト用リソース
- `utilization`: テスト用利活用方法
- `resource_comment`: テスト用リソースコメント
- `download_summary`: テスト用ダウンロードサマリー

### フィクスチャの使用方法

例: テスト内で仮のresourceとutilizationを利用する場合
```python
def test_example(self, resource, utilization):
    # resourceとutilizationフィクスチャが自動的に利用可能
    assert resource['id'] == utilization.resource_id
    assert utilization.title == 'test_title'
```

### フィクスチャの依存関係

フィクスチャは自動的に依存関係が解決されます：

例: utilizationフィクスチャ
```python
@pytest.fixture(scope='function')
def utilization(user, resource):  # userとresourceに依存
    # userとresourceフィクスチャが先に実行される
    utilization = Utilization(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],  # resourceフィクスチャの値を使用
        approval_user_id=user['id'], # userフィクスチャの値を使用
        # ... その他の属性
    )
    session.add(utilization)
    session.flush()
    return utilization
```

## データベーステストの実行

### @pytest.mark.db_testデコレーター

データベースを使用するテストには、`@pytest.mark.db_test`デコレーターを付ける必要があります：

例: データベースを操作するテストにデコレーターを付与
```python
@pytest.mark.db_test
def test_database_operation(self, resource, utilization):
    # データベース操作を含むテスト
    pass
```

### データベーステストの動作メカニズム

#### 1. テスト開始時

```python
@pytest.fixture(autouse=True)
def reset_transaction(request):
    if request.node.get_closest_marker('db_test'):
        reset_db()                    # データベースをリセット
        model.repo.init_db()          # データベースを初期化
        engine = model.meta.engine
        create_utilization_tables(engine)    # 必要なテーブルを作成
        create_resource_tables(engine)
        create_download_tables(engine)
        
        yield
        
        session.rollback()            # テスト完了後にロールバック
        reset_db()                    # データベースをクリーンアップ
```

#### 2. テスト実行中

```python
@pytest.mark.db_test
def test_refresh_utilization_summary(self, resource, utilization):
    resource_ids = [resource['id']]
    
    # データベース操作を実行
    utilization_service.refresh_utilization_summary(resource_ids)
    
    # 変更をコミット（テスト内で可能）
    session.commit()
    
    # コミット後のデータを取得して検証
    utilization_summary = get_registered_utilization_summary(resource['id'])
    assert utilization_summary.utilization == 1
```

#### 3. テスト完了時

- `session.rollback()`でテスト中の変更がすべてロールバック
- `reset_db()`でデータベースがクリーンアップ
- 次のテストのための準備完了

## テストコードの記述パターン

### 基本的なテスト構造

```python
class TestUtilizationService:
    @pytest.mark.db_test
    def test_method_name(self, resource, utilization):
        # 1. テストデータの準備（フィクスチャで自動化）
        # 2. テスト対象のメソッドを実行
        # 3. 結果を検証
        # 4. 必要に応じてsession.commit()
        pass
```

### 時間固定テスト

```python
@pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
def test_time_dependent_function(self, resource, utilization):
    # 固定された時間でテストを実行
    result = time_dependent_function()
    assert result.created == datetime(2024, 1, 1, 15, 0, 0)
```

### 複数フィクスチャの組み合わせ

```python
def test_complex_scenario(self, user, resource, utilization, resource_comment):
    # 複数のフィクスチャを組み合わせて複雑なシナリオをテスト
    assert resource_comment.resource_id == resource['id']
    assert utilization.resource_id == resource['id']
    assert utilization.approval_user_id == user['id']
```

## よくある使用例

### 1. 基本的なCRUD操作のテスト

```python
@pytest.mark.db_test
def test_create_utilization(self, resource, user):
    # 新しい利活用方法を作成
    utilization_data = {
        'resource_id': resource['id'],
        'title': 'New Utilization',
        'url': 'http://example.com',
        'description': 'Test description'
    }
    
    result = utilization_service.create(utilization_data)
    session.commit()
    
    # 作成結果を検証
    assert result.title == 'New Utilization'
    assert result.resource_id == resource['id']
```

### 2. 集計処理のテスト

```python
@pytest.mark.db_test
def test_utilization_summary_calculation(self, resource, utilization):
    # 複数の利活用方法を作成
    create_multiple_utilizations(resource['id'])
    session.commit()
    
    # 集計処理を実行
    summary = utilization_service.calculate_summary(resource['id'])
    
    # 集計結果を検証
    assert summary.total_count > 0
    assert summary.approved_count >= 0
```


## 注意事項

### 1. フィクスチャのスコープ

- `scope='function'`: 各テスト関数ごとに新しいインスタンスが作成される
- テスト間でのデータの独立性が保たれる

### 2. データベースのクリーンアップ

- `@pytest.mark.db_test`を使用することで、テスト完了時に自動的にロールバックされる
- 手動でのクリーンアップは不要

### 3. テストデータの一貫性

- フィクスチャで定義されたテストデータは固定値を使用
- テストの再現性が保たれる

### 4. 並行実行

- 各テストが独立して実行されるため、並行実行が可能
- データベースの競合状態を考慮する必要がない
