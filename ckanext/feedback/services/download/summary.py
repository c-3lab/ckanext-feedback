from ckanext.feedback.models.download import metadata, download_summary
from sqlalchemy import *


def init_download_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=[
        'resource'
    ])
    download_summary.drop(engine, checkfirst=true)
    download_summary.create(engine)
    metadata.clear()
