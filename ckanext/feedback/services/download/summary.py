from ckanext.feedback.models.download import metadata, download_summary


def init_download_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=['resource'])
    download_summary.drop(engine, checkfirst=True)
    download_summary.create(engine)
    metadata.clear()
