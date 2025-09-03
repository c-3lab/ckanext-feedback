from ckan.lib import api_token as api_token_lib
from ckan.plugins import toolkit
from flask import Response, request

from ckanext.feedback.services.user import user as user_service
from ckanext.feedback.utils.excel_export import export_moral_check_log


def get_api_token_from_request():
    api_token = request.headers.get("Authorization")

    if not api_token:
        return toolkit.abort(401, {"message": "API Token is missing."})

    return api_token


def is_sysadmin_by_token(api_token):
    try:
        data = api_token_lib.decode(api_token)
    except Exception:
        return toolkit.abort(
            401, {"message": "Invalid API Token.", "code": "DECODE_FAILED"}
        )

    token_id = data.get('jti')

    if not token_id:
        return toolkit.abort(
            401, {"message": "Invalid API Token.", "code": "MISSING_JTI"}
        )

    user = user_service.get_user_by_api_token(token_id)

    if not user:
        return toolkit.abort(
            401, {"message": "Invalid API Token.", "code": "USER_NOT_FOUND"}
        )

    return bool(getattr(user, 'sysadmin', False))


def download_moral_check_log():
    api_token = get_api_token_from_request()

    if not is_sysadmin_by_token(api_token):
        return toolkit.abort(403, {"message": "The user is not a sysadmin."})

    is_separation = request.args.get("separation", "false") == "true"

    output = export_moral_check_log(is_separation)

    filename = (
        "moral_check_log_separation.xlsx" if is_separation else "moral_check_log.xlsx"
    )

    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
