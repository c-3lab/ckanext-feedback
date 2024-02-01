from ckan.common import _, c
from ckan.plugins import toolkit


def check_administrator(func):
    def wrapper(*args, **kwargs):
        if c.userobj is not None:
            if is_organization_admin() or c.userobj.sysadmin:
                return func(*args, **kwargs)
        toolkit.abort(
            404,
            _(
                'The requested URL was not found on the server. If you entered the'
                ' URL manually please check your spelling and try again.'
            ),
        )

    return wrapper


def is_organization_admin():
    if c.userobj is None:
        return False

    ids = c.userobj.get_group_ids(group_type='organization', capacity='admin')
    return len(ids) != 0


def has_organization_admin_role(owner_org):
    if c.userobj is None:
        return False

    ids = c.userobj.get_group_ids(group_type='organization', capacity='admin')
    return owner_org in ids
