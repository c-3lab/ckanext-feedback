from ckan.model.group import Group

from ckanext.feedback.models.session import session


def get_organization_name(organization=None):
    return (
        session.query(Group.name.label('name')).filter(Group.id == organization).first()
    )
