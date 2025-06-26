# ディレクトリ構成

以下のディレクトリ構造に従って実装を行ってください：

```
ckanext-feedback/
├── ckanext/                      # CKAN拡張機能のメインディレクトリ
│   └── feedback/                 # フィードバック拡張機能
│       ├── assets/               # 静的ファイル（CSS、JS）
│       │   ├── css/              # スタイルシート
│       │   ├── js/               # JavaScriptファイル
│       │   └── webassets.yml     # Webassets設定
│       ├── command/              # CKAN CLIコマンド
│       ├── components/           # CKANコンポーネント
│       ├── controllers/          # Flaskコントローラー
│       │   └── api/              # APIエンドポイント
│       ├── i18n/                 # 国際化ファイル
│       │   └── ja/               # 日本語翻訳
│       │       └── LC_MESSAGES/
│       ├── migration/            # データベースマイグレーション
│       │   └── feedback/
│       │       └── versions/     # マイグレーションファイル
│       ├── models/               # SQLAlchemyモデル
│       ├── services/             # ビジネスロジック
│       │   ├── admin/            # 管理者機能
│       │   ├── common/           # 共通機能
│       │   ├── download/         # ダウンロード機能
│       │   ├── group/            # グループ機能
│       │   ├── organization/     # 組織機能
│       │   ├── ranking/          # ランキング機能
│       │   ├── recaptcha/        # reCAPTCHA機能
│       │   ├── resource/         # リソース機能
│       │   └── utilization/      # 活用事例機能
│       ├── templates/            # Jinja2テンプレート
│       │   ├── admin/            # 管理者画面
│       │   ├── email_notification/ # メール通知テンプレート
│       │   ├── package/          # パッケージ関連
│       │   ├── resource/         # リソース関連
│       │   ├── snippets/         # 再利用可能なテンプレート
│       │   └── utilization/      # 活用事例関連
│       ├── tests/                # テストファイル
│       │   ├── command/          # コマンドテスト
│       │   ├── components/       # コンポーネントテスト
│       │   ├── controllers/      # コントローラーテスト
│       │   ├── models/           # モデルテスト
│       │   ├── services/         # サービステスト
│       │   └── views/            # ビューテスト
│       ├── views/                # Flask Blueprint
│       ├── __init__.py           # パッケージ初期化
│       ├── plugin.py             # CKANプラグイン定義
│       └── README.md             # 拡張機能説明
├── development/                  # 開発環境設定
│   ├── docker-compose.yml        # Docker Compose設定
│   ├── container_setup.sh        # コンテナセットアップ
│   └── feedback_setup.sh         # フィードバックセットアップ
├── docs/                         # ドキュメント
│   ├── assets/                   # ドキュメント用画像
│   └── ja/                       # 日本語ドキュメント
├── .github/                      # GitHub設定
├── .cursor/                      # Cursor設定
├── babel.cfg                     # Babel設定
├── pyproject.toml                # Poetry設定
├── poetry.lock                   # 依存関係ロックファイル
├── feedback_config_sample.json   # 設定サンプル
├── .gitignore                    # Git除外設定
├── .pre-commit-config.yaml       # pre-commit設定
├── .coveragerc                   # カバレッジ設定
├── LICENSE                       # ライセンス
├── README.md                     # プロジェクト説明
└── README-en.md                  # 英語プロジェクト説明
```

### 配置ルール
- ビジネスロジック → `ckanext/feedback/services/`
- データベースモデル → `ckanext/feedback/models/`
- Flaskコントローラー → `ckanext/feedback/controllers/`
- Flask Blueprint → `ckanext/feedback/views/`
- Jinja2テンプレート → `ckanext/feedback/templates/`
- 静的ファイル（CSS/JS） → `ckanext/feedback/assets/`
- 国際化ファイル → `ckanext/feedback/i18n/`
- テストファイル → `ckanext/feedback/tests/`
- データベースマイグレーション → `ckanext/feedback/migration/`
- CKAN CLIコマンド → `ckanext/feedback/command/`
- CKANコンポーネント → `ckanext/feedback/components/`
