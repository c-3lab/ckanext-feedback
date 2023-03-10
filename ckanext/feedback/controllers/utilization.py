from ckan.common import c, request
from ckan.plugins import toolkit

import ckanext.feedback.services.utilization.search as search_service


class UtilizationController:
    # Render HTML pages
    # utilization/details.html
    @staticmethod
    def details():
        return toolkit.render('utilization/details.html')

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
        approval = None
        if c.userobj is None or c.userobj.sysadmin is None:
            approval = True
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
