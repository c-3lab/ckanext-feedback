import io

import pandas as pd
from flask import Response, request

from ckanext.feedback.services.resource import comment as resource_comment_service
from ckanext.feedback.services.user import user as user_service
from ckanext.feedback.services.utilization import details as utilization_detail_service
from ckanext.feedback.utils.auth import AuthTokenHandler


def generate_moral_check_log_excel_bytes(is_separation):
    """
    Generates the moral check log as an Excel file (BytesIO) using pandas.

    - If is_separation is True, outputs two sheets: one for resource comments
        and one for utilization comments.
    - If is_separation is False, combines both types of comments into a single sheet.

    Args:
        is_separation (bool): Whether to separate logs into different sheets
        or combine them.

    Returns:
        BytesIO: The Excel file data in memory.
    """
    resource_comments = resource_comment_service.get_resource_comment_moral_check_logs()
    utilization_comments = (
        utilization_detail_service.get_utilization_comment_moral_check_logs()
    )

    def resource_to_dict(rc):
        return {
            'id': rc.id,
            'resource_id': rc.resource_id,
            'action': rc.action.name,
            'input_comment': rc.input_comment,
            'suggested_comment': rc.suggested_comment,
            'output_comment': rc.output_comment,
            'timestamp': rc.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def utilization_to_dict(uc):
        return {
            'id': uc.id,
            'utilization_id': uc.utilization_id,
            'action': uc.action.name,
            'input_comment': uc.input_comment,
            'suggested_comment': uc.suggested_comment,
            'output_comment': uc.output_comment,
            'timestamp': uc.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }

    resource_dicts = [resource_to_dict(rc) for rc in resource_comments]
    utilization_dicts = [utilization_to_dict(uc) for uc in utilization_comments]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if is_separation:
            pd.DataFrame(resource_dicts).to_excel(
                writer, sheet_name='ResourceCommentMoralCheckLog', index=False
            )
            pd.DataFrame(utilization_dicts).to_excel(
                writer, sheet_name='UtilizationCommentMoralCheckLog', index=False
            )
        else:
            merged = []
            for rc in resource_dicts:
                merged.append(
                    {
                        'id': rc['id'],
                        'type': 'resource',
                        'resource_or_utilization_id': rc['resource_id'],
                        'action': rc['action'],
                        'input_comment': rc['input_comment'],
                        'suggested_comment': rc['suggested_comment'],
                        'output_comment': rc['output_comment'],
                        'timestamp': rc['timestamp'],
                    }
                )
            for uc in utilization_dicts:
                merged.append(
                    {
                        'id': uc['id'],
                        'type': 'utilization',
                        'resource_or_utilization_id': uc['utilization_id'],
                        'action': uc['action'],
                        'input_comment': uc['input_comment'],
                        'suggested_comment': uc['suggested_comment'],
                        'output_comment': uc['output_comment'],
                        'timestamp': uc['timestamp'],
                    }
                )
            pd.DataFrame(merged).to_excel(
                writer, sheet_name='MoralCheckLog', index=False
            )
    output.seek(0)
    return output


def get_moral_check_log_excel_response(is_separation):
    """
    Creates the Excel response for the moral check log.

    This function calls `generate_moral_check_log_excel_bytes` to create an Excel
    workbook and returns a Flask Response object with the Excel file
    for download.

    Args:
        is_separation (bool): Determines whether to separate the logs into
        different sheets or combine them into one.

    Returns:
        Response: A Flask Response object containing the Excel file
        for download.
    """
    output = generate_moral_check_log_excel_bytes(is_separation)
    filename = (
        "moral_check_log_separation.xlsx" if is_separation else "moral_check_log.xlsx"
    )
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# /api/feedback/download_moral_check_log
def download_moral_check_log():
    """
    Handles the download of the moral check log as an Excel file.
    Ensures the user is authenticated and authorized as a sysadmin.

    This function retrieves the API token from the request headers,
    validates it, decodes it to get the token ID, and checks if the
    associated user is a sysadmin. If all checks pass, it generates
    an Excel file containing the moral check log.

    Returns:
        Response: A Flask Response object containing the Excel file
        for download.

    Raises:
        toolkit.NotAuthorized: If the API token is missing, invalid,
        or if the user is not a sysadmin.
    """
    api_token = request.headers.get("Authorization")
    AuthTokenHandler.validate_api_token(api_token)
    token_id = AuthTokenHandler.decode_api_token(api_token)
    user = user_service.get_user_by_token_id(token_id)
    AuthTokenHandler.check_sysadmin(user)
    is_separation = request.args.get("separation", "false") == "true"
    return get_moral_check_log_excel_response(is_separation)
