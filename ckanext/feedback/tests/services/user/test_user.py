import pytest
from ckan.lib import api_token as api_token_lib

from ckanext.feedback.services.user import user as user_service


@pytest.mark.db_test
class TestUser:
    def test_get_user_by_token_id(self, user, api_token):
        token_id = api_token_lib.decode(api_token['token'])['jti']
        user = user_service.get_user_by_token_id(token_id)

        assert user is not None
        assert user.state == 'active'
