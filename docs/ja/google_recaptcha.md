# google_reCAPTCHA

各種投稿のスパム対策機能です。</br>
以下の投稿実行時に Google reCAPTCHA v3 を使用した検証を行い、算出されたscoreが閾値未満の場合はユーザへ投稿実行の再試行を要求します。

- Utilization投稿
- Utilizationコメント投稿
- Resourceコメント投稿

## 設定方法
`ckan.ini`内にて以下の設定項目を追記する事で有効化されます。</br>
また、必要なサイトキー、シークレットキーは、[公式ガイド](https://developers.google.com/recaptcha/intro?hl=ja)に従ってv3のものを取得してください。

```ini
ckan.feedback.recaptcha.enable = true
ckan.feedback.recaptcha.publickey = サイトキー
ckan.feedback.recaptcha.privatekey = シークレットキー
```

また、閾値に関しては内部的に独自のデフォルト値として0.5が設定されています。そのため、検証結果の score が 0.5 未満の場合はユーザに再試行を要求しますが、閾値を任意の値に変更したい場合は以下の設定項目を追記してください。

```ini
ckan.feedback.recaptcha.score_threshold = 0.0 ~ 1.0
```

適切な閾値を判断する方法については [公式ドキュメント スコアの解釈](https://developers.google.com/recaptcha/docs/v3?hl=ja#interpreting_the_score)を参照してください。</br>
その他、google reACAPTCHA v3の詳しい仕様については[公式ドキュメント](https://developers.google.com/recaptcha/docs/v3?hl=ja)を参照してください。