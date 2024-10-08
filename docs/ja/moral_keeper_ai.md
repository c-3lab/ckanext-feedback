# コメント提案機能

[moral-keeper-ai](https://github.com/c-3lab/moral-keeper-ai)を使用したコメント提案機能です。  
コメント投稿時に入力された文章を以下の観点からAIを使って評価し、文章の修正案をユーザへ提供します。

- ユーザーの投稿文が読者にとって不快なものにならないようにする。
- 投稿者に対する社会的反発の回避
- 曖昧な意見投稿による顧客対応業務の増加を抑制する

コメント提案機能を有効化すると、以下のコメント投稿に対して適用されます。

- リソースコメント
- 利活用コメント

## 制約事項

- コメントへの返信には適用されません
- 使用可能なAIのモデルやエンドポイントはmoral-keeper-aiに依存します。  
詳しくは[moral-keeper-aiのリポジトリ](https://github.com/c-3lab/moral-keeper-ai)を参照してください。

## インストール方法

### 環境変数の設定

以下の環境変数が必須です。
コンテナの環境変数設定などに記載してください。

```
AZURE_OPENAI_DEPLOY_NAME='your-deploy-name'
AZURE_OPENAI_API_KEY='your-api-key'
AZURE_OPENAI_ENDPOINT='https://your-endpoint-url.com/'
```

### moral-keeper-aiの取得(CKANコンテナ等の環境内で実行してください)

`pip install moral-keeper-ai`

### feedbackのインストール

* [クイックスタート](../../README.md) **1~4番**の手順を参照してください

### moral-keeper-aiを使用したコメント提案機能の有効化

`ckan.ini`に以下の設定を追記する

```ini
ckan.feedback.moral_keeper_ai.enable = True
```
