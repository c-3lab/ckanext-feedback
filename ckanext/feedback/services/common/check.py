from functools import wraps

from ckan.common import _, current_user
from ckan.logic import NotAuthorized, NotFound, get_action
from ckan.model import User
from ckan.plugins import toolkit

NOT_FOUND_ERROR_MESSAGE = _(
    'The requested URL was not found on the server. If you entered the'
    ' URL manually please check your spelling and try again.'
)


def check_administrator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if isinstance(current_user, User):
            if is_organization_admin() or current_user.sysadmin:
                return func(*args, **kwargs)
        toolkit.abort(404, NOT_FOUND_ERROR_MESSAGE)

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


def user_has_organization_admin_role(user_id, owner_org):
    if not user_id:
        return False

    user = User.get(user_id)
    if not isinstance(user, User):
        return False

    if getattr(user, 'sysadmin', False):
        return True

    ids = user.get_group_ids(group_type='organization', capacity='admin')
    return owner_org in ids


def get_authorized_package(package_id, context):
    """
    Get package data if user is authorized (efficient - single DB call).

    This function checks access permissions and returns the package data
    in a single operation, avoiding duplicate DB queries.

    Args:
        package_id: The package ID to check
        context: CKAN's context object (must be provided by caller)

    Returns:
        dict: Package data from package_show

    Raises:
        toolkit.abort(404): If access permissions are lacking or package not found
    """
    try:
        package = get_action('package_show')(context, {'id': package_id})
        return package
    except (NotAuthorized, NotFound):
        toolkit.abort(404, NOT_FOUND_ERROR_MESSAGE)


def require_package_access(package_id, context):
    """
    Require package access permissions (package data is retrieved but discarded).

    Note: If you need the package data, use get_authorized_package() instead
    to avoid duplicate DB queries.

    Args:
        package_id: The package ID to check
        context: CKAN's context object (must be provided by caller)

    Raises:
        toolkit.abort(404): If access permissions are lacking
    """
    get_authorized_package(package_id, context)
    # Package data is retrieved but not returned


def require_resource_package_access(resource_id, context):
    """
    Require access permissions for the resource's owning package

    Args:
        resource_id: Resource ID
        context: CKAN context object (must be provided by caller)

    Raises:
        toolkit.abort(404): If access permissions are denied
    """
    import ckanext.feedback.services.resource.comment as comment_service

    resource = comment_service.get_resource(resource_id)
    if resource:
        require_package_access(resource.Resource.package_id, context)
