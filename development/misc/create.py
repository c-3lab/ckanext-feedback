import psycopg2
import click

DB_HOST = "db"
DB_PORT = "5432"
DB_NAME = "ckan"
DB_USER = "ckan"
DB_PASS = "ckan"

UTILIZATION = """
    CREATE TABLE utilization (
        id TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        title TEXT,
        url TEXT,
        description TEXT,
        created TIMESTAMP,
        approval BOOLEAN DEFAULT false,
        approved TIMESTAMP,
        PRIMARY KEY (id),
        FOREIGN KEY (resource_id) REFERENCES resource (id)
    );
    """

UTILIZATION_SUMMARY = """
    CREATE TABLE utilization_summary (
        id TEXT NOT NULL,
        utilization_id TEXT NOT NULL,
        issue_resolution INTEGER,
        created TIMESTAMP,
        updated TIMESTAMP,
        PRIMARY KEY (id),
        FOREIGN KEY (utilization_id) REFERENCES utilization (id)
    );
    """

UTILIZATION_FEEDBACK = """
    CREATE TYPE genre1 AS ENUM ('1', '2');
    CREATE TABLE utilization_feedback (
        id TEXT NOT NULL,
        utilization_id TEXT NOT NULL,
        type genre1 NOT NULL,
        desctiption TEXT,
        created TIMESTAMP,
        approval BOOLEAN DEFAULT false,
        approved TIMESTAMP,
        PRIMARY KEY (id),
        FOREIGN KEY (utilization_id) REFERENCES utilization (id)
    );
    """

ISSUE_RESOLUTION = """
    CREATE TABLE issue_resolution (
        id TEXT NOT NULL,
        utilization_id TEXT NOT NULL,
        description TEXT,
        created TIMESTAMP,
        creator_user_id TEXT,
        PRIMARY KEY (id),
        FOREIGN KEY (utilization_id) REFERENCES utilization (id)
    );
    """

UTILIZATION_FEEDBACK_REPLY = """
    CREATE TABLE utilization_feedback_reply (
        id TEXT NOT NULL,
        utilization_feedback_id TEXT NOT NULL,
        description TEXT,
        created TIMESTAMP,
        creator_user_id TEXT,
        PRIMARY KEY (id),
        FOREIGN KEY (utilization_feedback_id) REFERENCES utilization_feedback (id)
    );
    """

RESOURCE_FEEDBACK = """
    CREATE TYPE genre2 AS ENUM ('1', '2');
    CREATE TABLE resource_feedback (
        id TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        type genre2 NOT NULL,
        description TEXT,
        rating INTEGER,
        created TIMESTAMP,
        approval BOOLEAN DEFAULT false,
        approved TIMESTAMP,
        PRIMARY KEY (id),
        FOREIGN KEY (resource_id) REFERENCES resource (id)
    );
    """

RESOURCE_FEEDBACK_REPLY = """
    CREATE TABLE resource_feedback_reply (
        id TEXT NOT NULL,
        resource_feedback_id TEXT NOT NULL,
        desctiption TEXT,
        created TIMESTAMP,
        created_user_id TEXT,
        PRIMARY KEY (id),
        FOREIGN KEY (resource_feedback_id) REFERENCES resource_feedback (id)
    );
    """

RESOURCE_SUMMARY = """
    CREATE TABLE resource_summary (
        id TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        utilization INTEGER,
        download INTEGER,
        created TIMESTAMP,
        updated TIMESTAMP,
        PRIMARY KEY (id),
        FOREIGN KEY (resource_id) REFERENCES resource (id)
    );
    """


@click.group(short_help="create tables to use extension")
def create():
    pass


def get_connection():
    return psycopg2.connect(
        "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
            user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT, dbname=DB_NAME
        )
    )


@create.command(name="table", short_help="create tables in ckan db.")
@click.option(
    "-u",
    "--utilization",
    is_flag=True,
    help=(
        "create tables which are "
        "utilization, utilization_summary, "
        "utilization_feedback, issue_resolution, "
        "utilization_feedback_reply."
    ),
)
@click.option(
    "-r",
    "--resource",
    is_flag=True,
    help=("create tables which are " "resource_feedback, resource_feedback_reply."),
)
@click.option(
    "-c", "--count", is_flag=True, help=("create table which is " "resource_summary")
)
@click.option("-A", "--alltables", is_flag=True)
def table(alltables, utilization, resource, count):

    with get_connection() as conn:
        with conn.cursor() as cur:

            if alltables:
                utilization = True
                resource = True
                count = True

            if utilization:
                cur.execute(UTILIZATION)
                cur.execute(UTILIZATION_SUMMARY)
                cur.execute(UTILIZATION_FEEDBACK)
                cur.execute(ISSUE_RESOLUTION)
                cur.execute(UTILIZATION_FEEDBACK_REPLY)

            if resource:
                cur.execute(RESOURCE_FEEDBACK)
                cur.execute(RESOURCE_FEEDBACK_REPLY)

            if count:
                cur.execute(RESOURCE_SUMMARY)

            conn.commit()
