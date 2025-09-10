import io

from flask import Response, request
from openpyxl import Workbook

from ckanext.feedback.services.resource import comment as resource_comment_service
from ckanext.feedback.services.user import user as user_service
from ckanext.feedback.services.utilization import details as utilization_detail_service
from ckanext.feedback.utils.auth import AuthTokenHandler


def create_moral_check_log_excel_workbook(is_separation):
    """
    Creates the moral check log to an Excel workbook.

    This function retrieves resource and utilization comments for moral
    checks and writes them into an Excel workbook. If `is_separation` is
    True, it creates separate sheets for resource and utilization comments.
    Otherwise, it combines them into a single sheet.

    Args:
        is_separation (bool): Determines whether to separate the logs into
        different sheets or combine them into one.

    Returns:
        BytesIO: A BytesIO object containing the Excel workbook data.
    """
    wb = Workbook()

    resource_comments = resource_comment_service.get_resource_comment_moral_check_logs()
    utilization_comments = (
        utilization_detail_service.get_utilization_comment_moral_check_logs()
    )

    if is_separation:
        first_sheet = wb.active
        first_sheet.title = 'ResourceCommentMoralCheckLog'
        headers = [
            'id',
            'resource_id',
            'action',
            'input_comment',
            'suggested_comment',
            'output_comment',
            'timestamp',
        ]
        first_sheet.append(headers)
        for resource_comment in resource_comments:
            first_sheet.append(
                [
                    resource_comment.id,
                    resource_comment.resource_id,
                    resource_comment.action.name,
                    resource_comment.input_comment,
                    resource_comment.suggested_comment,
                    resource_comment.output_comment,
                    resource_comment.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                ]
            )

        second_sheet = wb.create_sheet('UtilizationCommentMoralCheckLog')
        headers = [
            'id',
            'utilization_id',
            'action',
            'input_comment',
            'suggested_comment',
            'output_comment',
            'timestamp',
        ]
        second_sheet.append(headers)
        for utilization_comment in utilization_comments:
            second_sheet.append(
                [
                    utilization_comment.id,
                    utilization_comment.utilization_id,
                    utilization_comment.action.name,
                    utilization_comment.input_comment,
                    utilization_comment.suggested_comment,
                    utilization_comment.output_comment,
                    utilization_comment.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                ]
            )
    else:
        sheet = wb.active
        sheet.title = 'MoralCheckLog'
        headers = [
            'id',
            'type',
            'resource_or_utilization_id',
            'action',
            'input_comment',
            'suggested_comment',
            'output_comment',
            'timestamp',
        ]
        sheet.append(headers)
        for resource_comment in resource_comments:
            sheet.append(
                [
                    resource_comment.id,
                    'resource',
                    resource_comment.resource_id,
                    resource_comment.action.name,
                    resource_comment.input_comment,
                    resource_comment.suggested_comment,
                    resource_comment.output_comment,
                    resource_comment.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                ]
            )
        for utilization_comment in utilization_comments:
            sheet.append(
                [
                    utilization_comment.id,
                    'utilization',
                    utilization_comment.utilization_id,
                    utilization_comment.action.name,
                    utilization_comment.input_comment,
                    utilization_comment.suggested_comment,
                    utilization_comment.output_comment,
                    utilization_comment.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                ]
            )

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def create_moral_check_log_excel_response(is_separation):
    """
    Creates the Excel response for the moral check log.

    This function calls `create_moral_check_log_excel_workbook` to create an Excel
    workbook and returns a Flask Response object with the Excel file
    for download.

    Args:
        is_separation (bool): Determines whether to separate the logs into
        different sheets or combine them into one.

    Returns:
        Response: A Flask Response object containing the Excel file
        for download.
    """
    output = create_moral_check_log_excel_workbook(is_separation)
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
    return create_moral_check_log_excel_response(is_separation)
