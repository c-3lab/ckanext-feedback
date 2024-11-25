from ckan.model.resource import Resource
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from ckanext.feedback.models.session import Base


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

    resource = relationship(Resource)


class DownloadMonthly(Base):
    __tablename__ = 'download_monthly'
    id = Column(Text, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    download_count = Column(Integer)
    created = Column(TIMESTAMP)
    updated = Column(TIMESTAMP)

    resource = relationship(Resource)
