# dataset一覧画面のソートオプションの追加 

dataset一覧画面のソートオプションにいいね数とダウンロード数を追加します。

![dataset ソート機能 いいね数 イメージ図](../assets/dataset_sort_30.jpg)

## 概要

**本機能を利用するには、feedbackプラグインのLikeモジュールまたはDownloadモジュールを有効にする必要があります。**

- いいね数でソート: Likeモジュールが有効な場合にのみ利用可能
- ダウンロード数でソート: Downloadモジュールが有効な場合にのみ利用可能


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

設定ファイル`feedback_config.json`で本機能をOFFにしてください。

```bash
"custom_sort": {
    "enable": false
}
```

または、`ckan.ini`で設定している場合

```bash
ckan.feedback.custom_sort.enable = False
```

OFFにした場合、dataset一覧画面のソートオプションからいいね数とダウンロード数が削除されます。

>[!IMPORTANT]
>上記の手順でOFFにした場合、画面のソートオプションからは削除されますが、
>URLに直接`?sort=likes_total_i desc`や`?sort=downloads_total_i desc`というパラメータを入力すると、
>ソート機能が動作してしまいます。
>
>これを防ぎ、ソート機能を完全に無効化したい場合は、以下の「ソート機能の完全な切り戻し手順」を実施してください。
>ただし、データセット数によっては時間がかかる可能性があるので注意してください。

### ソート機能の完全な切り戻し手順

本機能を有効化した後に完全に切り戻したい場合（URLパラメータからのアクセスも含めて無効化したい場合）、以下の手順を実施してください。この手順では、Solrから該当フィールド(`downloads_total_i`、`likes_total_i`)を削除し、完全にソート機能を無効化します。

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