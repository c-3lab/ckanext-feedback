import os

from ckan import model
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base(metadata=model.meta.metadata)


def is_test_environment():
    return (
        os.environ.get('PYTEST_CURRENT_TEST') is not None
        or os.environ.get('TESTING') == 'True'
        or 'test' in os.environ.get('CKAN_INI', '').lower()
    )


if is_test_environment():
    SessionLocal = sessionmaker(bind=model.meta.engine)
    session = SessionLocal()
else:
    session = model.Session
