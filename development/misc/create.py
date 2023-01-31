# encoding: utf-8

import click

@click.group(name=u'create', short_help=u"Create database tables")
def create():
    """Create the required database tables.
    """
    pass

@create.command()
def create_tables():
    """Create the required database tables.
    """
    click.secho(u'The create_tables command was executed successfully.', fg=u'green', bold=True)