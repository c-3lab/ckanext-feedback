import os
import sys
import psycopg2
import click

import ckan.plugins.toolkit as tk

CLEAN = """
    DROP TABLE IF EXISTS utilization CASCADE;
    DROP TABLE IF EXISTS utilization_feedback CASCADE;
    DROP TABLE IF EXISTS utilization_feedback_reply CASCADE;
    DROP TABLE IF EXISTS utilization_summary CASCADE;
    DROP TABLE IF EXISTS resource_feedback CASCADE;
    DROP TABLE IF EXISTS resource_feedback_reply CASCADE;
    DROP TYPE IF EXISTS genre1;
    DROP TYPE IF EXISTS genre2;
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

    CREATE TYPE genre1 AS ENUM ("1", "2");
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

RESOURCE = """
    CREATE TYPE genre2 AS ENUM ("1", "2");
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


@click.group()
def feedback():
    """CLI tool for ckanext-feedback plugin."""


def get_connection(host, port, dbname, user, password):
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
        sys.exit(1)
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
    help="specify the module you want to use from "utilization", "resource", "download"",
)
@click.option(
    "-h", "--host", envvar="POSTGRES_HOST", default="db", help="specify the host name of postgresql"
)
@click.option(
    "-p", "--port", envvar="POSTGRES_PORT", default="5432", help="specify the port number of postgresql"
)
@click.option("-d", "--dbname", envvar="POSTGRES_DB", default="ckan", help="specify the name of postgresql")
@click.option(
    "-u", "--user", envvar="POSTGRES_USER", default="ckan", help="specify the user name of postgresql"
)
@click.option(
    "-P",
    "--password",
    envvar="POSTGRES_PASSWORD",
    default="ckan",
    help="specify the password to connect postgresql",
)
def init(modules, host, port, dbname, user, password):
    with get_connection(host, port, dbname, user, password) as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(CLEAN)
            except Exception as e:
                tk.error_shout(e)
                sys.exit(1)
            else:
                click.secho("Clean all modules: SUCCESS", fg="green", bold=True)

            if not modules:
                try:
                    cursor.execute(UTILIZATION)
                    cursor.execute(RESOURCE)
                    cursor.execute(DOWNLOAD)
                except Exception as e:
                    tk.error_shout(e)
                    sys.exit(1)
                else:
                    click.secho(
                        "Initialize all modules: SUCCESS", fg="green", bold=True
                    )
            elif "utilization" in modules:
                try:
                    cursor.execute(UTILIZATION)
                except Exception as e:
                    tk.error_shout(e)
                    sys.exit(1)
                else:
                    click.secho(
                        "Initialize utilization: SUCCESS", fg="green", bold=True
                    )
            elif "resource" in modules:
                try:
                    cursor.execute(RESOURCE)
                except Exception as e:
                    tk.error_shout(e)
                    sys.exit(1)
                else:
                    click.secho(
                        "Initialize resource: SUCCESS", fg="green", bold=True
                    )
            elif "download" in modules:
                try:
                    cursor.execute(DOWNLOAD)
                except Exception as e:
                    tk.error_shout(e)
                    sys.exit(1)
                else:
                    click.secho(
                        "Initialize download: SUCCESS", fg="green", bold=True
                    )

            connection.commit()
