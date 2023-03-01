from ckan.common import request
from ckan.plugins import toolkit

import ckanext.feedback.services.utilization.details as detail_service
import ckanext.feedback.services.utilization.search as search_service


class UtilizationController:
    # Render HTML pages
    # utilization/details.html
    def details():
        if request.method == 'POST':
            utilization_id = request.form.get('utilization_id', '')
            resource_id = request.form.get('resource_id', '')
            comment_id = request.form.get('comment_id')
            comment_type = request.form.get('comment_type', '')
            comment_content = request.form.get('comment_content', '')
            approval_user = request.form.get('approval_user')
            approval_flag = request.form.get('approval_flag', '')
            comment_flag = request.form.get('comment_flag', '')
            if approval_flag == 'true':
                detail_service.approve_utilization(utilization_id, approval_user)
            elif comment_flag == 'true':
                detail_service.submit_comment(
                    utilization_id, comment_type, comment_content
                )
                detail_service.update_utilization_summary(resource_id)
            elif comment_id:
                detail_service.submit_approval(comment_id, approval_user)
        else:
            utilization_id = request.args.get('utilization_id', '')
        details = detail_service.get_utilization_details(utilization_id)
        comments = detail_service.get_utilization_comments(utilization_id)
        approved_comments = detail_service.get_approved_utilization_comments(
            utilization_id
        )
        categories = detail_service.get_categories()

        return toolkit.render(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'details': details,
                'comments': comments,
                'approved_comments': approved_comments,
                'categories': categories,
            },
        )

    # utilization/registration.html
    def registration():
        return toolkit.render('utilization/registration.html')

    # utilization/edit.html
    def edit():
        return toolkit.render('utilization/edit.html')

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
