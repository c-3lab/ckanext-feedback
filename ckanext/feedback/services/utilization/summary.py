from ckanext.feedback.models.utilization import metadata, utilization,utilization_comment,utilization_summary,issue_resolution,issue_resolution_summary
from sqlalchemy import *

def init_utilization_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=[
        'user',
        'resource'
    ])
    issue_resolution_summary.drop(engine, checkfirst=true)
    issue_resolution.drop(engine, checkfirst=true)
    utilization_summary.drop(engine, checkfirst=true)
    utilization_comment.drop(engine, checkfirst=true)
    utilization.drop(engine, checkfirst=true)
    utilization.create(engine)
    utilization_comment.create(engine)
    utilization_summary.create(engine)
    issue_resolution.create(engine)
    issue_resolution_summary.create(engine)
    metadata.clear()
