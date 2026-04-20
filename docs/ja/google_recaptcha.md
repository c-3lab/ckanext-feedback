# Google reCAPTCHA

botによる各種投稿へのスパム対策機能です。

## 導入の利点

* botによる新規投稿やコメント投稿時のスパムを軽減できます。

## 機能説明

* 以下の投稿実行時に Google reCAPTCHA v3 を使用した検証を行い、算出されたスコアが閾値未満の場合はユーザへ投稿実行の再試行を要求します。
    * データリソースへのコメント投稿。
    * 利活用の新規投稿。
    * 利活用へのコメント投稿。

    ※ 本機能はデフォルトではオフになっています

## 設定方法

1. [Google reCAPTCHA の公式ガイド](https://developers.google.com/recaptcha/intro?hl=ja)に従って v3 のサイトキー、シークレットキーを取得する。

2. `ckan.ini` に以下の行を追記する

    * google_reCAPTCHA機能のON(必須)

        ```ini
        ckan.feedback.recaptcha.enable = true
        ```

    * サイトキー、シークレットキーの設定(必須)

        ```ini
        ckan.feedback.recaptcha.publickey = サイトキー
        ckan.feedback.recaptcha.privatekey = シークレットキー
        ```

    * 閾値の設定(任意)

        ```ini
        ckan.feedback.recaptcha.score_threshold = 0.0 ~ 1.0
        ```

        * 未設定の場合のデフォルト値は 0.5 です。
        * Google reCAPTCHA による検証結果のスコアが 閾値未満の場合はユーザに再試行を要求します。
        * 適切な閾値を判断する方法については [公式ドキュメント スコアの解釈](https://developers.google.com/recaptcha/docs/v3?hl=ja#interpreting_the_score)を参照してください。 

3. Webアプリケーションサーバを再起動する

google reCAPTCHA v3の詳しい仕様については[公式ドキュメント](https://developers.google.com/recaptcha/docs/v3?hl=ja)を参照してください。