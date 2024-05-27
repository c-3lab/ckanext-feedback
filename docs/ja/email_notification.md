# メール通知

* ckanext-feedbackには組織が所有するデータセットに対しての新規投稿を組織管理者にメールで通知する機能があります。
  * Resourceへのコメント投稿
  * Utilizationの新規投稿
  * Utilizationへのコメント投稿

※ デフォルトでは通知機能はオフになっています

## 設定手順

1. SMTPサーバ設定を行う
    `ckanext-feedback/development/.env.dev`の以下の項目で、使用するSMTPサーバの設定を行う。

    ```dotenv
    CKAN_SMTP_SERVER=smtp.corporateict.domain:25
    CKAN_SMTP_STARTTLS=True
    CKAN_SMTP_USER=user
    CKAN_SMTP_PASSWORD=pass
    ```

    上記の手順で設定を行わない、つまり設定値が空の場合、手順3 以降にて`ckan.ini`内の以下の項目で使用するSMTPサーバの設定を行う。</br>
    ※設定の反映にはWebアプリケーションサーバの再起動が必要

    ```ini
    smtp.server = smtp.corporateict.domain:25
    smtp.starttls = true
    smtp.user = user
    smtp.password = pass
    ```

2. インストール
    * [クイックスタート](../../README.md) **1~4番**の手順を参照してください

3. **各種設定**を行う。`ckan.ini`内の`ckan.plugins`以降に以下の記述を追記する
    * 通知機能のON

        ```ini
        ckan.feedback.notice.email.enable = True
        ```

    * メールテンプレートの格納ディレクトリの指定(任意)

        ```ini
        ckan.feedback.notice.email.template_directory = /path/to/template_dir
        ```

        ※設定されていない場合は`/srv/app/src_extensions/ckanext-feedback/ckanext/feedback/templates/email_notification`が使用される。

    * メールテンプレート名の設定(必須)

        * Resourceへのコメント投稿通知に使用するテンプレート名

            ```ini
            ckan.feedback.notice.email.template_resource_comment = resource_comment.text
            ```

        * Utilizationの新規投稿通知に使用するテンプレート名

            ```ini
            ckan.feedback.notice.email.template_utilization = utilization.text
            ```

        * Utilizationへのコメント投稿通知に使用するテンプレート名

            ```ini
            ckan.feedback.notice.email.template_utilization_comment = utilization_comment.text
            ```

        ※ 独自のテンプレートを使用する場合は任意のテンプレート名に変更可能。

    * 件名の指定 (任意)

        * Resourceへのコメント投稿通知に使用する件名

            ```ini
            ckan.feedback.notice.email.subject_resource_comment = Post a Resource comment
            ```

        * Utilizationの新規投稿通知に使用する件名

            ```ini
            ckan.feedback.notice.email.subject_utilization = Post a Utilization
            ```

        * Utilizationへのコメント投稿通知に使用する件名

            ```ini
            ckan.feedback.notice.email.subject_utilization_comment = Post a Utilization comment
            ```

        ※指定がない場合は「New Submission Notification」となる。

4. workerの起動確認
    * メール送信をバックグラウンドで実行する為のworkerコンテナ:`ckan-docker-ckan-worker-1`が起動している事を確認する。

    ```bash
    docker ps
    ```
