# メール通知

新規投稿やコメント投稿を組織管理者にメールで通知する機能です。

## 導入の利点

* 新規投稿やコメント投稿があったことをメールで知ることができます。

## 機能説明

* 以下の投稿実行時、そのデータセットの組織管理者にメールで通知します。
    * データリソースへのコメント投稿。
    * 利活用の新規投稿。
    * 利活用へのコメント投稿。

    ※ 本機能はデフォルトではオフになっています

## 設定方法

1. SMTPサーバ設定を行う

    以下の環境変数で、使用するSMTPサーバの設定を行う。

    ```
    CKAN_SMTP_SERVER=smtp.corporateict.domain:25
    CKAN_SMTP_STARTTLS=True
    CKAN_SMTP_USER=user
    CKAN_SMTP_PASSWORD=pass
    ```

    または、`ckan.ini`内の以下の項目で使用するSMTPサーバの設定を行う。  

    ```ini
    smtp.server = smtp.corporateict.domain:25
    smtp.starttls = true
    smtp.user = user
    smtp.password = pass
    ```
    
    ※ 環境変数の設定が優先されます。

2. ckan.ini に以下の行を追記する

    * 通知機能のON(必須)

        ```ini
        ckan.feedback.notice.email.enable = true
        ```

    * メールテンプレートの格納ディレクトリの指定(任意)

        ```ini
        ckan.feedback.notice.email.template_directory = /path/to/template_dir
        ```

        ※設定されていない場合は`{ckanext-feedbackがインストールされているディレクトリ}/templates/email_notification`が使用される。

    * メールテンプレート名の設定(必須)  

        メールテンプレートの格納ディレクトリ内にあるファイルのファイル名を指定してください。  

        独自のテンプレートを使用する場合は、メールテンプレートの格納ディレクトリ内にあるファイルの内容を変更するか、別のテンプレートファイルを作成し、そのファイル名を指定してください。

        * データリソースへのコメント投稿通知に使用するテンプレート名

            ```ini
            ckan.feedback.notice.email.template_resource_comment = template.text
            ```

            ※初期テンプレートを使用したい場合は[resource_comment.text](../../ckanext/feedback/templates/email_notification/resource_comment.text) を設定してください。

        * 利活用の新規投稿通知に使用するテンプレート名

            ```ini
            ckan.feedback.notice.email.template_utilization = template.text
            ```

            ※初期テンプレートを使用したい場合は[utilization.text](../../ckanext/feedback/templates/email_notification/utilization.text)を設定してください。

        * 利活用へのコメント投稿通知に使用するテンプレート名

            ```ini
            ckan.feedback.notice.email.template_utilization_comment = template.text
            ```

            ※初期テンプレートを使用したい場合は[utilization_comment.text](../../ckanext/feedback/templates/email_notification/utilization_comment.text)を設定してください。

    * 件名の指定 (任意)

        * データリソースへのコメント投稿通知に使用する件名

            ```ini
            ckan.feedback.notice.email.subject_resource_comment = Post a Resource comment
            ```

        * 利活用の新規投稿通知に使用する件名

            ```ini
            ckan.feedback.notice.email.subject_utilization = Post a Utilization
            ```

        * 利活用へのコメント投稿通知に使用する件名

            ```ini
            ckan.feedback.notice.email.subject_utilization_comment = Post a Utilization comment
            ```

        ※指定がない場合は「New Submission Notification」となります。

3. Webアプリケーションサーバを再起動する