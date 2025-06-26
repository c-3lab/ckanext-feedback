# CKAN Feedback Extension データベースモデル定義

このドキュメントは、ckanext-feedback拡張機能で使用されるデータベーステーブルのモデル定義をまとめたものです。

## テーブル一覧

### 1. resource_comment
リソースコメントを管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | コメントの一意識別子 |
| resource_id | Text | FOREIGN KEY (resource.id), NOT NULL | リソースID |
| category | Enum(ResourceCommentCategory) | - | コメントカテゴリ（Request/Question/Thank） |
| content | Text | - | コメント内容 |
| rating | Integer | - | 評価値 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| approval | BOOLEAN | DEFAULT False | 承認フラグ |
| approved | TIMESTAMP | - | 承認日時 |
| approval_user_id | Text | FOREIGN KEY (user.id) | 承認者ID |

**リレーションシップ:**
- `resource`: Resourceテーブルとの関連
- `approval_user`: Userテーブルとの関連（承認者）
- `reply`: ResourceCommentReplyテーブルとの1対1関連

### 2. resource_comment_reply
リソースコメントの返信を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | 返信の一意識別子 |
| resource_comment_id | Text | FOREIGN KEY (resource_comment.id), NOT NULL | コメントID |
| content | Text | - | 返信内容 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| creator_user_id | Text | FOREIGN KEY (user.id) | 作成者ID |

**リレーションシップ:**
- `resource_comment`: ResourceCommentテーブルとの関連
- `creator_user`: Userテーブルとの関連（作成者）

### 3. resource_comment_summary
リソースコメントの集計情報を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | 集計の一意識別子 |
| resource_id | Text | FOREIGN KEY (resource.id), NOT NULL | リソースID |
| comment | Integer | DEFAULT 0 | 総コメント数 |
| rating_comment | Integer | DEFAULT 0 | 評価付きコメント数 |
| rating | Float | DEFAULT 0 | 平均評価値 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| updated | TIMESTAMP | - | 更新日時 |

**リレーションシップ:**
- `resource`: Resourceテーブルとの関連

### 4. utilization
リソースの活用事例を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | 活用事例の一意識別子 |
| resource_id | Text | FOREIGN KEY (resource.id), NOT NULL | リソースID |
| title | Text | - | 活用事例のタイトル |
| url | Text | - | 活用事例のURL |
| description | Text | - | 活用事例の説明 |
| comment | Integer | DEFAULT 0 | コメント数 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| approval | BOOLEAN | DEFAULT False | 承認フラグ |
| approved | TIMESTAMP | - | 承認日時 |
| approval_user_id | Text | FOREIGN KEY (user.id) | 承認者ID |

**リレーションシップ:**
- `resource`: Resourceテーブルとの関連
- `approval_user`: Userテーブルとの関連（承認者）
- `comments`: UtilizationCommentテーブルとの1対多関連
- `issue_resolutions`: IssueResolutionテーブルとの1対多関連
- `issue_resolution_summary`: IssueResolutionSummaryテーブルとの1対1関連

### 5. utilization_comment
活用事例のコメントを管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | コメントの一意識別子 |
| utilization_id | Text | FOREIGN KEY (utilization.id), NOT NULL | 活用事例ID |
| category | Enum(UtilizationCommentCategory) | NOT NULL | コメントカテゴリ（Request/Question/Thank） |
| content | Text | - | コメント内容 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| approval | BOOLEAN | DEFAULT False | 承認フラグ |
| approved | TIMESTAMP | - | 承認日時 |
| approval_user_id | Text | FOREIGN KEY (user.id) | 承認者ID |

**リレーションシップ:**
- `utilization`: Utilizationテーブルとの関連
- `approval_user`: Userテーブルとの関連（承認者）

### 6. utilization_summary
活用事例の集計情報を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | 集計の一意識別子 |
| resource_id | Text | FOREIGN KEY (resource.id), NOT NULL | リソースID |
| utilization | Integer | DEFAULT 0 | 活用事例数 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| updated | TIMESTAMP | - | 更新日時 |

**リレーションシップ:**
- `resource`: Resourceテーブルとの関連

### 7. resource_like
リソースのいいね情報を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | いいねの一意識別子 |
| resource_id | Text | FOREIGN KEY (resource.id), NOT NULL | リソースID |
| like_count | Integer | DEFAULT 0 | いいね数 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| updated | TIMESTAMP | - | 更新日時 |

**リレーションシップ:**
- `resource`: Resourceテーブルとの関連

