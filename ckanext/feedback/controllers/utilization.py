from ckan.common import request
from ckan.plugins import toolkit

import ckanext.feedback.services.utilization.search as search_service


class UtilizationController:
    # Render HTML pages
    # utilization/details.html
    def details():
        return tk.render('utilization/details.html')

    # utilization/registration.html
    def registration():
        return tk.render('utilization/registration.html')

    # utilization/comment_approval.html
    def comment_approval():
        return tk.render('utilization/comment_approval.html')

    # utilization/recommentview.html
    def comment():
        return tk.render('utilization/comment.html')

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
