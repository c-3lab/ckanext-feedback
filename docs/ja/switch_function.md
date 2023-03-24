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

    * downloadモジュールをオフにする場合

        ```bash
        ckan.feedback.downloads.enable = False
        ```

3. テーブル作成(まだの方のみ)
    * [feedbackコマンド](./feedback_command.md)の```-modules```オプションを参考に**オンにするモジュール**のテーブル作成を行なってください
