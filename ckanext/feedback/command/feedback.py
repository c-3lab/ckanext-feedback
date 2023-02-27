import sys
import click
from ckan.plugins import toolkit
from sqlalchemy import create_engine
from ckanext.feedback.services.utilization.summary import (
    drop_utilization_tables,
    create_utilization_tables,
)
from ckanext.feedback.services.resource.summary import (
    drop_resource_tables,
    create_resource_tables,
)
from ckanext.feedback.services.download.summary import (
    drop_download_tables,
    create_download_tables,
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

    engine.dispose()
