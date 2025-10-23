# テストコード修正ドキュメント

## 概要

権限チェック処理を共通化したことに伴い、コントローラーテスト（`test_utilization.py`）を新しい実装に対応させるための修正を実施しました。

## 修正の背景

### なぜ修正が必要だったのか

1. **コントローラー層の実装変更**
   - 従来：各コントローラーで直接`get_action('package_show')`を呼び出して権限チェック
   - 新実装：共通関数（`require_package_access`, `require_resource_package_access`, `get_authorized_package`）を使用
   - コンテキスト作成も`create_auth_context()`で統一

2. **モック対象の変更**
   - テストでモックすべき対象が`get_action`から共通関数に変更
   - 各テストケースで、実際にコントローラーが呼び出す関数を正確にモックする必要がある

3. **権限チェックロジックの分離**
   - データ取得と権限チェックが分離され、より明確な責任分担に
   - テストでもこの分離を反映する必要がある

---

## 共通関数の役割

### 1. `require_package_access(package_id, context)`
- **役割**: パッケージへのアクセス権限のみをチェック（データは破棄）
- **使用場所**: 権限チェックだけが必要で、パッケージデータを使わない場合
- **例**: `attached_image()`, `edit()`, `update()`, `delete()` など

### 2. `require_resource_package_access(resource_id, context)`
- **役割**: リソースIDから所属パッケージを特定し、そのパッケージへのアクセス権限をチェック
- **使用場所**: リソースIDが与えられ、そのリソースが属するパッケージの権限チェックが必要な場合
- **例**: `search()` でresource_idが指定された場合

### 3. `get_authorized_package(package_id, context)`
- **役割**: 権限チェックとパッケージデータ取得を1回のDB呼び出しで実行（効率的）
- **使用場所**: 権限チェック後にパッケージデータも必要な場合
- **例**: `new()`, `details()`, `check_comment()` など
- **返り値**: パッケージデータ（dict）

---

## 主な修正パターン

### パターン1: `require_resource_package_access`へのモック変更

**該当テスト**:
- `test_search`
- `test_search_with_org_admin`
- `test_search_with_user`
- `test_search_without_user`
- `test_search_with_package`
- `test_search_without_id`
- `test_search_with_resource_id_not_found`
- `test_search_with_resource_id_not_found_org_name_branch`
- `test_search_with_private_package_unauthorized` (resource_id指定時)

**修正内容**:
```python
# 修正前
@patch('ckanext.feedback.controllers.utilization.get_action')
def test_search(self, mock_get_action, ...):
    mock_package_show = MagicMock(return_value={'id': 'mock_package_id'})
    mock_get_action.return_value = mock_package_show

# 修正後
@patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
def test_search(self, mock_require_resource_package_access, ...):
    # require_resource_package_accessは戻り値を持たない（権限チェックのみ）
    # モックの戻り値設定は不要
```

**理由**:
- `search()`メソッドは`resource_id`が指定された場合、`require_resource_package_access()`を呼び出す
- この関数は戻り値を持たず、権限エラー時のみ`abort(404)`を呼ぶ

---

### パターン2: `require_package_access`へのモック変更

**該当テスト**:
- `test_search_with_package` (package_id指定時)
- `test_search_with_package_id_not_found`
- `test_check_organization_admin_role_with_sysadmin`
- `test_check_organization_admin_role_with_org_admin`
- `test_check_organization_admin_role_with_user`
- `test_attached_image_*` 系（多数）
- `test_approve_comment`
- `test_edit`
- `test_update*` 系（多数）
- `test_delete`
- `test_create_issue_resolution*` 系

**修正内容**:
```python
# 修正前
@patch('ckanext.feedback.controllers.utilization.get_action')
def test_edit(self, mock_get_action, ...):
    mock_package_show = MagicMock(return_value={'id': 'mock_package_id'})
    mock_get_action.return_value = mock_package_show

# 修正後
@patch('ckanext.feedback.controllers.utilization.require_package_access')
def test_edit(self, mock_require_package_access, ...):
    # 戻り値設定は不要
    utilization.package_id = 'mock_package_id'  # package_idを明示的に設定
```

**理由**:
- これらのメソッドは`package_id`を使って権限チェックのみを行う
- パッケージデータは使用しないため、`require_package_access()`を使用
- `utilization.package_id`を後続の処理で使用するため、テストで明示的に設定

