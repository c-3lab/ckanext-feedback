from ckan.common import request
from ckan.plugins import toolkit

import ckanext.feedback.services.utilization.details as detail_service
import ckanext.feedback.services.utilization.search as search_service


class UtilizationController:
    # Render HTML pages
    # utilization/details.html
    def details():
        utilization_id = request.args.get('utilization_id', '')
        comment_id = request.args.get('comment_id', '')
        comment_type = request.args.get('comment_type', '')
        comment_content = request.args.get('comment_content', '')
        approval_user = request.args.get('approval_user', '')
        details = detail_service.get_utilization_details(utilization_id)
        comments = detail_service.get_utilization_comments(utilization_id)
        submit_comment = detail_service.submit_comment(
            utilization_id, comment_type, comment_content
        )
        submit_approval = detail_service.submit_approval(comment_id, approval_user)

        return toolkit.render(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'details': details,
                'comments': comments,
                'submit_comment': submit_comment,
                'submit_approval': submit_approval,
            },
        )

    # utilization/registration.html
    def registration():
        return toolkit.render('utilization/registration.html')

    # utilization/comment_approval.html
    def comment_approval():
        return toolkit.render('utilization/comment_approval.html')

    # utilization/recommentview.html
    def comment():
        return toolkit.render('utilization/comment.html')

    # utilization/search.html
    def search():
        keyword = request.args.get('keyword', '')
        transitioned = request.args.get('transitioned', '')
        utilizations = search_service.get_utilizations(keyword)
        approved_utilizations = search_service.get_approved_utilizations(keyword)

        return toolkit.render(
            'utilization/search.html',
            {
                'keyword': keyword,
                'transitioned': transitioned,
                'utilizations': utilizations,
                'approved_utilizations': approved_utilizations,
            },
        )
