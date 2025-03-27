import uuid
from datetime import datetime

from ckan.model.resource import Resource
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from ckanext.feedback.models.session import Base


class ResourceLike(Base):
    __tablename__ = 'resource_like'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    like_count = Column(Integer, default=0)
    created = Column(TIMESTAMP, default=datetime.now)
    updated = Column(TIMESTAMP)

    resource = relationship(Resource)


class ResourceLikeMonthly(Base):
    __tablename__ = 'resource_like_monthly'
    id = Column(Text, default=uuid.uuid4, primary_key=True, nullable=False)
    resource_id = Column(
        Text,
        ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    like_count = Column(Integer)
    created = Column(TIMESTAMP)
    updated = Column(TIMESTAMP)

    resource = relationship(Resource)
