# ckan feedback init

指定した機能に関係するPostgreSQLのテーブルを初期化する。

## 実行

```bash
ckan feedback init [options]
```

### オプション

#### -m, --modules < utilization/ resource/ download >

任意項目

* 一部の機能を利用する場合に以下の3つから指定して実行する。(複数選択可)  
* このオプションの指定がない場合は全てのテーブルに対して初期化処理を行う。
  * utilization
  * resource
  * download

##### 実行例 (--module オプション)

```bash
# ckanext-feedback plugins に関わる全てのテーブルに対して初期化を行う
ckan --config=/etc/ckan/production.ini feedback init

# utilization(利活用方法)機能に関わるテーブルに対して初期化を行う
ckan --config=/etc/ckan/production.ini feedback init -m utilization

# resource(データリソース)機能に関わるテーブルに対して初期化を行う
ckan --config=/etc/ckan/production.ini feedback init -m resource

# download(ダウンロード)機能に関わるテーブルに対して初期化を行う
ckan --config=/etc/ckan/production.ini feedback init -m download

# resource(データリソース)機能とdownload(ダウンロード)機能に関わるテーブルに対して初期化を行う
ckan --config=/etc/ckan/production.ini feedback init -m resource -m download
```

※ ckanコマンドを実行する際は```--config=/etc/ckan/production.ini```と記述して、configファイルを指定する必要がある

#### -h, --host <host_name>

任意項目

* PostgreSQLコンテナのホスト名を指定する。  
* 指定しない場合、以下の順で参照された値を使用する。
  * 環境変数 ```POSTGRES_HOST```
  * CKANのデフォルト値 ```db```

#### -p, --port \<port\>

任意項目

* PostgreSQLコンテナのポート番号を指定する。  
* 指定しない場合、以下の順で参照された値を使用する。
  * 環境変数 ```POSTGRES_PORT```
  * CKANのデフォルト値 ```5432```

#### -d, --dbname <db_name>

任意項目

* PostgreSQLのデータベース名を指定する。  
* 指定しない場合、以下の順で参照された値を使用する。
  * 環境変数 ```POSTGRES_DB```
  * CKANのデフォルト値 ```ckan```

#### -u, --user <user_name>

任意項目

* PostgreSQLに接続するためのユーザ名を指定する。  
* 指定しない場合、以下の順で参照された値を使用する。
  * 環境変数 ```POSTGRES_USER```
  * CKANのデフォルト値 ```ckan```

#### -P, --password \<password\>

任意項目

* PostgreSQLに接続するためのパスワードを指定する。  
* 指定しない場合、以下の順で参照された値を使用する。
  * 環境変数 ```POSTGRES_PASSWORD```
  * CKANのデフォルト値 ```ckan```

##### 実行例 (その他 オプション)

```bash
# ホスト名として"postgresdb"を指定する
ckan --config=/etc/ckan/production.ini feedback init -h postgresdb

# ポート番号として"5000"を指定する
ckan --config=/etc/ckan/production.ini feedback init -p 5000

# データベース名として"ckandb"を指定する
ckan --config=/etc/ckan/production.ini feedback init -d ckandb

# ユーザ名として"root"を指定する
ckan --config=/etc/ckan/production.ini feedback init -u root

# パスワードとして"root"を指定する
ckan --config=/etc/ckan/production.ini feedback init -P root

# ホスト名として"postgresdb", ユーザ名として"root", パスワードとして"root"を指定する
ckan --config=/etc/ckan/production.ini feedback init -h postgresdb -u root -P root
```
