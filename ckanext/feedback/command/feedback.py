import sys

import click
from ckan.plugins import toolkit
from sqlalchemy import create_engine

from ckanext.feedback.models.download import download_summary
from ckanext.feedback.models.download import metadata as download_metadata
from ckanext.feedback.models.issue import issue_resolution, issue_resolution_summary
from ckanext.feedback.models.resource_comment import metadata as resource_metadata
from ckanext.feedback.models.resource_comment import (
    resource_comment,
    resource_comment_reply,
    resource_comment_summary,
)
from ckanext.feedback.models.utilization import metadata as utilization_metadata
from ckanext.feedback.models.utilization import (
    utilization,
    utilization_comment,
    utilization_summary,
)


@click.group()
def feedback():
    '''CLI tool for ckanext-feedback plugin.'''


def get_engine(host, port, dbname, user, password):
    try:
        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{dbname}')
    except Exception as e:
        toolkit.error_shout(e)
        sys.exit(1)
    else:
        return engine


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
    engine = get_engine(host, port, dbname, user, password)
    try:
        if not modules:
            drop_utilization_tables(engine)
            create_utilization_tables(engine)
            drop_resource_tables(engine)
            create_resource_tables(engine)
            drop_download_tables(engine)
            create_download_tables(engine)
            click.secho('Initialize all modules: SUCCESS', fg='green', bold=True)
        elif 'utilization' in modules:
            drop_utilization_tables(engine)
            create_utilization_tables(engine)
            click.secho('Initialize utilization: SUCCESS', fg='green', bold=True)
        elif 'resource' in modules:
            drop_resource_tables(engine)
            create_resource_tables(engine)
            click.secho('Initialize resource: SUCCESS', fg='green', bold=True)
        elif 'download' in modules:
            drop_download_tables(engine)
            create_download_tables(engine)
            click.secho('Initialize download: SUCCESS', fg='green', bold=True)
    except Exception as e:
        toolkit.error_shout(e)
        sys.exit(1)


def drop_utilization_tables(engine):
    utilization_metadata.bind = engine
    utilization_metadata.reflect(only=['user', 'resource'])
    issue_resolution_summary.drop(engine, checkfirst=True)
    issue_resolution.drop(engine, checkfirst=True)
    utilization_summary.drop(engine, checkfirst=True)
    utilization_comment.drop(engine, checkfirst=True)
    utilization.drop(engine, checkfirst=True)
    utilization_metadata.clear()


def create_utilization_tables(engine):
    utilization_metadata.bind = engine
    utilization_metadata.reflect(only=['user', 'resource'])
    utilization.create(engine)
    utilization_comment.create(engine)
    utilization_summary.create(engine)
    issue_resolution.create(engine)
    issue_resolution_summary.create(engine)
    utilization_metadata.clear()


def drop_resource_tables(engine):
    resource_metadata.bind = engine
    resource_metadata.reflect(only=['user', 'resource'])
    resource_comment_summary.drop(engine, checkfirst=True)
    resource_comment_reply.drop(engine, checkfirst=True)
    resource_comment.drop(engine, checkfirst=True)
    resource_metadata.clear()


def create_resource_tables(engine):
    resource_metadata.bind = engine
    resource_metadata.reflect(only=['user', 'resource'])
    resource_comment.create(engine)
    resource_comment_reply.create(engine)
    resource_comment_summary.create(engine)
    resource_metadata.clear()


def drop_download_tables(engine):
    download_metadata.bind = engine
    download_metadata.reflect(only=['resource'])
    download_summary.drop(engine, checkfirst=True)
    download_metadata.clear()


def create_download_tables(engine):
    download_metadata.bind = engine
    download_metadata.reflect(only=['resource'])
    download_summary.create(engine)
    download_metadata.clear()
