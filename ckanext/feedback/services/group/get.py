from ckan.model import Group

from ckanext.feedback.models.session import session


def get_group_names(name=None):
    query = session.query(Group.name)

    if name:
        query = query.filter(
            Group.name == name,
            Group.state == "active",
            Group.is_organization.is_(True),
        )

    results = query.all()

    return [result[0] for result in results]
