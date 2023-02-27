from ckanext.feedback.models.resource import metadata, resource_comment, resource_comment_reply, resource_comment_summary
from sqlalchemy import *

def init_resource_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=[
        'user',
        'resource'
    ])
    resource_comment_summary.drop(engine, checkfirst=true)
    resource_comment_reply.drop(engine, checkfirst=true)
    resource_comment.drop(engine, checkfirst=true)
    resource_comment.create(engine)
    resource_comment_reply.create(engine)
    resource_comment_summary.create(engine)
    metadata.clear()
    