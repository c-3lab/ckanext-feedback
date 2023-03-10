# ckanext-feedback

このCKAN拡張機能は公開しているオープンデータの品質をより良くするための機能を提供します。  
オープンデータの利活用状況を把握し、利用者のニーズに合わせた整備や新規データの公開を行うのに役立ちます。  
また、オープンデータの利用者と提供者のコミュニケーションを促進し、オープンデータの品質向上に貢献します。

## フィードバック機能

✅ 数量データを記録と表示  
* データのダウンロード数
* データの利活用数
* データによる課題解決数  

✅ データへ紐づけた利活用方法の登録  
✅ データや利活用方法へのコメントと評価  
✅ データへの問い合わせ( 要望 / 質問 / 宣伝 / 感謝 )  

## クイックスタート

1. CKANの仮想環境をアクティブにする
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

## オンオフ機能

* ckanext-feedbackには以下の3つのモジュールがあり、各モジュールのオンオフを切り替えることが出来ます。
  * utilization(データの利活用方法に関するモジュール)
  * resource(リソースへのレビューに関するモジュール)
  * download(ダウンロードに関するモジュール)  

※ デフォルトでは全てのモジュールがオンになっています

### 設定手順

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

   オフにしたい機能がある場合は`ckan.plugins`の下に以下の記述を追記する

    utilizationモジュールをオフにする  
    ```
    ckan.feedback.utilizations.enable = False
    ```

    resourceモジュールをオフにする  
    ```
    ckan.feedback.resources.enable = False
    ```

    downloadモジュールをオフにする  
    ```
    ckan.feedback.downloads.enable = False
    ```

5. それぞれのモジュールに必要なテーブルを作成する(コマンドのオプションで作成するテーブルを指定する)

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