# データセットランキング取得API

## 概要

本APIは、指定した条件に基づき、データセットのランキング情報を取得します。  
ランキングは、指定した期間・条件に応じて集計された利用数に基づいて算出されます。

## エンドポイント

GET /api/3/action/datasets_ranking

## 入力パラメータ

| パラメータ名        | 意味                         | 型    | 必須 | デフォルト値            | 備考                                                     |
| ------------------- | ---------------------------- | ----- | ---- | ----------------------- | -------------------------------------------------------- |
| top_ranked_limit     | 取得件数                     | int   | 任意 | 5                       | ランキングの上位何件を取得するかを指定します。           |
| period_months_ago    | 相対期間（過去Xヶ月）        | int   | 任意[^1] | なし                    | 例: `3`を指定すると、直近3ヶ月間の集計を取得します。     |
| start_year_month     | 固定期間の開始年月          | string| 任意[^1] | なし                    | 例: `2024-01` で2024年1月が開始。  
| end_year_month       | 固定期間の終了年月          | string| 任意[^1] | なし                    | 例: `2024-03` で2024年3月が終了。開始・終了ともに指定した場合、その期間で集計します。 |
| aggregation_metric   | 集計指標                     | string| 任意 | "download"              |  |
| organization_name    | 自治体名による絞り込み       | string| 任意 | なし  |   |

[^1]: period_months_ago, start_year_month, end_year_month のいずれかの指定が必須

## 出力（レスポンス）の説明

| パラメータ名        | 意味                         | 型 | 備考                                                     |
| ------------------- | ---------------------------- | ----- |  -------------------------------------------------------- |
| help     | APIのヘルプを返すURL                     | string   | このURLをGETでアクセスすると、APIの概略を示すJSONを取得できる  |
| success    | APIの実行成功/失敗を示すブール値        | bool  |   |
| result     | 結果データ        | object | |    
| datasets_ranking  | データセットランキング | array| |
| rank | 順位 | int | 首位の場合、1を返す |
| group_name | データセットが所属するグループの名前 | string |  |
| group_title | データセットが所属するグループのタイトル | string |  |
| dataset_title | データセットのタイトル | string |  |
| dataset_notes | データセットの説明文 | string |  |
| dataset_link | データセットのURL | string |  |
| download_count_by_period | 集計期間内のダウンロード数 | int | aggregation_metric として download を指定した場合に存在する |
| total_download_count | 全期間のダウンロード数 | int | aggregation_metric として download を指定した場合に存在する |

## レスポンス例

以下、コマンドラインから `curl https://your-ckan-site/api/3/action/datasets_ranking?period_months_ago=3` とした場合に、APIが返すJSONの例です。

```json
{
  "help": "https://your-ckan-site/api/3/action/help_show?name=datasets_ranking",
  "success": true,
  "result": {
    "datasets_ranking": [
      {
        "rank": 1,
        "group_name": "o0001",
        "group_title": "Organization name1",
        "dataset_title": "Dataset name11",
        "dataset_notes": "Dataset notes",
        "dataset_link": "https://your-ckan-site/dataset/d11",
        "download_count_by_period": 123,
        "total_download_count": 6789,
      },
      {
        "rank": 2,
        "group_name": "o0002",
        "group_title": "Organization name2",
        "dataset_title": "Dataset name21",
        "dataset_notes": "Dataset explanation",
        "dataset_link": "https://your-ckan-site/dataset/d21",
        "download_count_by_period": 121,
        "total_download_count": 7000,
      },
      // ...
    ]
  }
}
```

### Unicodeのエスケープシーケンスについて（例：\u65e5\u672c\u8a9e）
APIのレスポンスに日本語が含まれている場合、curl コマンドなどで取得すると、文字コードの影響により日本語が正しく表示されず、エスケープされた形式で出力されることがあります。  
これは、curlの使用環境やターミナルの設定によるもので、API自体の問題ではありません。必要に応じて、ツールやエディタで文字コードを適切に変換・表示することで、日本語を正しく確認できます。たとえば、
 - jqを使って整形表示（Unicodeのでコードを含む）する
 - 出力をファイルに保存して、UTF-8対応のエディタで開く
 - Pythonなどのスクリプトででコードして確認する

## エラー概説

success が false の場合、error オブジェクトが含まれ、エラーに関する情報が提供されます。
エラーは、主に以下のようなケースで発生します。

- 必須パラメータの指定不足 period_months_ago、start_year_month、end_year_month のいずれかを指定しない場合、エラーとなります。

- パラメータ形式の不正 日付形式が YYYY-MM に合致しない、または period_months_ago に不正な値（負数など）が指定された場合、エラーとなります。


### エラーオブジェクトの主なフィールド
| パラメータ名        | 意味                         | 型 | 備考                                                     |
| ------------------- | ---------------------------- | ----- |  -------------------------------------------------------- |
| message     | エラーの内容を示すメッセージ  | string   |   |
| __type    | エラーの種類        | string  | 例: "Validation Error" |

## エラーレスポンス例

以下にエラー発生時のレスポンス例を示します。

### 必須パラメータ未指定エラーの例
```
{
  "help": "https://your-ckan-site/api/3/action/help_show?name=datasets_ranking",
  "success": false,
  "error": {
    "message": "Please set the period for aggregation.",
    "__type": "Validation Error"
  }
}
```

### パラメータ形式不正エラーの例

```
{
  "help": "https://your-ckan-site/api/3/action/help_show?name=datasets_ranking",
  "success": false,
  "error": {
    "message": "Invalid format for 'start_year_month'. Expected format is YYYY-MM.",
    "__type": "Validation Error"
  }
}
```