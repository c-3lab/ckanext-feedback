from ckanext.feedback.models.resource import (
    metadata,
    resource_comment,
    resource_comment_reply,
    resource_comment_summary,
)


def drop_resource_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=['user', 'resource'])
    resource_comment_summary.drop(engine, checkfirst=True)
    resource_comment_reply.drop(engine, checkfirst=True)
    resource_comment.drop(engine, checkfirst=True)
    metadata.clear()


def create_resource_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=['user', 'resource'])
    resource_comment.create(engine)
    resource_comment_reply.create(engine)
    resource_comment_summary.create(engine)
    metadata.clear()
