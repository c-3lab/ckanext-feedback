import logging
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional

import ckan.model as model
from ckan.common import _, current_user, g, request
from ckan.lib import helpers
from ckan.plugins import toolkit
from flask import Response, make_response, send_file
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage

import ckanext.feedback.services.resource.comment as comment_service
import ckanext.feedback.services.resource.likes as likes_service
import ckanext.feedback.services.resource.summary as summary_service
import ckanext.feedback.services.resource.validate as validate_service
from ckanext.feedback.controllers.cookie import (
    get_like_status_cookie,
    get_repeat_post_limit_cookie,
    set_like_status_cookie,
    set_repeat_post_limit_cookie,
)
from ckanext.feedback.controllers.pagination import get_pagination_value
from ckanext.feedback.models.resource_comment import ResourceCommentCategory
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import (
    MoralCheckAction,
    ResourceCommentResponseStatus,
)
from ckanext.feedback.services.common.ai_functions import (
    check_ai_comment,
    suggest_ai_comment,
)
from ckanext.feedback.services.common.check import (
    check_administrator,
    get_authorized_package,
    has_organization_admin_role,
    require_package_access,
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
    COMMENT_SUGGESTED = 'comment-suggested'
    INPUT_COMMENT = 'input-comment'
    SUGGESTED_COMMENT = 'suggested-comment'
    ACTION = 'action'


class DefaultValues:
    """Default values and constants"""

    TRUE_STRING = 'True'
    AUTO_SUGGEST_FAILED = 'AUTO_SUGGEST_FAILED'
    FALSE_STRING = 'False'


class ResponseStatusMap:
    """Response status mapping constants"""

    STATUS_MAP = {
        'status-none': ResourceCommentResponseStatus.STATUS_NONE.name,
        'not-started': ResourceCommentResponseStatus.NOT_STARTED.name,
        'in-progress': ResourceCommentResponseStatus.IN_PROGRESS.name,
        'completed': ResourceCommentResponseStatus.COMPLETED.name,
        'rejected': ResourceCommentResponseStatus.REJECTED.name,
    }


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


@dataclass
class ProcessedInput:
    """Result of processing comment input"""

    form_data: dict
    attached_filename: str | None
    error_response: Response | None


class ResourceController:
    @staticmethod
    def _determine_approval_status(owner_org: str) -> bool | None:
        """
        Determine approval status based on current user.
        Returns: True (only approved), False (all), None (all for admin/sysadmin)
        """
        if not isinstance(current_user, model.User):
            return True
        elif has_organization_admin_role(owner_org) or current_user.sysadmin:
            return None
        return True

    @staticmethod
    def _persist_operation(
        operation: callable, resource_id: str, error_message: str
    ) -> OperationResult:
        """Generic database operation with error handling"""
        try:
            operation()
            session.commit()
            return OperationResult(success=True)
        except SQLAlchemyError:
            session.rollback()
            log.exception(f'Database error for resource {resource_id}')
            return OperationResult(success=False, error_message=_(error_message))
        except Exception:
            session.rollback()
            log.exception(f'Unexpected error for resource {resource_id}')
            return OperationResult(success=False, error_message=_(error_message))

    @staticmethod
    def _parse_rating(rating_str: str) -> int | None:
        """Parse rating string to integer or None"""
        if not rating_str or rating_str == 'None':
            return None
        try:
            return int(rating_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_comment_form_data() -> dict:
        content = request.form.get('comment-content', '')
        category = request.form.get('category', '')
        rating = ResourceController._parse_rating(request.form.get('rating', ''))
        attached_image_filename = request.form.get('attached_image_filename', None)

        return {
            'category': category,
            'content': content,
            'rating': rating,
            'attached_image_filename': attached_image_filename,
        }

    @staticmethod
    def _handle_image_upload(file_key: str) -> str | None:
        attached_image: FileStorage = request.files.get(file_key)
        if not attached_image:
            return None
        return ResourceController._upload_image(attached_image)

    @staticmethod
    def _format_validation_error_message(error: toolkit.ValidationError) -> str:
        """Extract and format error messages from ValidationError"""
        if not isinstance(error.error_summary, dict):
            return str(error.error_summary)

        error_messages = []
        for field, messages in error.error_summary.items():
            if isinstance(messages, list):
                error_messages.extend(messages)
            else:
                error_messages.append(str(messages))

        return '<br>'.join(error_messages)

    @staticmethod
    def _handle_image_upload_with_error_handling(
        file_key: str, resource_id: str, category: str, content: str
    ) -> tuple[str | None, Response | None]:
        """Returns (filename, None) on success, (None, error_response) on error"""
        try:
            uploaded_filename = ResourceController._handle_image_upload(file_key)
            return uploaded_filename, None
        except toolkit.ValidationError as e:
            error_text = ResourceController._format_validation_error_message(e)
            helpers.flash_error(error_text, allow_html=True)
            error_response = ResourceController.comment(resource_id, category, content)
            return None, error_response
        except (IOError, OSError) as e:
            log.exception(f'Image upload failed for resource {resource_id}: {e}')
            toolkit.abort(HTTPStatus.INTERNAL_SERVER_ERROR)
        except Exception as e:
            log.exception(
                f'Unexpected error during image upload for resource {resource_id}: {e}'
            )
            toolkit.abort(HTTPStatus.INTERNAL_SERVER_ERROR)

    @staticmethod
    def _validate_comment_data(
        category: str | None,
        content: str,
        resource_id: str | None = None,
    ) -> tuple[bool, str | None]:
        """Returns (is_valid, error_message)"""
        if not (category and content):
            return False, None

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())
        admin_bypass = False

        if isinstance(current_user, model.User) and resource_id:
            try:
                resource = comment_service.get_resource(resource_id)
                admin_bypass = current_user.sysadmin or has_organization_admin_role(
                    resource.Resource.package.owner_org
                )
            except Exception:
                admin_bypass = current_user.sysadmin

        if (force_all or not admin_bypass) and not is_recaptcha_verified(request):
            return False, _('Bad Captcha. Please try again.')

        if message := validate_service.validate_comment(content):
            return False, _(message)

        return True, None

    @staticmethod
    def _get_resource_context(resource_id: str) -> dict:
        resource = comment_service.get_resource(resource_id)
        context = create_auth_context()
        package = get_authorized_package(resource.Resource.package_id, context)
        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        return {'resource': resource, 'package': package, 'context': context}

    @staticmethod
    def _handle_validation_error(
        resource_id: str,
        error_message: str | None,
        category: str,
        content: str,
        attached_image_filename: str | None = None,
    ):
        if error_message:
            helpers.flash_error(error_message, allow_html=True)
        return ResourceController.comment(
            resource_id, category, content, attached_image_filename
        )

    @staticmethod
    def _send_comment_notification_email(resource_id: str, category: str, content: str):
        """Send notification email. Exceptions are logged but not raised."""
        category_map = {
            ResourceCommentCategory.REQUEST.name: _('Request'),
            ResourceCommentCategory.QUESTION.name: _('Question'),
            ResourceCommentCategory.THANK.name: _('Thank'),
        }

        try:
            resource = comment_service.get_resource(resource_id)
            send_email(
                template_name=(
                    FeedbackConfig().notice_email.template_resource_comment.get()
                ),
                organization_id=resource.Resource.package.owner_org,
                subject=FeedbackConfig().notice_email.subject_resource_comment.get(),
                target_name=resource.Resource.name,
                category=category_map[category],
                content=content,
                url=toolkit.url_for(
                    'resource_comment.comment', resource_id=resource_id, _external=True
                ),
            )
        except Exception:
            log.exception('Send email failed, for feedback notification.')

    # Render HTML pages
    # resource_comment/<resource_id>
    @staticmethod
    def comment(
        resource_id, category='', content='', attached_image_filename: str | None = None
    ):
        resource = comment_service.get_resource(resource_id)

        # Check access and get package data
        context = create_auth_context()
        package = get_authorized_package(resource.Resource.package_id, context)

        approval = ResourceController._determine_approval_status(
            resource.Resource.package.owner_org
        )

        page, limit, offset, _ = get_pagination_value('resource_comment.comment')
        comments, total_count = comment_service.get_resource_comments(
            resource_id, approval, limit=limit, offset=offset
        )

        categories = comment_service.get_resource_comment_categories()
        cookie = get_repeat_post_limit_cookie(resource_id)
        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        selected_category = category or ResourceCommentCategory.REQUEST.name

        return toolkit.render(
            'resource/comment.html',
            {
                'resource': resource.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': cookie,
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

    @staticmethod
    def _persist_comment(
        resource_id: str,
        category: str,
        content: str,
        rating: int | None,
        attached_image_filename: str | None,
    ) -> OperationResult:
        """Persist comment to database"""
        try:
            comment_service.create_resource_comment(
                resource_id, category, content, rating, attached_image_filename
            )
            summary_service.create_resource_summary(resource_id)
            session.commit()
            return OperationResult(success=True)
        except SQLAlchemyError:
            session.rollback()
            log.exception(
                f'Database error while creating comment for resource {resource_id}'
            )
            return OperationResult(
                success=False,
                error_message=_('Failed to create comment. Please try again.'),
            )
        except Exception:
            session.rollback()
            log.exception(
                f'Unexpected error while creating comment for resource {resource_id}'
            )
            return OperationResult(
                success=False,
                error_message=_('Failed to create comment. Please try again.'),
            )

    @staticmethod
    def _create_success_response(package_name: str, resource_id: str) -> Response:
        """Create success response with flash message and cookie"""
        helpers.flash_success(
            _(
                'Your comment has been sent.<br>The comment will not be displayed until'
                ' approved by an administrator.'
            ),
            allow_html=True,
        )
        resp = make_response(
            toolkit.redirect_to(
                'resource.read', id=package_name, resource_id=resource_id
            )
        )
        return set_repeat_post_limit_cookie(resp, resource_id)

    @staticmethod
    def _process_comment_input(
        file_key: str, resource_id: str, form_data: dict | None = None
    ) -> ProcessedInput:
        """
        Process and validate comment input.
        Returns ProcessedInput with form_data, attached_filename, and error_response.
        """
        if form_data is None:
            form_data = ResourceController._extract_comment_form_data()

        category = form_data['category']
        content = form_data['content']
        attached_image_filename = form_data['attached_image_filename']

        uploaded_filename, error_response = (
            ResourceController._handle_image_upload_with_error_handling(
                file_key, resource_id, category, content
            )
        )
        if error_response:
            return ProcessedInput(form_data, None, error_response)

        if uploaded_filename:
            attached_image_filename = uploaded_filename

        is_valid, error_message = ResourceController._validate_comment_data(
            category, content, resource_id
        )
        if not is_valid:
            error_response = ResourceController._handle_validation_error(
                resource_id, error_message, category, content, attached_image_filename
            )
            return ProcessedInput(form_data, attached_image_filename, error_response)

        return ProcessedInput(form_data, attached_image_filename, None)

    @staticmethod
    def _handle_moral_keeper_ai(
        resource_id: str,
        category: str,
        content: str,
        rating: int | None,
        attached_image_filename: str | None,
    ) -> Response | None:
        """
        Handle moral keeper AI check.
        Returns suggestion page or None if check passes.
        """
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

            comment_service.create_resource_comment_moral_check_log(
                resource_id=resource_id,
                action=action,
                input_comment=input_comment,
                suggested_comment=suggested_comment,
                output_comment=content,
            )
        else:
            if check_ai_comment(comment=content) is False:
                return ResourceController.suggested_comment(
                    resource_id=resource_id,
                    rating=rating,
                    category=category,
                    content=content,
                    attached_image_filename=attached_image_filename,
                )

            comment_service.create_resource_comment_moral_check_log(
                resource_id=resource_id,
                action=MoralCheckAction.CHECK_COMPLETED.name,
                input_comment=content,
                suggested_comment=None,
                output_comment=content,
            )

        return None

    @staticmethod
    def _persist_moral_check_log(resource_id: str) -> OperationResult:
        """Persist moral check log to database"""
        try:
            session.commit()
            return OperationResult(success=True)
        except SQLAlchemyError:
            session.rollback()
            log.exception(
                f'Database error while creating moral check log '
                f'for resource {resource_id}'
            )
            return OperationResult(
                success=False,
                error_message=_('Failed to create moral check log. Please try again.'),
            )
        except Exception:
            session.rollback()
            log.exception(
                f'Unexpected error while creating moral check log '
                f'for resource {resource_id}'
            )
            return OperationResult(
                success=False,
                error_message=_('Failed to create moral check log. Please try again.'),
            )

    # resource_comment/<resource_id>/comment/new
    @staticmethod
    def create_comment(resource_id):
        package_name = request.form.get('package_name', '')

        result = ResourceController._process_comment_input(
            FormFields.IMAGE_UPLOAD, resource_id
        )

        if not (result.form_data['category'] and result.form_data['content']):
            toolkit.abort(HTTPStatus.BAD_REQUEST)

        if result.error_response:
            return result.error_response

        persist_result = ResourceController._persist_comment(
            resource_id,
            result.form_data['category'],
            result.form_data['content'],
            result.form_data['rating'],
            result.attached_filename,
        )
        if not persist_result.success:
            helpers.flash_error(persist_result.error_message, allow_html=True)
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        ResourceController._send_comment_notification_email(
            resource_id, result.form_data['category'], result.form_data['content']
        )

        return ResourceController._create_success_response(package_name, resource_id)

    # resource_comment/<resource_id>/comment/suggested
    @staticmethod
    def suggested_comment(
        resource_id,
        category='',
        content='',
        rating='',
        attached_image_filename: Optional[str] = None,
    ):
        resource = comment_service.get_resource(resource_id)

        # Check access and get package data in a single efficient call
        context = create_auth_context()
        package = get_authorized_package(resource.Resource.package_id, context)

        softened = suggest_ai_comment(comment=content)

        g.pkg_dict = {'organization': {'name': resource.organization_name}}

        common_context = {
            'resource': resource.Resource,
            'pkg_dict': package,
            'selected_category': category,
            'rating': rating,
            'content': content,
            'attached_image_filename': attached_image_filename,
            'action': MoralCheckAction,
        }

        if softened is None:
            return toolkit.render('resource/expect_suggestion.html', common_context)

        return toolkit.render(
            'resource/suggestion.html', {**common_context, 'softened': softened}
        )

    # resource_comment/<resource_id>/comment/check
    @staticmethod
    def check_comment(resource_id):
        if request.method == 'GET':
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        # Early check for category and content before processing
        form_data = ResourceController._extract_comment_form_data()
        if not (form_data['category'] and form_data['content']):
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        # Process with existing form_data to avoid duplication
        result = ResourceController._process_comment_input(
            FormFields.ATTACHED_IMAGE, resource_id, form_data
        )

        if result.error_response:
            return result.error_response

        resource_context = ResourceController._get_resource_context(resource_id)
        categories = comment_service.get_resource_comment_categories()

        if FeedbackConfig().moral_keeper_ai.is_enable(
            resource_context['resource'].Resource.package.owner_org
        ):
            ai_response = ResourceController._handle_moral_keeper_ai(
                resource_id,
                result.form_data['category'],
                result.form_data['content'],
                result.form_data['rating'],
                result.attached_filename,
            )
            if ai_response:
                return ai_response

            persist_result = ResourceController._persist_moral_check_log(resource_id)
            if not persist_result.success:
                helpers.flash_error(persist_result.error_message, allow_html=True)
                return toolkit.redirect_to(
                    'resource_comment.comment', resource_id=resource_id
                )

        return toolkit.render(
            'resource/comment_check.html',
            {
                'resource': resource_context['resource'].Resource,
                'pkg_dict': resource_context['package'],
                'categories': categories,
                'selected_category': result.form_data['category'],
                'rating': result.form_data['rating'],
                'content': result.form_data['content'],
                'attached_image_filename': result.attached_filename,
            },
        )

    # resource_comment/<resource_id>/comment/check/attached_image/<attached_image_filename>
    @staticmethod
    def check_attached_image(resource_id: str, attached_image_filename: str):
        attached_image_path = comment_service.get_attached_image_path(
            attached_image_filename
        )
        return send_file(attached_image_path)

    # resource_comment/<resource_id>/comment/approve
    @staticmethod
    @check_administrator
    def approve_comment(resource_id):
        ResourceController._check_organization_admin_role(resource_id)
        resource_comment_id = request.form.get('resource_comment_id')
        if not resource_comment_id:
            toolkit.abort(HTTPStatus.BAD_REQUEST)

        def operation():
            comment_service.approve_resource_comment(
                resource_comment_id, current_user.id
            )
            summary_service.refresh_resource_summary(resource_id)

        result = ResourceController._persist_operation(
            operation, resource_id, 'Failed to approve comment. Please try again.'
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)

        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

    @staticmethod
    @check_administrator
    def approve_reply(resource_id):
        ResourceController._check_organization_admin_role(resource_id)
        reply_id = request.form.get('resource_comment_reply_id')
        if not reply_id:
            toolkit.abort(HTTPStatus.BAD_REQUEST)

        try:
            comment_service.approve_reply(reply_id, current_user.id)
            session.commit()
        except PermissionError:
            helpers.flash_error(
                _('Cannot approve reply before the parent comment is approved.'),
                allow_html=True,
            )
        except ValueError:
            toolkit.abort(HTTPStatus.NOT_FOUND)
        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

    # resource_comment/<resource_id>/comment/reply
    @staticmethod
    def reply(resource_id):
        resource_comment_id = request.form.get('resource_comment_id', '')
        content = request.form.get('reply_content', '')
        if not (resource_comment_id and content):
            toolkit.abort(HTTPStatus.BAD_REQUEST)

        attached_image_filename = None
        attached_image: FileStorage = request.files.get("attached_image")
        if attached_image:
            try:
                attached_image_filename = ResourceController._upload_image(
                    attached_image
                )
            except toolkit.ValidationError as e:
                helpers.flash_error(e.error_summary, allow_html=True)
                return toolkit.redirect_to(
                    'resource_comment.comment', resource_id=resource_id
                )
            except Exception as e:
                log.exception(f'Exception: {e}')
                toolkit.abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        # Admins (org-admin or sysadmin) skip reCAPTCHA unless forced
        force_all = toolkit.asbool(FeedbackConfig().recaptcha.force_all.get())

        # Reply permission control (admin or reply_open)
        reply_open = False
        _res = None
        is_admin = False

        # Get resource and check reply_open setting
        try:
            _res = comment_service.get_resource(resource_id)
            reply_open = FeedbackConfig().resource_comment.reply_open.is_enable(
                _res.Resource.package.owner_org
            )
        except Exception:
            reply_open = False

        # Check if user is admin (only for logged-in users)
        if isinstance(current_user, model.User):
            try:
                is_admin = current_user.sysadmin or has_organization_admin_role(
                    _res.Resource.package.owner_org
                )
            except Exception:
                is_admin = current_user.sysadmin

        if not (reply_open or is_admin):
            helpers.flash_error(
                _('Reply is restricted to administrators.'), allow_html=True
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        if (force_all or not is_admin) and is_recaptcha_verified(request) is False:
            helpers.flash_error(_('Bad Captcha. Please try again.'), allow_html=True)
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        if message := validate_service.validate_comment(content):
            helpers.flash_error(
                _(message),
                allow_html=True,
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )

        creator_user_id = (
            current_user.id if isinstance(current_user, model.User) else None
        )

        def operation():
            comment_service.create_reply(
                resource_comment_id, content, creator_user_id, attached_image_filename
            )

        result = ResourceController._persist_operation(
            operation, resource_id, 'Failed to create reply. Please try again.'
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)

        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

    @staticmethod
    def reply_attached_image(
        resource_id: str, reply_id: str, attached_image_filename: str
    ):
        resource = comment_service.get_resource(resource_id)
        if resource is None:
            return toolkit.abort(HTTPStatus.NOT_FOUND)

        approval = True
        if isinstance(current_user, model.User) and (
            current_user.sysadmin
            or has_organization_admin_role(resource.Resource.package.owner_org)
        ):
            approval = None

        from ckanext.feedback.models.resource_comment import (
            ResourceComment,
            ResourceCommentReply,
        )

        reply_query = (
            _session.query(ResourceCommentReply)
            .join(
                ResourceComment,
                ResourceCommentReply.resource_comment_id == ResourceComment.id,
            )
            .filter(
                ResourceCommentReply.id == reply_id,
                ResourceComment.resource_id == resource_id,
            )
        )
        if approval is not None:
            reply_query = reply_query.filter(ResourceCommentReply.approval == approval)
        reply = reply_query.first()
        if reply is None or reply.attached_image_filename != attached_image_filename:
            return toolkit.abort(HTTPStatus.NOT_FOUND)

        attached_image_path = comment_service.get_attached_image_path(
            attached_image_filename
        )
        if not os.path.exists(attached_image_path):
            return toolkit.abort(HTTPStatus.NOT_FOUND)
        return send_file(attached_image_path)

    # resource_comment/<resource_id>/comment/<comment_id>/attached_image/<attached_image_filename>
    @staticmethod
    def attached_image(resource_id: str, comment_id: str, attached_image_filename: str):
        resource = comment_service.get_resource(resource_id)
        if resource is None:
            toolkit.abort(HTTPStatus.NOT_FOUND)

        approval = ResourceController._determine_approval_status(
            resource.Resource.package.owner_org
        )

        comment = comment_service.get_resource_comment(
            comment_id, resource_id, approval, attached_image_filename
        )
        if comment is None:
            toolkit.abort(HTTPStatus.NOT_FOUND)

        attached_image_path = comment_service.get_attached_image_path(
            attached_image_filename
        )
        if not os.path.exists(attached_image_path):
            toolkit.abort(HTTPStatus.NOT_FOUND)

        return send_file(attached_image_path)

    @staticmethod
    def _check_organization_admin_role(resource_id):
        from ckanext.feedback.services.common.check import NOT_FOUND_ERROR_MESSAGE

        resource = comment_service.get_resource(resource_id)

        # Check package access authorization
        context = create_auth_context()
        require_package_access(resource.Resource.package_id, context)

        if (
            not has_organization_admin_role(resource.Resource.package.owner_org)
            and not current_user.sysadmin
        ):
            toolkit.abort(HTTPStatus.NOT_FOUND, NOT_FOUND_ERROR_MESSAGE)

    @staticmethod
    def like_status(resource_id):
        status = get_like_status_cookie(resource_id)
        return status or DefaultValues.FALSE_STRING

    @staticmethod
    def like_toggle(package_name, resource_id):
        data = request.get_json()
        like_status_raw = data.get('likeStatus')
        like_status = (
            like_status_raw
            if isinstance(like_status_raw, bool)
            else str(like_status_raw).lower() == 'true'
        )

        def operation():
            if like_status:
                likes_service.increment_resource_like_count(resource_id)
                likes_service.increment_resource_like_count_monthly(resource_id)
            else:
                likes_service.decrement_resource_like_count(resource_id)
                likes_service.decrement_resource_like_count_monthly(resource_id)

        result = ResourceController._persist_operation(
            operation, resource_id, 'Failed to toggle like.'
        )

        if not result.success:
            return Response(
                'Error', status=HTTPStatus.INTERNAL_SERVER_ERROR, mimetype='text/plain'
            )

        resp = Response('OK', status=HTTPStatus.OK, mimetype='text/plain')
        return set_like_status_cookie(resp, resource_id, like_status)

    # resource_comment/<resource_id>/comment/reactions
    @staticmethod
    @check_administrator
    def reactions(resource_id):
        ResourceController._check_organization_admin_role(resource_id)

        comment_id = request.form.get('resource_comment_id')
        # Normalize and validate comment id
        if comment_id is not None:
            comment_id = comment_id.strip()
        if not comment_id:
            log.error(
                'reactions: missing resource_comment_id (resource_id=%s)', resource_id
            )
            helpers.flash_error(
                _('Failed to change status due to invalid target.'), allow_html=True
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )
        target_comment = comment_service.get_resource_comment(
            comment_id=comment_id, resource_id=resource_id
        )
        if target_comment is None:
            log.error(
                'reactions: comment not found or not belong to resource '
                '(resource_id=%s, comment_id=%s)',
                resource_id,
                comment_id,
            )
            helpers.flash_error(
                _('Failed to change status due to invalid target.'), allow_html=True
            )
            return toolkit.redirect_to(
                'resource_comment.comment', resource_id=resource_id
            )
        # Use canonical id from DB to avoid empty/invalid ids propagating further
        comment_id = str(getattr(target_comment, 'id'))
        response_status = request.form.get('response_status')
        admin_liked = request.form.get('admin_liked') == 'on'

        resource_comment_reactions = comment_service.get_resource_comment_reactions(
            comment_id
        )

        def operation():
            mapped_status = ResponseStatusMap.STATUS_MAP[response_status]
            if resource_comment_reactions:
                comment_service.update_resource_comment_reactions(
                    resource_comment_reactions,
                    mapped_status,
                    admin_liked,
                    current_user.id,
                )
            else:
                comment_service.create_resource_comment_reactions(
                    comment_id,
                    mapped_status,
                    admin_liked,
                    current_user.id,
                )

        result = ResourceController._persist_operation(
            operation, resource_id, 'Failed to update reactions. Please try again.'
        )

        if not result.success:
            helpers.flash_error(result.error_message, allow_html=True)

        return toolkit.redirect_to('resource_comment.comment', resource_id=resource_id)

    @staticmethod
    def _upload_image(image: FileStorage) -> str:
        """Upload an image file with validation."""

        upload_destination = comment_service.get_upload_destination()
        return upload_image_with_validation(image, upload_destination)

    # resource_comment/<resource_id>/comment/create_previous_log
    @staticmethod
    def create_previous_log(resource_id):
        resource = comment_service.get_resource(resource_id)
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
            comment_service.create_resource_comment_moral_check_log(
                resource_id=resource_id,
                action=action,
                input_comment=input_comment,
                suggested_comment=suggested_comment,
                output_comment=None,
            )

        # Return 204 even on error to avoid disrupting UI
        ResourceController._persist_operation(
            operation, resource_id, 'Failed to create previous log.'
        )

        return '', HTTPStatus.NO_CONTENT
