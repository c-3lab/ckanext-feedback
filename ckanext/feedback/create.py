from sqlalchemy import *

# Declare the target database connection string
engine = create_engine("postgresql+psycopg2://ckan:ckan@db:5432/ckan")
# Create a metadata object
metadata_obj = MetaData()
# Bind the database-connected engine to the metadata object
metadata_obj.bind = engine
# Get all tables from ckan DB
metadata_obj.reflect()

# Declare the utilization table
utilization = Table(
    "utilization",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("resource_id", Text, ForeignKey("resource_comment.resource_id"), nullable=False),
    Column("title", Text),
    Column("description", Text),
    Column("created", TIMESTAMP),
    Column("approval", BOOLEAN, default=False),
    Column("approved", TIMESTAMP),
    Column("approval_user_id", Text, ForeignKey("resource_comment.approval_user_id"))
)

# Declare the utilization_comment table
utilization_comment = Table(
    "utilization_comment",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("utilization_id", Text, ForeignKey("issue_resolution.utilization_id"), nullable=False),
    Column("category", Enum("承認待ち", "承認済", name="category_enum"), nullable=False),
    Column("content", Text),
    Column("created", TIMESTAMP),
    Column("approval", BOOLEAN, default=False),
    Column("approved", TIMESTAMP),
    Column("approval_user_id", Text, ForeignKey("issue_resolution.creator_user_id"), ForeignKey("resource_comment_reply.creator_user_id"))
)

# Declare the issue_resolution table
issue_resolution = Table(
    "issue_resolution",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("utilization_id", Text, ForeignKey("utilization_comment.utilization_id"), nullable=False),
    Column("description", Text),
    Column("created", TIMESTAMP),
    Column("creator_user_id", Text, ForeignKey("utilization_comment.approval_user_id"), ForeignKey("resource_comment_reply.creator_user_id"))
)

# Declare the issue_resolution_summary table
issue_resolution_summary = Table(
    "issue_resolution_summary",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("utilization_id", Text, ForeignKey("utilization.id"), nullable=False),
    Column("issue_resolution", Integer),
    Column("created", TIMESTAMP),
    Column("updated", TIMESTAMP)
)

# Declare the resource_comment table
resource_comment = Table(
    "resource_comment",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("resource_id", Text, ForeignKey("utilization.resource_id"), nullable=False),
    Column("category", Enum("承認待ち", "承認済", name="category_enum"), nullable=False),
    Column("content", Text),
    Column("rating", Integer),
    Column("created", TIMESTAMP),
    Column("approval", BOOLEAN, default=False),
    Column("approved", TIMESTAMP),
    Column("approval_user_id", Text, ForeignKey("utilization.approval_user_id"))
)

# Declare the resource_comment_reply table
resource_comment_reply = Table(
    "resource_comment_reply",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("resource_comment_id", Text, ForeignKey("resource_comment.id"), nullable=False),
    Column("content", Text),
    Column("created", TIMESTAMP),
    Column("creator_user_id", Text, ForeignKey("utilization_comment.approval_user_id"), ForeignKey("issue_resolution.creator_user_id"))
)

# Declare the utilization_summary table
utilization_summary = Table(
    "utilization_summary",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("resource_id", Text, ForeignKey("resource.id"), nullable=False),
    Column("utilization", Integer),
    Column("review", Integer),
    Column("created", TIMESTAMP),
    Column("updated", TIMESTAMP)
)

# Declare the resource_comment_summary table
resource_comment_summary = Table(
    "resource_comment_summary",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("resource_id", Text, ForeignKey("resource.id"), nullable=False),
    Column("comment", Integer),
    Column("rating", Integer),
    Column("created", TIMESTAMP),
    Column("updated", TIMESTAMP)
)

# Declare the download_summary table
download_summary = Table(
    "download_summary",
    metadata_obj,
    Column("id", Text, primary_key=True, nullable=False),
    Column("resource_id", Text, ForeignKey("resource.id"), nullable=False),
    Column("download", Integer),
    Column("created", TIMESTAMP),
    Column("updated", TIMESTAMP)
)

#@create.command(name=u'create', short_help=u'データベースにckanext-feedback用のテーブルを作成します。')
# Method to show all tables currently recognized by SQLAlchemy
def show_tables():
    for t in metadata_obj.sorted_tables:
        print(t.name)

# Run show_tables()
#show_tables()

try:
    metadata_obj.create_all(engine)
    print("テーブルの作成が成功しました。")
except (Exception) as e:
    print("テーブルの作成が失敗しました。理由：", e)
    engine.dispose()
    print("接続を閉じました。")