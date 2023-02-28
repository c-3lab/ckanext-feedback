from ckan.model import domain_object, meta
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Table, Text

__all__ = ['download_summary']

download_summary = Table(
    'download_summary',
    meta.metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column('resource_id', Text, ForeignKey('resource.id'), nullable=False),
    Column('download', Integer),
    Column('created', TIMESTAMP),
    Column('updated', TIMESTAMP),
)


class DownloadSummary(domain_object.DomainObject):
    def __init__(self, id, resource_id, download, created, updated):
        self.id = id
        self.resource_id = resource_id
        self.download = download
        self.created = created
        self.updated = updated


meta.mapper(DownloadSummary, download_summary)
