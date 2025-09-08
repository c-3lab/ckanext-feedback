from ckan.model.api_token import ApiToken
from ckan.model.user import User

from ckanext.feedback.models.session import session


def get_user_by_token_id(token_id):
    user = (
        session.query(User)
        .join(ApiToken)
        .filter(ApiToken.id == token_id)
        .filter(User.state == 'active')
        .first()
    )
    return user
