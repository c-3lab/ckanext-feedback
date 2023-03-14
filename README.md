# ckanext-feedback

このCKAN Extensionはデータ利用者からのフィードバックを得るための機能を提供します。
本Extensionの利用者からの意見・要望や活用事例の報告を受け付ける仕組み等によって、データ利用者はデータの理解が進みデータ利活用が促進され、データ提供者はデータのニーズ理解やデータ改善プロセスの効率化が行えます。

フィードバックにより利用者と提供者間でデータを改善し続けるエコシステムを実現することができます。

## 主な機能

* 👀 集計情報の可視化機能(ダウンロード数、利活用数、課題解決数)
* 💬 データおよび利活用方法に対するコメント・評価機能
* 🖼 データを利活用したアプリやシステムの紹介機能
* 🏆 データを利活用したアプリやシステムの課題解決認定機能

## クイックスタート

1. CKANの仮想環境をアクティブにする(CKANコンテナ等の環境内で実行してください)
```
. /usr/lib/ckan/venv/bin/activate
```

2. 仮想環境にckanext-feedbackをインストールする
```
pip install ckanext-feedback
```

3. 以下のコマンドで設定を行うファイルを開く
```
vim /etc/ckan/production.ini
```

4. 以下の行に`feedback`を追加
```
ckan.plugins = stats ・・・ recline_view feedback
```

5. フィードバック機能に必要なテーブルを作成する
```
ckan --config=/etc/ckan/production.ini feedback init
```

## 開発者向け

### ビルド方法

1. `ckanext-feedback`をローカル環境にGitHub上からクローンする
```
git clone https://github.com/c-3lab/ckanext-feedback.git
```

2. `ckanext-feedback/development`下にある`setup.py`を実行し、コンテナを起動

3. CKAN公式の手順に従い、以下のコマンドを実行
```
docker exec ckan /usr/local/bin/ckan -c /etc/ckan/production.ini datastore set-permissions | docker exec -i db psql -U ckan
```
```
docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/production.ini sysadmin add admin
```

4. 以下のコマンドを実行し、コンテナ内に入る
```
docker exec -it ckan bash
```

5. CKANの仮想環境をアクティブにする
```
. /usr/lib/ckan/venv/bin/activate
```

6. 仮想環境にckanext-feedbackをインストールする
```
pip install /opt/ckanext-feedback
```

7. 以下のコマンドで設定を行うためのファイルを開く
```
vim /etc/ckan/production.ini
```

8. 以下の行に`feedback`を追加
```
ckan.plugins = stats ・・・ recline_view feedback
```

9. フィードバック機能に必要なテーブルを作成する
```
ckan --config=/etc/ckan/production.ini feedback init
```

10. `http://localhost:5000`にアクセスする

## テスト

## LICENSE

[AGPLv3 LICENSE](https://github.com/c-3lab/ckanext-feedback/blob/feature/documentation-README/LICENSE)

## CopyRight

Copyright (c) 2023 C3Lab
