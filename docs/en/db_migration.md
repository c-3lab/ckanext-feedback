# Updating Models and Reflecting Changes in the DB

When you make changes to the models under `ckanext/feedback/models`, you need to reflect those changes in the actual DB as well.  
This document explains how to update the DB following the [CKAN official best practices](https://docs.ckan.org/en/latest/extensions/best-practices.html).

## Creating Migration Scripts

Files related to migration are located under `ckanext/feedback/migration/feedback/`.  
Move to the directory and execute the `alembic revision` command to create a migration script template in `ckanext/feedback/migration/feedback/versions/`.  
The created script file will have an appropriate revision ID set, so it is usually recommended to edit and use this created file.

If you want to add a message to the migration script you create, add `-m "message"`.

Example:

```bash
cd ckanext/feedback/migration/feedback
alembic revision -m "Add some columns to utilizations table"
```

### Example Template

```python
"""Add some columns to utilizations table

Revision ID: ba229313341d
Revises: 2a8c621c22c8
Create Date: 2024-06-03 09:43:44.127539

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba229313341d'
down_revision = '2a8c621c22c8'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

```

## Editing the Migration Script Filename

You can edit the generated filename to add any prefix you like.  
However, do not change the Revision ID already included in the filename.

## Editing the Migration Script

Usually, the parts to edit are the `upgrade()` and `downgrade()` processes.  
You can make general schema changes such as adding or deleting columns using SQLAlchemy.  
For more details, refer to the [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-second-migration).

## Running the Migration

```bash
docker exec -it ckan-docker-ckan-dev-1 bash -c "command explained below"
```

To apply the migration script, execute `ckan db upgrade -p feedback`.

To revert changes made by applying the migration script, execute `ckan db downgrade -p feedback`.

To `upgrade` or `downgrade` to a specific revision ID, add `-v <revision ID>` to the command.  
Example: `ckan db downgrade -p feedback -v 40bf9a900ef5`

## Checking Migration Status

### Checking the Current Revision ID

```bash
docker exec -it ckan-docker-ckan-dev-1 bash -c "ckan db version -p feedback"
```

### Checking for Pending Migrations

```bash
docker exec -it ckan-docker-ckan-dev-1 bash -c 'export CKAN__PLUGINS="$CKAN__PLUGINS feedback"; ckan db pending-migrations'
```

## Other Commands

If you want to execute the `alembic` command directly, move to `/usr/lib/python3.10/site-packages/ckanext/feedback/migration/feedback` inside the container and execute the appropriate commands below.

### Checking the Current Revision ID

- `alembic current`

### Checking Past Application History

- `alembic history`

## Troubleshooting

If there is a discrepancy between the progress of the revision and the actual DB for any reason, you can manually change the revision settings using `alembic stamp`.  
This is useful when you have created a new migration script to add a column, but the column already exists in the DB, or if the DB has been rolled back for some reason.

Read the [command explanation](https://inspirehep.readthedocs.io/en/latest/alembic.html#alembic-stamp) carefully and proceed with caution.

### Example: Reverting the Revision to init

```bash
cd /usr/lib/python3.10/site-packages/ckanext/feedback/migration/feedback
alembic stamp 40bf9a900ef5
ckan db upgrade -p feedback
```

*`40bf9a900ef5` is the ID of the initial revision `ckanext/feedback/migration/feedback/versions/000_40bf9a900ef5_init.py`.*
