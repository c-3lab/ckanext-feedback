# オンオフ機能

* ckanext-feedbackには以下の3つのモジュールがあり、各モジュールのオンオフを切り替えることが出来ます。
  * [Utilization](./utilization.md) (データの利活用方法に関するモジュール)
  * [Resource](./resource.md) (リソースへのレビューに関するモジュール)
  * [Download](./download.md) (ダウンロードに関するモジュール)

※ デフォルトでは全てのモジュールがオンになっています

## 設定手順

1. CKANの仮想環境をアクティブにする
```
. /usr/lib/ckan/venv/bin/activate
```

2. 仮想環境にckanext-feedbackをインストールする
```
pip install ckanext-feedback
```

3. 以下のコマンドで設定を行うためのファイルを開く
```
vim /etc/ckan/production.ini
```

4. 以下の行に`feedback`を追加
```
ckan.plugins = stats ・・・ recline_view feedback
```

5. オフにする機能について、`ckan.plugins`の下に以下の記述を追記する

utilizationモジュールをオフにする場合
```
ckan.feedback.utilizations.enable = False
```

resourceモジュールをオフにする場合
```
ckan.feedback.resources.enable = False
```

downloadモジュールをオフにする場合
```
ckan.feedback.downloads.enable = False
 ```

6. それぞれのモジュールに必要なテーブルを作成する(コマンドのオプションで作成するテーブルを指定する)

utilizationモジュールを利用する場合
```
ckan --config=/etc/ckan/production.ini feedback init -m utilization
```

resourceモジュールを利用する場合
```
ckan --config=/etc/ckan/production.ini feedback init -m resource
```

downloadモジュールを利用する場合
```
ckan --config=/etc/ckan/production.ini feedback init -m download
```