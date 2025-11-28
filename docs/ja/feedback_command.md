# ckanext-feedback コマンド一覧

運用・保守を目的とした専用の CLI コマンドを提供しています。  
フィードバック機能に関するデータの 初期化・整備・クリーンアップ を柔軟に行うことができます。  

> [!IMPORTANT]
> `ckan`コマンドは、`ckan.ini`がある場所で実行するか、`-c`で`ckan.ini`の指定が必要です。


## 目次

- [init](#init)
  - [実行](#実行)
  - [オプション](#オプション)
  - [実行例](#実行例)
- [clean-files](#clean-files)
  - [実行](#実行)
  - [オプション](#オプション)
  - [実行例](#実行例)
  - [補足：削除対象の判定基準](#補足削除対象の判定基準)
- [reset-solr-fields](#reset-solr-fields)
  - [概要](#概要)
  - [実行](#実行)
  - [オプション](#オプション)
  - [実行例](#実行例)
  - [注意事項](#注意事項)

## init

指定した機能に関係する PostgreSQLのテーブルを初期化 します。  
初期化の対象はオプションで制御でき、指定がない場合は すべてのテーブル が対象となります。

### 実行

```bash
ckan ckan.ini feedback init [options]
```

### オプション

```bash
-m, --modules < utilization resource download >
```

対象機能を限定して初期化処理を実行（任意）

指定なし： すべてのテーブルに対して初期化処理を実行  
モジュール指定：以下のモジュール名を複数指定可能
- utilization
- resource
- download

```bash
-h, --host <host_name>
```

PostgreSQLホスト名の指定（任意）

優先順位：  
１．コマンドライン引数  
２．環境変数 POSTGRES_HOST  
３．CKANのデフォルト：db

```bash
-p, --port <port>
```

PostgreSQLポート番号の指定（任意）

優先順位：  
１．コマンドライン引数  
２．環境変数 POSTGRES_PORT  
３．CKANのデフォルト：5432

```bash
-d, --dbname <db_name>
```

PostgreSQLデータベース名の指定（任意）

優先順位：  
１．コマンドライン引数  
２．環境変数 POSTGRES_DB  
３．CKANのデフォルト：ckan

```bash
-u, --user <user_name>
```

PostgreSQL接続ユーザ名の指定（任意）

優先順位：  
１．コマンドライン引数  
２．環境変数 POSTGRES_USER  
３．CKANのデフォルト：ckan

```bash
-P, --password <password>
```

PostgreSQL接続パスワードの指定（任意）

優先順位：  
１．コマンドライン引数  
２．環境変数 POSTGRES_PASSWORD  
３．CKANのデフォルト：ckan

### 実行例

```bash
# ckanext-feedback plugins に関わる全てのテーブルに対して初期化を行う
ckan ckan.ini feedback init

# utilization(利活用方法)機能に関わるテーブルに対して初期化を行う
ckan ckan.ini feedback init -m utilization

# resource(データリソース)機能に関わるテーブルに対して初期化を行う
ckan ckan.ini feedback init -m resource

# download(ダウンロード)機能に関わるテーブルに対して初期化を行う
ckan ckan.ini feedback init -m download

# resource(データリソース)機能とdownload(ダウンロード)機能に関わるテーブルに対して初期化を行う
ckan ckan.ini feedback init -m resource -m download

# ホスト名として"postgresdb"を指定する
ckan ckan.ini feedback init -h postgresdb

# ポート番号として"5000"を指定する
ckan ckan.ini feedback init -p 5000

# データベース名として"ckandb"を指定する
ckan ckan.ini feedback init -d ckandb

# ユーザ名として"root"を指定する
ckan ckan.ini feedback init -u root

# パスワードとして"root"を指定する
ckan ckan.ini feedback init -P root

# ホスト名として"postgresdb", ユーザ名として"root", パスワードとして"root"を指定する
ckan ckan.ini feedback init -h postgresdb -u root -P root
```

## clean-files

コメント投稿時にアップロードされた画像ファイルのうち、実際にはコメントに添付されなかった不要なファイルを検索・削除します。  
フィードバック投稿中に一時的にアップロードされたものの、投稿が完了せずに残ったファイルなどが対象です。

### 実行

```bash
ckan ckan.ini feedback clean-files [options]
```

### オプション

```bash
-d, --dry-run
```

削除を実行せず、削除対象となるファイルの一覧を表示します。  
実行前に影響範囲を確認したい場合に便利です。

### 実行例

```bash
# 不要ファイルを削除する
ckan ckan.ini feedback clean-files

# 実際には削除せず、削除対象となるファイルの一覧を表示する
ckan ckan.ini feedback clean-files --dry-run
```

### 補足：削除対象の判定基準

- 投稿完了したコメントに **関連付けられていないファイル**
- サーバーに一時的に保存されたまま **孤立した画像ファイル**

※ 意図せず消してしまわないよう、`--dry-run` での事前確認を推奨します。  
※ 本コマンドは、cronなどで定期的に実行することを推奨します。

## reset-solr-fields

### 概要

**カスタムソート機能**で使用されるSolrスキーマのフィールド（`downloads_total_i`と`likes_total_i`）を削除します。

このコマンドは、以下の場合に使用します：
- カスタムソート機能を完全に無効化し、切り戻す場合
- 開発・テスト環境でのクリーンアップ
- フィールドの再作成が必要な場合

> [!TIP]
> カスタムソート機能の詳細については、[dataset一覧画面のソートオプションの追加](./dataset_sort.md)を参照してください。

> [!WARNING]
> このコマンドは、フィールドとインデックス済みデータを削除します。  
> 削除後は、必ず`ckan search-index rebuild`を実行してください。

> [!NOTE]
> このコマンドは、`custom_sort`設定に関係なく実行できます。  
> 以前に作成されたフィールドをクリーンアップするために使用されます。

### 実行

```bash
ckan feedback reset-solr-fields [options]
```

### オプション

```bash
-y, --yes
```

確認プロンプトをスキップして実行します。

### 実行例

```bash
# 確認プロンプトを表示して削除
ckan feedback reset-solr-fields

# 確認をスキップして削除
ckan feedback reset-solr-fields --yes

# 削除後に再インデックスを実行
ckan feedback reset-solr-fields --yes
ckan search-index rebuild
```

### 注意事項

1. **データの削除**: フィールドを削除すると、そのフィールドにインデックスされたすべてのデータが失われます。

2. **自動再作成の防止**: フィールド削除後、`custom_sort.enable`を`false`に設定しないと、次回CKANコマンド実行時にフィールドが自動的に再作成されます。

3. **削除の確認**: 削除後は、`curl`コマンドで確認してください：
> [!NOTE]
  >`SOLR_URL`は使用しているsolrのURLを指定してください。

   ```bash
   curl http://SOLR_URL/solr/ckan/schema/fields | grep -E "(downloads_total_i|likes_total_i)"
   ```

4. **本番環境での使用**: 本番環境で実行する場合は、事前にバックアップを取得することを推奨します。

**実行例（完全な手順）：**
```bash
# 1. フィールドを削除
ckan feedback reset-solr-fields --yes

# 2. feedback_config.jsonでcustom_sortを無効にする（重要！）
#    "modules": {
#      "custom_sort": {
#        "enable": false
#      }
#    }

# 3. 削除を確認（curlコマンドを使用）
curl http://SOLR_URL/solr/ckan/schema/fields | grep -E "(downloads_total_i|likes_total_i)"

# 4. 検索インデックスを再構築
ckan search-index rebuild

# （オプション）フィールドを再作成する場合：
# 5. feedback_config.jsonでcustom_sortを有効にする
# 6. CKANを再起動（フィールドが自動再作成される）
# 7. 検索インデックスを再構築
ckan search-index rebuild
```