import os
import sys

import click
import requests
from ckan.common import config
from ckan.model import meta
from ckan.plugins import toolkit

import ckanext.feedback.services.common.upload as upload_service
import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.utilization.details as detail_service
from ckanext.feedback.controllers.api.moral_check_log import (
    generate_moral_check_log_excel_bytes,
)
from ckanext.feedback.models.download import DownloadMonthly, DownloadSummary
from ckanext.feedback.models.issue import IssueResolution, IssueResolutionSummary
from ckanext.feedback.models.likes import ResourceLike, ResourceLikeMonthly
from ckanext.feedback.models.resource_comment import (
    ResourceComment,
    ResourceCommentMoralCheckLog,
    ResourceCommentReactions,
    ResourceCommentReply,
    ResourceCommentSummary,
)
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentMoralCheckLog,
    UtilizationCommentReply,
    UtilizationSummary,
)

# Solr configuration constants
FEEDBACK_SOLR_FIELDS = ['downloads_total_i', 'likes_total_i']


def get_solr_url():
    """
    Get Solr URL from CKAN config.

    Checks multiple possible config keys in order:
    1. ckan.solr_url (CKAN standard)
    2. solr_url (alternative)
    3. Default fallback
    """
    # Try CKAN standard config key first
    solr_url = config.get('ckan.solr_url')
    if solr_url:
        return solr_url

    # Try alternative config key
    solr_url = config.get('solr_url')
    if solr_url:
        return solr_url

    # Fallback to default (for development environments)
    return 'http://solr:8983/solr/ckan'


def get_solr_schema_api():
    """Get Solr schema API URL from config."""
    solr_url = get_solr_url()
    return f"{solr_url}/schema"


@click.group()
def feedback():
    '''CLI tool for ckanext-feedback plugin.'''


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
def init(modules):
    engine = meta.engine
    try:
        if not modules:
            drop_utilization_tables(engine)
            create_utilization_tables(engine)
            drop_resource_tables(engine)
            create_resource_tables(engine)
            drop_download_tables(engine)
            create_download_tables(engine)
            click.secho('Initialize all modules: SUCCESS', fg='green', bold=True)
        else:
            if 'utilization' in modules:
                drop_utilization_tables(engine)
                create_utilization_tables(engine)
                click.secho('Initialize utilization: SUCCESS', fg='green', bold=True)
            if 'resource' in modules:
                drop_resource_tables(engine)
                create_resource_tables(engine)
                click.secho('Initialize resource: SUCCESS', fg='green', bold=True)
            if 'download' in modules:
                drop_download_tables(engine)
                create_download_tables(engine)
                click.secho('Initialize download: SUCCESS', fg='green', bold=True)
    except Exception as e:
        toolkit.error_shout(e)
        sys.exit(1)


def drop_utilization_tables(engine):
    IssueResolutionSummary.__table__.drop(engine, checkfirst=True)
    IssueResolution.__table__.drop(engine, checkfirst=True)
    UtilizationCommentMoralCheckLog.__table__.drop(engine, checkfirst=True)
    UtilizationSummary.__table__.drop(engine, checkfirst=True)
    UtilizationCommentReply.__table__.drop(engine, checkfirst=True)
    UtilizationComment.__table__.drop(engine, checkfirst=True)
    Utilization.__table__.drop(engine, checkfirst=True)


def create_utilization_tables(engine):
    Utilization.__table__.create(engine, checkfirst=True)
    UtilizationComment.__table__.create(engine, checkfirst=True)
    UtilizationCommentReply.__table__.create(engine, checkfirst=True)
    UtilizationSummary.__table__.create(engine, checkfirst=True)
    UtilizationCommentMoralCheckLog.__table__.create(engine, checkfirst=True)
    IssueResolution.__table__.create(engine, checkfirst=True)
    IssueResolutionSummary.__table__.create(engine, checkfirst=True)


