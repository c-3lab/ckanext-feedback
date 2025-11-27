# dataset一覧画面のソートオプションの追加 

detaset一覧画面のソートオプションにいいね数とダウンロード数を追加します。

![dataset ソート機能 いいね数 イメージ図](../assets/dataset_sort_30.jpg)

## 概要

**本機能は、feedbackプラグインのLikeとDownloadを有効にしている場合に機能します。**


## 主要機能



### いいね数でソート

いいね数の降順でデータセットをソートすることができます。

![dataset ソート機能 いいね数 イメージ図](../assets/dataset_sort_10.jpg)



### ダウンロード数でソート

ダウンロード数の降順でデータセットをソートすることができます。

![dataset ソート機能 ダウンロード数 イメージ図](../assets/dataset_sort_20.jpg)


## 設定方法

### 適応方法

既存のデータセットに本機能を適応させる場合、以下のコマンドを実行する必要があります。 



```bash
# 全データセットを再インデックス
ckan -c /path/to/ckan.ini search-index rebuild

# 特定のデータセットのみ再インデックス
ckan -c /path/to/ckan.ini search-index rebuild <dataset-name> 
```

再インデックスが必要なデータセットを探すには、以下のコマンドを実行してください。

```bash
# インデックスされていないデータセットの確認
ckan -c /path/to/ckan.ini search-index check
```

### 本機能をOFFにする場合

上記の手順で適応した後、本機能をOFFにしたい場合、必ず以下の手順でOFFにしてください。

1. 設定ファイル`feedback_config.json`で本機能をOFF

    ```bash
    "custom_sort": {
        "enable": false
    }
    ```
    または、`ckan.ini`で設定している場合
    ```bash
    ckan.feedback.custom_sort.enable = False
    ```

2. 本機能がOFFになっていることを確認したあとに、以下のコマンドを実行

    ```bash
    ckan feedback reset-solr-fields [options]
    ```
    コマンドの詳細は以下のドキュメントを参照してください。

    [feedback_command](./feedback_command.md)

3. 実行後、インデックスクリアコマンドを実行

    ```bash
    ckan search-index clear
    ```

4. 再インデックスコマンドを実行

    ```bash
    ckan search-index rebuild
    ```

> [!IMPORTANT]
> `ckan`コマンドは、`ckan.ini`がある場所で実行するか、`-c`で`ckan.ini`の指定が必要です。

[コマンド参照ページ](https://docs.ckan.org/en/latest/maintaining/cli.html#search-index-rebuild-search-index)


---


各機能のON/OFF設定については、以下のドキュメントをご参照ください：

📖 [ON/OFF機能の詳細ドキュメント](./switch_function.md)