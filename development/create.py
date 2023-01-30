# encoding: utf-8

import click

#class UtilizationSummary(domain_object.DomainObject):

@click.group(name=u'create', short_help=u"Create database tables")
def create():
    """Create the required database tables.
    """
    pass

@create.command()
def create_tables():
    """Create the required database tables.
    """
    click.secho(u'「createのcreate_tables」コマンドが実行されました。', fg=u'green', bold=True)