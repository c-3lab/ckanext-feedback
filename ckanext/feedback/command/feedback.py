import sys

import click
from ckan import model
from ckan.plugins import toolkit
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from ckanext.feedback.models.download import DownloadSummary
from ckanext.feedback.models.issue import IssueResolution, IssueResolutionSummary
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentReply,
    ResourceCommentSummary,
)
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationSummary,
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
    metadata = model.meta.metadata
    metadata.bind = engine
    metadata.reflect(only=['resource', 'user'])
    Base = declarative_base(metadata)
    Base.metadata.drop_all(
        bind=engine,
        tables=[
            Utilization.__table__,
            UtilizationComment.__table__,
            UtilizationComment.__table__,
            IssueResolution.__table__,
            IssueResolutionSummary.__table__,
        ],
    )
    metadata.clear()


def create_utilization_tables(engine):
    Base = declarative_base(metadata=model.meta.metadata)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            Utilization.__table__,
            UtilizationComment.__table__,
            UtilizationSummary.__table__,
            IssueResolution.__table__,
            IssueResolutionSummary.__table__,
        ],
    )


def drop_resource_tables(engine):
    metadata = model.meta.metadata
    metadata.bind = engine
    metadata.reflect(only=['resource', 'user'])
    Base = declarative_base(metadata)
    Base.metadata.drop_all(
        bind=engine,
        tables=[
            ResourceComment.__table__,
            ResourceCommentReply.__table__,
            ResourceCommentSummary.__table__,
        ],
    )
    metadata.clear()


def create_resource_tables(engine):
    Base = declarative_base(metadata=model.meta.metadata)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            ResourceComment.__table__,
            ResourceCommentReply.__table__,
            ResourceCommentSummary.__table__,
        ],
    )


def drop_download_tables(engine):
    metadata = model.meta.metadata
    metadata.bind = engine
    metadata.reflect(only=['resource'])
    Base = declarative_base(metadata)
    Base.metadata.drop_all(bind=engine, tables=[DownloadSummary.__table__])
    metadata.clear()


def create_download_tables(engine):
    Base = declarative_base(metadata=model.meta.metadata)
    Base.metadata.create_all(bind=engine, tables=[DownloadSummary.__table__])
