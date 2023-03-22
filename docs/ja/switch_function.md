# オンオフ機能

* ckanext-feedbackには以下の3つのモジュールがあり、各モジュールのオンオフを切り替えることが出来ます。
  * [Utilization](./utilization.md) (データの利活用方法に関するモジュール)
  * [Resource](./resource.md) (リソースへのレビューに関するモジュール)
  * [Download](./download.md) (ダウンロードに関するモジュール)

※ デフォルトでは全てのモジュールがオンになっています

## 設定手順

1. まだインストールをされていない方  
  [クイックスタート](../../README.md) **1~4番**の手順を参照してください

2. オフにする機能について、`ckan.plugins`の下に以下の記述を追記する

    * utilizationモジュールをオフにする場合
      ```
      ckan.feedback.utilizations.enable = False
      ```

    * resourceモジュールをオフにする場合
      ```
      ckan.feedback.resources.enable = False
      ```

    * downloadモジュールをオフにする場合
      ```
      ckan.feedback.downloads.enable = False
      ```

3. それぞれのモジュールに必要なテーブルを作成する(コマンドのオプションで作成するテーブルを指定する)

    * utilizationモジュールを利用する場合
      ```
      ckan --config=/etc/ckan/production.ini feedback init -m utilization
      ```

    * resourceモジュールを利用する場合
      ```
      ckan --config=/etc/ckan/production.ini feedback init -m resource
      ```

    * downloadモジュールを利用する場合
      ```
      ckan --config=/etc/ckan/production.ini feedback init -m download
      ```