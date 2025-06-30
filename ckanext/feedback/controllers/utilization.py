import logging

import ckan.model as model
from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.logic import get_action
from ckan.plugins import toolkit

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.utilization.details as detail_service
import ckanext.feedback.services.utilization.edit as edit_service
import ckanext.feedback.services.utilization.registration as registration_service
import ckanext.feedback.services.utilization.search as search_service
import ckanext.feedback.services.utilization.summary as summary_service
import ckanext.feedback.services.utilization.validate as validate_service
from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import UtilizationCommentCategory
from ckanext.feedback.services.common.ai_functions import (
    check_ai_comment,
    suggest_ai_comment,
)
from ckanext.feedback.services.common.check import (
    check_administrator,
    has_organization_admin_role,
    is_organization_admin,
)
from ckanext.feedback.services.common.config import FeedbackConfig
from ckanext.feedback.services.common.send_mail import send_email
from ckanext.feedback.services.recaptcha.check import is_recaptcha_verified

log = logging.getLogger(__name__)


class UtilizationController:
    # Render HTML pages
    # utilization/search
    @staticmethod
    def search():
        id = request.args.get('id', '')
        keyword = request.args.get('keyword', '')
        org_name = request.args.get('organization', '')

        unapproved_status = request.args.get('waiting', 'on')
        approval_status = request.args.get('approval', 'on')

        page, limit, offset, pager_url = get_pagination_value('utilization.search')

        # If the login user is not an admin, display only approved utilizations
        approval = True
        admin_owner_orgs = None
        if not isinstance(current_user, model.User):
            # If the user is not login, display only approved utilizations
            approval = True
        elif current_user.sysadmin:
            # If the user is an admin, display all utilizations
            approval = None
        elif is_organization_admin():
            # If the user is an organization admin, display all utilizations
            approval = None
            admin_owner_orgs = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )

        disable_keyword = request.args.get('disable_keyword', '')
        utilizations, total_count = search_service.get_utilizations(
            id,
            keyword,
            approval,
            admin_owner_orgs,
            org_name,
            limit,
            offset,
        )

        # If the organization name can be identified,
        # set it as a global variable accessible from templates.
        if id and not org_name:
            resource = comment_service.get_resource(id)
            if resource:
                org_name = resource.organization_name
            else:
                org_name = search_service.get_organization_name_from_pkg(id)
        if org_name:
            g.pkg_dict = {
                'organization': {
                    'name': org_name,
                },
            }

        return toolkit.render(
            'utilization/search.html',
            {
                'keyword': keyword,
                'disable_keyword': disable_keyword,
                'unapproved_status': unapproved_status,
                'approval_status': approval_status,
                'page': helpers.Page(
                    collection=utilizations,
                    page=page,
                    url=pager_url,
                    item_count=total_count,
                    items_per_page=limit,
                ),
            },
        )

    # utilization/new
    @staticmethod
    def new(resource_id=None, title='', description=''):
        if not resource_id:
            resource_id = request.args.get('resource_id', '')
        return_to_resource = request.args.get('return_to_resource', False)
        resource = comment_service.get_resource(resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package.id}
        )
        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        return toolkit.render(
            'utilization/new.html',
            {
                'pkg_dict': package,
                'return_to_resource': return_to_resource,
                'resource': resource.Resource,
            },
        )

    # utilization/new
    @staticmethod
    def create():
        package_name = request.form.get('package_name', '')
        resource_id = request.form.get('resource_id', '')
        title = request.form.get('title', '')
        url = request.form.get('url', '')
        description = request.form.get('description', '')

        url_err_msg = validate_service.validate_url(url)
        title_err_msg = validate_service.validate_title(title)
        dsc_err_msg = validate_service.validate_description(description)
        if (url and url_err_msg) or title_err_msg or dsc_err_msg:
            if title_err_msg:
                helpers.flash_error(
                    _(title_err_msg),
                    allow_html=True,
                )
            if url and url_err_msg:
                helpers.flash_error(
                    _(url_err_msg),
                    allow_html=True,
                )
            if dsc_err_msg:
                helpers.flash_error(
                    _(dsc_err_msg),
                    allow_html=True,
                )
            return toolkit.redirect_to(
                'utilization.new',
                resource_id=resource_id,
            )

        if not (resource_id and title and description):
            toolkit.abort(400)

        if not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return toolkit.redirect_to(
                'utilization.new',
                resource_id=resource_id,
                title=title,
                description=description,
            )
        return_to_resource = toolkit.asbool(request.form.get('return_to_resource'))
        utilization = registration_service.create_utilization(
            resource_id, title, url, description
        )
        summary_service.create_utilization_summary(resource_id)
        utilization_id = utilization.id
        session.commit()

        try:
            resource = comment_service.get_resource(resource_id)
            send_email(
                template_name=FeedbackConfig().notice_email.template_utilization.get(),
                organization_id=resource.Resource.package.owner_org,
                subject=FeedbackConfig().notice_email.subject_utilization.get(),
                target_name=resource.Resource.name,
                content_title=title,
                content=description,
                url=toolkit.url_for(
                    'utilization.details', utilization_id=utilization_id, _external=True
                ),
            )
        except Exception:
            log.exception('Send email failed, for feedback notification.')

        helpers.flash_success(
            _(
                'Your application is complete.<br>The utilization will not be displayed'
                ' until approved by an administrator.'
            ),
            allow_html=True,
        )

        if return_to_resource:
            return toolkit.redirect_to(
                'resource.read', id=package_name, resource_id=resource_id
            )
        else:
            return toolkit.redirect_to('dataset.read', id=package_name)

    # utilization/<utilization_id>
    @staticmethod
    def details(utilization_id, category='', content=''):
        approval = True
        utilization = detail_service.get_utilization(utilization_id)
        if not isinstance(current_user, model.User):
            approval = True
        elif (
            has_organization_admin_role(utilization.owner_org) or current_user.sysadmin
        ):
            # if the user is an organization admin or a sysadmin, display all comments
            approval = None

        page, limit, offset, _ = get_pagination_value('utilization.details')

        comments, total_count = detail_service.get_utilization_comments(
            utilization_id, approval, limit=limit, offset=offset
        )
        categories = detail_service.get_utilization_comment_categories()
        issue_resolutions = detail_service.get_issue_resolutions(utilization_id)
        g.pkg_dict = {
            'organization': {
                'name': (
                    comment_service.get_resource(
                        utilization.resource_id
                    ).organization_name
                )
            }
        }
        if not category:
            selected_category = UtilizationCommentCategory.REQUEST.name
        else:
            selected_category = category

        return toolkit.render(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': utilization,
                'categories': categories,
                'issue_resolutions': issue_resolutions,
                'selected_category': selected_category,
                'content': content,
                'page': helpers.Page(
                    collection=comments,
                    page=page,
                    item_count=total_count,
                    items_per_page=limit,
                ),
            },
        )

    # utilization/<utilization_id>/approve
    @staticmethod
    @check_administrator
    def approve(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        resource_id = detail_service.get_utilization(utilization_id).resource_id
        detail_service.approve_utilization(utilization_id, current_user.id)
        summary_service.refresh_utilization_summary(resource_id)
        session.commit()

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/new
    @staticmethod
    def create_comment(utilization_id):
        category = request.form.get('category', '')
        content = request.form.get('comment-content', '')
        if not (category and content):
            toolkit.abort(400)

        if not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return UtilizationController.details(utilization_id, category, content)

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'utilization.details',
                utilization_id=utilization_id,
                category=category,
            )

        detail_service.create_utilization_comment(utilization_id, category, content)
        session.commit()

        category_map = {
            UtilizationCommentCategory.REQUEST.name: _('Request'),
            UtilizationCommentCategory.QUESTION.name: _('Question'),
            UtilizationCommentCategory.THANK.name: _('Thank'),
        }

        try:
            utilization = detail_service.get_utilization(utilization_id)
            send_email(
                template_name=(
                    FeedbackConfig().notice_email.template_utilization_comment.get()
                ),
                organization_id=comment_service.get_resource(
                    utilization.resource_id
                ).Resource.package.owner_org,
                subject=FeedbackConfig().notice_email.subject_utilization_comment.get(),
                target_name=utilization.title,
                category=category_map[category],
                content=content,
                url=toolkit.url_for(
                    'utilization.details', utilization_id=utilization_id, _external=True
                ),
            )
        except Exception:
            log.exception('Send email failed, for feedback notification.')

        helpers.flash_success(
            _(
                'Your comment has been sent.<br>The comment will not be displayed until'
                ' approved by an administrator.'
            ),
            allow_html=True,
        )

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/suggested
    @staticmethod
    def suggested_comment(utilization_id, category, content):
        softened = suggest_ai_comment(comment=content)

        utilization = detail_service.get_utilization(utilization_id)
        g.pkg_dict = {
            'organization': {
                'name': (
                    comment_service.get_resource(
                        utilization.resource_id
                    ).organization_name
                )
            }
        }

        if softened is None:
            return toolkit.render(
                'utilization/expect_suggestion.html',
                {
                    'utilization_id': utilization_id,
                    'utilization': utilization,
                    'selected_category': category,
                    'content': content,
                },
            )

        return toolkit.render(
            'utilization/suggestion.html',
            {
                'utilization_id': utilization_id,
                'utilization': utilization,
                'selected_category': category,
                'content': content,
                'softened': softened,
            },
        )

    # utilization/<utilization_id>/comment/check
    @staticmethod
    def check_comment(utilization_id):
        if request.method == 'GET':
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        category = request.form.get('category', '')
        content = request.form.get('comment-content', '')
        if not (category and content):
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        if not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return UtilizationController.details(utilization_id, category, content)

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'utilization.details',
                utilization_id=utilization_id,
                category=category,
            )

        categories = detail_service.get_utilization_comment_categories()
        utilization = detail_service.get_utilization(utilization_id)
        resource = comment_service.get_resource(utilization.resource_id)
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
        )
        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        if not request.form.get(
            'comment-suggested', False
        ) and FeedbackConfig().moral_keeper_ai.is_enable(
            resource.Resource.package.owner_org
        ):
            if check_ai_comment(comment=content) is False:
                return UtilizationController.suggested_comment(
                    utilization_id=utilization_id,
                    category=category,
                    content=content,
                )

        return toolkit.render(
            'utilization/comment_check.html',
            {
                'pkg_dict': package,
                'utilization_id': utilization_id,
                'utilization': utilization,
                'content': content,
                'selected_category': category,
                'categories': categories,
            },
        )

    # utilization/<utilization_id>/comment/<comment_id>/approve
    @staticmethod
    @check_administrator
    def approve_comment(utilization_id, comment_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        detail_service.approve_utilization_comment(comment_id, current_user.id)
        detail_service.refresh_utilization_comments(utilization_id)
        session.commit()

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/edit
    @staticmethod
    @check_administrator
    def edit(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        utilization_details = edit_service.get_utilization_details(utilization_id)
        resource_details = edit_service.get_resource_details(
            utilization_details.resource_id
        )
        g.pkg_dict = {
            'organization': {
                'name': (
                    comment_service.get_resource(
                        utilization_details.resource_id
                    ).organization_name
                )
            }
        }

        return toolkit.render(
            'utilization/edit.html',
            {
                'utilization_details': utilization_details,
                'resource_details': resource_details,
            },
        )

    # utilization/<utilization_id>/edit
    @staticmethod
    @check_administrator
    def update(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        title = request.form.get('title', '')
        url = request.form.get('url', '')
        description = request.form.get('description', '')
        if not (title and description):
            toolkit.abort(400)

        url_err_msg = validate_service.validate_url(url)
        title_err_msg = validate_service.validate_title(title)
        dsc_err_msg = validate_service.validate_description(description)
        if (url and url_err_msg) or title_err_msg or dsc_err_msg:
            if title_err_msg:
                helpers.flash_error(
                    _(title_err_msg),
                    allow_html=True,
                )
            if url and url_err_msg:
                helpers.flash_error(
                    _(url_err_msg),
                    allow_html=True,
                )
            if dsc_err_msg:
                helpers.flash_error(
                    _(dsc_err_msg),
                    allow_html=True,
                )
            return toolkit.redirect_to(
                'utilization.edit',
                utilization_id=utilization_id,
            )

        edit_service.update_utilization(utilization_id, title, url, description)
        session.commit()

        helpers.flash_success(
            _('The utilization has been successfully updated.'),
            allow_html=True,
        )

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/delete
    @staticmethod
    @check_administrator
    def delete(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        resource_id = detail_service.get_utilization(utilization_id).resource_id
        edit_service.delete_utilization(utilization_id)
        session.commit()
        summary_service.refresh_utilization_summary(resource_id)
        session.commit()

        helpers.flash_success(
            _('The utilization has been successfully deleted.'),
            allow_html=True,
        )

        return toolkit.redirect_to('utilization.search')

    # utilization/<utilization_id>/issue_resolution/new
    @staticmethod
    @check_administrator
    def create_issue_resolution(utilization_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        description = request.form.get('description')
        if not description:
            toolkit.abort(400)

        detail_service.create_issue_resolution(
            utilization_id, description, current_user.id
        )
        summary_service.increment_issue_resolution_summary(utilization_id)
        session.commit()

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    @staticmethod
    def _check_organization_admin_role(utilization_id):
        utilization = detail_service.get_utilization(utilization_id)
        if (
            not has_organization_admin_role(utilization.owner_org)
            and not current_user.sysadmin
        ):
            toolkit.abort(
                404,
                _(
                    'The requested URL was not found on the server. If you entered the'
                    ' URL manually please check your spelling and try again.'
                ),
            )
