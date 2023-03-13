from ckan.common import c, request
from ckan.plugins import toolkit
from flask import redirect, url_for

import ckanext.feedback.services.utilization.details as detail_service
import ckanext.feedback.services.utilization.search as search_service
from ckanext.feedback.models.session import session


class UtilizationController:
    # Render HTML pages
    # utilization/details.html
    @staticmethod
    def details(utilization_id):
        approval = c.userobj is None or c.userobj.sysadmin is None
        utilization = detail_service.get_utilization(utilization_id)
        comments = detail_service.get_utilization_comments(utilization_id, approval)
        categories = detail_service.get_utilization_comment_categories()

        return toolkit.render(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': utilization,
                'comments': comments,
                'categories': categories,
            },
        )

    # utilization/<utilization_id>/approve
    def approve(utilization_id):
        approval_user_id = request.form.get('approval_user_id')
        detail_service.approve_utilization(utilization_id, approval_user_id)
        session.commit()

        return redirect(url_for('utilization.details', utilization_id=utilization_id))

    # utilization/<utilization_id>/create_comment
    def create_comment(utilization_id):
        category = request.form.get('category', '')
        content = request.form.get('content', '')
        detail_service.create_utilization_comment(utilization_id, category, content)
        session.commit()

        return redirect(url_for('utilization.details', utilization_id=utilization_id))

    # utilization/<utilization_id>/approve_comment
    def approve_comment(utilization_id):
        comment_id = request.form.get('comment_id')
        approval_user_id = request.form.get('approval_user_id')
        detail_service.approve_utilization_comment(comment_id, approval_user_id)
        session.commit()

        return redirect(url_for('utilization.details', utilization_id=utilization_id))

    # utilization/registration.html
    @staticmethod
    def registration():
        return toolkit.render('utilization/registration.html')

    # utilization/comment_approval.html
    @staticmethod
    def comment_approval():
        return toolkit.render('utilization/comment_approval.html')

    # utilization/recommentview.html
    @staticmethod
    def comment():
        return toolkit.render('utilization/comment.html')

    # utilization/search.html
    @staticmethod
    def search():
        id = request.args.get('id', '')
        keyword = request.args.get('keyword', '')
        approval = c.userobj is None or c.userobj.sysadmin is None
        disable_keyword = request.args.get('disable_keyword', '')
        utilizations = search_service.get_utilizations(id, keyword, approval)

        return toolkit.render(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'utilizations': utilizations,
            },
        )
