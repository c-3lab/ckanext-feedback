from ckan.common import request
from ckan.plugins import toolkit

import ckanext.feedback.services.utilization.search as search_service


class UtilizationController:
    # Render HTML pages
    # utilization/details.html
    def details():
        return toolkit.render('utilization/details.html')

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
        utilizations = search_service.get_utilizations(keyword)

        return toolkit.render(
            'utilization/search.html',
            {'keyword': keyword, 'utilizations': utilizations},
        )