### 8. resource_like_monthly
リソースの月次いいね情報を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | 月次いいねの一意識別子 |
| resource_id | Text | FOREIGN KEY (resource.id), NOT NULL | リソースID |
| like_count | Integer | - | 月次いいね数 |
| created | TIMESTAMP | - | 作成日時 |
| updated | TIMESTAMP | - | 更新日時 |

**リレーションシップ:**
- `resource`: Resourceテーブルとの関連

### 9. download_summary
リソースのダウンロード集計情報を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL | ダウンロード集計の一意識別子 |
| resource_id | Text | FOREIGN KEY (resource.id), NOT NULL | リソースID |
| download | Integer | - | ダウンロード数 |
| created | TIMESTAMP | - | 作成日時 |
| updated | TIMESTAMP | - | 更新日時 |

**リレーションシップ:**
- `resource`: Resourceテーブルとの関連

### 10. download_monthly
リソースの月次ダウンロード情報を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL | 月次ダウンロードの一意識別子 |
| resource_id | Text | FOREIGN KEY (resource.id), NOT NULL | リソースID |
| download_count | Integer | - | 月次ダウンロード数 |
| created | TIMESTAMP | - | 作成日時 |
| updated | TIMESTAMP | - | 更新日時 |

**リレーションシップ:**
- `resource`: Resourceテーブルとの関連

### 11. issue_resolution
活用事例の問題解決情報を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | 問題解決の一意識別子 |
| utilization_id | Text | FOREIGN KEY (utilization.id), NOT NULL | 活用事例ID |
| description | Text | - | 問題解決の説明 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| creator_user_id | Text | FOREIGN KEY (user.id) | 作成者ID |

**リレーションシップ:**
- `utilization`: Utilizationテーブルとの関連
- `creator_user`: Userテーブルとの関連（作成者）

### 12. issue_resolution_summary
活用事例の問題解決集計情報を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | 問題解決集計の一意識別子 |
| utilization_id | Text | FOREIGN KEY (utilization.id), NOT NULL | 活用事例ID |
| issue_resolution | Integer | - | 問題解決数 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| updated | TIMESTAMP | - | 更新日時 |

**リレーションシップ:**
- `utilization`: Utilizationテーブルとの関連

### 13. resource_comment_reactions
リソースコメントに対する管理者の反応を管理するテーブル

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | Text | PRIMARY KEY, NOT NULL, DEFAULT uuid.uuid4 | 問題解決集計の一意識別子 |
| resource_comment_id | Text | FOREIGN KEY (resource_comment.id), NOT NULL | 活用事例ID |
| response_status | Enum(ResourceCommentResponseStatus) | - | レスポンスステータス（StatusNone/NotStarted/InProgress/Completed/Rejected） |
| admin_liked | BOOLEAN | DEFAULT False | 管理者からの高評価 |
| created | TIMESTAMP | DEFAULT datetime.now | 作成日時 |
| updated | TIMESTAMP | - | 更新日時 |
| updater_user_id | Text | - | 更新者ID |

**リレーションシップ**
- `resource_comment`: ResourceCommentテーブルとの関連
- `updater_user`: Userテーブルとの関連（更新者）

## 列挙型（Enum）定義

### ResourceCommentCategory / UtilizationCommentCategory / CommentCategory
- `REQUEST`: 'Request'
- `QUESTION`: 'Question'
- `THANK`: 'Thank'

### ResourceCommentResponseStatus
- `STATUS_NONE`: 'StatusNone'
- `NOT_STARTED`: 'NotStarted'
- `IN_PROGRESS`: 'InProgress'
- `COMPLETED`: 'Completed'
- `REJECTED`: 'Rejected'

## 外部キー制約

すべてのテーブルは以下の外部キー制約を持ちます：

- **resource.id**: `ON UPDATE CASCADE, ON DELETE CASCADE`
- **user.id**: `ON UPDATE CASCADE, ON DELETE SET NULL`
- **resource_comment.id**: `ON UPDATE CASCADE, ON DELETE CASCADE`
- **utilization.id**: `ON UPDATE CASCADE, ON DELETE CASCADE`

## 注意事項

- すべてのテーブルは `Base` クラスを継承しており、SQLAlchemy ORMを使用しています
- 主キーは基本的にUUIDを使用しています（一部のテーブルを除く）
- タイムスタンプフィールドは `datetime.now` をデフォルト値として使用しています
- 承認機能を持つテーブルは `approval` と `approved` フィールドを持っています 