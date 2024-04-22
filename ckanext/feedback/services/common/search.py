from ckan.model.group import Group

from ckanext.feedback.models.session import session


def get_organization(org_id=None):
    return (
        session.query(Group.name.label('name')).filter(Group.id == org_id).first()
    )
