from ckan.model.api_token import ApiToken
from ckan.model.user import User

from ckanext.feedback.models.session import session


def get_user_by_api_token(api_token):
    user = (
        session.query(User)
        .join(ApiToken)
        .filter(ApiToken.id == api_token)
        .filter(User.state == 'active')
        .first()
    )
    return user
