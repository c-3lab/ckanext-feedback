from ckan import model
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(metadata=model.meta.metadata)

# Use CKAN's scoped session to enable proper session management
# This allows using session.remove() in teardown_app_request
# which is the recommended pattern for Flask applications
session = model.Session
