from ckanext.feedback.models.download import metadata, download_summary


def drop_download_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=['resource'])
    download_summary.drop(engine, checkfirst=True)
    metadata.clear()


def create_download_tables(engine):
    metadata.bind = engine
    metadata.reflect(only=['resource'])
    download_summary.create(engine)
    metadata.clear()
