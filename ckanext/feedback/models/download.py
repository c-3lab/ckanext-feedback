from ckan import model
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(metadata=model.meta.metadata)


class DownloadSummary(Base):
    __tablename__ = 'download_summary'
    id = Column(Text, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    download = Column(Integer)
    created = Column(TIMESTAMP)
    updated = Column(TIMESTAMP)
