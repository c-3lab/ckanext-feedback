import os
import psycopg2
import click

import ckan.plugins.toolkit as tk

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ckan")
DB_USER = os.getenv("POSTGRES_USER", "ckan")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "ckan")

UTILIZATION_CLEAN = """
    DROP TABLE IF EXISTS utilization CASCADE;
    DROP TABLE IF EXISTS utilization_feedback CASCADE;
    DROP TABLE IF EXISTS utilization_feedback_reply CASCADE;
    DROP TABLE IF EXISTS utilization_summary CASCADE;
    DROP TYPE IF EXISTS genre1;
    """

REVIEW_CLEAN = """
    DROP TABLE IF EXISTS resource_feedback CASCADE;
    DROP TABLE IF EXISTS resource_feedback_reply CASCADE;
    DROP TYPE IF EXISTS genre2;
    """

DOWNLOAD_CLEAN = """
    DROP TABLE IF EXISTS utilization_summary CASCADE;
    """

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

    CREATE TYPE genre1 AS ENUM ('1', '2');
    CREATE TABLE utilization_feedback (
        id TEXT NOT NULL,
        utilization_id TEXT NOT NULL,
        type genre1 NOT NULL,
        description TEXT,
        created TIMESTAMP,
        approval BOOLEAN DEFAULT false,
        approved TIMESTAMP,
        PRIMARY KEY (id),
        FOREIGN KEY (utilization_id) REFERENCES utilization (id)
    );

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

REVIEW = """
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

    CREATE TABLE resource_feedback_reply (
        id TEXT NOT NULL,
        resource_feedback_id TEXT NOT NULL,
        description TEXT,
        created TIMESTAMP,
        creator_user_id TEXT,
        PRIMARY KEY (id),
        FOREIGN KEY (resource_feedback_id) REFERENCES resource_feedback (id)
        
    );
    """

DOWNLOAD = """
    CREATE TABLE utilization_summary (
        id TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        utilization INTEGER,
        download INTEGER,
        issue_resolution INTEGER,
        created TIMESTAMP,
        updated TIMESTAMP,
        PRIMARY KEY (id),
        FOREIGN KEY (resource_id) REFERENCES resource (id)
    );
    """


@click.group(short_help="create tables to use extension")
def feedback():
    pass


def get_connection(user, password, host, port, name):
    try:
        connector = psycopg2.connect(
            "postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}".format(
                db_user=user,
                db_password=password,
                db_host=host,
                db_port=port,
                db_name=name,
            )
        )
    except Exception as e:
        tk.error_shout(e)
    else:
        return connector


@feedback.command(
    name="init", short_help="create tables in ckan db to activate modules."
)
@click.option(
    "-m",
    "--modules",
    multiple=True,
    type=click.Choice(["utilization", "resource", "download"]),
    help="specify the module you want to use from 'utilization', 'resource', 'download'",
)
@click.option(
    "-h", "--host", default=DB_HOST, help="specify the host name of postgresql"
)
@click.option(
    "-p", "--port", default=DB_PORT, help="specify the port number of postgresql"
)
@click.option("-n", "--name", default=DB_NAME, help="specify the name of postgresql")
@click.option(
    "-u", "--user", default=DB_USER, help="specify the user name of postgresql"
)
@click.option(
    "-pw",
    "--password",
    default=DB_PASS,
    help="specify the password to connect postgresql",
)
def table(modules, host, port, name, user, password):
    with get_connection(user, password, host, port, name) as conn:
        with conn.cursor() as cur:

            if bool(modules):
                if "utilization" in modules:
                    try:
                        cur.execute(UTILIZATION_CLEAN)
                        cur.execute(UTILIZATION)
                        conn.commit()
                    except Exception as e:
                        tk.error_shout(e)
                    else:
                        click.secho(
                            "Initialize utilization: SUCCESS", fg="green", bold=True
                        )
                if "resource" in modules:
                    try:
                        cur.execute(REVIEW_CLEAN)
                        cur.execute(REVIEW)
                        conn.commit()
                    except Exception as e:
                        tk.error_shout(e)
                    else:
                        click.secho(
                            "Initialize resource: SUCCESS", fg="green", bold=True
                        )
                if "download" in modules:
                    try:
                        cur.execute(DOWNLOAD_CLEAN)
                        cur.execute(DOWNLOAD)
                        conn.commit()
                    except Exception as e:
                        tk.error_shout(e)
                    else:
                        click.secho(
                            "Initialize download: SUCCESS", fg="green", bold=True
                        )
            else:
                try:
                    cur.execute(UTILIZATION_CLEAN)
                    cur.execute(UTILIZATION)
                    cur.execute(REVIEW_CLEAN)
                    cur.execute(REVIEW)
                    cur.execute(DOWNLOAD_CLEAN)
                    cur.execute(DOWNLOAD)
                    conn.commit()
                except Exception as e:
                    tk.error_shout(e)
                else:
                    click.secho(
                        "Initialize all modules: SUCCESS", fg="green", bold=True
                    )
