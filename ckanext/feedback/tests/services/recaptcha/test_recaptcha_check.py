from unittest.mock import MagicMock, patch

import pytest
from ckan import model
from ckan.common import config

from ckanext.feedback.services.common.config import FeedbackConfig
from ckanext.feedback.services.recaptcha import check

engine = model.repo.session.get_bind()


class MockResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def json(self):
        return self._json_data


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestCheck:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()

    @patch('ckanext.feedback.services.recaptcha.check.requests')
    def test_recaptcha(self, mock_requests):
        config['ckan.feedback.recaptcha.enable'] = True
        config['ckan.feedback.recaptcha.privatekey'] = 'test_private_key'

        mock_request = MagicMock()
        mock_request.form.get.return_value = 'test_recaptcha_response'

        mock_requests.get.return_value = MockResponse({"success": True, "score": 0.9})
        assert check.is_recaptcha_verified(mock_request) is True

    def test_recaptcha_is_disable(self):
        config['ckan.feedback.recaptcha.enable'] = False
        mock_request = MagicMock()
        assert check.is_recaptcha_verified(mock_request) is True

    @patch('ckanext.feedback.services.recaptcha.check.logger')
    @patch('ckanext.feedback.services.recaptcha.check.requests')
    def test_recaptcha_without_no_recaptcha_response(self, mock_requests, mock_logger):
        config['ckan.feedback.recaptcha.enable'] = True

        mock_request = MagicMock()
        mock_request.form.get.return_value = None
        assert check.is_recaptcha_verified(mock_request) is False
        mock_logger.warning.assert_called_once_with("not recaptcha_response")

    @patch('ckanext.feedback.services.recaptcha.check.logger')
    @patch('ckanext.feedback.services.recaptcha.check.requests')
    def test_recaptcha_without_no_privatekey(self, mock_requests, mock_logger):
        config['ckan.feedback.recaptcha.enable'] = True
        config['ckan.feedback.recaptcha.privatekey'] = ''

        mock_request = MagicMock()
        mock_request.form.get.return_value = 'test_recaptcha_response'
        mock_requests.get.return_value = MockResponse({"success": True, "score": 0.9})
        assert check.is_recaptcha_verified(mock_request) is False
        mock_logger.warning.assert_called_once_with("not recaptcha_private_key")

    @patch('ckanext.feedback.services.recaptcha.check.logger')
    @patch('ckanext.feedback.services.recaptcha.check.requests')
    def test_recaptcha_without_not_success(self, mock_requests, mock_logger):
        config['ckan.feedback.recaptcha.enable'] = True
        config['ckan.feedback.recaptcha.privatekey'] = 'test_private_key'

        mock_request = MagicMock()
        mock_request.form.get.return_value = 'test_recaptcha_response'
        data = {"success": False}

        mock_requests.get.return_value = MockResponse(data)
        assert check.is_recaptcha_verified(mock_request) is False
        mock_logger.warning.assert_called_once_with(f"not success:{data}")

    @patch('ckanext.feedback.services.recaptcha.check.logger')
    @patch('ckanext.feedback.services.recaptcha.check.requests')
    def test_recaptcha_without_score(self, mock_requests, mock_logger):
        config['ckan.feedback.recaptcha.enable'] = True
        config['ckan.feedback.recaptcha.privatekey'] = 'test_private_key'

        mock_request = MagicMock()
        mock_request.form.get.return_value = 'test_recaptcha_response'
        data = {"success": True, "score": 0.1}

        mock_requests.get.return_value = MockResponse(data)
        assert check.is_recaptcha_verified(mock_request) is False
        mock_logger.warning.assert_called_once_with(
            f"Score is below the threshold:{data}:score_threshold={0.5}"
        )

    @patch('ckanext.feedback.services.recaptcha.check.logger')
    @patch('ckanext.feedback.services.recaptcha.check.requests')
    def test_recaptcha_without_keyerror(self, mock_requests, mock_logger):
        config['ckan.feedback.recaptcha.enable'] = True
        config['ckan.feedback.recaptcha.privatekey'] = 'test_private_key'

        mock_request = MagicMock()
        mock_request.form.get.return_value = 'test_recaptcha_response'
        mock_requests.get.return_value = MockResponse({"score": None})
        assert check.is_recaptcha_verified(mock_request) is False
        mock_logger.error.assert_called_once_with("KeyError")

    def test_get_feedback_recaptcha_publickey(self):
        config['ckan.feedback.recaptcha.publickey'] = 'test_publick_key'
        ret_value = FeedbackConfig().recaptcha.publickey.get()
        assert ret_value == 'test_publick_key'