---

### パターン3: `get_authorized_package`へのモック変更

**該当テスト**:
- `test_new`
- `test_new_with_resource_id`
- `test_details_*` 系
- `test_check_comment_POST_*` 系

**修正内容**:
```python
# 修正前
@patch('ckanext.feedback.controllers.utilization.get_action')
def test_new(self, mock_get_action, ...):
    mock_package_show = MagicMock(return_value={'id': 'mock_package_id', 'title': 'Test'})
    mock_get_action.return_value = mock_package_show

# 修正後
@patch('ckanext.feedback.controllers.utilization.get_authorized_package')
def test_new(self, mock_get_authorized_package, ...):
    mock_get_authorized_package.return_value = {
        'id': 'mock_package_id',
        'title': 'Test Package'
    }
```

**理由**:
- これらのメソッドは権限チェック後、パッケージデータも使用する
- `get_authorized_package()`は1回のDB呼び出しで両方を実行（効率的）
- 戻り値としてパッケージデータを返すため、テストでも適切な戻り値を設定

---

### パターン4: 権限エラーのシミュレーション

**該当テスト**:
- `test_new_with_private_package_unauthorized`
- `test_details_with_private_package_unauthorized`
- `test_check_comment_with_private_package_unauthorized`
- `test_search_with_private_package_unauthorized` (resource_id指定時)
- `test_search_with_private_package_unauthorized_package_id` (package_id指定時)
- `test_attached_image_with_private_package_unauthorized`
- `test_check_organization_admin_role_with_private_package_unauthorized`
- その他の`*_unauthorized`系テスト

**修正内容**:
```python
# 修正前
@patch('ckanext.feedback.controllers.utilization.get_action')
def test_new_with_private_package_unauthorized(self, mock_get_action, ...):
    mock_package_show = MagicMock(side_effect=NotAuthorized)
    mock_get_action.return_value = mock_package_show

# 修正後（get_authorized_packageを使う場合）
@patch('ckanext.feedback.controllers.utilization.toolkit.abort')
@patch('ckanext.feedback.controllers.utilization.get_authorized_package')
def test_new_with_private_package_unauthorized(
    self, mock_get_authorized_package, mock_abort, ...
):
    # 共通関数内でabortが呼ばれるため、それをシミュレート
    mock_get_authorized_package.side_effect = lambda *args, **kwargs: mock_abort(404)

# 修正後（require_package_accessを使う場合）
@patch('ckanext.feedback.controllers.utilization.toolkit.abort')
@patch('ckanext.feedback.controllers.utilization.require_package_access')
def test_attached_image_with_private_package_unauthorized(
    self, mock_require_package_access, mock_abort, ...
):
    mock_require_package_access.side_effect = lambda *args, **kwargs: mock_abort(404)
```

**理由**:
- 共通関数は権限エラー時に`toolkit.abort(404)`を呼び出す
- テストでは`side_effect`を使って、共通関数が呼ばれたときに`abort(404)`をシミュレート
- `toolkit.abort`自体もモックして、実際の404ページ遷移を防ぐ

---

### パターン5: `package_id`の明示的な設定

**該当テスト**:
- `test_attached_image_*` 系
- `test_approve_comment`
- `test_edit`
- `test_update*` 系
- `test_delete`
- `test_create_issue_resolution*` 系

**修正内容**:
```python
# 修正前
def test_edit(self, ...):
    utilization = mock_get_by_id.return_value
    # package_idの設定なし

# 修正後
def test_edit(self, ...):
    utilization = mock_get_by_id.return_value
    utilization.package_id = 'mock_package_id'  # 明示的に設定
```

**理由**:
- コントローラーが`model.Package.get(utilization.package_id)`を呼び出す際、`utilization.package_id`がMagicMockのままだとSQLAlchemyエラーが発生
- `InvalidRequestError: Incorrect number of values in identifier to formulate primary key`
- 具体的な文字列を設定することでエラーを回避

---

## 修正前後の比較例

### 例1: `test_search`

