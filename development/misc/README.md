## ckanコマンドの仕様

### デフォルト

```
ckan feedback init
```

* ```ckanext-feedback```で利用する全てのテーブル作成を行う
    * すでにテーブルが作成されている場合は全て削除した後にテーブル作成を行う

#### 成功時

* 以下のログが出力される(緑色太字)
```
Clean all modules: SUCCESS
Initialize all modules: SUCCESS
```

#### 失敗時
    
* エラー文が出力される

* __コマンド実行前の状態に戻る__

### オプション

#### Moduleに関連したオプション

```
--modules -m
```

* ```ckanext-feedback```のオンオフ機能と連動して、必要になるテーブルを作成する
    * すでにテーブルが作成されている場合は全て削除をしてから指定の機能のテーブルを作成する
    * 以下の中から選択が可能
        * utilization (利活用方法)
        * resource (データリソース)
        * download (ダウンロード数)

* 使用例 (```utilization```の機能に関連したテーブル作成を行う)
```
ckan --config=/etc/ckan/production.ini feedback init -m utilization
```

#### 成功時

* ```utilization```指定時は以下のログが出力される(緑色太字)
```
Clean all modules: SUCCESS
Initialize utilization: SUCCESS
```
* ```resource```指定時は以下のログが出力される(緑色太字)
```
Clean all modules: SUCCESS
Initialize resource: SUCCESS
```
* ```download```指定時は以下のログが出力される(緑色太字)
```
Clean all modules: SUCCESS
Initialize download: SUCCESS
```

#### 失敗時

* エラー文が出力される

* __コマンド実行前の状態に戻る__

#### Postgresqlに関連したオプション

##### 参照される順番について

* 以下の優先順位で値を参照する
    * オプションで指定した値
    * 以下の名前の環境変数として設定されている値
        * ```POSTGRES_HOST```
        * ```POSTGRES_PORT```
        * ```POSTGRES_DB```
        * ```POSTGRES_USER```
        * ```POSTGRES_PASSWORD```
    * デフォルト値としてはCKANにデフォルトで設定されている値
        * ホスト名：```db```
        * ポート番号：```5432```
        * データベース名：```ckan```
        * ユーザー名：```ckan```
        * パスワード：```ckan```

※ 環境変数を登録する方法は以下の通り

* ```ckan/contrib/docker/.env```に環境変数を記述する  
        (例) POSTGRES_PORT=5432 
* ```ckan/contrib/docker/docker-compose.yml```の```ckan```の```environment```に上で設定した環境変数を記述する  
        (例) POSTGRES_PORT=${POSTGRES_PORT}

##### オプションについて

* Postgresql の接続に使うホスト名をコマンド上から指定する際に利用する
```
--host -h
```

* Postgresql の接続に使うポート番号をコマンド上から指定する際に利用する
```
--port -p
```

* Postgresql の接続に使うデータベース名をコマンド上から指定する際に利用する
```
--name -n
```

* Postgresql の接続に使うユーザー名をコマンド上から指定する際に利用する
```
--user -u
```

* Postgresql の接続に使うパスワードをコマンド上から指定する際に利用する
```
--password -P
```