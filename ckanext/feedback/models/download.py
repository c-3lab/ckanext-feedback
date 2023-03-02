import ckan.model.domain_object as domain_object
from ckan.model import meta
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Table, Text

metadata = meta.metadata

download_summary = Table(
    'download_summary',
    metadata,
    Column('id', Text, primary_key=True, nullable=False),
    Column(
        'resource_id',
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
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
