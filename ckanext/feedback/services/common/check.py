from ckan.common import _, current_user
from ckan.model import User
from ckan.plugins import toolkit


def check_administrator(func):
    def wrapper(*args, **kwargs):
        if isinstance(current_user, User):
            if is_organization_admin() or current_user.sysadmin:
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
    if not isinstance(current_user, User):
        return False

    ids = current_user.get_group_ids(group_type='organization', capacity='admin')
    return len(ids) != 0


def has_organization_admin_role(owner_org):
    if not isinstance(current_user, User):
        return False

    ids = current_user.get_group_ids(group_type='organization', capacity='admin')
    return owner_org in ids
