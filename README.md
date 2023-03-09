# ckanext-feedback

このCKAN Extensionは大きく3つのモジュールを提供します。

* データの利活用方法に関するモジュール
* リソースへのレビューに関するモジュール
* ダウンロードに関するモジュール

## 現状の課題

### オープンデータ公開元(自治体など)

* オープンデータの活用状況がわからない
  * 公開したオープンデータの重要性がわからない
  * 公開済みのオープンデータをどのように整備したら良いかわからない

### 利用者(シビックハッカーなど)

* オープンデータ活用へのハードルが高い
  * オープンデータに対する質問や問い合わせに時間と労力がかかる

<br />
<center><font size=4px>このような課題を解決するための機能を提供するCkan Extensionです。</font></center>
<br />

## 提供する機能

### データの利活用に関するモジュール

* 活用された事例をオープンデータに紐付けて登録できる
  * 活用事例を知ることでオープンデータの**重要性を確認できる**
  * 需要のあるオープンデータが分かり、今後のオープンデータ公開に関する**計画が立てやすくなる**

* 登録された活用事例に対してコメントできる( 要望 / 質問 / 宣伝 / 感謝 )
  * どのような要望があるかわかる
  * データ利活用者のモチベーションアップ

### データへのレビューに関するモジュール

* 公開しているオープンデータを評価してもらうことができる
  * どのオープンデータを整備するかの優先度がつけやすくなる
  * 評価の高い(信頼できる)オープンデータをすぐに見つけ、利活用できる

* オープンデータに対してコメントができる( 要望 / 質問 / 宣伝 / 感謝 )
  * 公開済みのデータをどのように整備したら良いかわかる
  * 問い合わせをすぐに楽に行える

### ダウンロードに関するモジュール

* 公開しているオープンデータのダウンロード数がわかる
  * オープンデータの利用状況や需要がわかる

## インストール

### クイックスタート

1. CKANの仮想環境をアクティブにする\
   `. /usr/lib/ckan/venv/bin/activate`

2. 仮想環境にckanext*feedbackをインストールする\
   `pip install ckanext*feedback`

3. CKAN config fileの`ckan.plugins`に`feedback`を追加する\
   `vim /etc/ckan/production.ini` 以下の行に`feedback`を追加\
   `ckan.plugins = stats ・・・ recline_view feedback`

4. フィードバック機能に必要なテーブルを作成する  
   `ckan *config=/etc/ckan/production.ini feedback init`

### オンオフ機能

* ckanext*feedbackには以下の3つのモジュールがあり、それぞれのモジュールのオンオフを切り替えることが出来ます。
  * utilization(データの利活用方法に関するモジュール)
  * resource(リソースへのレビューに関するモジュール)
  * download(ダウンロードに関するモジュール)  
※ デフォルトでは全てのモジュールがオンになっています

#### 設定手順

1. CKANの仮想環境をアクティブにする\
   `. /usr/lib/ckan/venv/bin/activate`

2. 仮想環境にckanext*feedbackをインストールする\
   `pip install ckanext*feedback`

3. CKAN config fileの`ckan.plugins`に`feedback`を追加する\
   `vim /etc/ckan/production.ini` 以下の行に`feedback`を追加\
   `ckan.plugins = stats ・・・ recline_view feedback`

   オフにしたい機能がある場合は`ckan.plugins`の下に以下の記述を追記する

    * utilizationモジュールをオフにする  
    `ckan.feedback.utilizations.enable = False`

    * resourceモジュールをオフにする  
    `ckan.feedback.resources.enable = False`

    * downloadモジュールをオフにする  
    `ckan.feedback.downloads.enable = False`

4. それぞれのモジュールに必要なテーブルを作成する(コマンドのオプションで作成するテーブルを指定する)

    * utilizationモジュールを利用する場合
    `ckan config=/etc/ckan/production.ini feedback init -m utilization`

    * resourceモジュールを利用する場合
    `ckan config=/etc/ckan/production.ini feedback init -m resource`

    * downloadモジュールを利用する場合
    `ckan config=/etc/ckan/production.ini feedback init -m download`

