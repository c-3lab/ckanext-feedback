# models更新とDBへの反映

`ckanext-feedback/ckanext/feedback/tests/models` 以下の各モデルについて修正を行った場合、DBの実体にも反映する必要があります。  
[CKAN公式のベストプラクティス](https://docs.ckan.org/en/latest/extensions/best-practices.html)に従ったDBアップデート方法を説明します。

## マイグレーションスクリプトの作成

ckanext-feedbackがインストールされたコンテナ内で `ckan generate migration -p feedback` を実行すると、マイグレーションスクリプトのひな形が`/usr/lib/python3.10/site-packages/ckanext/feedback/migration/feedback/versions/`に作成されます。  
作成されたスクリプトファイルには適切なリビジョンIDが設定されているため、通常はこの作成されたファイルを編集して使用することが推奨されます。  

### ひな形の例

```python
"""

Revision ID: 40bf9a900ef5
Revises:
Create Date: 2024-05-30 04:24:42.871134

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '40bf9a900ef5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
```

### マイグレーションスクリプトの保存
編集したファイルを恒久的に保存するためには、`/srv/app/src_extensions/ckanext-feedback/ckanext/feedback/migration/feedback/versions/`にコピーしてください。このディレクトリに保存することで、ckanext-feedbackの再インストール時にコピー元のディレクトリへ適切に配置されます。

## マイグレーションスクリプトの編集

通常、編集する箇所は`upgrade()`および`downgrade()`の処理内容です。  
SQLAlchemyを使用したカラムの追加や削除などの一般的なスキーマ変更が可能です。  
詳しい内容は[Alembicチュートリアル](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-second-migration)を参照してください。

## マイグレーションの実行

マイグレーションスクリプトの適用を行う場合は `ckan db upgrade -p feedback` を実行してください。

マイグレーションスクリプトの適用による変更を元に戻す場合は `ckan db downgrade -p feedback` を実行してください。

特定のリビジョンIDまで`upgrade`または`downgrade`を行う場合、コマンドに`-v <リビジョンID>`を追加してください。  
例）`ckan db downgrade -p feedback -v 40bf9a900ef5`

## マイグレーション適用状況の確認

`/usr/lib/python3.10/site-packages/ckanext/feedback/migration/feedback`に移動して、以下のコマンドを適宜実行してください。

### 現在のリビジョンIDの確認

- `alembic current`

### 過去の適用履歴の確認

- `alembic history`

## トラブルシューティング

何らかの理由でリビジョンの進行状況とDB本体の同期にズレが生じた場合、`alembic stamp`によってリビジョンの設定を手動で変更することができます。  
これは、カラムを追加するマイグレーションスクリプトを新たに作成したが既にDBにカラムが存在する場合や、何らかの理由でDBがロールバックした場合などに有効です。

[コマンドの説明](https://inspirehep.readthedocs.io/en/latest/alembic.html#alembic-stamp)をよく読み、慎重に作業してください。

### 例）リビジョンをinitに戻す場合

```bash
cd /usr/lib/python3.10/site-packages/ckanext/feedback/migration/feedback
alembic stamp 40bf9a900ef5
ckan db upgrade -p feedback
```

※`40bf9a900ef5`は初期リビジョンである`ckanext-feedback/ckanext/feedback/migration/feedback/versions/000_40bf9a900ef5_init.py`のID。