def drop_resource_tables(engine):
    ResourceCommentMoralCheckLog.__table__.drop(engine, checkfirst=True)
    ResourceCommentReactions.__table__.drop(engine, checkfirst=True)
    ResourceLikeMonthly.__table__.drop(engine, checkfirst=True)
    ResourceLike.__table__.drop(engine, checkfirst=True)
    ResourceCommentSummary.__table__.drop(engine, checkfirst=True)
    ResourceCommentReply.__table__.drop(engine, checkfirst=True)
    ResourceComment.__table__.drop(engine, checkfirst=True)


def create_resource_tables(engine):
    ResourceComment.__table__.create(engine, checkfirst=True)
    ResourceCommentReply.__table__.create(engine, checkfirst=True)
    ResourceCommentSummary.__table__.create(engine, checkfirst=True)
    ResourceLike.__table__.create(engine, checkfirst=True)
    ResourceLikeMonthly.__table__.create(engine, checkfirst=True)
    ResourceCommentReactions.__table__.create(engine, checkfirst=True)
    ResourceCommentMoralCheckLog.__table__.create(engine, checkfirst=True)


def drop_download_tables(engine):
    DownloadMonthly.__table__.drop(engine, checkfirst=True)
    DownloadSummary.__table__.drop(engine, checkfirst=True)


def create_download_tables(engine):
    DownloadSummary.__table__.create(engine, checkfirst=True)
    DownloadMonthly.__table__.create(engine, checkfirst=True)


@feedback.command(
    name='clean-files', short_help='delete uploaded files not linked to comments.'
)
@click.option(
    '-d',
    '--dry-run',
    is_flag=True,
    help='List files to be deleted without actually removing them.',
)
def clean_files(dry_run):
    # Get base destination directory for uploaded files
    base_storage_path = upload_service.get_feedback_storage_path()

    # Get relative paths for resource_comment and utilization_comment
    resource_comment_relpath = comment_service.get_upload_destination()
    utilization_comment_relpath = detail_service.get_upload_destination()

    # Construct the absolute path of each destination directory
    resource_comment_dir = os.path.join(base_storage_path, resource_comment_relpath)
    utilization_comment_dir = os.path.join(
        base_storage_path, utilization_comment_relpath
    )

    # Get all files that exist in the relevant directory
    all_resource_comment_files = set(os.listdir(resource_comment_dir))
    all_utilization_comment_files = set(os.listdir(utilization_comment_dir))

    # Get a list of the actual image file names used in connection with the comment
    valid_resource_comment_files = comment_service.get_comment_attached_image_files()
    valid_utilization_comment_files = detail_service.get_comment_attached_image_files()

    # Calculate orphan files
    invalid_resource_comment_files = all_resource_comment_files - set(
        valid_resource_comment_files
    )
    invalid_utilization_comment_files = all_utilization_comment_files - set(
        valid_utilization_comment_files
    )

    # Delete orphan files (if dry_run=True, do not run, only show target for deletion)
    delete_invalid_files(dry_run, resource_comment_dir, invalid_resource_comment_files)
    delete_invalid_files(
        dry_run, utilization_comment_dir, invalid_utilization_comment_files
    )


def delete_invalid_files(dry_run, dir_path, invalid_files):
    # If there are no orphan files to delete, do nothing and exit
    if not invalid_files:
        click.secho(f"No files for deletion were found: {dir_path}", fg='green')
        return

    # of files to be deleted
    click.secho(
        f"Found {len(invalid_files)} unwanted files in: {dir_path}", fg='yellow'
    )

    # Sort by file name
    for filename in sorted(invalid_files):
        file_path = os.path.join(dir_path, filename)
        handle_file_deletion(dry_run, file_path)


