from ckanext.feedback.models.utilization import (
    metadata,
    utilization,
    utilization_comment,
    utilization_summary,
    issue_resolution,
    issue_resolution_summary,
)


def init_utilization_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=['user', 'resource'])
    issue_resolution_summary.drop(engine, checkfirst=True)
    issue_resolution.drop(engine, checkfirst=True)
    utilization_summary.drop(engine, checkfirst=True)
    utilization_comment.drop(engine, checkfirst=True)
    utilization.drop(engine, checkfirst=True)
    utilization.create(engine)
    utilization_comment.create(engine)
    utilization_summary.create(engine)
    issue_resolution.create(engine)
    issue_resolution_summary.create(engine)
    metadata.clear()
