import os
import sys

import click
from ckan.common import config
from ckan.model import meta
from ckan.plugins import toolkit

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.utilization.details as detail_service
from ckanext.feedback.models.download import DownloadMonthly, DownloadSummary
from ckanext.feedback.models.issue import IssueResolution, IssueResolutionSummary
from ckanext.feedback.models.likes import ResourceLike
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
        if 'utilization' in modules:
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
            drop_download_monthly_tables(engine)
            create_download_monthly_tables(engine)
            click.secho('Initialize download: SUCCESS', fg='green', bold=True)
        else:
            drop_utilization_tables(engine)
            create_utilization_tables(engine)
            drop_resource_tables(engine)
            create_resource_tables(engine)
            drop_download_tables(engine)
            create_download_tables(engine)
            drop_resource_like_tables(engine)
            create_resource_like_tables(engine)
            drop_download_monthly_tables(engine)
            create_download_monthly_tables(engine)
            click.secho('Initialize all modules: SUCCESS', fg='green', bold=True)
    except Exception as e:
        toolkit.error_shout(e)
        sys.exit(1)


def drop_utilization_tables(engine):
    IssueResolutionSummary.__table__.drop(engine, checkfirst=True)
    IssueResolution.__table__.drop(engine, checkfirst=True)
    UtilizationSummary.__table__.drop(engine, checkfirst=True)
    UtilizationComment.__table__.drop(engine, checkfirst=True)
    Utilization.__table__.drop(engine, checkfirst=True)


def create_utilization_tables(engine):
    Utilization.__table__.create(engine, checkfirst=True)
    UtilizationComment.__table__.create(engine, checkfirst=True)
    UtilizationSummary.__table__.create(engine, checkfirst=True)
    IssueResolution.__table__.create(engine, checkfirst=True)
    IssueResolutionSummary.__table__.create(engine, checkfirst=True)


def drop_resource_tables(engine):
    ResourceCommentSummary.__table__.drop(engine, checkfirst=True)
    ResourceCommentReply.__table__.drop(engine, checkfirst=True)
    ResourceComment.__table__.drop(engine, checkfirst=True)


def create_resource_tables(engine):
    ResourceComment.__table__.create(engine, checkfirst=True)
    ResourceCommentReply.__table__.create(engine, checkfirst=True)
    ResourceCommentSummary.__table__.create(engine, checkfirst=True)


def drop_download_tables(engine):
    DownloadSummary.__table__.drop(engine, checkfirst=True)


def create_download_tables(engine):
    DownloadSummary.__table__.create(engine, checkfirst=True)


def drop_resource_like_tables(engine):
    ResourceLike.__table__.drop(engine, checkfirst=True)


def create_resource_like_tables(engine):
    ResourceLike.__table__.create(engine, checkfirst=True)


def drop_download_monthly_tables(engine):
    DownloadMonthly.__table__.drop(engine, checkfirst=True)


def create_download_monthly_tables(engine):
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
    base_storage_path = config.get('ckan.feedback.storage_path')

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
        click.secho("No files for deletion were found.", fg='green')
        return

    # of files to be deleted
    click.secho(f"{len(invalid_files)} found unwanted files.", fg='yellow')

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