def handle_file_deletion(dry_run, file_path):
    if dry_run:
        # Dry-run mode: shows the file path to be deleted
        # without actually deleting the file.
        click.secho(f"[DRY RUN] Deletion Schedule: {file_path}", fg='blue')
    else:
        try:
            # Normal mode: Deletes files and displays completion log
            os.remove(file_path)
            click.secho(f"Deleted: {file_path}", fg='green')
        except Exception as e:
            # Exception handling when deletion fails
            click.secho(f"Deletion failure: {file_path}. {e}", fg='red', err=True)


@feedback.command(
    name='moral-check-log',
    short_help='Export as a joined sheet (default) or separate sheets in Excel.',
)
@click.option(
    '-s',
    '--separation',
    is_flag=True,
    default=False,
    show_default=True,
    help='Export each table to a separate sheet.',
)
@click.option(
    '-o',
    '--output',
    default='moral_check_log.xlsx',
    show_default=True,
    help='Output file name. (default: moral_check_log.xlsx)',
)
def moral_check_log(separation, output):
    try:
        result = generate_moral_check_log_excel_bytes(separation)
        with open(output, 'wb') as f:
            f.write(result.getvalue())
        click.secho(f'Exported moral check log to {output}', fg='green')
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@feedback.command(
    name='reset-solr-fields',
    short_help='Delete feedback Solr fields (requires reindex after).',
)
@click.option(
    '-y',
    '--yes',
    is_flag=True,
    help='Skip confirmation prompt.',
)
def reset_solr_fields(yes):
    try:
        schema_api = get_solr_schema_api()

        if not yes:
            click.echo()
            click.secho(
                'WARNING: This will delete Solr fields:', fg='yellow', bold=True
            )
            for field_name in FEEDBACK_SOLR_FIELDS:
                click.echo(f'  - {field_name}')
            click.echo()
            if not click.confirm('Do you want to continue?'):
                click.secho('Operation cancelled.', fg='blue')
                return

        click.echo()
        deleted_count = 0
        error_count = 0

        for field_name in FEEDBACK_SOLR_FIELDS:
            try:
                response = requests.post(
                    schema_api, json={"delete-field": {"name": field_name}}, timeout=10
                )

                if response.status_code in [200, 201]:
                    click.secho(f'  ✓ Deleted: {field_name}', fg='green')
                    deleted_count += 1
                elif response.status_code == 404:
                    click.secho(f'  - Not found: {field_name}', fg='yellow')
                else:
                    click.secho(
                        f'  ✗ Failed: {field_name} (HTTP {response.status_code})',
                        fg='red',
                    )
                    error_count += 1
            except Exception as e:
                click.secho(f'  ✗ Error: {field_name} - {e}', fg='red')
                error_count += 1

        click.echo()
        if deleted_count > 0:
            click.secho('✓ Fields deleted successfully!', fg='green', bold=True)
            click.echo()
            click.secho('=' * 70, fg='red', bold=True)
            click.secho('⚠️  IMPORTANT ⚠️', fg='red', bold=True)
            click.secho('=' * 70, fg='red', bold=True)
            click.echo()
            click.secho(
                '  If you do NOT want downloads_total_i and likes_total_i '
                'to be automatically recreated,',
                fg='yellow',
                bold=True,
            )
            click.secho(
                '  set custom_sort.enable to false in feedback_config.json',
                fg='yellow',
                bold=True,
            )
            click.secho(
                '  before running any CKAN commands that trigger reindexing.',
                fg='yellow',
                bold=True,
            )
            click.echo()
            click.secho('=' * 70, fg='red', bold=True)
            click.echo()
            solr_url = get_solr_url()
            verify_cmd = (
                f'curl {solr_url}/schema/fields | '
                f'grep -E "(downloads_total_i|likes_total_i)"'
            )
            click.secho(f'Verify: {verify_cmd}', fg='cyan')
        elif error_count > 0:
            click.secho('Some errors occurred.', fg='red')
            sys.exit(1)
        else:
            click.secho('Fields were already deleted or never existed.', fg='yellow')

    except Exception as e:
        click.secho(f'Error: {e}', fg='red', err=True)
        raise click.Abort()
