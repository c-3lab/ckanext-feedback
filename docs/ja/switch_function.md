# オンオフ機能

* ckanext-feedbackには以下の3つのモジュールがあり、各モジュールのオンオフを切り替えることが出来ます。
  * [Utilization](./utilization.md) (データの利活用方法に関するモジュール)
  * [Resource](./resource.md) (リソースへのコメントに関するモジュール)
  * [Download](./download.md) (ダウンロードに関するモジュール)

※ デフォルトでは全てのモジュールがオンになっています

## 設定手順

1. インストール(まだの方のみ)
    * [クイックスタート](../../README.md) **1~4番**の手順を参照してください

2. **オフにするモジュール**について、`ckan.plugins`の下に以下の記述を追記する
    * utilizationモジュールをオフにする場合

        ```bash
        ckan.feedback.utilizations.enable = False
        ```

    * resourceモジュールをオフにする場合

        ```bash
        ckan.feedback.resources.enable = False
        ```

        * 1つのリソースに対してコメントできる回数を各ユーザーごと、１回に制限する場合(ユーザーのCookieを利用)
            * デフォルトの設定(False)では複数回のコメントが可能です

            ```bash
            ckan.feedback.resources.comment.repeated_post_limit.enable = True
            ```

    * downloadモジュールをオフにする場合

        ```bash
        ckan.feedback.downloads.enable = False
        ```

3. テーブル作成(まだの方のみ)
    * [feedbackコマンド](./feedback_command.md)の```-modules```オプションを参考に**オンにするモジュール**のテーブル作成を行なってください

## downloadモジュールを外部プラグインと連携する場合

リソースがダウンロードされると、downloadモジュールはダウンロード数のカウント処理を行った後、デフォルトのダウンロードコールバックである`ckan.views.resource:download`を呼び出します。しかし、`ckan.ini`内の設定変数`ckan.feedback.download_handler`により、`ckan.views.resource:download`を他のExtension（例：[googleanalytics](https://github.com/ckan/ckanext-googleanalytics)）のダウンロードハンドラに置き換えることも可能です。

例：ckanext-googleanalytics の場合

```bash
ckan.feedback.download_handler = ckanext.googleanalytics.views:download
```

また、逆に外部ハンドラを設定できる他のExtensionのコールバックとしてckanext-feedbackのdownloadモジュールを指定したい場合は、`ckanext.feedback.views.download:download`を使用できます。

例：ckanext-googleanalytics の場合

```bash
googleanalytics.download_handler = ckanext.feedback.views.download:download
```

これらの連携方法は、複数のextensionを使用する際に`/download`などのパスが競合してしまう場合に役立ちます。
