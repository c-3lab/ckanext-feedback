# 技術スタック

## コア技術
- Python: ^3.8.16
- CKAN: 2.10.3

## フロントエンド
- JavaScript (Vanilla JS)
- CSS (Vanilla CSS)
- Webassets: 0.12.1
- Jinja2: 3.1.2

## バックエンド
- Flask: 2.0.3
- SQLAlchemy: ^1.3.5
- PostgreSQL (psycopg2: 2.9.3)
- Alembic: 1.13.1

## 開発ツール
- Poetry: ^1.0.0
- pytest: ^7.2.1
- mypy: ^0.991
- pre-commit: 3.5.0
- Babel: 2.10.3 (国際化)
- Black (コードフォーマッター)
- isort (インポート整理)
- flake8 (リンター)

---

# API バージョン管理
## 重要な制約事項

- **CKAN拡張機能の標準構造**: CKANの拡張機能開発ガイドラインに従った構造
- **Flask Blueprint**: views/ディレクトリでBlueprintを定義
- **SQLAlchemyモデル**: models/ディレクトリでデータベースモデルを定義
- **サービス層**: services/ディレクトリでビジネスロジックを分離
- **テンプレート**: Jinja2テンプレートを使用
- **静的ファイル**: Webassetsで管理

## 実装規則

- CKANプラグインの標準的なディレクトリ構造に従う
- ビジネスロジックはservices/ディレクトリに配置
- データベース操作はmodels/ディレクトリで定義
- フロントエンドはVanilla JavaScript/CSSを使用
- 国際化はi18n/ディレクトリで管理
- テストは各機能に対応するディレクトリに配置
