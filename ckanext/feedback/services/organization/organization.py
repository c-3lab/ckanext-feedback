from ckan.model.group import Group

from ckanext.feedback.models.session import session


# Get organization using owner_org
def get_organization(owner_org):
    organization = session.query(Group).filter(Group.id == owner_org).first()
    return organization


def get_org_list(id=None):
    query = session.query(Group.name, Group.title).filter(
        Group.state == "active",
        Group.is_organization.is_(True),
    )

    if id is not None:
        query = query.filter(Group.id.in_(id))

    results = query.all()

    org_list = []
    for result in results:
        org = {'name': result.name, 'title': result.title}
        org_list.append(org)

    return org_list
