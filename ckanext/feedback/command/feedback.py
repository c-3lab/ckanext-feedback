import sys
import psycopg2
import click

import ckan.plugins.toolkit as tk


@click.group()
def feedback():
    '''CLI tool for ckanext-feedback plugin.'''


def get_connection(host, port, dbname, user, password):
    try:
        connector = psycopg2.connect(
            f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
        )
    except Exception as e:
        tk.error_shout(e)
        sys.exit(1)
    else:
        return connector


@feedback.command(
    name='init', short_help='create tables in ckan db to activate modules.'
)
@click.option(
    '-m',
    '--modules',
    multiple=True,
    type=click.Choice(['utilization', 'resource', 'download']),
    help='specify the module you want to use from utilization, resource, download',
)
@click.option(
    '-h',
    '--host',
    envvar='POSTGRES_HOST',
    default='db',
    help='specify the host name of postgresql',
)
@click.option(
    '-p',
    '--port',
    envvar='POSTGRES_PORT',
    default=5432,
    help='specify the port number of postgresql',
)
@click.option(
    '-d',
    '--dbname',
    envvar='POSTGRES_DB',
    default='ckan',
    help='specify the name of postgresql',
)
@click.option(
    '-u',
    '--user',
    envvar='POSTGRES_USER',
    default='ckan',
    help='specify the user name of postgresql',
)
@click.option(
    '-P',
    '--password',
    envvar='POSTGRES_PASSWORD',
    default='ckan',
    help='specify the password to connect postgresql',
)
def init(modules, host, port, dbname, user, password):
    with get_connection(host, port, dbname, user, password) as connection:
        with connection.cursor() as cursor:
            try:
                if not modules:
                    _drop_utilization_tables(cursor)
                    _drop_resource_tables(cursor)
                    _drop_download_tables(cursor)
                    _create_utilization_tables(cursor)
                    _create_resource_tabels(cursor)
                    _create_download_tables(cursor)
                    click.secho(
                        'Initialize all modules: SUCCESS', fg='green', bold=True
                    )
                elif 'utilization' in modules:
                    _drop_utilization_tables(cursor)
                    _create_utilization_tables(cursor)
                    click.secho(
                        'Initialize utilization: SUCCESS', fg='green', bold=True
                    )
                elif 'resource' in modules:
                    _drop_resource_tables(cursor)
                    _create_resource_tabels(cursor)
                    click.secho('Initialize resource: SUCCESS', fg='green', bold=True)
                elif 'download' in modules:
                    _drop_download_tables(cursor)
                    _create_download_tables(cursor)
                    click.secho('Initialize download: SUCCESS', fg='green', bold=True)
            except Exception as e:
                tk.error_shout(e)
                sys.exit(1)

            connection.commit()


def _drop_utilization_tables(cursor):
    cursor.execute(
        '''
        DROP TABLE IF EXISTS utilization CASCADE;
        DROP TABLE IF EXISTS issue_resolution_summary CASCADE;
        DROP TABLE IF EXISTS issue_resolution CASCADE;
        DROP TABLE IF EXISTS utilization_comment CASCADE;
        DROP TABLE IF EXISTS utilization_summary CASCADE;
        DROP TYPE IF EXISTS utilization_comment_category;
    '''
    )


def _drop_resource_tables(cursor):
    cursor.execute(
        '''
        DROP TABLE IF EXISTS resource_comment CASCADE;
        DROP TABLE IF EXISTS resource_comment_reply CASCADE;
        DROP TABLE IF EXISTS resource_comment_summary CASCADE;
        DROP TYPE IF EXISTS resource_comment_category;
    '''
    )


def _drop_download_tables(cursor):
    cursor.execute(
        '''
        DROP TABLE IF EXISTS download_summary CASCADE;
    '''
    )


def _create_utilization_tables(cursor):
    cursor.execute(
        '''
        CREATE TABLE utilization (
            id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            created TIMESTAMP,
            approval BOOLEAN DEFAULT false,
            approved TIMESTAMP,
            approval_user_id TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY (resource_id) REFERENCES resource (id),
            FOREIGN KEY (approval_user_id) REFERENCES public.user (id)
        );

        CREATE TABLE issue_resolution_summary (
            id TEXT NOT NULL,
            utilization_id TEXT NOT NULL,
            issue_resolution INTEGER,
            created TIMESTAMP,
            updated TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY (utilization_id) REFERENCES utilization (id)
        );

        CREATE TABLE issue_resolution (
            id TEXT NOT NULL,
            utilization_id TEXT NOT NULL,
            description TEXT,
            created TIMESTAMP,
            creator_user_id TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY (utilization_id) REFERENCES utilization (id),
            FOREIGN KEY (creator_user_id) REFERENCES public.user (id)
        );

        CREATE TYPE utilization_comment_category AS ENUM (
            'Request', 'Question', 'Advertise', 'Thank'
            );
        CREATE TABLE utilization_comment (
            id TEXT NOT NULL,
            utilization_id TEXT NOT NULL,
            category utilization_comment_category NOT NULL,
            content TEXT,
            created TIMESTAMP,
            approval BOOLEAN DEFAULT false,
            approved TIMESTAMP,
            approval_user_id TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY (utilization_id) REFERENCES utilization (id),
            FOREIGN KEY (approval_user_id) REFERENCES public.user (id)
        );

        CREATE TABLE utilization_summary (
            id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            utilization INTEGER,
            comment INTEGER,
            created TIMESTAMP,
            updated TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY (resource_id) REFERENCES resource (id)
        );
        '''
    )


def _create_resource_tabels(cursor):
    cursor.execute(
        '''
        CREATE TYPE resource_comment_category AS ENUM (
            'Request', 'Question', 'Advertise', 'Thank'
            );
        CREATE TABLE resource_comment (
            id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            category resource_comment_category NOT NULL,
            content TEXT,
            rating INTEGER,
            created TIMESTAMP,
            approval BOOLEAN DEFAULT false,
            approved TIMESTAMP,
            approval_user_id TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY (resource_id) REFERENCES resource (id),
            FOREIGN KEY (approval_user_id) REFERENCES public.user (id)
        );

         CREATE TABLE resource_comment_reply (
            id TEXT NOT NULL,
            resource_comment_id TEXT NOT NULL,
            content TEXT,
            created TIMESTAMP,
            creator_user_id TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY (resource_comment_id) REFERENCES resource_comment (id),
            FOREIGN KEY (creator_user_id) REFERENCES public.user (id)
        );

         CREATE TABLE resource_comment_summary (
            id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            comment INTEGER,
            rating NUMERIC,
            created TIMESTAMP,
            updated TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY (resource_id) REFERENCES resource (id)
        );
    '''
    )


def _create_download_tables(cursor):
    cursor.execute(
        '''
        CREATE TABLE download_summary (
            id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            download INTEGER,
            created TIMESTAMP,
            updated TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY (resource_id) REFERENCES resource (id)
        );
    '''
    )
