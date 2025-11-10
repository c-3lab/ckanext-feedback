import types

import pytest
from ckan.lib import api_token as api_token_lib
from ckan.plugins import toolkit

from ckanext.feedback.utils.auth import AuthTokenHandler, create_auth_context


@pytest.mark.db_test
class TestAuthTokenHandler:
    def test_validate_api_token(self, api_token):
        AuthTokenHandler.validate_api_token(api_token['token'])

    def test_validate_api_token_none(self):
        with pytest.raises(toolkit.NotAuthorized):
            AuthTokenHandler.validate_api_token(None)

    def test_decode_api_token(self, api_token):
        token_id = AuthTokenHandler.decode_api_token(api_token['token'])
        assert token_id == api_token_lib.decode(api_token['token'])['jti']

    def test_decode_api_token_invalid(self):
        with pytest.raises(toolkit.NotAuthorized):
            AuthTokenHandler.decode_api_token('invalid_token')

    def test_check_sysadmin(self, sysadmin):
        sysadmin_obj = types.SimpleNamespace(**sysadmin)
        AuthTokenHandler.check_sysadmin(sysadmin_obj)

    def test_check_sysadmin_not_sysadmin(self, user):
        with pytest.raises(toolkit.NotAuthorized):
            AuthTokenHandler.check_sysadmin(user)

    def test_check_sysadmin_none(self):
        with pytest.raises(toolkit.NotAuthorized):
            AuthTokenHandler.check_sysadmin(None)


@pytest.mark.db_test
class TestCreateAuthContext:
    def test_create_auth_context(self):
        context = create_auth_context()

        assert 'model' in context
        assert 'session' in context
        assert 'for_view' in context
        assert context['for_view'] is True

        import ckan.model as expected_model

        assert context['model'] == expected_model
        assert context['session'] == expected_model.Session
