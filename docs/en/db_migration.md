# Model Updates and DB Migration

## Overview

This document describes the procedure for reflecting model changes in `ckanext-feedback` to the database using Alembic.
It complies with [CKAN's official best practices](https://docs.ckan.org/en/latest/extensions/best-practices.html).

---

## Migration Basics

Alembic manages the history of database changes using "revision files (migration files)". Each revision has the following:
#### **Fields that should not be changed**
- **`revision`: Unique revision ID (automatically generated)**
- **`down_revision`: Parent revision ID (automatically generated, must match "Revises" in docstring)**
#### Fields to be modified
- `upgrade()`: Operations to perform when applying the revision (e.g., add column, create index)
- `downgrade()`: Operations to perform when rolling back (e.g., drop column, drop index)
---
## Prerequisites

* This assumes running the CKAN core and this Extension in the following Docker environment:
  * OS: Linux
  * Distribution: Ubuntu 22.04
  * Python 3.10.13
  * Docker 27.4.0

  **Please replace `REPO_ROOT` and similar variables according to your development environment.**
---

### Creating Migration Scripts
```bash
cd "$REPO_ROOT/ckanext/feedback/migration/feedback"
alembic revision 
```
- To add a message to the migration script, append `-m "message"`.
```bash 
alembic revision -m "message"
```
- Migration-related files are placed under `$REPO_ROOT/ckanext/feedback/migration/feedback` in the repository.
- Generated file: `versions/<revision_id>_<message>.py`
  - Verify that `down_revision` points to the correct parent revision and matches "Revises" in the docstring.

### Template Example:
```python
"""empty message

Revision ID: abcdef123456
Revises: 123456abcdef
Create Date: 2025-01-01 00:00:00.00000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abcdef123456'
down_revision = '123456abcdef'
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
```
### Template Example with Message using `-m "Sample Message"`:
```python
"""Sample Message

Revision ID: abcdef123456
Revises: 123456abcdef
Create Date: 2025-01-01 00:00:00.00000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abcdef123456'
down_revision = '123456abcdef'
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
```
---

## Editing Migration Scripts
- **Typically, you only need to edit the content of `upgrade()` and `downgrade()`.**  
- You can edit the generated filename to add an optional prefix.
- Common schema changes such as adding or removing columns using SQLAlchemy are possible.
- For more details, refer to the [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-second-migration).

### Example: Creating/Dropping a New Table
```python
def upgrade():
    op.create_table(
        'example_table',
        sa.Column('id', sa.Text, primary_key=True, nullable=False),
        sa.Column('created', sa.TIMESTAMP, nullable=True),
    )

def downgrade():
    op.drop_table('example_table')
```

### Example: Adding a Column
```python
def upgrade():
    op.add_column('utilizations', sa.Column('summary', sa.Text(), nullable=True))
    op.execute("UPDATE utilizations SET summary = '' WHERE summary IS NULL")
    op.alter_column('utilizations', 'summary', nullable=False)

def downgrade():
    op.drop_column('utilizations', 'summary')
```

### Example: Modifying an Enum
```python
def downgrade():
    op.execute('DROP TYPE IF EXISTS your_enum_type;')
```

---

## Executing Migrations

### Upgrade
```bash
# To the latest version
ckan db upgrade --plugin feedback
```
### Downgrade
```bash
# Downgrade to before the feedback plugin was applied
ckan db downgrade --plugin feedback
# Downgrade to a specific revision
ckan db downgrade --plugin feedback -v <revision_id>
```

---

## Checking Migration Status

### Check Current Revision ID
```bash
ckan db version --plugin feedback
```

### Check for Pending Migrations
```bash
ckan db pending-migrations
```

## Executing Alembic Commands Directly
```bash
cd "$REPO_ROOT/ckanext/feedback/migration/feedback"
# Check current revision ID
alembic current
# Check past application history
alembic history
```
---

## Troubleshooting

### Adjusting Alembic Migration History
This is useful when the database structure and Alembic migration history become out of sync.  
You can use the `alembic stamp` command to adjust only the Alembic version history without changing the database structure.  
Please read the [command explanation](https://inspirehep.readthedocs.io/en/latest/alembic.html#alembic-stamp) carefully and work cautiously.  
```bash
# Change to the latest version
alembic stamp head
```
```bash
# Change to a specific version
alembic stamp <revision_id>
```


