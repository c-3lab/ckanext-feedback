# モデル更新とDBマイグレーション

## 概要

本ドキュメントは、`ckanext-feedback` のモデル変更を Alembic でDBに反映する手順です。
[CKAN公式のベストプラクティス](https://docs.ckan.org/en/latest/extensions/best-practices.html)に準拠します。

---

## マイグレーションの基本

Alembic は「リビジョンファイル（マイグレーションファイル）」でDB変更の履歴を管理します。各リビジョンは次を持ちます。
#### **変更しない個所**
- **`revision`: リビジョンの一意ID(自動生成)**
- **`down_revision`: 親リビジョンID(自動生成、docstring の「Revises」と一致させる)**
#### 変更を加える個所
- `upgrade()`: リビジョン適用時に進める操作（例: カラム追加、インデックス作成）
- `downgrade()`: ロールバック時に戻す操作（例: カラム削除、インデックス削除）
---
## 前提

* 以下のDocker環境で CKAN 本体と本Extensionを実行することを想定しています。
  * OS: Linux
  * ディストリビューション: Ubuntu 22.04
  * Python 3.10.13
  * Docker 27.4.0

  **`REPO_ROOT` などは開発環境によって置き換えてください。**
---

### マイグレーションスクリプトの作成
```bash
cd "$REPO_ROOT/ckanext/feedback/migration/feedback"
alembic revision 
```
- また、作成するマイグレーションスクリプトにメッセージを付ける場合は、`-m "message"`を追加します。
```bash 
alembic revision -m "message"
```
- マイグレーションに関するファイルはリポジトリの `$REPO_ROOT/ckanext/feedback/migration/feedback`以下に配置されます。
- 生成物: `versions/<revision_id>_<message>.py`
  - `down_revision` が正しい親リビジョンを指すか、docstring の「Revises」と一致しているか確認。

### テンプレート例:
```python
"""empty message

Revision ID: abcdef123456
Revises: 123456abcdef
Create Date: 2025-01-01 00:00:00.00000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abcdef123456'
down_revision = '123456abcdef'
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
```
### `-m "Sample Message"`でメッセージをつけた場合のテンプレート例:
```python
"""Sample Message

Revision ID: abcdef123456
Revises: 123456abcdef
Create Date: 2025-01-01 00:00:00.00000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abcdef123456'
down_revision = '123456abcdef'
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
```
---

## マイグレーションスクリプトの編集
- **通常、編集する箇所は`upgrade()`および`downgrade()`の処理内容です。**  
- 生成されたファイル名を編集して任意のプレフィックスを追加する事が可能です。
- SQLAlchemyを使用したカラムの追加や削除などの一般的なスキーマ変更が可能です。
- 詳しい内容は[Alembicチュートリアル](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-second-migration)を参照してください。

### 新規テーブル作成/削除例
```python
def upgrade():
    op.create_table(
        'example_table',
        sa.Column('id', sa.Text, primary_key=True, nullable=False),
        sa.Column('created', sa.TIMESTAMP, nullable=True),
    )

def downgrade():
    op.drop_table('example_table')
```

### カラム追加例
```python
def upgrade():
    op.add_column('utilizations', sa.Column('summary', sa.Text(), nullable=True))
    op.execute("UPDATE utilizations SET summary = '' WHERE summary IS NULL")
    op.alter_column('utilizations', 'summary', nullable=False)

def downgrade():
    op.drop_column('utilizations', 'summary')
```

### Enum 変更例
```python
def downgrade():
    op.execute('DROP TYPE IF EXISTS your_enum_type;')
```

---

## マイグレーションの実行

### アップグレード
```bash
# 最新へ
ckan db upgrade --plugin feedback
```
### ダウングレード
```bash
# feedbackプラグイン適用前までダウングレード
ckan db downgrade --plugin feedback
# 指定リビジョンへ
ckan db downgrade --plugin feedback -v <revision_id>
```

---

## マイグレーション適用状況の確認

### 現在のリビジョンIDの確認
```bash
ckan db version --plugin feedback
```

### 未適用が存在するかを確認
```bash
ckan db pending-migrations
```

## Alembicコマンドを直接実行したい場合
```bash
cd "$REPO_ROOT/ckanext/feedback/migration/feedback"
# 現在のリビジョンIDの確認
alembic current
# 過去の適用履歴の確認
alembic history
```
---

## トラブルシューティング

### 実DBと Alembic の履歴がずれた場合
 何らかの理由でリビジョンの進行状況とDB本体の同期にズレが生じた場合、`alembic stamp`によってリビジョンの設定を手動で変更することができます。  
 これは、カラムを追加するマイグレーションスクリプトを新たに作成したが既にDBにカラムが存在する場合や、何らかの理由でDBがロールバックした場合などに有効です。
 [コマンドの説明](https://inspirehep.readthedocs.io/en/latest/alembic.html#alembic-stamp)をよく読み、慎重に作業してください。
#### 実データは変更せず、履歴だけ合わせる
```bash
# 最新バージョンに変更
alembic stamp head
```
```bash
# 指定バージョンに変更
alembic stamp <revision_id>
```
