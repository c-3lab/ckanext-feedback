from unittest.mock import MagicMock, patch

from ckan.common import config

from ckanext.feedback.services.common import ai_functions
from ckanext.feedback.services.common.config import FeedbackConfig


class TestAIFunctions:
    def test_moral_keeper_ai_is_enabled_default_false(self):
        assert FeedbackConfig().moral_keeper_ai.is_enable() is False

    def test_moral_keeper_ai_is_enabled_true(self):
        config['ckan.feedback.moral_keeper_ai.enable'] = True
        assert FeedbackConfig().moral_keeper_ai.is_enable() is True

    @patch('ckanext.feedback.services.common.ai_functions.importlib.import_module')
    def test_check_ai_comment_true(self, mock_import_module):
        content = 'comment_content'
        judgement = True
        ng_reasons = []

        mock_MoralKeeperAI = MagicMock()
        mock_ai = MagicMock()
        mock_ai.check.return_value = (judgement, ng_reasons)
        mock_MoralKeeperAI.MoralKeeperAI.return_value = mock_ai
        mock_import_module.return_value = mock_MoralKeeperAI

        assert ai_functions.check_ai_comment(content) is True

    @patch('ckanext.feedback.services.common.ai_functions.importlib.import_module')
    @patch('ckanext.feedback.services.common.ai_functions.log.exception')
    def test_check_ai_comment_false_RateLimitError(
        self, mock_log_exception, mock_import_module
    ):
        content = 'comment_content'
        judgement = False
        ng_reasons = ['RateLimitError']

        mock_MoralKeeperAI = MagicMock()
        mock_ai = MagicMock()
        mock_ai.check.return_value = (judgement, ng_reasons)
        mock_MoralKeeperAI.MoralKeeperAI.return_value = mock_ai
        mock_import_module.return_value = mock_MoralKeeperAI

        ret = ai_functions.check_ai_comment(content)

        assert ret is False
        mock_log_exception.assert_called_once_with('AI response failed. %s', ng_reasons)

    @patch('ckanext.feedback.services.common.ai_functions.importlib.import_module')
    @patch('ckanext.feedback.services.common.ai_functions.log.exception')
    def test_check_ai_comment_false_APIConnectionError(
        self, mock_log_exception, mock_import_module
    ):
        content = 'comment_content'
        judgement = False
        ng_reasons = ['APIConnectionError']

        mock_MoralKeeperAI = MagicMock()
        mock_ai = MagicMock()
        mock_ai.check.return_value = (judgement, ng_reasons)
        mock_MoralKeeperAI.MoralKeeperAI.return_value = mock_ai
        mock_import_module.return_value = mock_MoralKeeperAI

        ret = ai_functions.check_ai_comment(content)

        assert ret is False
        mock_log_exception.assert_called_once_with('AI response failed. %s', ng_reasons)

    @patch('ckanext.feedback.services.common.ai_functions.importlib.import_module')
    @patch('ckanext.feedback.services.common.ai_functions.log.exception')
    def test_check_ai_comment_false_APIAuthenticationError(
        self, mock_log_exception, mock_import_module
    ):
        content = 'comment_content'
        judgement = False
        ng_reasons = ['APIAuthenticationError']

        mock_MoralKeeperAI = MagicMock()
        mock_ai = MagicMock()
        mock_ai.check.return_value = (judgement, ng_reasons)
        mock_MoralKeeperAI.MoralKeeperAI.return_value = mock_ai
        mock_import_module.return_value = mock_MoralKeeperAI

        ret = ai_functions.check_ai_comment(content)

        assert ret is False
        mock_log_exception.assert_called_once_with('AI response failed. %s', ng_reasons)

    @patch('ckanext.feedback.services.common.ai_functions.importlib.import_module')
    def test_suggest_ai_comment(self, mock_import_module):
        content = 'comment_content'
        softened = 'mock_softened'

        mock_ai = MagicMock()
        mock_ai.suggest.return_value = softened
        mock_MoralKeeperAI = MagicMock()
        mock_MoralKeeperAI.MoralKeeperAI.return_value = mock_ai
        mock_import_module.return_value = mock_MoralKeeperAI

        ret = ai_functions.suggest_ai_comment(content)

        assert ret == softened

    @patch('ckanext.feedback.services.common.ai_functions.importlib.import_module')
    def test_suggest_ai_comment_OpenAiFilter(self, mock_import_module):
        content = ''

        ret = ai_functions.suggest_ai_comment(content)

        assert ret is None
