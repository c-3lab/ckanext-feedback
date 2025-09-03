import io

from openpyxl import Workbook

from ckanext.feedback.services.resource import comment as resource_comment_service
from ckanext.feedback.services.utilization import details as utilization_detail_service


def export_moral_check_log(is_separation):
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