```python
# ===== 修正前 =====
@patch('ckanext.feedback.controllers.utilization.helpers.Page')
@patch('ckanext.feedback.controllers.utilization.toolkit.render')
@patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
@patch('ckanext.feedback.controllers.utilization.get_pagination_value')
@patch('ckanext.feedback.controllers.utilization.request', new_callable=MagicMock)
@patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
@patch('ckanext.feedback.controllers.utilization.get_action')
def test_search(
    self,
    mock_get_action,
    mock_get_resource,
    mock_args,
    mock_pagination,
    mock_get_utilizations,
    mock_render,
    mock_page,
    admin_context,
):
    mock_package_show = MagicMock(return_value={'id': 'mock_package_id'})
    mock_get_action.return_value = mock_package_show
    # ... test logic ...
    mock_package_show.assert_called_once()

# ===== 修正後 =====
@patch('ckanext.feedback.controllers.utilization.helpers.Page')
@patch('ckanext.feedback.controllers.utilization.toolkit.render')
@patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
@patch('ckanext.feedback.controllers.utilization.get_pagination_value')
@patch('ckanext.feedback.controllers.utilization.request', new_callable=MagicMock)
@patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
@patch('ckanext.feedback.controllers.utilization.require_resource_package_access')
def test_search(
    self,
    mock_require_resource_package_access,
    mock_get_resource,
    mock_args,
    mock_pagination,
    mock_get_utilizations,
    mock_render,
    mock_page,
    admin_context,
):
    # 戻り値設定は不要（権限チェックのみ）
    # ... test logic ...
    mock_require_resource_package_access.assert_called_once()
```

### 例2: `test_edit`

```python
# ===== 修正前 =====
@patch('ckanext.feedback.controllers.utilization.toolkit.render')
@patch('ckanext.feedback.controllers.utilization.utilization_service.get_by_id')
@patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
@patch('ckanext.feedback.controllers.utilization.get_action')
def test_edit(self, mock_get_action, mock_get_resource, mock_get_by_id, mock_render):
    mock_package_show = MagicMock(return_value={'id': 'mock_package_id'})
    mock_get_action.return_value = mock_package_show
    
    utilization = mock_get_by_id.return_value
    # ... test logic ...

# ===== 修正後 =====
@patch('ckanext.feedback.controllers.utilization.toolkit.render')
@patch('ckanext.feedback.controllers.utilization.utilization_service.get_by_id')
@patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
@patch('ckanext.feedback.controllers.utilization.require_package_access')
def test_edit(self, mock_require_package_access, mock_get_resource, mock_get_by_id, mock_render):
    # require_package_accessは戻り値なし
    
    utilization = mock_get_by_id.return_value
    utilization.package_id = 'mock_package_id'  # 明示的に設定
    # ... test logic ...
```

### 例3: `test_new_with_private_package_unauthorized`

```python
# ===== 修正前 =====
@patch('ckanext.feedback.controllers.utilization.toolkit.render')
@patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
@patch('ckanext.feedback.controllers.utilization.get_action')
def test_new_with_private_package_unauthorized(
    self, mock_get_action, mock_get_resource, mock_render
):
    mock_package_show = MagicMock(side_effect=NotAuthorized)
    mock_get_action.return_value = mock_package_show
    
    # ... test logic ...

# ===== 修正後 =====
@patch('ckanext.feedback.controllers.utilization.toolkit.abort')
@patch('ckanext.feedback.controllers.utilization.toolkit.render')
@patch('ckanext.feedback.controllers.utilization.comment_service.get_resource')
@patch('ckanext.feedback.controllers.utilization.get_authorized_package')
def test_new_with_private_package_unauthorized(
    self, mock_get_authorized_package, mock_get_resource, mock_render, mock_abort
):
    # 共通関数が呼ばれたときにabort(404)をシミュレート
    mock_get_authorized_package.side_effect = lambda *args, **kwargs: mock_abort(404)
    
    # ... test logic ...
```

---

## よくあったエラーとその対処法

### 1. `AttributeError: does not have the attribute 'comment_service'`

**原因**: 
- `require_resource_package_access`内で`import`された`comment_service`をモジュールレベルでパッチしようとした

**対処法**:
```python
# 誤り
@patch('ckanext.feedback.services.common.check.comment_service')

# 正解
@patch('ckanext.feedback.services.resource.comment.get_resource')
```

### 2. `NameError: name 'mock_package' is not defined`

