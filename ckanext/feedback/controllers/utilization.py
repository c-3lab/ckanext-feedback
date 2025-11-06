import logging
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Callable

import ckan.model as model
from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.plugins import toolkit
from flask import Response, send_file
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.utilization.details as detail_service
import ckanext.feedback.services.utilization.edit as edit_service
import ckanext.feedback.services.utilization.registration as registration_service
import ckanext.feedback.services.utilization.search as search_service
import ckanext.feedback.services.utilization.summary as summary_service
import ckanext.feedback.services.utilization.validate as validate_service
from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    MoralCheckAction,
    UtilizationCommentCategory,
)
from ckanext.feedback.services.common.ai_functions import (
    check_ai_comment,
    suggest_ai_comment,
)
from ckanext.feedback.services.common.check import (
    check_administrator,
    get_authorized_package,
    has_organization_admin_role,
    is_organization_admin,
    require_package_access,
    require_resource_package_access,
)
from ckanext.feedback.services.common.config import FeedbackConfig
from ckanext.feedback.services.common.send_mail import send_email
from ckanext.feedback.services.common.upload import upload_image_with_validation
from ckanext.feedback.services.recaptcha.check import is_recaptcha_verified
from ckanext.feedback.utils.auth import create_auth_context

log = logging.getLogger(__name__)

# Expose session as _session for test patching
_session = session


class FormFields:
    """Form field name constants"""

    IMAGE_UPLOAD = 'image-upload'
    ATTACHED_IMAGE = 'attached_image'
    CATEGORY = 'category'
    COMMENT_CONTENT = 'comment-content'
    ATTACHED_IMAGE_FILENAME = 'attached_image_filename'
    RETURN_TO_RESOURCE = 'return_to_resource'
    COMMENT_SUGGESTED = 'comment-suggested'
    INPUT_COMMENT = 'input-comment'
    SUGGESTED_COMMENT = 'suggested-comment'
    ACTION = 'action'
    TITLE = 'title'
    URL = 'url'
    DESCRIPTION = 'description'
    PACKAGE_NAME = 'package_name'
    RESOURCE_ID = 'resource_id'


class QueryParams:
    """URL query parameter constants"""

    RESOURCE_ID = 'resource_id'
    PACKAGE_ID = 'package_id'
    KEYWORD = 'keyword'
    ORGANIZATION = 'organization'
    WAITING = 'waiting'
    APPROVAL = 'approval'
    DISABLE_KEYWORD = 'disable_keyword'


class DefaultValues:
    """Default values and constants"""

    ON = 'on'
    TRUE_STRING = 'True'
    FALSE_STRING = 'False'
    AUTO_SUGGEST_FAILED = 'AUTO_SUGGEST_FAILED'
    EMPTY_STRING = ''


class MoralCheckActionMap:
    """Moral check action mapping constants"""

    ACTION_MAP = {
        'suggestion': MoralCheckAction.PREVIOUS_SUGGESTION.name,
        'confirm': MoralCheckAction.PREVIOUS_CONFIRM.name,
    }


@dataclass
class OperationResult:
    """Generic result for operations that can succeed or fail"""

    success: bool
    error_message: str | None = None
    data: Any | None = None


@dataclass
class ApprovalContext:
    """Approval status context for determining user permissions"""

    approval: bool | None
    admin_owner_orgs: list[str] | None
    user_orgs: list[str] | str | None


@dataclass
class ProcessedInput:
    """Result of processing comment input"""

    form_data: dict
    attached_filename: str | None
    error_response: Response | None


