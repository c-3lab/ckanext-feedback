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


def get_organization_name_list():
    org_name_list = (
        session.query(Group.name)
        .filter(Group.state == "active", Group.is_organization.is_(True))
        .all()
    )
    return [name for (name,) in org_name_list]


def get_organization_name_by_name(name):
    org_name = (
        session.query(Group.name)
        .filter(
            Group.name == name,
            Group.state == "active",
            Group.is_organization.is_(True),
        )
        .first()
    )

    return org_name


def get_organization_name_by_id(org_id):
    org_name = (
        session.query(Group.name.label('name')).filter(Group.id == org_id).first()
    )
    return org_name
