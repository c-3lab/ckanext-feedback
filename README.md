# ckanext-feedback

[![codecov](https://codecov.io/github/c-3lab/ckanext-feedback/graph/badge.svg?token=8T2RIXPXOM)](https://codecov.io/github/c-3lab/ckanext-feedback)

このCKAN Extensionはデータ利用者からのフィードバックを得るための機能を提供します。
本Extensionの利用者からの意見・要望や活用事例の報告を受け付ける仕組み等によって、データ利用者はデータの理解が進みデータ利活用が促進され、データ提供者はデータのニーズ理解やデータ改善プロセスの効率化が行えます。

This CKAN Extension provides functionality to obtain feedback from data users. The mechanism for receiving opinions/requests and reports on usage examples from users of this extension will help data users understand data and promote data utilization, while data providers will be able to understand data needs and improve the data improvement process. You can improve efficiency.

フィードバックにより利用者と提供者間でデータを改善し続けるエコシステムを実現することができます。

Feedback enables an ecosystem between users and providers that continually improves the data.

## Main features

* 👀 集計情報の可視化機能(ダウンロード数、利活用数、課題解決数)
  * Visualization function for aggregate information (number of downloads, number of uses, number of problems solved)
* 💬 データおよび利活用方法に対するコメント・評価機能
  * Comment and evaluation function for data and usage methods
* 🖼 データを利活用したアプリやシステムの紹介機能
  * Feature to introduce apps and systems that utilize data
* 🏆 データを利活用したアプリやシステムの課題解決認定機能
  * Problem-solving certification function for apps and systems that utilize data

## Quick Start

1. CKANの仮想環境をアクティブにする(CKANコンテナ等の環境内で実行してください)

    ```bash
    . /usr/lib/ckan/venv/bin/activate
    ```

2. 仮想環境にckanext-feedbackをインストールする

    ```bash
    pip install ckanext-feedback
    ```

3. 以下のコマンドで設定を行うファイルを開く

    ```bash
    vim /etc/ckan/production.ini
    ```

4. 以下の行に`feedback`を追加

    ```bash
    ckan.plugins = stats ・・・ recline_view feedback
    ```

5. フィードバック機能に必要なテーブルを作成する

    ```bash
    ckan --config=/etc/ckan/production.ini feedback init
    ```

## 構成

### 本Extensionは3つのモジュールで構成されています

* [utilization](./docs/ja/utilization.md)
* [resource](./docs/ja/resource.md)
* [download](./docs/ja/download.md)

### 設定や管理に関するドキュメント

* リソースや利活用方法へのコメントを管理することが出来ます
  * 詳しくは[管理者用画面ドキュメント](docs/ja/admin.md)をご覧ください

* 特定のモジュールのみを利用することも可能です
  * 設定方法は[オンオフ機能の詳細ドキュメント](./docs/ja/switch_function.md)をご覧ください

## 開発者向け

### ビルド方法

1. `ckanext-feedback`をローカル環境にGitHub上からクローンする

    ```bash
    git clone https://github.com/c-3lab/ckanext-feedback.git
    ```

2. `ckanext-feedback/development`下にある`setup.py`を実行し、コンテナを起動

3. CKAN公式の手順に従い、以下のコマンドを実行

    ```bash
    docker exec ckan /usr/local/bin/ckan -c /etc/ckan/production.ini datastore set-permissions | docker exec -i db psql -U ckan
    ```

    ```bash
    docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/production.ini sysadmin add admin
    ```

4. 以下のコマンドを実行し、コンテナ内に入る

    ```bash
    docker exec -it ckan bash
    ```

5. CKANの仮想環境をアクティブにする

    ```bash
    . /usr/lib/ckan/venv/bin/activate
    ```

6. 仮想環境にckanext-feedbackをインストールする

    ```bash
    pip install /opt/ckanext-feedback
    ```

7. 以下のコマンドで設定を行うためのファイルを開く

    ```bash
    vim /etc/ckan/production.ini
    ```

8. 以下の行に`feedback`を追加

    ```bash
    ckan.plugins = stats ・・・ recline_view feedback
    ```

9. フィードバック機能に必要なテーブルを作成する

    ```bash
    ckan --config=/etc/ckan/production.ini feedback init
    ```

10. `http://localhost:5000`にアクセスする

### 参考ドキュメント

* [feedbackコマンド 詳細ドキュメント](./docs/ja/feedback_command.md)
* [言語対応(i18n) 詳細ドキュメント](./docs/ja/i18n.md)

## テスト

1. 上記のビルド方法に従い、ビルドを行う

2. コンテナ内に入る

    ```bash
    docker exec -it --user root ckan /bin/bash
    ```

3. その他の必要なものをインストールする

    ```bash
    pip install -r /usr/lib/ckan/venv/src/ckan/dev-requirements.txt
    pip install pytest-ckan
    ```

4. テスト用DBを作成する

    ```bash
    createdb ckan_test -O ckan -E utf-8 -h db -U ckan
    ```

5. ディレクトリを移動

    ```bash
    cd /usr/lib/ckan/venv/lib/python3.8/site-packages/ckanext/feedback/tests
    ```

6. テストを実行

    ```bash
    CKAN_SQLALCHEMY_URL= CKAN_DATASTORE_READ_URL= CKAN_DATASTORE_WRITE_URL= pytest -s --ckan-ini=config/test.ini --cov=ckanext.feedback --cov-branch --disable-warnings ./
    ```

## LICENSE

[AGPLv3 LICENSE](https://github.com/c-3lab/ckanext-feedback/blob/feature/documentation-README/LICENSE)

## CopyRight

Copyright (c) 2023 C3Lab
