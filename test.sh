#!/bin/bash
set -e

# プロジェクトルート（pyproject.tomlのある場所）
PROJECT_ROOT="/srv/app/src_extensions/ckanext-feedback"

# site-packages側（テスト対象コード）
SITE_PACKAGES="/usr/lib/python3.10/site-packages/ckanext/feedback/tests"

cd "$PROJECT_ROOT"

# 環境変数設定
export PYTHONPATH="$SITE_PACKAGES:$PYTHONPATH"
export CKAN_SQLALCHEMY_URL=
export CKAN_DATASTORE_READ_URL=
export CKAN_DATASTORE_WRITE_URL=

# pytestをプロジェクトルートから実行（pyproject.tomlを読み込む）
pytest --rootdir="$PROJECT_ROOT" "$@"
