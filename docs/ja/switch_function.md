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

リソースがダウンロードされると、downloadモジュールはダウンロード数のカウント追加処理を行った後、デフォルトのダウンロードコールバックを呼び出します。CKAN>=2.10 を使用していて、一部のプラグインが`resource.download`ルートを再定義する場合(ckanext-googleanalytics など)、`ckan.views.resource:download`を使用する代わりにどの関数を呼び出す必要があるかを`ckan.ini`内の設定変数`ckan.feedback.download_handler`にて指定できます。</br>
例として、ckanext-googleanalytics を指定する場合は、以下の設定を使用できます。

```bash
ckan.feedback.download_handler = ckanext.googleanalytics.views:download
```

上記とは逆に、外部プラグインからckanext-feedbackのdownloadモジュールをコールバックとして指定する場合、`ckanext.feedback.views.download:download`が使用できます。</br>
例として、ckanext-googleanalyticsのdownloadハンドラとしてckanext-feedbackのdownloadモジュールを指定する場合は、以下の設定を使用できます。

```bash
googleanalytics.download_handler = ckanext.feedback.views.download:download
```