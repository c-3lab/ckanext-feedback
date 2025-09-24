from io import BytesIO
from unittest.mock import patch

import pytest
from ckan.lib import api_token as api_token_lib
from flask import Response

from ckanext.feedback.controllers.api.moral_check_log import (
    download_moral_check_log,
    generate_moral_check_log_excel_bytes,
    get_moral_check_log_excel_response,
)


@pytest.mark.db_test
class TestMoralCheckLog:
    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'resource_comment_service.get_resource_comment_moral_check_logs'
    )
    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'utilization_detail_service.get_utilization_comment_moral_check_logs'
    )
    def test_generate_moral_check_log_excel_bytes(
        self,
        mock_get_utilization_comment_moral_check_logs,
        mock_get_resource_comment_moral_check_logs,
        resource_comment_moral_check_log,
        utilization_comment_moral_check_log,
    ):
        mock_get_resource_comment_moral_check_logs.return_value = [
            resource_comment_moral_check_log
        ]
        mock_get_utilization_comment_moral_check_logs.return_value = [
            utilization_comment_moral_check_log
        ]

        output = generate_moral_check_log_excel_bytes(False)

        assert output is not None
        assert output.getbuffer().nbytes > 0

    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'resource_comment_service.get_resource_comment_moral_check_logs'
    )
    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'utilization_detail_service.get_utilization_comment_moral_check_logs'
    )
    def test_generate_moral_check_log_excel_bytes_with_separation(
        self,
        mock_get_utilization_comment_moral_check_logs,
        mock_get_resource_comment_moral_check_logs,
        resource_comment_moral_check_log,
        utilization_comment_moral_check_log,
    ):
        mock_get_resource_comment_moral_check_logs.return_value = [
            resource_comment_moral_check_log
        ]
        mock_get_utilization_comment_moral_check_logs.return_value = [
            utilization_comment_moral_check_log
        ]

        output = generate_moral_check_log_excel_bytes(True)

        assert output is not None
        assert output.getbuffer().nbytes > 0

    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'generate_moral_check_log_excel_bytes'
    )
    def test_get_moral_check_log_excel_response(
        self, mock_generate_moral_check_log_excel_bytes
    ):
        mock_output = BytesIO(b'test data')

        mock_generate_moral_check_log_excel_bytes.return_value = mock_output

        response = get_moral_check_log_excel_response(False)

        assert isinstance(response, Response)
        assert response.status_code == 200
        assert (
            response.mimetype
            == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        assert (
            response.headers['Content-Disposition']
            == 'attachment; filename="moral_check_log.xlsx"'
        )
        assert response.data == b'test data'

    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'generate_moral_check_log_excel_bytes'
    )
    def test_get_moral_check_log_excel_response_with_separation(
        self, mock_generate_moral_check_log_excel_bytes
    ):
        mock_output = BytesIO(b'test data')

        mock_generate_moral_check_log_excel_bytes.return_value = mock_output

        response = get_moral_check_log_excel_response(True)

        assert isinstance(response, Response)
        assert response.status_code == 200
        assert (
            response.mimetype
            == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        assert (
            response.headers['Content-Disposition']
            == 'attachment; filename="moral_check_log_separation.xlsx"'
        )
        assert response.data == b'test data'

    @pytest.mark.usefixtures('with_request_context')
    @patch('ckanext.feedback.controllers.api.moral_check_log.request.headers.get')
    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'AuthTokenHandler.validate_api_token'
    )
    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'AuthTokenHandler.decode_api_token'
    )
    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'user_service.get_user_by_token_id'
    )
    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'AuthTokenHandler.check_sysadmin'
    )
    @patch('ckanext.feedback.controllers.api.moral_check_log.request.args.get')
    @patch(
        'ckanext.feedback.controllers.api.moral_check_log.'
        'get_moral_check_log_excel_response'
    )
    def test_download_moral_check_log(
        self,
        mock_get_moral_check_log_excel_response,
        mock_request_args_get,
        mock_check_sysadmin,
        mock_get_user_by_token_id,
        mock_decode_api_token,
        mock_validate_api_token,
        mock_request_headers_get,
        user,
        api_token,
    ):
        mock_request_headers_get.return_value = api_token['token']
        mock_validate_api_token.return_value = None
        mock_decode_api_token.return_value = api_token_lib.decode(api_token['token'])[
            'jti'
        ]
        mock_get_user_by_token_id.return_value = user
        mock_check_sysadmin.return_value = None
        mock_request_args_get.return_value = False
        mock_get_moral_check_log_excel_response.return_value = Response(
            b'test data',
            mimetype=(
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ),
            headers={
                'Content-Disposition': 'attachment; filename="moral_check_log.xlsx"'
            },
        )

        response = download_moral_check_log()

        assert response.status_code == 200
        assert (
            response.mimetype
            == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        assert (
            response.headers['Content-Disposition']
            == 'attachment; filename="moral_check_log.xlsx"'
        )
        assert response.data == b'test data'
