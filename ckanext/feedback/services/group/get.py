from ckan.model import Group

from ckanext.feedback.models.session import session


def get_group_names(name=None):
    query = session.query(Group.name)

    if name:
        query = query.filter(Group.name == name)

    results = query.all()

    return [result[0] for result in results]
