# ckanext-feedback コマンド一覧

運用・保守を目的とした専用の CLI コマンドを提供しています。  
フィードバック機能に関するデータの 初期化・整備・クリーンアップ を柔軟に行うことができます。  
**本ドキュメントでは、`ckan feedback` サブコマンドの使い方を体系的にまとめています。**


※ ckanコマンドを実行する際は設定ファイル（`ckan.ini`）を指定する必要があります。

## 目次

- [ckan feedback init](#ckan-feedback-init)
  - [実行](#実行)
  - [オプション](#オプション)
  - [実行例](#実行例)
- [ckan feedback clean files](#ckan-feedback-clean-files)
  - [実行](#実行-1)
  - [オプション](#オプション-1)
  - [実行例](#実行例-1)
  - [補足：削除対象の判定基準](#補足削除対象の判定基準)

## ckan feedback init

指定した機能に関係する PostgreSQLのテーブルを初期化 します。  
初期化の対象はオプションで制御でき、指定がない場合は すべてのテーブル が対象となります。

### 実行

```bash
ckan feedback init [options]
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

## ckan feedback clean-files

コメント投稿時にアップロードされた画像ファイルのうち、実際にはコメントに添付されなかった不要なファイルを検索・削除します。  
フィードバック投稿中に一時的にアップロードされたものの、投稿が完了せずに残ったファイルなどが対象です。

### 実行

```bash
ckan feedback clean-files [options]
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