class UtilizationController:
    """Controller for utilization-related operations"""

    @staticmethod
    def _determine_approval_context() -> ApprovalContext:
        """
        Determine approval context based on current user.

        Returns:
            ApprovalContext with approval status and user organizations
        """
        if not isinstance(current_user, model.User):
            return ApprovalContext(approval=True, admin_owner_orgs=None, user_orgs=None)
        elif current_user.sysadmin:
            return ApprovalContext(
                approval=None, admin_owner_orgs=None, user_orgs='all'
            )
        elif is_organization_admin():
            admin_orgs = current_user.get_group_ids(
                group_type='organization', capacity='admin'
            )
            user_orgs = current_user.get_group_ids(group_type='organization')
            return ApprovalContext(
                approval=None, admin_owner_orgs=admin_orgs, user_orgs=user_orgs
            )
        else:
            user_orgs = current_user.get_group_ids(group_type='organization')
            return ApprovalContext(
                approval=True, admin_owner_orgs=None, user_orgs=user_orgs
            )

    @staticmethod
    def _determine_approval_status(owner_org: str) -> bool | None:
        """
        Determine approval status based on current user for details view.

        Returns:
            True (only approved), False (all), None (all for admin/sysadmin)
        """
        if not isinstance(current_user, model.User):
            return True
        elif has_organization_admin_role(owner_org) or current_user.sysadmin:
            return None
        return True

    @staticmethod
    def _persist_operation(
        operation: Callable[[], Any], utilization_id: str, error_message: str
    ) -> OperationResult:
        """Generic database operation with error handling"""
        try:
            result = operation()
            session.commit()
            return OperationResult(success=True, data=result)
        except SQLAlchemyError:
            session.rollback()
            log.exception(f'Database error for utilization {utilization_id}')
            return OperationResult(success=False, error_message=_(error_message))
        except Exception:
            session.rollback()
            log.exception(f'Unexpected error for utilization {utilization_id}')
            return OperationResult(success=False, error_message=_(error_message))

    @staticmethod
    def _extract_comment_form_data() -> dict:
        """Extract comment form data from request"""
        category = request.form.get(FormFields.CATEGORY, DefaultValues.EMPTY_STRING)
        content = request.form.get(
            FormFields.COMMENT_CONTENT, DefaultValues.EMPTY_STRING
        )
        attached_image_filename = request.form.get(
            FormFields.ATTACHED_IMAGE_FILENAME, None
        )
        return {
            'category': category,
            'content': content,
            'attached_image_filename': attached_image_filename,
        }

    @staticmethod
    def _handle_image_upload(file_key: str) -> str | None:
        """Handle image upload from request"""
        attached_image: FileStorage = request.files.get(file_key)
        if not attached_image:
            return None
        return UtilizationController._upload_image(attached_image)

    @staticmethod
    def _handle_image_upload_with_error_handling(
        file_key: str, utilization_id: str, category: str, content: str
    ) -> tuple[str | None, Response | None]:
        """Returns (filename, None) on success, (None, error_response) on error"""
        try:
            uploaded_filename = UtilizationController._handle_image_upload(file_key)
            return uploaded_filename, None
        except toolkit.ValidationError as e:
            helpers.flash_error(e.error_summary, allow_html=True)
            # Call details() directly to preserve form data
            error_response = UtilizationController.details(
                utilization_id, category, content
            )
            return None, error_response
        except (IOError, OSError) as e:
            log.exception(f'Image upload failed for utilization {utilization_id}: {e}')
            toolkit.abort(HTTPStatus.INTERNAL_SERVER_ERROR)
        except Exception as e:
            log.exception(
                f'Unexpected error during image upload for utilization'
                f' {utilization_id}: {e}'
            )
            toolkit.abort(HTTPStatus.INTERNAL_SERVER_ERROR)

    @staticmethod
    def _validate_comment_data(
        category: str | None, content: str
    ) -> tuple[bool, str | None]:
        """Returns (is_valid, error_message)"""
        if not (category and content):
            return True, None
        if message := validate_service.validate_comment(content):
            return False, _(message)

        return True, None

    @staticmethod
    def _handle_validation_error(
        utilization_id: str,
        error_message: str | None,
        category: str,
        content: str,
        attached_image_filename: str | None = None,
    ):
        """
        Handle validation error by flashing message and redirecting to
        details page
        """
        if error_message:
            helpers.flash_error(error_message, allow_html=True)
        return toolkit.redirect_to(
            'utilization.details',
            utilization_id=utilization_id,
            category=category,
            attached_image_filename=attached_image_filename,
        )

    @staticmethod
    def _process_comment_input(
        file_key: str, utilization_id: str, form_data: dict | None = None
    ) -> ProcessedInput:
        """
        Returns ProcessedInput with form_data, attached_filename,
        and error_response
        """
        if form_data is None:
            form_data = UtilizationController._extract_comment_form_data()

        category = form_data['category']
        content = form_data['content']
        attached_image_filename = form_data['attached_image_filename']

        uploaded_filename, error_response = (
            UtilizationController._handle_image_upload_with_error_handling(
                file_key, utilization_id, category, content
            )
        )
        if error_response:
            return ProcessedInput(form_data, None, error_response)

        if uploaded_filename:
            attached_image_filename = uploaded_filename

        # Check reCAPTCHA (errors call details() directly to preserve form data)

        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False
        if isinstance(current_user, model.User):
            try:
                utilization = detail_service.get_utilization(utilization_id)
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    utilization.owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin

        if (force_all or not admin_bypass) and not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            error_response = UtilizationController.details(
                utilization_id, category, content, attached_image_filename
            )
            return ProcessedInput(form_data, attached_image_filename, error_response)

        # Validate comment data (errors use redirect_to)
        is_valid, error_message = UtilizationController._validate_comment_data(
            category, content
        )
        if not is_valid:
            error_response = UtilizationController._handle_validation_error(
                utilization_id,
                error_message,
                category,
                content,
                attached_image_filename,
            )
            return ProcessedInput(form_data, attached_image_filename, error_response)

        return ProcessedInput(form_data, attached_image_filename, None)

    @staticmethod
    def _handle_moral_keeper_ai(
        utilization_id: str,
        category: str,
        content: str,
        attached_image_filename: str | None,
    ) -> Response | None:
        """Returns suggestion page or None if check passes"""
        is_suggested = (
            request.form.get(FormFields.COMMENT_SUGGESTED, False)
            == DefaultValues.TRUE_STRING
        )

        if is_suggested:
            action = request.form.get(FormFields.ACTION, None)
            input_comment = request.form.get(FormFields.INPUT_COMMENT, None)
            suggested_comment = request.form.get(
                FormFields.SUGGESTED_COMMENT, DefaultValues.AUTO_SUGGEST_FAILED
            )

            detail_service.create_utilization_comment_moral_check_log(
                utilization_id=utilization_id,
                action=action,
                input_comment=input_comment,
                suggested_comment=suggested_comment,
                output_comment=content,
            )
        else:
            if check_ai_comment(comment=content) is False:
                return UtilizationController.suggested_comment(
                    utilization_id=utilization_id,
                    category=category,
                    content=content,
                    attached_image_filename=attached_image_filename,
                )

            detail_service.create_utilization_comment_moral_check_log(
                utilization_id=utilization_id,
                action=MoralCheckAction.CHECK_COMPLETED.name,
                input_comment=content,
                suggested_comment=None,
                output_comment=content,
            )

        return None

    @staticmethod
    def _send_utilization_notification_email(
        resource_id: str, title: str, description: str, utilization_id: str
    ):
        """Send notification email. Exceptions are logged but not raised."""
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

    @staticmethod
    def _send_comment_notification_email(
        utilization_id: str, category: str, content: str
    ):
        """Send notification email for comment. Exceptions are logged but not raised."""
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

    @staticmethod
    def _set_organization_context(org_name: str):
        """Set organization context in global g object"""
        if org_name:
            g.pkg_dict = {'organization': {'name': org_name}}

    @staticmethod
    def _validate_utilization_form(
        title: str, url: str, description: str
    ) -> tuple[bool, list[str]]:
        """Returns (is_valid, error_messages)"""
        errors = []

        if title_err_msg := validate_service.validate_title(title):
            errors.append(_(title_err_msg))

        if url and (url_err_msg := validate_service.validate_url(url)):
            errors.append(_(url_err_msg))

        if dsc_err_msg := validate_service.validate_description(description):
            errors.append(_(dsc_err_msg))

        return len(errors) == 0, errors

    @staticmethod
    def _flash_validation_errors(errors: list[str]):
        """Flash multiple validation error messages"""
        for error in errors:
            helpers.flash_error(error, allow_html=True)

    # === Render HTML Pages ===

    # utilization/search
    @staticmethod
    def search():
        # Accept explicit resource_id or package_id parameters
        resource_id = request.args.get(
            QueryParams.RESOURCE_ID, DefaultValues.EMPTY_STRING
        )
        package_id = request.args.get(
            QueryParams.PACKAGE_ID, DefaultValues.EMPTY_STRING
        )

        keyword = request.args.get(QueryParams.KEYWORD, DefaultValues.EMPTY_STRING)
        org_name = request.args.get(
            QueryParams.ORGANIZATION, DefaultValues.EMPTY_STRING
        )

        unapproved_status = request.args.get(QueryParams.WAITING, DefaultValues.ON)
        approval_status = request.args.get(QueryParams.APPROVAL, DefaultValues.ON)

        page, limit, offset, pager_url = get_pagination_value('utilization.search')

        resource_for_org = None

        # Create context for authorization checks
        context = create_auth_context()

        # Check package access authorization for resource_id
        if resource_id:
            require_resource_package_access(resource_id, context)
            resource_for_org = comment_service.get_resource(resource_id)

        # Check package access authorization for package_id
        if package_id:
            require_package_access(package_id, context)

        # Determine approval context based on user role
        approval_ctx = UtilizationController._determine_approval_context()

        disable_keyword = request.args.get(
            QueryParams.DISABLE_KEYWORD, DefaultValues.EMPTY_STRING
        )
        utilizations, total_count = search_service.get_utilizations(
            resource_id=resource_id,
            package_id=package_id,
            keyword=keyword,
            approval=approval_ctx.approval,
            admin_owner_orgs=approval_ctx.admin_owner_orgs,
            org_name=org_name,
            limit=limit,
            offset=offset,
            user_orgs=approval_ctx.user_orgs,
        )

        # If the organization name can be identified,
        # set it as a global variable accessible from templates.
        if (resource_id or package_id) and not org_name:
            if resource_id and resource_for_org:
                # Already fetched, no need to query again
                org_name = resource_for_org.organization_name
            elif package_id:
                org_name = search_service.get_organization_name_from_pkg(package_id)

        UtilizationController._set_organization_context(org_name)

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
    def new(
        resource_id=None,
        title=DefaultValues.EMPTY_STRING,
        description=DefaultValues.EMPTY_STRING,
    ):
        if not resource_id:
            resource_id = request.args.get(
                QueryParams.RESOURCE_ID, DefaultValues.EMPTY_STRING
            )
        return_to_resource = request.args.get(FormFields.RETURN_TO_RESOURCE, False)
        resource = comment_service.get_resource(resource_id)

        # Check access and get package data in a single efficient call
        context = create_auth_context()
        package = get_authorized_package(resource.Resource.package.id, context)
        UtilizationController._set_organization_context(resource.organization_name)

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
        package_name = request.form.get(
            FormFields.PACKAGE_NAME, DefaultValues.EMPTY_STRING
        )
        resource_id = request.form.get(
            FormFields.RESOURCE_ID, DefaultValues.EMPTY_STRING
        )
        title = request.form.get(FormFields.TITLE, DefaultValues.EMPTY_STRING)
        url = request.form.get(FormFields.URL, DefaultValues.EMPTY_STRING)
        description = request.form.get(
            FormFields.DESCRIPTION, DefaultValues.EMPTY_STRING
        )

        # Validate form data
        is_valid, errors = UtilizationController._validate_utilization_form(
            title, url, description
        )
        if not is_valid:
            UtilizationController._flash_validation_errors(errors)
            return toolkit.redirect_to('utilization.new', resource_id=resource_id)

        if not (resource_id and title and description):
            toolkit.abort(HTTPStatus.BAD_REQUEST)

        if not is_recaptcha_verified(request):
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return toolkit.redirect_to(
                'utilization.new',
                resource_id=resource_id,
                title=title,
                description=description,
            )

        return_to_resource = toolkit.asbool(
            request.form.get(FormFields.RETURN_TO_RESOURCE)
        )

        def operation():
            utilization = registration_service.create_utilization(
                resource_id, title, url, description
            )
            summary_service.create_utilization_summary(resource_id)
            return utilization

        result = UtilizationController._persist_operation(
            operation, resource_id, 'Failed to create utilization. Please try again.'
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)
            return toolkit.redirect_to(
                'utilization.new',
                resource_id=resource_id,
                title=title,
                description=description,
            )

        utilization = result.data
        utilization_id = utilization.id

        UtilizationController._send_utilization_notification_email(
            resource_id, title, description, utilization_id
        )

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
    def details(
        utilization_id,
        category=DefaultValues.EMPTY_STRING,
        content=DefaultValues.EMPTY_STRING,
        attached_image_filename: str | None = None,
    ):
        utilization = detail_service.get_utilization(utilization_id)
        if not utilization:
            toolkit.abort(HTTPStatus.NOT_FOUND, _('Utilization not found'))

        # Check access and get package data in a single efficient call
        context = create_auth_context()
        package = get_authorized_package(utilization.package_id, context)

        approval = UtilizationController._determine_approval_status(
            utilization.owner_org
        )

        page, limit, offset, pager_url = get_pagination_value('utilization.details')

        comments, total_count = detail_service.get_utilization_comments(
            utilization_id, approval, limit=limit, offset=offset
        )

        categories = detail_service.get_utilization_comment_categories()
        issue_resolutions = detail_service.get_issue_resolutions(utilization_id)
        resource = comment_service.get_resource(utilization.resource_id)
        UtilizationController._set_organization_context(resource.organization_name)

        selected_category = (
            category if category else UtilizationCommentCategory.REQUEST.name
        )

        return toolkit.render(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': utilization,
                'pkg_dict': package,
                'categories': categories,
                'issue_resolutions': issue_resolutions,
                'selected_category': selected_category,
                'content': content,
                'attached_image_filename': attached_image_filename,
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
        utilization = detail_service.get_utilization(utilization_id)
        if not utilization:
            toolkit.abort(HTTPStatus.NOT_FOUND, _('Utilization not found'))

        # Use CKAN's authorization system to check package access
        context = create_auth_context()
        require_package_access(utilization.package_id, context)

        def operation():
            detail_service.approve_utilization(utilization_id, current_user.id)
            summary_service.refresh_utilization_summary(utilization.resource_id)

        result = UtilizationController._persist_operation(
            operation,
            utilization_id,
            'Failed to approve utilization. Please try again.',
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/new
    @staticmethod
    def create_comment(utilization_id):
        # Early check for required fields
        form_data = UtilizationController._extract_comment_form_data()
        if not (form_data['category'] and form_data['content']):
            toolkit.abort(HTTPStatus.BAD_REQUEST)

        # Process input with pre-extracted form data
        result = UtilizationController._process_comment_input(
            FormFields.IMAGE_UPLOAD, utilization_id, form_data
        )

        if result.error_response:
            return result.error_response

        def operation():
            detail_service.create_utilization_comment(
                utilization_id,
                result.form_data['category'],
                result.form_data['content'],
                result.attached_filename,
            )

        persist_result = UtilizationController._persist_operation(
            operation, utilization_id, 'Failed to create comment. Please try again.'
        )

        if not persist_result.success:
            helpers.flash_error(persist_result.error_message, allow_html=True)
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        # Send notification
        UtilizationController._send_comment_notification_email(
            utilization_id, result.form_data['category'], result.form_data['content']
        )

        helpers.flash_success(
            _(
                'Your comment has been sent.<br>The comment will not be displayed until'
                ' approved by an administrator.'
            ),
            allow_html=True,
        )

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/reply
    @staticmethod
    def reply(utilization_id):
        utilization_comment_id = request.form.get('utilization_comment_id', '')
        content = request.form.get('reply_content', '')
        if not (utilization_comment_id and content):
            return toolkit.abort(HTTPStatus.BAD_REQUEST)

        # Get utilization first to avoid UnboundLocalError
        try:
            _uti = detail_service.get_utilization(utilization_id)
        except Exception:
            helpers.flash_error(_('Utilization not found.'), allow_html=True)
            return toolkit.redirect_to('utilization.search')

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False
        if isinstance(current_user, model.User):
            try:
                owner_org = _uti.owner_org
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin

        # Reply permission control (admin or reply_open)
        reply_open = False
        try:
            owner_org = _uti.owner_org
            reply_open = FeedbackConfig().utilization_comment.reply_open.is_enable(
                owner_org
            )
        except Exception:
            reply_open = False
        is_org_admin = False
        try:
            owner_org = _uti.owner_org
            is_org_admin = has_organization_admin_role(owner_org)
        except Exception:
            is_org_admin = False
        if not reply_open and not (
            is_org_admin
            or (isinstance(current_user, model.User) and current_user.sysadmin)
        ):
            helpers.flash_error(
                _('Reply is restricted to administrators.'), allow_html=True
            )
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        if (force_all or not admin_bypass) and is_recaptcha_verified(request) is False:
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        creator_user_id = (
            current_user.id if isinstance(current_user, model.User) else None
        )
        attached_image_filename = None
        attached_image: FileStorage = request.files.get("attached_image")
        if attached_image:
            try:
                attached_image_filename = UtilizationController._upload_image(
                    attached_image
                )
            except toolkit.ValidationError as e:
                helpers.flash_error(e.error_summary, allow_html=True)
                return toolkit.redirect_to(
                    'utilization.details', utilization_id=utilization_id
                )
            except Exception as e:
                log.exception(f'Exception: {e}')
                toolkit.abort(HTTPStatus.INTERNAL_SERVER_ERROR)
                return

        def operation():
            detail_service.create_utilization_comment_reply(
                utilization_comment_id,
                content,
                creator_user_id,
                attached_image_filename,
            )

        result = UtilizationController._persist_operation(
            operation, utilization_id, 'Failed to create reply. Please try again.'
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/reply/attached_image/<reply_id>/<attached_image_filename>
    @staticmethod
    def reply_attached_image(
        utilization_id: str, reply_id: str, attached_image_filename: str
    ):
        utilization = detail_service.get_utilization(utilization_id)
        if utilization is None:
            return toolkit.abort(HTTPStatus.NOT_FOUND)

        approval = True
        if isinstance(current_user, model.User) and (
            current_user.sysadmin or has_organization_admin_role(utilization.owner_org)
        ):
            approval = None

        from ckanext.feedback.models.utilization import (
            UtilizationComment,
            UtilizationCommentReply,
        )

        q = (
            _session.query(UtilizationCommentReply)
            .join(
                UtilizationComment,
                UtilizationCommentReply.utilization_comment_id == UtilizationComment.id,
            )
            .filter(
                UtilizationCommentReply.id == reply_id,
                UtilizationComment.utilization_id == utilization_id,
            )
        )
        if approval is not None:
            q = q.filter(UtilizationCommentReply.approval == approval)
        reply = q.first()
        if reply is None or reply.attached_image_filename != attached_image_filename:
            return toolkit.abort(HTTPStatus.NOT_FOUND)

        attached_image_path = detail_service.get_attached_image_path(
            attached_image_filename
        )
        if not os.path.exists(attached_image_path):
            return toolkit.abort(HTTPStatus.NOT_FOUND)
        return send_file(attached_image_path)

    # utilization/<utilization_id>/comment/suggested
    @staticmethod
    def suggested_comment(
        utilization_id,
        category,
        content,
        attached_image_filename: str | None = None,
    ):
        softened = suggest_ai_comment(comment=content)

        utilization = detail_service.get_utilization(utilization_id)
        org_name = comment_service.get_resource(
            utilization.resource_id
        ).organization_name
        UtilizationController._set_organization_context(org_name)

        common_context = {
            'utilization_id': utilization_id,
            'utilization': utilization,
            'selected_category': category,
            'content': content,
            'attached_image_filename': attached_image_filename,
            'action': MoralCheckAction,
        }

        if softened is None:
            return toolkit.render('utilization/expect_suggestion.html', common_context)

        return toolkit.render(
            'utilization/suggestion.html', {**common_context, 'softened': softened}
        )

    # utilization/<utilization_id>/comment/check
    @staticmethod
    def check_comment(utilization_id):
        if request.method == 'GET':
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        # Early check for category and content before processing
        form_data = UtilizationController._extract_comment_form_data()
        if not (form_data['category'] and form_data['content']):
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        # Process with existing form_data to avoid duplication
        result = UtilizationController._process_comment_input(
            FormFields.ATTACHED_IMAGE, utilization_id, form_data
        )

        if result.error_response:
            return result.error_response

        utilization = detail_service.get_utilization(utilization_id)

        categories = detail_service.get_utilization_comment_categories()
        resource = comment_service.get_resource(utilization.resource_id)

        # Check access and get package data in a single efficient call
        context = create_auth_context()
        package = get_authorized_package(resource.Resource.package_id, context)
        UtilizationController._set_organization_context(resource.organization_name)

        if FeedbackConfig().moral_keeper_ai.is_enable(
            resource.Resource.package.owner_org
        ):
            ai_response = UtilizationController._handle_moral_keeper_ai(
                utilization_id,
                result.form_data['category'],
                result.form_data['content'],
                result.attached_filename,
            )
            if ai_response:
                return ai_response

            persist_result = UtilizationController._persist_operation(
                lambda: None,
                utilization_id,
                'Failed to create moral check log. Please try again.',
            )
            if not persist_result.success:
                helpers.flash_error(persist_result.error_message, allow_html=True)
                return toolkit.redirect_to(
                    'utilization.details', utilization_id=utilization_id
                )

        return toolkit.render(
            'utilization/comment_check.html',
            {
                'pkg_dict': package,
                'utilization_id': utilization_id,
                'utilization': utilization,
                'content': result.form_data['content'],
                'selected_category': result.form_data['category'],
                'categories': categories,
                'attached_image_filename': result.attached_filename,
            },
        )

    # <utilization_id>/comment/check/attached_image/<attached_image_filename>
    @staticmethod
    def check_attached_image(utilization_id: str, attached_image_filename: str):
        attached_image_path = detail_service.get_attached_image_path(
            attached_image_filename
        )
        return send_file(attached_image_path)

    # utilization/<utilization_id>/comment/<comment_id>/approve
    @staticmethod
    @check_administrator
    def approve_comment(utilization_id, comment_id):
        UtilizationController._check_organization_admin_role(utilization_id)

        def operation():
            detail_service.approve_utilization_comment(comment_id, current_user.id)
            detail_service.refresh_utilization_comments(utilization_id)

        result = UtilizationController._persist_operation(
            operation, utilization_id, 'Failed to approve comment. Please try again.'
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/reply/<reply_id>/approve
    @staticmethod
    @check_administrator
    def approve_reply(utilization_id, reply_id):
        UtilizationController._check_organization_admin_role(utilization_id)
        try:
            detail_service.approve_utilization_comment_reply(reply_id, current_user.id)
            session.commit()
        except ValueError as e:
            log.warning(f'approve_reply ValueError: {e}')
        except PermissionError:
            helpers.flash_error(
                _('Cannot approve reply because its parent comment is not approved.'),
                allow_html=True,
            )
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
        org_name = comment_service.get_resource(
            utilization_details.resource_id
        ).organization_name
        UtilizationController._set_organization_context(org_name)

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
        title = request.form.get(FormFields.TITLE, DefaultValues.EMPTY_STRING)
        url = request.form.get(FormFields.URL, DefaultValues.EMPTY_STRING)
        description = request.form.get(
            FormFields.DESCRIPTION, DefaultValues.EMPTY_STRING
        )

        if not (title and description):
            toolkit.abort(HTTPStatus.BAD_REQUEST)

        # Validate form data
        is_valid, errors = UtilizationController._validate_utilization_form(
            title, url, description
        )
        if not is_valid:
            UtilizationController._flash_validation_errors(errors)
            return toolkit.redirect_to(
                'utilization.edit', utilization_id=utilization_id
            )

        def operation():
            edit_service.update_utilization(utilization_id, title, url, description)

        result = UtilizationController._persist_operation(
            operation, utilization_id, 'Failed to update utilization. Please try again.'
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)
            return toolkit.redirect_to(
                'utilization.edit', utilization_id=utilization_id
            )

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

        def operation():
            edit_service.delete_utilization(utilization_id)
            summary_service.refresh_utilization_summary(resource_id)

        result = UtilizationController._persist_operation(
            operation, utilization_id, 'Failed to delete utilization. Please try again.'
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

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
        description = request.form.get(FormFields.DESCRIPTION)
        if not description:
            toolkit.abort(HTTPStatus.BAD_REQUEST)

        def operation():
            detail_service.create_issue_resolution(
                utilization_id, description, current_user.id
            )
            summary_service.increment_issue_resolution_summary(utilization_id)

        result = UtilizationController._persist_operation(
            operation,
            utilization_id,
            'Failed to create issue resolution. Please try again.',
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)
            return toolkit.redirect_to(
                'utilization.details', utilization_id=utilization_id
            )

        return toolkit.redirect_to('utilization.details', utilization_id=utilization_id)

    # utilization/<utilization_id>/comment/<comment_id>/attached_image/<attached_image_filename>
    @staticmethod
    def attached_image(
        utilization_id: str, comment_id: str, attached_image_filename: str
    ):
        utilization = detail_service.get_utilization(utilization_id)
        if utilization is None:
            toolkit.abort(HTTPStatus.NOT_FOUND)

        # Use CKAN's authorization system to check package access
        context = create_auth_context()
        require_package_access(utilization.package_id, context)

        approval = UtilizationController._determine_approval_status(
            utilization.owner_org
        )

        comment = detail_service.get_utilization_comment(
            comment_id, utilization_id, approval, attached_image_filename
        )
        if comment is None:
            toolkit.abort(HTTPStatus.NOT_FOUND)

        attached_image_path = detail_service.get_attached_image_path(
            attached_image_filename
        )
        if not os.path.exists(attached_image_path):
            toolkit.abort(HTTPStatus.NOT_FOUND)

        return send_file(attached_image_path)

    @staticmethod
    def _check_organization_admin_role(utilization_id):
        from ckanext.feedback.services.common.check import NOT_FOUND_ERROR_MESSAGE

        utilization = detail_service.get_utilization(utilization_id)
        if not utilization:
            toolkit.abort(HTTPStatus.NOT_FOUND, NOT_FOUND_ERROR_MESSAGE)

        # Use CKAN's authorization system to check package access
        context = create_auth_context()
        require_package_access(utilization.package_id, context)

        if (
            not has_organization_admin_role(utilization.owner_org)
            and not current_user.sysadmin
        ):
            toolkit.abort(HTTPStatus.NOT_FOUND, NOT_FOUND_ERROR_MESSAGE)

    @staticmethod
    def _upload_image(image: FileStorage) -> str:
        """Upload an image file with validation."""
        upload_destination = detail_service.get_upload_destination()
        return upload_image_with_validation(image, upload_destination)

    # utilization/<utilization_id>/comment/create_previous_log
    @staticmethod
    def create_previous_log(utilization_id):
        resource = detail_service.get_resource_by_utilization_id(utilization_id)
        if not FeedbackConfig().moral_keeper_ai.is_enable(
            resource.Resource.package.owner_org
        ):
            return '', HTTPStatus.NO_CONTENT

        data = request.get_json()
        previous_type = data.get('previous_type', None)
        input_comment = data.get('input_comment', None)
        suggested_comment = data.get('suggested_comment', None)

        action = MoralCheckActionMap.ACTION_MAP.get(previous_type, None)
        if action is None:
            return '', HTTPStatus.NO_CONTENT

        def operation():
            detail_service.create_utilization_comment_moral_check_log(
                utilization_id=utilization_id,
                action=action,
                input_comment=input_comment,
                suggested_comment=suggested_comment,
                output_comment=None,
            )

        # Return 204 even on error to avoid disrupting UI
        UtilizationController._persist_operation(
            operation, utilization_id, 'Failed to create previous log.'
        )

        return '', HTTPStatus.NO_CONTENT