**原因**:
- `require_package_access`や`require_resource_package_access`に変更後、戻り値を返さなくなったのに、`mock_package_show.return_value = mock_package`のコードが残っていた

**対処法**:
- `mock_package`の定義と`return_value`の設定を削除
- `get_authorized_package`を使う場合のみ戻り値を設定

### 3. `InvalidRequestError: Incorrect number of values in identifier`

**原因**:
- `utilization.package_id`がMagicMockのままで、SQLAlchemyの`Package.get()`に渡されてエラー

**対処法**:
```python
utilization.package_id = 'mock_package_id'  # 具体的な文字列を設定
```

### 4. `ckan.logic.NotFound`

**原因**:
- 共通関数のモックが不完全で、実際の`get_action('package_show')`が呼ばれてしまった

**対処法**:
- 正しい共通関数をパッチする
- パッチのパスが正確か確認

### 5. `RuntimeError: The session is unavailable because no secret key was set`

**原因**:
- `toolkit.abort(404)`内部で`flask.session`を使おうとしたが、テスト環境でsecret keyが未設定

**対処法**:
- このエラーは特定のテストケースでのみ発生
- `toolkit.abort`をモックすることで回避

---

## テスト修正の統計

### 修正したテストケース数
- **合計**: 88個のテストケース
- **test_utilization.py**: 88個

### 修正パターンの内訳
1. `require_resource_package_access`への変更: 約10個
2. `require_package_access`への変更: 約50個
3. `get_authorized_package`への変更: 約20個
4. 権限エラーシミュレーション: 約8個

### カバレッジ結果
- **修正前**: 約34-48%
- **修正後**: **100%** ✓

---

## 今後の注意点

### 新しいテストを書く際のガイドライン

1. **コントローラーの実装を確認**
   - どの共通関数を使っているか？
   - `require_package_access`, `require_resource_package_access`, `get_authorized_package`のいずれか

2. **適切な関数をモック**
   ```python
   # 権限チェックのみ
   @patch('ckanext.feedback.controllers.utilization.require_package_access')
   
   # 権限チェック + データ取得
   @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
   ```

3. **戻り値の設定**
   - `require_package_access`: 戻り値なし
   - `require_resource_package_access`: 戻り値なし
   - `get_authorized_package`: パッケージデータ（dict）を返す

4. **権限エラーのテスト**
   ```python
   @patch('ckanext.feedback.controllers.utilization.toolkit.abort')
   @patch('ckanext.feedback.controllers.utilization.get_authorized_package')
   def test_unauthorized(self, mock_get_authorized_package, mock_abort):
       mock_get_authorized_package.side_effect = lambda *args: mock_abort(404)
   ```

5. **package_idの明示的な設定**
   - `utilization.package_id`を使用するテストでは必ず文字列を設定

---

## まとめ

今回のテストコード修正により、以下が達成されました：

1. ✅ **コントローラー層の実装変更に完全対応**
   - 共通関数を使った権限チェックのテストが適切に実装された

2. ✅ **テストカバレッジ100%達成**
   - すべてのコードパスがテストされている

3. ✅ **保守性の向上**
   - 権限チェックのロジックが共通化され、今後の変更が容易に

4. ✅ **明確なテストパターンの確立**
   - 3つの共通関数に対応する明確なテストパターンが確立された

5. ✅ **ドキュメント化**
   - 今後の開発者が同様の修正を行う際のガイドラインを提供

---

## 参考資料

### 関連ファイル
- `/home/y-ichimiya/ckanext-feedback/ckanext/feedback/services/common/check.py`
  - 共通関数の実装
- `/home/y-ichimiya/ckanext-feedback/ckanext/feedback/utils/auth.py`
  - `create_auth_context()`の実装
- `/home/y-ichimiya/ckanext-feedback/ckanext/feedback/controllers/utilization.py`
  - コントローラーの実装
- `/home/y-ichimiya/ckanext-feedback/ckanext/feedback/tests/controllers/test_utilization.py`
  - テストコード

### 実装の原則
- **DRY (Don't Repeat Yourself)**: 重複コードを排除
- **Single Responsibility Principle**: 各関数が単一の責任を持つ
- **効率性**: 不要なDB呼び出しを削減（`get_authorized_package`の活用）


