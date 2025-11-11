from unittest.mock import MagicMock, Mock, patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.logic import get_action
from ckan.plugins import toolkit
from flask import g
from werkzeug.exceptions import NotFound

import ckanext.feedback.services.resource.comment as comment_service
from ckanext.feedback.controllers.resource import ResourceController
from ckanext.feedback.models.resource_comment import ResourceCommentCategory
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import (
    MoralCheckAction,
    ResourceCommentResponseStatus,
)


@pytest.mark.usefixtures('with_plugins', 'with_request_context')
@pytest.mark.db_test
class TestResourceController:
    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.get_pagination_value')
    @patch('ckanext.feedback.controllers.resource.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.get_repeat_post_limit_cookie')
    def test_comment_with_sysadmin(
        self,
        mock_get_repeat_post_limit_cookie,
        mock_request,
        mock_render,
        mock_page,
        mock_pagination,
        current_user,
        admin_context,
        sysadmin,
        organization,
        resource,
    ):
        current_user.return_value = model.User.get(sysadmin['id'])
        mock_get_repeat_post_limit_cookie.return_value = 'mock_cookie'
        resource_id = resource['id']

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_page.return_value = 'mock_page'

        ResourceController.comment(resource_id)

        approval = None
        res_obj = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()

        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': res_obj.Resource.package_id}
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': res_obj.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': 'mock_cookie',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )
        g.pkg_dict = package
        assert g.pkg_dict["organization"]['name'] == organization['name']

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': res_obj.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': 'mock_cookie',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.get_pagination_value')
    @patch('ckanext.feedback.controllers.resource.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.get_repeat_post_limit_cookie')
    def test_comment_with_user(
        self,
        mock_get_repeat_post_limit_cookie,
        mock_request,
        mock_render,
        mock_page,
        mock_pagination,
        user_context,
        organization,
        resource,
    ):
        mock_get_repeat_post_limit_cookie.return_value = 'mock_cookie'
        resource_id = resource['id']

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_page.return_value = 'mock_page'

        ResourceController.comment(resource_id)

        approval = True
        res_obj = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()

        package = get_action('package_show')(
            {'model': model, 'session': session, 'for_view': True},
            {'id': res_obj.Resource.package_id},
        )
        mock_page.assert_called_once_with(
            collection=comments, page=page, item_count=total_count, items_per_page=limit
        )
        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': res_obj.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': 'mock_cookie',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch(
        'ckanext.feedback.controllers.resource.has_organization_admin_role',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.resource.get_pagination_value')
    @patch('ckanext.feedback.controllers.resource.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.get_repeat_post_limit_cookie')
    def test_comment_with_org_admin(
        self,
        mock_get_repeat_post_limit_cookie,
        mock_request,
        mock_render,
        mock_page,
        mock_pagination,
        _mock_has_org_admin,
        current_user,
        user_context,
        organization,
        resource,
    ):
        mock_get_repeat_post_limit_cookie.return_value = 'mock_cookie'
        resource_id = resource['id']

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [page, limit, offset, _]
        mock_page.return_value = 'mock_page'

        ResourceController.comment(resource_id)

        approval = None
        res_obj = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': res_obj.Resource.package_id}
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )

        g.pkg_dict = package
        assert g.pkg_dict["organization"]['name'] == organization['name']

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': res_obj.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': 'mock_cookie',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.get_pagination_value')
    @patch('ckanext.feedback.controllers.resource.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.get_repeat_post_limit_cookie')
    def test_comment_question_with_user(
        self,
        mock_get_repeat_post_limit_cookie,
        mock_request,
        mock_render,
        mock_page,
        mock_pagination,
        user_context,
        organization,
        resource,
    ):
        resource_id = resource['id']

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_page.return_value = 'mock_page'
        mock_get_repeat_post_limit_cookie.return_value = 'mock_cookie'

        ResourceController.comment(resource_id, category='QUESTION')

        approval = True
        res_obj = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': res_obj.Resource.package_id}
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': res_obj.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': 'mock_cookie',
                'selected_category': 'QUESTION',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch(
        'ckanext.feedback.controllers.resource.has_organization_admin_role',
        return_value=False,
    )
    @patch('ckanext.feedback.controllers.resource.get_pagination_value')
    @patch('ckanext.feedback.controllers.resource.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    @patch('ckanext.feedback.controllers.resource.get_repeat_post_limit_cookie')
    def test_comment_with_non_admin_user(
        self,
        mock_get_repeat_post_limit_cookie,
        mock_request,
        mock_render,
        mock_page,
        mock_pagination,
        _mock_has_org_admin,
        current_user,
        user_context,
        organization,
        resource,
        user,
    ):
        mock_get_repeat_post_limit_cookie.return_value = 'mock_cookie'
        resource_id = resource['id']

        page = 1
        limit = 20
        offset = 0
        _ = ''

        current_user.return_value = model.User.get(user['id'])
        mock_pagination.return_value = [page, limit, offset, _]
        mock_page.return_value = 'mock_page'

        ResourceController.comment(resource_id)

        res_obj = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            True,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': res_obj.Resource.package_id}
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )
        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': res_obj.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': 'mock_cookie',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.resource.get_pagination_value')
    @patch('ckanext.feedback.controllers.resource.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.get_repeat_post_limit_cookie')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_comment_without_user(
        self,
        mock_request,
        mock_get_repeat_post_limit_cookie,
        mock_render,
        mock_page,
        mock_pagination,
        organization,
        resource,
    ):
        resource_id = resource['id']

        page = 1
        limit = 20
        offset = 0
        _ = ''

        mock_pagination.return_value = [
            page,
            limit,
            offset,
            _,
        ]

        mock_page.return_value = 'mock_page'
        mock_get_repeat_post_limit_cookie.return_value = 'mock_cookie'
        ResourceController.comment(resource_id)

        approval = True
        res_obj = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': res_obj.Resource.package_id}
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )

        g.pkg_dict = package
        assert g.pkg_dict["organization"]['name'] == organization['name']

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': res_obj.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': 'mock_cookie',
                'selected_category': 'REQUEST',
                'content': '',
                'attached_image_filename': None,
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_success')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.toolkit.url_for')
    @patch('ckanext.feedback.controllers.resource.make_response')
    @patch('ckanext.feedback.controllers.resource.send_email')
    @patch('ckanext.feedback.controllers.resource.set_repeat_post_limit_cookie')
    def test_create_comment(
        self,
        mock_set_repeat_post_limit_cookie,
        mock_send_email,
        mock_make_response,
        mock_url_for,
        mock_redirect_to,
        mock_session_commit,
        mock_flash_success,
        mock_comment_service,
        mock_summary_service,
        mock_upload_image,
        mock_files,
        mock_form,
    ):
        resource_id = 'resource id'
        package_name = 'package_name'
        category = ResourceCommentCategory.REQUEST.name
        comment_content = 'content'
        rating = '1'
        attached_image_filename = 'attached_image_filename'

        mock_form.get.side_effect = lambda x, default: {
            'package_name': package_name,
            'comment-content': comment_content,
            'category': category,
            'rating': rating,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)

        mock_file = MagicMock()
        mock_file.filename = attached_image_filename
        mock_file.content_type = 'image/png'
        mock_file.read.return_value = b'fake image data'
        mock_files.return_value = mock_file

        mock_upload_image.return_value = attached_image_filename

        mock_send_email.side_effect = Exception("Mock Exception")
        mock_url_for.return_value = 'resource comment'
        ResourceController().create_comment(resource_id)
        mock_comment_service.create_resource_comment.assert_called_once_with(
            resource_id,
            category,
            comment_content,
            int(rating),
            attached_image_filename,
        )
        mock_summary_service.create_resource_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id, _external=True
        )
        mock_redirect_to.assert_called_once_with(
            'resource.read', id=package_name, resource_id=resource_id
        )
        mock_make_response.assert_called_once_with(mock_redirect_to())
        mock_set_repeat_post_limit_cookie.value = 'mock_cookie_value'
        mock_set_repeat_post_limit_cookie.assert_called_once_with(
            mock_make_response(), resource_id
        )

    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_success')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.make_response')
    def test_create_comment_without_category_content(
        self,
        mock_make_response,
        mock_redirect_to,
        mock_session_commit,
        mock_flash_success,
        mock_comment_service,
        mock_summary_service,
        mock_form,
        mock_toolkit_abort,
        mock_validate_comment,
        mock_comment,
    ):
        resource_id = 'resource id'
        mock_form.get.side_effect = lambda x, default: {
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)
        mock_validate_comment.return_value = None

        ResourceController.create_comment(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_image_upload'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._extract_comment_form_data'
    )
    def test_create_comment_with_image_validation_error(
        self,
        mock_extract_form_data,
        mock_handle_image_upload,
        mock_flash_error,
        mock_comment,
    ):
        """Test create_comment handles ValidationError from image upload"""
        resource_id = 'resource-id'
        category = 'REQUEST'
        content = 'Test comment content that is long enough'

        mock_extract_form_data.return_value = {
            'category': category,
            'content': content,
            'rating': None,
            'attached_image_filename': None,
        }

        error_msg = {'image-upload': ['Invalid image format']}
        mock_handle_image_upload.side_effect = toolkit.ValidationError(error_msg)

        result = ResourceController.create_comment(resource_id)

        assert mock_flash_error.called
        call_args = mock_flash_error.call_args
        assert call_args[1]['allow_html'] is True
        assert call_args[0][0] == 'Invalid image format'
        mock_comment.assert_called_once_with(resource_id, category, content)
        assert result == mock_comment.return_value

    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_image_upload'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._extract_comment_form_data'
    )
    def test_create_comment_with_image_ioerror(
        self, mock_extract_form_data, mock_handle_image_upload
    ):
        """Test create_comment handles IOError from image upload"""
        resource_id = 'resource-id'

        mock_extract_form_data.return_value = {
            'category': 'REQUEST',
            'content': 'Test comment content that is long enough',
            'rating': None,
            'attached_image_filename': None,
        }

        mock_handle_image_upload.side_effect = IOError('Disk full')

        from werkzeug.exceptions import InternalServerError

        with pytest.raises(InternalServerError):
            ResourceController.create_comment(resource_id)

    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_create_comment_with_bad_image_exception(
        self,
        mock_abort,
        mock_upload_image,
        mock_files,
        mock_form,
    ):
        resource_id = 'resource id'
        package_name = 'package_name'
        comment_content = 'content'
        category = ResourceCommentCategory.REQUEST.name
        rating = '1'
        attached_image_filename = 'attached_image_filename'

        mock_form.get.side_effect = lambda x, default: {
            'package_name': package_name,
            'comment-content': comment_content,
            'category': category,
            'rating': rating,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)

        mock_file = MagicMock()
        mock_file.filename = attached_image_filename
        mock_file.content_type = 'image/png'
        mock_file.read.return_value = b'fake image data'
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = Exception('Upload failed')

        mock_abort.side_effect = Exception('abort')
        with pytest.raises(Exception):
            ResourceController.create_comment(resource_id)

        mock_upload_image.assert_called_once_with(mock_file)
        mock_abort.assert_called_once_with(500)

    # test_create_comment_without_comment_length and
    # test_create_comment_without_bad_recaptcha removed -
    # covered by TestResourceControllerCommonMethods.test_validate_comment_data_*

    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch('ckanext.feedback.controllers.resource.suggest_ai_comment')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    def test_suggested_comment(
        self,
        mock_get_resource,
        mock_suggest_ai_comment,
        mock_get_authorized_package,
        mock_render,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        attached_image_filename = None
        softened = 'mock_softened'

        mock_suggest_ai_comment.return_value = softened

        mock_get_resource.return_value = MagicMock()

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_resource.organization_name = 'mock_organization_name'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_authorized_package.return_value = mock_package

        ResourceController.suggested_comment(resource_id, category, content, rating)
        mock_render.assert_called_once_with(
            'resource/suggestion.html',
            {
                'resource': mock_resource.Resource,
                'pkg_dict': mock_package,
                'selected_category': category,
                'rating': rating,
                'content': content,
                'attached_image_filename': attached_image_filename,
                'softened': softened,
                'action': MoralCheckAction,
            },
        )

    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch('ckanext.feedback.controllers.resource.suggest_ai_comment')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    def test_suggested_comment_is_None(
        self,
        mock_get_resource,
        mock_suggest_ai_comment,
        mock_get_authorized_package,
        mock_render,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        attached_image_filename = None
        softened = None

        mock_suggest_ai_comment.return_value = softened

        mock_get_resource.return_value = MagicMock()

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_resource.organization_name = 'mock_organization_name'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_authorized_package.return_value = mock_package

        ResourceController.suggested_comment(resource_id, category, content, rating)
        mock_render.assert_called_once_with(
            'resource/expect_suggestion.html',
            {
                'resource': mock_resource.Resource,
                'pkg_dict': mock_package,
                'selected_category': category,
                'rating': rating,
                'content': content,
                'attached_image_filename': attached_image_filename,
                'action': MoralCheckAction,
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_check_comment_GET(
        self,
        mock_redirect_to,
        mock_method,
    ):
        resource_id = 'resource_id'

        mock_method.return_value = 'GET'

        ResourceController.check_comment(resource_id)
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.get_resource_comment_categories'
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    def test_check_comment_POST_moral_keeper_ai_disable(
        self,
        mock_render,
        mock_get_authorized_package,
        mock_get_resource,
        mock_get_resource_comment_categories,
        mock_is_recaptcha_verified,
        mock_upload_image,
        mock_files,
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        attached_image_filename = 'attached_image_filename'

        config['ckan.feedback.moral_keeper_ai.enable'] = False

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'attached_image_filename': attached_image_filename,
        }.get(x, default)

        mock_file = MagicMock()
        mock_file.filename = attached_image_filename
        mock_file.content_type = 'image/png'
        mock_file.read.return_value = b'fake image data'
        mock_files.return_value = mock_file

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_authorized_package.return_value = mock_package

        mock_upload_image.return_value = attached_image_filename

        mock_get_resource_comment_categories.return_value = 'mock_categories'

        ResourceController.check_comment(resource_id)
        mock_render.assert_called_once_with(
            'resource/comment_check.html',
            {
                'resource': mock_resource.Resource,
                'pkg_dict': mock_package,
                'categories': 'mock_categories',
                'selected_category': category,
                'rating': int(rating),
                'content': content,
                'attached_image_filename': attached_image_filename,
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.check_ai_comment')
    @patch.object(ResourceController, 'suggested_comment')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.get_resource_comment_categories'
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.create_resource_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    def test_check_comment_POST_judgement_True(
        self,
        mock_render,
        mock_create_resource_comment_moral_check_log,
        mock_get_authorized_package,
        mock_get_resource,
        mock_get_resource_comment_categories,
        mock_suggested_comment,
        mock_check_ai_comment,
        mock_is_recaptcha_verified,
        mock_redirect_to,
        mock_files,
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        attached_image_filename = None
        judgement = True

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'comment-suggested': False,
        }.get(x, default)

        mock_files.return_value = None

        mock_check_ai_comment.return_value = judgement

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_authorized_package.return_value = mock_package

        mock_create_resource_comment_moral_check_log.return_value = None

        mock_get_resource_comment_categories.return_value = 'mock_categories'

        ResourceController.check_comment(resource_id)
        mock_render.assert_called_once_with(
            'resource/comment_check.html',
            {
                'resource': mock_resource.Resource,
                'pkg_dict': mock_package,
                'categories': 'mock_categories',
                'selected_category': category,
                'rating': int(rating),
                'content': content,
                'attached_image_filename': attached_image_filename,
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.check_ai_comment')
    @patch(
        'ckanext.feedback.controllers.resource.' 'ResourceController.suggested_comment'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.get_resource_comment_categories'
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    def test_check_comment_POST_judgement_False(
        self,
        mock_render,
        mock_get_authorized_package,
        mock_get_resource,
        mock_get_resource_comment_categories,
        mock_suggested_comment,
        mock_check_ai_comment,
        mock_is_recaptcha_verified,
        mock_redirect_to,
        mock_files,
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        attached_image_filename = None
        judgement = False

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': False,
        }.get(x, default)

        mock_files.return_value = None

        mock_check_ai_comment.return_value = judgement

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_authorized_package.return_value = mock_package

        mock_get_resource_comment_categories.return_value = 'mock_categories'

        ResourceController.check_comment(resource_id)
        mock_suggested_comment.assert_called_once_with(
            resource_id=resource_id,
            rating=int(rating),
            category=category,
            content=content,
            attached_image_filename=attached_image_filename,
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.get_resource_comment_categories'
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.create_resource_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    def test_check_comment_POST_suggested(
        self,
        mock_render,
        mock_create_resource_comment_moral_check_log,
        mock_get_authorized_package,
        mock_get_resource,
        mock_get_resource_comment_categories,
        mock_is_recaptcha_verified,
        mock_redirect_to,
        mock_files,
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        attached_image_filename = None

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': 'True',
            'action': MoralCheckAction.INPUT_SELECTED,
            'input-comment': 'test_input_comment',
            'suggested-comment': 'test_suggested_comment',
        }.get(x, default)

        mock_files.return_value = None

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_authorized_package.return_value = mock_package

        mock_create_resource_comment_moral_check_log.return_value = None

        mock_get_resource_comment_categories.return_value = 'mock_categories'

        ResourceController.check_comment(resource_id)
        mock_render.assert_called_once_with(
            'resource/comment_check.html',
            {
                'resource': mock_resource.Resource,
                'pkg_dict': mock_package,
                'categories': 'mock_categories',
                'selected_category': category,
                'rating': int(rating),
                'content': content,
                'attached_image_filename': attached_image_filename,
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_check_comment_without_no_comment_and_category(
        self,
        mock_redirect_to,
        mock_method,
    ):
        resource_id = 'resource_id'
        mock_method.return_value = 'POST'

        ResourceController.check_comment(resource_id)
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_image_upload'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._extract_comment_form_data'
    )
    @patch('ckanext.feedback.controllers.resource.request.method', 'POST')
    def test_check_comment_with_image_validation_error(
        self,
        mock_extract_form_data,
        mock_handle_image_upload,
        mock_flash_error,
        mock_comment,
    ):
        """Test check_comment handles ValidationError from image upload"""
        resource_id = 'resource-id'
        category = 'REQUEST'
        content = 'Test comment content that is long enough'

        mock_extract_form_data.return_value = {
            'category': category,
            'content': content,
            'rating': None,
            'attached_image_filename': None,
        }

        error_dict = {'attached_image': ['Invalid image format']}
        validation_error = toolkit.ValidationError(error_dict)
        mock_handle_image_upload.side_effect = validation_error

        result = ResourceController.check_comment(resource_id)

        assert mock_flash_error.called
        call_args = mock_flash_error.call_args
        assert call_args[1]['allow_html'] is True
        assert call_args[0][0] == 'Invalid image format'
        mock_comment.assert_called_once_with(resource_id, category, content)
        assert result == mock_comment.return_value

    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_image_upload'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._extract_comment_form_data'
    )
    @patch('ckanext.feedback.controllers.resource.request.method', 'POST')
    def test_check_comment_with_image_oserror(
        self, mock_extract_form_data, mock_handle_image_upload
    ):
        """Test check_comment handles OSError from image upload"""
        resource_id = 'resource-id'

        mock_extract_form_data.return_value = {
            'category': 'REQUEST',
            'content': 'Test comment content that is long enough',
            'rating': None,
            'attached_image_filename': None,
        }

        mock_handle_image_upload.side_effect = OSError('Permission denied')

        from werkzeug.exceptions import InternalServerError

        with pytest.raises(InternalServerError):
            ResourceController.check_comment(resource_id)

    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_validation_error'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._validate_comment_data'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_image_upload'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._extract_comment_form_data'
    )
    @patch('ckanext.feedback.controllers.resource.request.method', 'POST')
    def test_check_comment_with_validation_error(
        self,
        mock_extract_form_data,
        mock_handle_image_upload,
        mock_validate_comment_data,
        mock_handle_validation_error,
    ):
        """Test check_comment handles validation error"""
        resource_id = 'resource-id'
        category = 'REQUEST'
        content = 'short'

        mock_extract_form_data.return_value = {
            'category': category,
            'content': content,
            'rating': None,
            'attached_image_filename': None,
        }

        mock_handle_image_upload.return_value = None

        error_message = 'Content is too short'
        mock_validate_comment_data.return_value = (False, error_message)

        result = ResourceController.check_comment(resource_id)

        mock_handle_validation_error.assert_called_once_with(
            resource_id, error_message, category, content, None
        )
        assert result == mock_handle_validation_error.return_value

    # test_check_comment_without_bad_recaptcha and
    # test_check_comment_without_comment_validation removed -
    # covered by TestResourceControllerCommonMethods.test_validate_comment_data_*

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path'
    )
    @patch('ckanext.feedback.controllers.resource.send_file')
    def test_check_attached_image(
        self,
        mock_send_file,
        mock_get_attached_image_path,
    ):
        resource_id = 'resource_id'
        attached_image_filename = 'attached_image_filename'

        mock_get_attached_image_path.return_value = 'attached_image_path'

        ResourceController.check_attached_image(resource_id, attached_image_filename)

        mock_send_file.assert_called_once_with('attached_image_path')

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.require_package_access')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_approve_comment_with_sysadmin(
        self,
        mock_redirect_to,
        mock_session_commit,
        mock_comment_service,
        mock_summary_service,
        mock_form,
        mock_require_package_access,
        current_user,
        mock_current_user_fixture,
        sysadmin,
    ):
        resource_id = 'resource id'
        resource_comment_id = 'resource comment id'

        mock_current_user_fixture(current_user, sysadmin)
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_comment_service.get_resource.return_value = mock_resource

        mock_form.get.side_effect = [resource_comment_id]

        mock_redirect_to.return_value = 'resource comment url'
        ResourceController.approve_comment(resource_id)

        mock_comment_service.approve_resource_comment.assert_called_once_with(
            resource_comment_id, sysadmin['id']
        )
        mock_summary_service.refresh_resource_summary.assert_called_once_with(
            resource_id
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_approve_comment_with_user(
        self, mock_toolkit_abort, current_user, mock_current_user_fixture, user
    ):
        resource_id = 'resource id'

        mock_current_user_fixture(current_user, user)
        g.userobj = current_user

        ResourceController.approve_comment(resource_id)
        mock_toolkit_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )

    @pytest.mark.db_test
    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.require_package_access')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_approve_comment_with_other_organization_admin_user(
        self,
        mock_redirect_to,
        mock_comment_service,
        mock_toolkit_abort,
        mock_require_package_access,
        current_user,
        user,
        dataset,
        organization,
        resource,
    ):
        import uuid

        user_obj = model.User.get(user['name'])

        dummy_organization = model.Group(
            name=f'test-org-{uuid.uuid4().hex[:8]}',
            title='Dummy Organization',
            type='organization',
        )
        model.Session.add(dummy_organization)
        model.Session.flush()

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = dataset['id']
        mock_resource.Resource.package.owner_org = organization['id']
        mock_comment_service.get_resource.return_value = mock_resource

        member = model.Member(
            group=dummy_organization,
            group_id=dummy_organization.id,
            table_id=user_obj.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        model.Session.expunge(user_obj)
        user_obj = model.User.get(user['name'])
        current_user.return_value = user_obj
        g.userobj = current_user

        ResourceController.approve_comment(resource['id'])

        mock_toolkit_abort.assert_any_call(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.require_package_access')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_approve_comment_without_resource_comment_id(
        self,
        mock_form,
        mock_comment_service,
        mock_summary_service,
        mock_toolkit_abort,
        mock_require_package_access,
        current_user,
        mock_current_user_fixture,
        sysadmin,
    ):
        resource_id = 'resource id'

        mock_current_user_fixture(current_user, sysadmin)
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_comment_service.get_resource.return_value = mock_resource

        mock_form.get.side_effect = [None]

        ResourceController.approve_comment(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.require_package_access')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_with_sysadmin(
        self,
        mock_redirect_to,
        mock_session_commit,
        mock_comment_service,
        mock_summary_service,
        mock_form,
        mock_require_package_access,
        current_user,
        mock_current_user_fixture,
        sysadmin,
    ):
        resource_id = 'resource id'
        resource_comment_id = 'resource comment id'
        reply_content = 'reply content'

        mock_current_user_fixture(current_user, sysadmin)
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_comment_service.get_resource.return_value = mock_resource

        mock_form.get.side_effect = [
            resource_comment_id,
            reply_content,
        ]

        mock_redirect_to.return_value = 'resource comment url'
        ResourceController.reply(resource_id)

        mock_comment_service.create_reply.assert_called_once_with(
            resource_comment_id, reply_content, sysadmin['id'], None
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

    @pytest.mark.db_test
    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.require_package_access')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_reply_with_user(
        self,
        mock_form,
        mock_comment_service,
        mock_toolkit_abort,
        mock_redirect_to,
        mock_flash_error,
        mock_require_package_access,
        current_user,
        user,
    ):
        resource_id = 'resource id'

        mock_form.get.side_effect = ['resource_comment_id', 'reply_content']

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'org-id'
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_comment_service.get_resource.return_value = mock_resource

        user_obj = model.User.get(user['name'])
        current_user.return_value = user_obj
        g.userobj = current_user

        from unittest.mock import patch as _patch

        with _patch(
            'ckanext.feedback.controllers.resource.FeedbackConfig'
        ) as MockFeedbackConfig:
            cfg = MagicMock()
            cfg.recaptcha.force_all.get.return_value = False
            cfg.resource_comment.reply_open.is_enable.return_value = False
            MockFeedbackConfig.return_value = cfg
            ResourceController.reply(resource_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )
        mock_toolkit_abort.assert_not_called()

    @pytest.mark.db_test
    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.require_package_access')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_with_other_organization_admin_user(
        self,
        mock_redirect_to,
        MockFeedbackConfig,
        mock_form,
        mock_comment_service,
        mock_flash_error,
        mock_require_package_access,
        current_user,
        user,
        dataset,
        organization,
        resource,
    ):
        import uuid

        user_obj = model.User.get(user['name'])

        dummy_organization = model.Group(
            name=f'test-org-{uuid.uuid4().hex[:8]}',
            title='Dummy Organization',
            type='organization',
        )
        model.Session.add(dummy_organization)
        model.Session.flush()

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = dataset['id']
        mock_resource.Resource.package.owner_org = organization['id']
        mock_comment_service.get_resource.return_value = mock_resource

        member = model.Member(
            group=dummy_organization,
            group_id=dummy_organization.id,
            table_id=user_obj.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        model.Session.expunge(user_obj)
        user_obj = model.User.get(user['name'])
        current_user.return_value = user_obj
        g.userobj = current_user

        mock_form.get.side_effect = ['resource_comment_id', 'reply_content']

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = False
        MockFeedbackConfig.return_value = cfg

        ResourceController.reply(resource['id'])
        mock_comment_service.create_reply.assert_not_called()
        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource['id']
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.require_package_access')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_reply_without_resource_comment_id(
        self,
        mock_form,
        mock_comment_service,
        mock_summary_service,
        mock_toolkit_abort,
        mock_require_package_access,
        current_user,
        mock_current_user_fixture,
        sysadmin,
    ):
        resource_id = 'resource id'

        mock_current_user_fixture(current_user, sysadmin)
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_comment_service.get_resource.return_value = mock_resource

        mock_form.get.side_effect = [
            None,
            None,
        ]

        mock_toolkit_abort.side_effect = Exception('abort')
        with pytest.raises(Exception):
            ResourceController.reply(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource_comment')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path'
    )
    @patch('ckanext.feedback.controllers.resource.os.path.exists')
    @patch('ckanext.feedback.controllers.resource.send_file')
    def test_attached_image_with_sysadmin(
        self,
        mock_send_file,
        mock_exists,
        mock_get_attached_image_path,
        mock_get_resource_comment,
        mock_get_resource,
        current_user,
        mock_current_user_fixture,
        sysadmin,
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        mock_current_user_fixture(current_user, sysadmin)
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'owner_org'
        mock_get_resource.return_value = mock_resource

        mock_get_resource_comment.return_value = 'mock_comment'

        mock_get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True

        mock_send_file.return_value = 'mock_response'

        response = ResourceController.attached_image(
            resource_id, comment_id, attached_image_filename
        )

        mock_get_resource.assert_called_once_with(resource_id)
        mock_get_resource_comment.assert_called_once_with(
            comment_id, resource_id, None, attached_image_filename
        )
        mock_get_attached_image_path.assert_called_once_with(attached_image_filename)
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

        assert response == 'mock_response'

    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource_comment')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path'
    )
    @patch('ckanext.feedback.controllers.resource.os.path.exists')
    @patch('ckanext.feedback.controllers.resource.send_file')
    def test_attached_image_without_user(
        self,
        mock_send_file,
        mock_exists,
        mock_get_attached_image_path,
        mock_get_resource_comment,
        mock_get_resource,
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        g.userobj = None

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'owner_org'
        mock_get_resource.return_value = mock_resource

        mock_get_resource_comment.return_value = 'mock_comment'
        mock_get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True
        mock_send_file.return_value = 'mock_response'

        response = ResourceController.attached_image(
            resource_id, comment_id, attached_image_filename
        )

        mock_get_resource.assert_called_once_with(resource_id)
        mock_get_resource_comment.assert_called_once_with(
            comment_id, resource_id, True, attached_image_filename
        )
        mock_get_attached_image_path.assert_called_once_with(attached_image_filename)
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

        assert response == 'mock_response'

    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource_comment')
    def test_attached_image_with_org_admin(
        self,
        mock_get_resource_comment,
        mock_get_resource,
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        with patch(
            'ckanext.feedback.controllers.resource.has_organization_admin_role',
            return_value=True,
        ), patch(
            'ckanext.feedback.controllers.resource.os.path.exists', return_value=True
        ), patch(
            'ckanext.feedback.controllers.resource.send_file', return_value='resp'
        ):
            mock_resource = MagicMock()
            mock_resource.Resource.package.owner_org = 'owner_org'
            mock_get_resource.return_value = mock_resource
            mock_get_resource_comment.return_value = 'c'
            # fmt: off
            with patch(
                'ckanext.feedback.controllers.resource.comment_service'
                '.get_attached_image_path',
                return_value='p',
            ):
                # fmt: on
                resp = ResourceController.attached_image(
                    resource_id, comment_id, attached_image_filename
                )
        assert resp == 'resp'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource_comment')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path'
    )
    @patch('ckanext.feedback.controllers.resource.os.path.exists')
    @patch('ckanext.feedback.controllers.resource.send_file')
    def test_attached_image_with_user(
        self,
        mock_send_file,
        mock_exists,
        mock_get_attached_image_path,
        mock_get_resource_comment,
        mock_get_resource,
        current_user,
        mock_current_user_fixture,
        user,
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        mock_current_user_fixture(current_user, user)
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'owner_org'
        mock_get_resource.return_value = mock_resource

        mock_get_resource_comment.return_value = 'mock_comment'

        mock_get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True

        mock_send_file.return_value = 'mock_response'

        response = ResourceController.attached_image(
            resource_id, comment_id, attached_image_filename
        )

        mock_get_resource.assert_called_once_with(resource_id)
        mock_get_resource_comment.assert_called_once_with(
            comment_id, resource_id, True, attached_image_filename
        )
        mock_get_attached_image_path.assert_called_once_with(attached_image_filename)
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

        assert response == 'mock_response'

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource_comment')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path'
    )
    @patch('ckanext.feedback.controllers.resource.os.path.exists')
    @patch('ckanext.feedback.controllers.resource.send_file')
    def test_attached_image_with_logged_in_non_admin(
        self,
        mock_send_file,
        mock_exists,
        mock_get_attached_image_path,
        mock_get_resource_comment,
        mock_get_resource,
        current_user,
        user_context,
        user,
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        current_user.return_value = model.User.get(user['id'])

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'owner_org'
        mock_get_resource.return_value = mock_resource

        mock_get_resource_comment.return_value = 'mock_comment'
        mock_get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = True
        mock_send_file.return_value = 'mock_response'

        response = ResourceController.attached_image(
            resource_id, comment_id, attached_image_filename
        )

        mock_get_resource.assert_called_once_with(resource_id)
        mock_get_resource_comment.assert_called_once_with(
            comment_id, resource_id, True, attached_image_filename
        )
        mock_get_attached_image_path.assert_called_once_with(attached_image_filename)
        mock_exists.assert_called_once_with('attached_image_path')
        mock_send_file.assert_called_once_with('attached_image_path')

        assert response == 'mock_response'

    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    def test_attached_image_without_resource(
        self,
        mock_get_resource,
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        mock_get_resource.return_value = None

        with pytest.raises(NotFound):
            ResourceController.attached_image(
                resource_id, comment_id, attached_image_filename
            )

        mock_get_resource.assert_called_once_with(resource_id)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource_comment')
    def test_attached_image_without_comment(
        self,
        mock_get_resource_comment,
        mock_get_resource,
        current_user,
        mock_current_user_fixture,
        user,
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        mock_current_user_fixture(current_user, user)
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'owner_org'
        mock_get_resource.return_value = mock_resource

        mock_get_resource_comment.return_value = None

        with pytest.raises(NotFound):
            ResourceController.attached_image(
                resource_id, comment_id, attached_image_filename
            )

        mock_get_resource.assert_called_once_with(resource_id)
        mock_get_resource_comment.assert_called_once_with(
            comment_id, resource_id, True, attached_image_filename
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource_comment')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path'
    )
    @patch('ckanext.feedback.controllers.resource.os.path.exists')
    def test_attached_image_without_image_file(
        self,
        mock_exists,
        mock_get_attached_image_path,
        mock_get_resource_comment,
        mock_get_resource,
        current_user,
        mock_current_user_fixture,
        user,
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        mock_current_user_fixture(current_user, user)
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'owner_org'
        mock_get_resource.return_value = mock_resource

        mock_get_resource_comment.return_value = 'mock_comment'

        mock_get_attached_image_path.return_value = 'attached_image_path'
        mock_exists.return_value = False

        with pytest.raises(NotFound):
            ResourceController.attached_image(
                resource_id, comment_id, attached_image_filename
            )

        mock_get_resource.assert_called_once_with(resource_id)
        mock_get_resource_comment.assert_called_once_with(
            comment_id, resource_id, True, attached_image_filename
        )
        mock_get_attached_image_path.assert_called_once_with(attached_image_filename)
        mock_exists.assert_called_once_with('attached_image_path')

    @patch('ckanext.feedback.controllers.resource.get_like_status_cookie')
    def test_like_status_return_True(self, mock_get_cookie):
        mock_get_cookie.return_value = 'True'
        resource_id = 'resource id'

        result = ResourceController.like_status(resource_id)
        assert result == 'True'

    @patch('ckanext.feedback.controllers.resource.get_like_status_cookie')
    def test_like_status_return_False(self, mock_get_cookie):
        mock_get_cookie.return_value = 'False'
        resource_id = 'resource id'

        result = ResourceController.like_status(resource_id)
        assert result == 'False'

    @patch('ckanext.feedback.controllers.resource.get_like_status_cookie')
    def test_like_status_none(self, mock_get_cookie):
        mock_get_cookie.return_value = None
        resource_id = 'resource id'

        result = ResourceController.like_status(resource_id)
        assert result == 'False'

    @patch('ckanext.feedback.controllers.resource.request.get_json')
    @patch('ckanext.feedback.controllers.resource.Response')
    @patch('ckanext.feedback.controllers.resource.set_like_status_cookie')
    @patch(
        'ckanext.feedback.controllers.resource.likes_service.'
        'increment_resource_like_count_monthly'
    )
    @patch(
        'ckanext.feedback.controllers.resource.likes_service.'
        'increment_resource_like_count'
    )
    def test_like_toggle_True(
        self,
        mock_increment,
        mock_increment_monthly,
        mock_set_like_status_cookie,
        mock_response,
        mock_get_json,
        dataset,
        resource,
    ):
        mock_get_json.return_value = {'likeStatus': True}

        mock_resp = Mock()
        mock_resp.data = b"OK"
        mock_resp.status_code = 200
        mock_resp.mimetype = 'text/plain'
        mock_response.return_value = mock_resp

        mock_set_like_status_cookie.return_value = mock_resp
        resp = ResourceController.like_toggle(dataset['name'], resource['id'])

        mock_increment.assert_called_once_with(resource['id'])
        mock_increment_monthly.assert_called_once_with(resource['id'])

        assert resp.data.decode() == "OK"
        assert resp.status_code == 200
        assert resp.mimetype == 'text/plain'
        assert resp == mock_resp

    @patch('ckanext.feedback.controllers.resource.' 'request.get_json')
    @patch('ckanext.feedback.controllers.resource.Response')
    @patch('ckanext.feedback.controllers.resource.set_like_status_cookie')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'likes_service.decrement_resource_like_count_monthly'
    )
    @patch(
        'ckanext.feedback.controllers.resource.likes_service.'
        'decrement_resource_like_count'
    )
    def test_like_toggle_False(
        self,
        mock_decrement,
        mock_decrement_monthly,
        mock_set_like_status_cookie,
        mock_response,
        mock_get_json,
        dataset,
        resource,
    ):
        mock_get_json.return_value = {'likeStatus': False}

        mock_resp = Mock()
        mock_resp.data = b"OK"
        mock_resp.status_code = 200
        mock_resp.mimetype = 'text/plain'
        mock_response.return_value = mock_resp

        mock_set_like_status_cookie.return_value = mock_resp
        resp = ResourceController.like_toggle(dataset['name'], resource['id'])

        mock_decrement.assert_called_once_with(resource['id'])
        mock_decrement_monthly.assert_called_once_with(resource['id'])

        assert resp.data.decode() == "OK"
        assert resp.status_code == 200
        assert resp.mimetype == 'text/plain'
        assert resp == mock_resp


@pytest.mark.usefixtures('with_request_context')
@pytest.mark.db_test
class TestResourceCommentReactions:
    @patch('flask_login.utils._get_user')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController.'
        '_check_organization_admin_role'
    )
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reactions_existing_reaction_sysadmin_updates_reaction(
        self,
        mock_redirect_to,
        mock_session_commit,
        mock_comment_service,
        mock_form,
        mock_check_organization_admin_role,
        current_user,
        sysadmin,
        resource_comment,
    ):
        resource_id = resource_comment.resource_id
        comment_id = resource_comment.id
        response_status = 'completed'
        admin_liked = False

        current_user.return_value = model.User.get(sysadmin['id'])
        g.userobj = current_user

        mock_check_organization_admin_role.return_value = None
        mock_form.get.side_effect = [
            comment_id,
            response_status,
            admin_liked,
        ]
        mock_comment = MagicMock()
        mock_comment.id = comment_id
        mock_comment_service.get_resource_comment.return_value = mock_comment

        mock_comment_service.get_resource_comment_reactions.return_value = (
            'resource_comment_reactions'
        )
        mock_comment_service.update_resource_comment_reactions.return_value = None

        ResourceController.reactions(resource_id)

        mock_check_organization_admin_role.assert_called_once_with(resource_id)
        mock_comment_service.get_resource_comment_reactions.assert_called_once_with(
            comment_id,
        )
        mock_comment_service.update_resource_comment_reactions.assert_called_once_with(
            'resource_comment_reactions',
            ResourceCommentResponseStatus.COMPLETED.name,
            admin_liked,
            sysadmin['id'],
        )
        mock_comment_service.create_resource_comment_reactions.assert_not_called()
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment',
            resource_id=resource_id,
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.require_package_access')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reactions_no_existing_reaction_sysadmin_creates_reaction(
        self,
        mock_redirect_to,
        mock_session_commit,
        mock_comment_service,
        mock_form,
        mock_require_package_access,
        current_user,
        sysadmin,
        resource_comment,
    ):
        resource_id = resource_comment.resource_id
        comment_id = resource_comment.id
        response_status = 'completed'
        admin_liked = False

        current_user.return_value = model.User.get(sysadmin['id'])
        g.userobj = current_user

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_comment_service.get_resource.return_value = mock_resource

        mock_form.get.side_effect = [
            comment_id,
            response_status,
            admin_liked,
        ]
        mock_comment = MagicMock()
        mock_comment.id = comment_id
        mock_comment_service.get_resource_comment.return_value = mock_comment

        mock_comment_service.get_resource_comment_reactions.return_value = None
        mock_comment_service.create_resource_comment_reactions.return_value = None

        ResourceController.reactions(resource_id)

        mock_comment_service.get_resource_comment_reactions.assert_called_once_with(
            comment_id,
        )
        mock_comment_service.update_resource_comment_reactions.assert_not_called()
        mock_comment_service.create_resource_comment_reactions.assert_called_once_with(
            comment_id,
            ResourceCommentResponseStatus.COMPLETED.name,
            admin_liked,
            sysadmin['id'],
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment',
            resource_id=resource_id,
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reactions_user_access_returns_404(
        self,
        mock_redirect_to,
        mock_session_commit,
        mock_comment_service,
        mock_form,
        mock_toolkit_abort,
        current_user,
        user,
        resource_comment,
    ):
        resource_id = resource_comment.resource_id

        current_user.return_value = model.User.get(user['id'])
        g.userobj = current_user

        ResourceController.reactions(resource_id)

        mock_toolkit_abort.assert_called_once_with(
            404,
            'The requested URL was not found on the server. If you entered the '
            'URL manually please check your spelling and try again.',
        )
        mock_form.get.assert_not_called()
        mock_comment_service.get_resource_comment_reactions.assert_not_called()
        mock_comment_service.update_resource_comment_reactions.assert_not_called()
        mock_comment_service.create_resource_comment_reactions.assert_not_called()
        mock_session_commit.assert_not_called()
        mock_redirect_to.assert_not_called()

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_upload_destination'
    )
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image(
        self,
        mock_get_uploader,
        mock_get_upload_destination,
    ):
        mock_image = MagicMock()
        mock_image.filename = 'test.png'
        mock_image.content_type = 'image/png'

        mock_get_upload_destination.return_value = '/test/upload/path'

        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'test_image.png'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        ResourceController._upload_image(mock_image)

        mock_get_upload_destination.assert_called_once()
        mock_get_uploader.assert_called_once_with('/test/upload/path')
        mock_uploader.update_data_dict.assert_called_once()
        mock_uploader.upload.assert_called_once()

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_upload_destination'
    )
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_invalid_extension(
        self, mock_get_uploader, mock_get_upload_destination
    ):
        """Test _upload_image rejects invalid file extensions"""
        mock_image = MagicMock()
        mock_image.filename = 'test.pdf'
        mock_image.content_type = 'application/pdf'

        with pytest.raises(toolkit.ValidationError) as exc_info:
            ResourceController._upload_image(mock_image)

        assert 'Image Upload' in str(exc_info.value) or 'Invalid file extension' in str(
            exc_info.value
        )

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_upload_destination'
    )
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_invalid_mimetype(
        self, mock_get_uploader, mock_get_upload_destination
    ):
        """Test _upload_image rejects invalid MIME types"""
        mock_image = MagicMock()
        mock_image.filename = 'test.png'
        mock_image.content_type = 'text/plain'

        with pytest.raises(toolkit.ValidationError) as exc_info:
            ResourceController._upload_image(mock_image)

        assert 'Image Upload' in str(exc_info.value) or 'Invalid file type' in str(
            exc_info.value
        )

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_upload_destination'
    )
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_valid_extensions(
        self, mock_get_uploader, mock_get_upload_destination
    ):
        """Test _upload_image accepts all valid extensions"""
        valid_files = [
            ('test.png', 'image/png'),
            ('test.jpg', 'image/jpeg'),
            ('test.jpeg', 'image/jpeg'),
            ('test.gif', 'image/gif'),
            ('test.webp', 'image/webp'),
        ]

        mock_get_upload_destination.return_value = '/test/upload/path'
        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'uploaded_image.png'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        for filename, mimetype in valid_files:
            mock_image = MagicMock()
            mock_image.filename = filename
            mock_image.content_type = mimetype

            result = ResourceController._upload_image(mock_image)
            assert result == 'uploaded_image.png'

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_upload_destination'
    )
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_no_filename(
        self, mock_get_uploader, mock_get_upload_destination
    ):
        """Test _upload_image handles missing filename"""
        mock_image = MagicMock()
        mock_image.filename = None
        mock_image.content_type = 'image/png'

        mock_get_upload_destination.return_value = '/test/upload/path'
        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'uploaded_image.png'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        result = ResourceController._upload_image(mock_image)
        assert result == 'uploaded_image.png'

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_upload_destination'
    )
    @patch('ckanext.feedback.services.common.upload.get_uploader')
    def test_upload_image_no_content_type(
        self, mock_get_uploader, mock_get_upload_destination
    ):
        """Test _upload_image handles missing content_type"""
        mock_image = MagicMock()
        mock_image.filename = 'test.png'
        mock_image.content_type = None

        mock_get_upload_destination.return_value = '/test/upload/path'
        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader

        def mock_update_data_dict(data_dict, url_field, file_field, clear_field):
            data_dict['image_url'] = 'uploaded_image.png'

        mock_uploader.update_data_dict.side_effect = mock_update_data_dict

        result = ResourceController._upload_image(mock_image)
        assert result == 'uploaded_image.png'


@pytest.mark.usefixtures('with_request_context')
@pytest.mark.db_test
class TestResourceCreatePreviousLog:
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.create_resource_comment_moral_check_log'
    )
    def test_create_previous_log_moral_keeper_ai_disabled(
        self,
        mock_create_resource_comment_moral_check_log,
        mock_get_resource,
        resource,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = False

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource.return_value = resource

        return_value = ResourceController.create_previous_log(resource['id'])

        mock_create_resource_comment_moral_check_log.assert_not_called()
        assert return_value == ('', 204)

    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.request.get_json')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.create_resource_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_suggestion(
        self,
        mock_create_resource_comment_moral_check_log,
        mock_get_json,
        mock_get_resource,
        resource,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'suggestion',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }
        mock_create_resource_comment_moral_check_log.return_value = None

        return_value = ResourceController.create_previous_log(resource['id'])

        mock_create_resource_comment_moral_check_log.assert_called_once_with(
            resource_id=resource['id'],
            action=MoralCheckAction.PREVIOUS_SUGGESTION.name,
            input_comment='test_input_comment',
            suggested_comment='test_suggested_comment',
            output_comment=None,
        )
        assert return_value == ('', 204)

    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.request.get_json')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.create_resource_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_confirm(
        self,
        mock_create_resource_comment_moral_check_log,
        mock_get_json,
        mock_get_resource,
        resource,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'confirm',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }
        mock_create_resource_comment_moral_check_log.return_value = None

        return_value = ResourceController.create_previous_log(resource['id'])

        mock_create_resource_comment_moral_check_log.assert_called_once_with(
            resource_id=resource['id'],
            action=MoralCheckAction.PREVIOUS_CONFIRM.name,
            input_comment='test_input_comment',
            suggested_comment='test_suggested_comment',
            output_comment=None,
        )
        assert return_value == ('', 204)

    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.request.get_json')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.create_resource_comment_moral_check_log'
    )
    def test_create_previous_log_previous_type_none(
        self,
        mock_create_resource_comment_moral_check_log,
        mock_get_json,
        mock_get_resource,
        resource,
    ):
        config['ckan.feedback.moral_keeper_ai.enable'] = True

        resource = MagicMock()
        resource.Resource.package.owner_org = 'mock_organization_id'
        mock_get_resource.return_value = resource
        mock_get_json.return_value = {
            'previous_type': 'none',
            'input_comment': 'test_input_comment',
            'suggested_comment': 'test_suggested_comment',
        }
        mock_create_resource_comment_moral_check_log.return_value = None

        return_value = ResourceController.create_previous_log(resource['id'])

        mock_create_resource_comment_moral_check_log.assert_not_called()
        assert return_value == ('', 204)

    # Error handling tests
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch(
        'ckanext.feedback.controllers.resource.summary_service.create_resource_summary'
    )
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.create_resource_comment'
    )
    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_create_comment_with_error(
        self,
        mock_form,
        mock_recaptcha,
        mock_validate,
        mock_create,
        mock_summary,
        mock_commit,
        mock_rollback,
        mock_flash_error,
        mock_redirect,
        resource,
    ):
        """Test create_comment() error handling"""
        mock_form.get.side_effect = lambda k, d='': {
            'category': 'REQUEST',
            'comment-content': 'Test',
            'rating': '5',
            'attached_image_filename': None,
        }.get(k, d)
        mock_recaptcha.return_value = True
        mock_validate.return_value = None
        mock_commit.side_effect = Exception('Database error')

        with patch(
            'ckanext.feedback.controllers.resource.request.files.get', return_value=None
        ):
            ResourceController.create_comment(resource['id'])

        mock_rollback.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.check_ai_comment')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service'
        '.create_resource_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service'
        '.get_resource_comment_categories'
    )
    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.method', 'POST')
    def test_check_comment_with_error(
        self,
        mock_form,
        mock_recaptcha,
        mock_validate,
        mock_categories,
        mock_get_resource,
        mock_get_authorized_package,
        mock_config,
        mock_create_log,
        mock_check_ai,
        mock_commit,
        mock_rollback,
        mock_flash_error,
        mock_redirect,
        resource,
    ):
        """Test check_comment() error handling"""
        mock_form.get.side_effect = lambda k, d='': {
            'category': 'REQUEST',
            'comment-content': 'Test',
            'attached_image_filename': None,
            'comment-suggested': 'False',
        }.get(k, d)
        mock_recaptcha.return_value = True
        mock_validate.return_value = None
        mock_categories.return_value = []

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'test-package'
        mock_resource.Resource.package.owner_org = 'test-org'
        mock_get_resource.return_value = mock_resource
        mock_get_authorized_package.return_value = {'id': 'test-package'}

        mock_feedback_config = MagicMock()
        mock_feedback_config.moral_keeper_ai.is_enable.return_value = True
        mock_config.return_value = mock_feedback_config
        mock_check_ai.return_value = True
        mock_commit.side_effect = Exception('Database error')

        with patch(
            'ckanext.feedback.controllers.resource.request.files.get', return_value=None
        ):
            ResourceController.check_comment(resource['id'])

        mock_rollback.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch(
        'ckanext.feedback.controllers.resource.summary_service.refresh_resource_summary'
    )
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.approve_resource_comment'
    )
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_approve_comment_with_error(
        self,
        mock_form,
        mock_approve,
        mock_refresh,
        mock_commit,
        mock_rollback,
        mock_flash_error,
        mock_redirect,
        current_user,
        mock_current_user_fixture,
        sysadmin,
        resource,
    ):
        """Test approve_comment() error handling"""
        mock_current_user_fixture(current_user, sysadmin)
        g.userobj = current_user

        mock_form.get.return_value = 'comment-id'
        mock_commit.side_effect = Exception('Database error')

        ResourceController.approve_comment(resource['id'])

        mock_rollback.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.comment_service.create_reply')
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_reply_with_error(
        self,
        mock_form,
        mock_create_reply,
        mock_commit,
        mock_rollback,
        mock_flash_error,
        mock_redirect,
        current_user,
        mock_current_user_fixture,
        sysadmin,
        resource,
    ):
        """Test reply() error handling"""
        mock_current_user_fixture(current_user, sysadmin)
        g.userobj = current_user

        mock_form.get.side_effect = lambda k, d='': {
            'resource_comment_id': 'comment-id',
            'reply_content': 'Reply',
        }.get(k, d)
        mock_commit.side_effect = Exception('Database error')

        ResourceController.reply(resource['id'])

        mock_rollback.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch(
        'ckanext.feedback.controllers.resource.likes_service'
        '.increment_resource_like_count_monthly'
    )
    @patch(
        'ckanext.feedback.controllers.resource.likes_service'
        '.increment_resource_like_count'
    )
    @patch('ckanext.feedback.controllers.resource.request.get_json')
    def test_like_toggle_with_error(
        self,
        mock_get_json,
        mock_increment,
        mock_increment_monthly,
        mock_commit,
        mock_rollback,
        resource,
    ):
        """Test like_toggle() error handling"""
        mock_get_json.return_value = {'likeStatus': True}
        mock_commit.side_effect = Exception('Database error')

        response = ResourceController.like_toggle('test-package', resource['id'])

        mock_rollback.assert_called_once()
        assert response.status_code == 500

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service'
        '.create_resource_comment_reactions'
    )
    @patch(
        'ckanext.feedback.controllers.resource.comment_service'
        '.get_resource_comment_reactions'
    )
    @patch(
        'ckanext.feedback.controllers.resource.comment_service' '.get_resource_comment'
    )
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_reactions_with_error(
        self,
        mock_form,
        mock_get_comment,
        mock_get_reactions,
        mock_create_reactions,
        mock_commit,
        mock_rollback,
        mock_flash_error,
        mock_redirect,
        current_user,
        mock_current_user_fixture,
        sysadmin,
        resource,
    ):
        """Test reactions() error handling"""
        mock_current_user_fixture(current_user, sysadmin)
        g.userobj = current_user

        mock_form.get.side_effect = lambda k, d='': {
            'resource_comment_id': 'comment-id',
            'response_status': 'not-started',
            'admin_liked': 'off',
        }.get(k, d)
        # Mock get_resource_comment to return a valid comment
        mock_comment = MagicMock()
        mock_comment.id = 'comment-id'
        mock_get_comment.return_value = mock_comment
        mock_get_reactions.return_value = None
        mock_commit.side_effect = Exception('Database error')

        ResourceController.reactions(resource['id'])

        mock_rollback.assert_called_once()
        mock_flash_error.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service'
        '.create_resource_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.request.get_json')
    def test_create_previous_log_with_error(
        self,
        mock_get_json,
        mock_get_resource,
        mock_config,
        mock_create_log,
        mock_commit,
        mock_rollback,
        resource,
    ):
        """Test create_previous_log() error handling"""
        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'test-org'
        mock_get_resource.return_value = mock_resource

        mock_feedback_config = MagicMock()
        mock_feedback_config.moral_keeper_ai.is_enable.return_value = True
        mock_config.return_value = mock_feedback_config

        mock_get_json.return_value = {
            'previous_type': 'suggestion',
            'input_comment': 'Test input',
            'suggested_comment': 'Test suggestion',
        }
        mock_commit.side_effect = Exception('Database error')

        result = ResourceController.create_previous_log(resource['id'])

        mock_rollback.assert_called_once()
        assert result == ('', 204)


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceControllerCommonMethods:
    """Test common helper methods introduced in refactoring"""

    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_extract_comment_form_data_success(self, mock_form):
        """Test _extract_comment_form_data with all fields"""
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': 'test content',
            'category': 'REQUEST',
            'rating': '5',
            'attached_image_filename': 'test.png',
        }.get(x, default)

        result = ResourceController._extract_comment_form_data()

        assert result['category'] == 'REQUEST'
        assert result['content'] == 'test content'
        assert result['rating'] == 5
        assert result['attached_image_filename'] == 'test.png'

    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_extract_comment_form_data_no_content(self, mock_form):
        """Test _extract_comment_form_data when content is empty"""
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': '',
            'category': 'REQUEST',
        }.get(x, default)

        result = ResourceController._extract_comment_form_data()

        assert result['category'] == 'REQUEST'
        assert result['content'] == ''
        assert result['rating'] is None

    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_extract_comment_form_data_no_rating(self, mock_form):
        """Test _extract_comment_form_data when rating is empty"""
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': 'test',
            'category': 'REQUEST',
            'rating': '',
        }.get(x, default)

        result = ResourceController._extract_comment_form_data()

        assert result['rating'] is None

    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_extract_comment_form_data_rating_none_string(self, mock_form):
        """Test _extract_comment_form_data when rating is 'None' string"""
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': 'test',
            'category': 'REQUEST',
            'rating': 'None',
        }.get(x, default)

        result = ResourceController._extract_comment_form_data()

        assert result['rating'] is None

    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_extract_comment_form_data_invalid_rating(self, mock_form):
        """Test _extract_comment_form_data with invalid rating value"""
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': 'test',
            'category': 'REQUEST',
            'rating': 'invalid',
        }.get(x, default)

        result = ResourceController._extract_comment_form_data()

        assert result['rating'] is None

    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    def test_handle_image_upload_success(self, mock_files, mock_upload):
        """Test _handle_image_upload with valid image"""
        mock_file = MagicMock()
        mock_file.filename = 'test.png'
        mock_files.return_value = mock_file
        mock_upload.return_value = 'uploaded_test.png'

        result = ResourceController._handle_image_upload("image-upload")

        assert result == 'uploaded_test.png'
        mock_upload.assert_called_once_with(mock_file)

    @patch('ckanext.feedback.controllers.resource.request.files.get')
    def test_handle_image_upload_no_file(self, mock_files):
        """Test _handle_image_upload when no file is uploaded"""
        mock_files.return_value = None

        result = ResourceController._handle_image_upload("image-upload")

        assert result is None

    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    def test_handle_image_upload_validation_error(self, mock_files, mock_upload):
        """Test _handle_image_upload with validation error"""
        mock_file = MagicMock()
        mock_files.return_value = mock_file
        mock_upload.side_effect = toolkit.ValidationError(
            {'upload': ['Invalid image file type']}
        )

        with pytest.raises(toolkit.ValidationError):
            ResourceController._handle_image_upload("image-upload")

    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    def test_handle_image_upload_exception(self, mock_files, mock_upload):
        """Test _handle_image_upload with unexpected exception"""
        mock_file = MagicMock()
        mock_files.return_value = mock_file
        mock_upload.side_effect = Exception('Unexpected error')

        with pytest.raises(Exception):
            ResourceController._handle_image_upload("image-upload")

    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    def test_validate_comment_data_success(self, mock_recaptcha, mock_validate):
        """Test _validate_comment_data with valid data"""
        mock_recaptcha.return_value = True
        mock_validate.return_value = None

        is_valid, error = ResourceController._validate_comment_data(
            'REQUEST', 'test content'
        )

        assert is_valid is True
        assert error is None

    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    def test_validate_comment_data_no_category(self, mock_recaptcha, mock_validate):
        """Test _validate_comment_data when category is missing"""
        is_valid, error = ResourceController._validate_comment_data(
            None, 'test content'
        )

        assert is_valid is False
        assert error is None
        mock_recaptcha.assert_not_called()

    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    def test_validate_comment_data_no_content(self, mock_recaptcha, mock_validate):
        """Test _validate_comment_data when content is missing"""
        is_valid, error = ResourceController._validate_comment_data('REQUEST', '')

        assert is_valid is False
        assert error is None
        mock_recaptcha.assert_not_called()

    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    def test_validate_comment_data_bad_recaptcha(self, mock_recaptcha, mock_validate):
        """Test _validate_comment_data with failed reCAPTCHA"""
        mock_recaptcha.return_value = False

        is_valid, error = ResourceController._validate_comment_data(
            'REQUEST', 'test content'
        )

        assert is_valid is False
        assert error == _('Bad Captcha. Please try again.')

    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    def test_validate_comment_data_content_too_long(
        self, mock_recaptcha, mock_validate
    ):
        """Test _validate_comment_data with content validation error"""
        mock_recaptcha.return_value = True
        mock_validate.return_value = 'Please keep the comment length below 1000'

        is_valid, error = ResourceController._validate_comment_data(
            'REQUEST', 'x' * 1001
        )

        assert is_valid is False
        assert error == _('Please keep the comment length below 1000')

    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch('flask_login.utils._get_user')
    def test_validate_comment_data_admin_bypass_recaptcha(
        self,
        mock_current_user,
        mock_config,
        mock_get_resource,
        mock_has_org_role,
        mock_recaptcha,
        mock_validate,
        sysadmin,
    ):
        """Test _validate_comment_data with admin bypassing reCAPTCHA"""
        mock_current_user.return_value = model.User.get(sysadmin['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        mock_config.return_value = cfg

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'org-id'
        mock_get_resource.return_value = mock_resource
        mock_has_org_role.return_value = True

        mock_recaptcha.return_value = False
        mock_validate.return_value = None

        is_valid, error = ResourceController._validate_comment_data(
            'REQUEST', 'test content', 'resource-id'
        )

        assert is_valid is True
        assert error is None

    @patch('ckanext.feedback.controllers.resource.validate_service.validate_comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch('flask_login.utils._get_user')
    def test_validate_comment_data_admin_bypass_exception_fallback(
        self,
        mock_current_user,
        mock_config,
        mock_get_resource,
        mock_recaptcha,
        mock_validate,
        sysadmin,
    ):
        """Test _validate_comment_data with exception in get_resource
        fallback to sysadmin"""
        mock_current_user.return_value = model.User.get(sysadmin['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        mock_config.return_value = cfg

        mock_get_resource.side_effect = Exception('Resource not found')

        mock_recaptcha.return_value = False
        mock_validate.return_value = None

        is_valid, error = ResourceController._validate_comment_data(
            'REQUEST', 'test content', 'resource-id'
        )

        assert is_valid is True
        assert error is None

    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    def test_get_resource_context_success(
        self, mock_get_resource, mock_get_authorized_package, app
    ):
        """Test _get_resource_context returns correct data"""
        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'test-package-id'
        mock_resource.organization_name = 'test-org'
        mock_get_resource.return_value = mock_resource

        mock_package = {'id': 'test-package-id', 'name': 'test-package'}
        mock_get_authorized_package.return_value = mock_package

        with app.get(url='/'):
            result = ResourceController._get_resource_context('test-resource-id')

        assert result['resource'] == mock_resource
        assert result['package'] == mock_package
        assert 'context' in result
        assert g.pkg_dict == {'organization': {'name': 'test-org'}}

    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    def test_handle_validation_error_with_message(self, mock_comment, mock_flash_error):
        """Test _handle_validation_error displays error message"""
        ResourceController._handle_validation_error(
            'resource-id', 'Error message', 'REQUEST', 'test content', 'test.png'
        )

        mock_flash_error.assert_called_once_with('Error message', allow_html=True)
        mock_comment.assert_called_once_with(
            'resource-id', 'REQUEST', 'test content', 'test.png'
        )

    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    def test_handle_validation_error_no_message(self, mock_comment, mock_flash_error):
        """Test _handle_validation_error without error message"""
        ResourceController._handle_validation_error(
            'resource-id', None, 'REQUEST', 'test content'
        )

        mock_flash_error.assert_not_called()
        mock_comment.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.send_email')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    def test_send_comment_notification_email_success(
        self, mock_get_resource, mock_send_email
    ):
        """Test _send_comment_notification_email sends email successfully"""
        mock_resource = MagicMock()
        mock_resource.Resource.name = 'Test Resource'
        mock_resource.Resource.package.owner_org = 'test-org'
        mock_get_resource.return_value = mock_resource

        ResourceController._send_comment_notification_email(
            'resource-id', 'REQUEST', 'test content'
        )

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[1]
        assert call_args['target_name'] == 'Test Resource'
        assert call_args['category'] == _('Request')
        assert call_args['content'] == 'test content'

    @patch('ckanext.feedback.controllers.resource.send_email')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    def test_send_comment_notification_email_exception(
        self, mock_get_resource, mock_send_email
    ):
        """Test _send_comment_notification_email handles exceptions gracefully"""
        mock_resource = MagicMock()
        mock_get_resource.return_value = mock_resource
        mock_send_email.side_effect = Exception('Email error')

        # Should not raise exception
        ResourceController._send_comment_notification_email(
            'resource-id', 'REQUEST', 'test content'
        )

        mock_send_email.assert_called_once()

    def test_format_validation_error_message_with_dict(self):
        """Test _format_validation_error_message with dict error_summary"""
        error = toolkit.ValidationError({'field1': ['Error 1'], 'field2': ['Error 3']})

        result = ResourceController._format_validation_error_message(error)

        assert 'Error 1' in result
        assert 'Error 3' in result
        assert '<br>' in result

    def test_format_validation_error_message_with_single_error(self):
        """Test _format_validation_error_message with single error in list"""
        error = toolkit.ValidationError({'field': ['Single error']})

        result = ResourceController._format_validation_error_message(error)

        assert 'Single error' in result

    def test_format_validation_error_message_with_list_messages(self):
        """Test _format_validation_error_message with list messages (direct mock)"""
        error = MagicMock()
        error.error_summary = {'field1': ['Error A', 'Error B'], 'field2': ['Error C']}

        result = ResourceController._format_validation_error_message(error)

        assert result == 'Error A<br>Error B<br>Error C'

    def test_format_validation_error_message_with_string_messages(self):
        """Test _format_validation_error_message with string messages (direct mock)"""
        error = MagicMock()
        error.error_summary = {'field1': 'String error 1', 'field2': 'String error 2'}

        result = ResourceController._format_validation_error_message(error)

        assert 'String error 1' in result
        assert 'String error 2' in result
        assert '<br>' in result

    def test_format_validation_error_message_with_non_dict(self):
        """Test _format_validation_error_message with non-dict error_summary"""
        error = MagicMock()
        error.error_summary = 'Simple string error'

        result = ResourceController._format_validation_error_message(error)

        assert result == 'Simple string error'

    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch(
        'ckanext.feedback.controllers.resource.summary_service.create_resource_summary'
    )
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.create_resource_comment'
    )
    def test_persist_comment_success(
        self, mock_create_comment, mock_create_summary, mock_commit
    ):
        """Test _persist_comment successfully saves comment"""
        result = ResourceController._persist_comment(
            'res-123', 'REQUEST', 'test content', 5, 'test.png'
        )

        assert result.success is True
        assert result.error_message is None
        mock_create_comment.assert_called_once_with(
            'res-123', 'REQUEST', 'test content', 5, 'test.png'
        )
        mock_create_summary.assert_called_once_with('res-123')
        mock_commit.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.create_resource_comment'
    )
    def test_persist_comment_failure_sqlalchemy_error(
        self, mock_create_comment, mock_commit, mock_rollback
    ):
        """Test _persist_comment handles SQLAlchemyError"""
        from sqlalchemy.exc import SQLAlchemyError

        mock_commit.side_effect = SQLAlchemyError('Database error')

        result = ResourceController._persist_comment(
            'res-123', 'REQUEST', 'test content', None, None
        )

        assert result.success is False
        assert result.error_message == _('Failed to create comment. Please try again.')
        mock_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.create_resource_comment'
    )
    def test_persist_comment_failure_general_exception(
        self, mock_create_comment, mock_commit, mock_rollback
    ):
        """Test _persist_comment handles general Exception"""
        mock_commit.side_effect = Exception('Unexpected error')

        result = ResourceController._persist_comment(
            'res-123', 'REQUEST', 'test content', None, None
        )

        assert result.success is False
        assert result.error_message == _('Failed to create comment. Please try again.')
        mock_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.set_repeat_post_limit_cookie')
    @patch('ckanext.feedback.controllers.resource.make_response')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_success')
    def test_create_success_response(
        self, mock_flash_success, mock_redirect_to, mock_make_response, mock_set_cookie
    ):
        """Test _create_success_response creates proper response"""
        mock_response = MagicMock()
        mock_make_response.return_value = mock_response
        mock_set_cookie.return_value = 'final_response'

        result = ResourceController._create_success_response('pkg-name', 'res-123')

        assert result == 'final_response'
        mock_flash_success.assert_called_once()
        assert mock_flash_success.call_args[1]['allow_html'] is True
        mock_redirect_to.assert_called_once_with(
            'resource.read', id='pkg-name', resource_id='res-123'
        )
        mock_make_response.assert_called_once()
        mock_set_cookie.assert_called_once_with(mock_response, 'res-123')

    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_validation_error'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._validate_comment_data'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_image_upload_with_error_handling'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._extract_comment_form_data'
    )
    def test_process_comment_input_success(
        self, mock_extract, mock_handle_image, mock_validate, mock_handle_error
    ):
        """Test _process_comment_input with valid input"""
        mock_extract.return_value = {
            'category': 'REQUEST',
            'content': 'test content',
            'rating': 5,
            'attached_image_filename': None,
        }
        mock_handle_image.return_value = ('uploaded.png', None)
        mock_validate.return_value = (True, None)

        result = ResourceController._process_comment_input('image-upload', 'res-123')

        assert result.form_data['category'] == 'REQUEST'
        assert result.attached_filename == 'uploaded.png'
        assert result.error_response is None
        mock_validate.assert_called_once_with('REQUEST', 'test content', 'res-123')

    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_image_upload_with_error_handling'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._extract_comment_form_data'
    )
    def test_process_comment_input_image_error(self, mock_extract, mock_handle_image):
        """Test _process_comment_input with image upload error"""
        mock_extract.return_value = {
            'category': 'REQUEST',
            'content': 'test content',
            'rating': None,
            'attached_image_filename': None,
        }
        error_response = MagicMock()
        mock_handle_image.return_value = (None, error_response)

        result = ResourceController._process_comment_input('image-upload', 'res-123')

        assert result.attached_filename is None
        assert result.error_response == error_response

    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_validation_error'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._validate_comment_data'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._handle_image_upload_with_error_handling'
    )
    @patch(
        'ckanext.feedback.controllers.resource.'
        'ResourceController._extract_comment_form_data'
    )
    def test_process_comment_input_validation_error(
        self, mock_extract, mock_handle_image, mock_validate, mock_handle_error
    ):
        """Test _process_comment_input with validation error"""
        mock_extract.return_value = {
            'category': 'REQUEST',
            'content': 'short',
            'rating': None,
            'attached_image_filename': None,
        }
        mock_handle_image.return_value = (None, None)
        mock_validate.return_value = (False, 'Content too short')
        error_response = MagicMock()
        mock_handle_error.return_value = error_response

        result = ResourceController._process_comment_input('image-upload', 'res-123')

        assert result.error_response == error_response
        mock_handle_error.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.ResourceController.suggested_comment')
    @patch('ckanext.feedback.controllers.resource.check_ai_comment')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.create_resource_comment_moral_check_log'
    )
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_handle_moral_keeper_ai_check_passes(
        self, mock_form, mock_create_log, mock_check_ai, mock_suggested
    ):
        """Test _handle_moral_keeper_ai when AI check passes"""
        from ckanext.feedback.controllers.resource import FormFields

        mock_form.get.side_effect = lambda key, default=None: {
            FormFields.COMMENT_SUGGESTED: False
        }.get(key, default)
        mock_check_ai.return_value = True

        result = ResourceController._handle_moral_keeper_ai(
            'res-123', 'REQUEST', 'test content', 5, None
        )

        assert result is None
        mock_suggested.assert_not_called()
        mock_create_log.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.ResourceController.suggested_comment')
    @patch('ckanext.feedback.controllers.resource.check_ai_comment')
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_handle_moral_keeper_ai_check_fails(
        self, mock_form, mock_check_ai, mock_suggested
    ):
        """Test _handle_moral_keeper_ai when AI check fails"""
        from ckanext.feedback.controllers.resource import FormFields

        mock_form.get.side_effect = lambda key, default=None: {
            FormFields.COMMENT_SUGGESTED: False
        }.get(key, default)
        mock_check_ai.return_value = False
        mock_suggested.return_value = 'suggestion_page'

        result = ResourceController._handle_moral_keeper_ai(
            'res-123', 'REQUEST', 'bad content', 5, None
        )

        assert result == 'suggestion_page'
        mock_suggested.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.session.commit')
    def test_persist_moral_check_log_success(self, mock_commit):
        """Test _persist_moral_check_log success"""
        result = ResourceController._persist_moral_check_log('res-123')

        assert result.success is True
        assert result.error_message is None
        mock_commit.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    def test_persist_moral_check_log_failure_sqlalchemy_error(
        self, mock_commit, mock_rollback
    ):
        """Test _persist_moral_check_log handles SQLAlchemyError"""
        from sqlalchemy.exc import SQLAlchemyError

        mock_commit.side_effect = SQLAlchemyError('Database error')

        result = ResourceController._persist_moral_check_log('res-123')

        assert result.success is False
        assert result.error_message == _(
            'Failed to create moral check log. Please try again.'
        )
        mock_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    def test_persist_moral_check_log_failure_general_exception(
        self, mock_commit, mock_rollback
    ):
        """Test _persist_moral_check_log handles general Exception"""
        mock_commit.side_effect = Exception('Unexpected error')

        result = ResourceController._persist_moral_check_log('res-123')

        assert result.success is False
        assert result.error_message == _(
            'Failed to create moral check log. Please try again.'
        )
        mock_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._handle_image_upload'
    )
    def test_handle_image_upload_with_error_handling_success(
        self, mock_handle_image_upload, mock_flash_error, mock_comment
    ):
        """Test _handle_image_upload_with_error_handling returns filename on success"""
        mock_handle_image_upload.return_value = 'test.png'

        filename, error = ResourceController._handle_image_upload_with_error_handling(
            'image-upload', 'res-123', 'REQUEST', 'test content'
        )

        assert filename == 'test.png'
        assert error is None
        mock_flash_error.assert_not_called()
        mock_comment.assert_not_called()

    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._handle_image_upload'
    )
    def test_handle_image_upload_with_error_handling_no_file(
        self, mock_handle_image_upload, mock_flash_error, mock_comment
    ):
        """Test _handle_image_upload_with_error_handling returns None when no file"""
        mock_handle_image_upload.return_value = None

        filename, error = ResourceController._handle_image_upload_with_error_handling(
            'image-upload', 'res-123', 'REQUEST', 'test content'
        )

        assert filename is None
        assert error is None
        mock_flash_error.assert_not_called()
        mock_comment.assert_not_called()

    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._handle_image_upload'
    )
    def test_handle_image_upload_with_error_handling_validation_error(
        self, mock_handle_image_upload, mock_flash_error, mock_comment
    ):
        """Test _handle_image_upload_with_error_handling handles ValidationError"""
        error_dict = {'upload': ['Invalid file type']}
        mock_handle_image_upload.side_effect = toolkit.ValidationError(error_dict)
        mock_comment.return_value = 'error_response'

        filename, error = ResourceController._handle_image_upload_with_error_handling(
            'image-upload', 'res-123', 'REQUEST', 'test content'
        )

        assert filename is None
        assert error == 'error_response'
        mock_flash_error.assert_called_once()
        call_args = mock_flash_error.call_args
        assert call_args[0][0] == 'Invalid file type'
        assert call_args[1]['allow_html'] is True
        mock_comment.assert_called_once_with('res-123', 'REQUEST', 'test content')

    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._handle_image_upload'
    )
    def test_handle_image_upload_with_error_handling_ioerror(
        self, mock_handle_image_upload
    ):
        """Test _handle_image_upload_with_error_handling handles IOError"""
        mock_handle_image_upload.side_effect = IOError('Disk full')

        from werkzeug.exceptions import InternalServerError

        with pytest.raises(InternalServerError):
            ResourceController._handle_image_upload_with_error_handling(
                'image-upload', 'res-123', 'REQUEST', 'test content'
            )

    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._handle_image_upload'
    )
    def test_handle_image_upload_with_error_handling_oserror(
        self, mock_handle_image_upload
    ):
        """Test _handle_image_upload_with_error_handling handles OSError"""
        mock_handle_image_upload.side_effect = OSError('Permission denied')

        from werkzeug.exceptions import InternalServerError

        with pytest.raises(InternalServerError):
            ResourceController._handle_image_upload_with_error_handling(
                'image-upload', 'res-123', 'REQUEST', 'test content'
            )

    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._handle_image_upload'
    )
    def test_handle_image_upload_with_error_handling_unexpected_exception(
        self, mock_handle_image_upload
    ):
        """Test _handle_image_upload_with_error_handling handles unexpected Exception"""
        mock_handle_image_upload.side_effect = RuntimeError('Unexpected error')

        from werkzeug.exceptions import InternalServerError

        with pytest.raises(InternalServerError):
            ResourceController._handle_image_upload_with_error_handling(
                'image-upload', 'res-123', 'REQUEST', 'test content'
            )

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    def test_persist_operation_success(self, mock_commit, mock_rollback):
        """Test _persist_operation with successful operation"""
        mock_operation = MagicMock()

        result = ResourceController._persist_operation(
            mock_operation, 'res-123', 'Test error message'
        )

        assert result.success is True
        assert result.error_message is None
        mock_operation.assert_called_once()
        mock_commit.assert_called_once()
        mock_rollback.assert_not_called()

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    def test_persist_operation_sqlalchemy_error(self, mock_commit, mock_rollback):
        """Test _persist_operation handles SQLAlchemyError"""
        from sqlalchemy.exc import SQLAlchemyError

        mock_operation = MagicMock()
        mock_commit.side_effect = SQLAlchemyError('Database error')

        result = ResourceController._persist_operation(
            mock_operation, 'res-123', 'Test error message'
        )

        assert result.success is False
        assert result.error_message == _('Test error message')
        mock_operation.assert_called_once()
        mock_commit.assert_called_once()
        mock_rollback.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.session.rollback')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    def test_persist_operation_general_exception(self, mock_commit, mock_rollback):
        """Test _persist_operation handles general Exception"""
        mock_operation = MagicMock()
        mock_commit.side_effect = Exception('Unexpected error')

        result = ResourceController._persist_operation(
            mock_operation, 'res-123', 'Test error message'
        )

        assert result.success is False
        assert result.error_message == _('Test error message')
        mock_operation.assert_called_once()
        mock_commit.assert_called_once()
        mock_rollback.assert_called_once()

    def test_determine_approval_status_not_logged_in(self):
        """Test _determine_approval_status when user is not logged in"""
        with patch('ckanext.feedback.controllers.resource.current_user', None):
            result = ResourceController._determine_approval_status('test-org')

        assert result is True

    @pytest.mark.db_test
    @patch('ckanext.feedback.controllers.resource.has_organization_admin_role')
    def test_determine_approval_status_org_admin(
        self, mock_has_org_admin_role, user, organization
    ):
        """Test _determine_approval_status for organization admin"""
        user_obj = model.User.get(user['name'])

        mock_has_org_admin_role.return_value = True

        with patch('ckanext.feedback.controllers.resource.current_user', user_obj):
            result = ResourceController._determine_approval_status(organization['id'])

        assert result is None
        mock_has_org_admin_role.assert_called_once_with(organization['id'])

    @pytest.mark.db_test
    def test_determine_approval_status_sysadmin(self, sysadmin, organization):
        """Test _determine_approval_status for sysadmin"""
        sysadmin_obj = model.User.get(sysadmin['name'])

        with patch('ckanext.feedback.controllers.resource.current_user', sysadmin_obj):
            result = ResourceController._determine_approval_status(organization['id'])

        assert result is None

    @pytest.mark.db_test
    def test_determine_approval_status_regular_user(self, user, organization):
        """Test _determine_approval_status for regular user"""
        user_obj = model.User.get(user['name'])

        with patch('ckanext.feedback.controllers.resource.current_user', user_obj):
            result = ResourceController._determine_approval_status(organization['id'])

        assert result is True

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.create_resource_comment'
    )
    @patch(
        'ckanext.feedback.controllers.resource.summary_service.create_resource_summary'
    )
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_success')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_create_comment_admin_bypass_recaptcha_ok(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_create_summary,
        mock_create_comment,
        mock_get_resource,
        MockFeedbackConfig,
        current_user,
        sysadmin,
        app,
    ):
        current_user.return_value = model.User.get(sysadmin['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        with app.flask_app.test_request_context(
            '/',
            method='POST',
            data={'package_name': 'pkg', 'comment-content': 'c', 'category': 'REQUEST'},
            content_type='application/x-www-form-urlencoded',
        ):
            mock_redirect_to.return_value = 'ok'
            ResourceController.create_comment('res-id')

        mock_create_comment.assert_called_once()
        mock_create_summary.assert_called_once()
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_redirect_to.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.'
        'get_resource_comment_categories'
    )
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    # fmt: on
    def test_check_comment_admin_bypass_exception_then_render(
        self,
        mock_render,
        mock_get_categories,
        mock_get_authorized_package,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        current_user,
        admin_context,
        sysadmin,
        app,
    ):
        """Test check_comment renders successfully with normal flow"""
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj
        g.userobj = user_obj

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.moral_keeper_ai.is_enable.return_value = False
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        res_obj.package_id = 'pkg-id'
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_res.organization_name = 'orgname'

        # get_resource returns normally
        mock_get_resource.return_value = mock_res
        mock_get_categories.return_value = ['REQUEST']

        mock_get_authorized_package.return_value = {
            'id': 'pkg-id',
            'name': 'test-package',
        }

        with app.flask_app.test_request_context(
            '/',
            method='POST',
            data={'comment-content': 'ok', 'category': 'REQUEST'},
            content_type='application/x-www-form-urlencoded',
        ):
            ResourceController.check_comment('res-id')

        # Should render the check comment page
        mock_render.assert_called_once_with(
            'resource/comment_check.html',
            {
                'resource': mock_res.Resource,
                'pkg_dict': {'id': 'pkg-id', 'name': 'test-package'},
                'categories': ['REQUEST'],
                'selected_category': 'REQUEST',
                'rating': None,
                'content': 'ok',
                'attached_image_filename': None,
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._check_organization_admin_role'  # noqa: E501
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.approve_reply')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_approve_reply_success(
        self,
        mock_redirect_to,
        mock_commit,
        mock_approve,
        mock_check_org_role,
        mock_get_resource,
        mock_current_user,
        admin_context,
        sysadmin,
    ):
        user_obj = model.User.get(sysadmin['id'])
        mock_current_user.return_value = user_obj
        g.userobj = user_obj

        mock_check_org_role.return_value = None

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        with patch(
            'ckanext.feedback.controllers.resource.request.form.get', return_value='rid'
        ):
            ResourceController.approve_reply('rid_res')

        mock_approve.assert_called_once()
        mock_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='rid_res'
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._check_organization_admin_role'  # noqa: E501
    )
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.approve_reply',
        side_effect=PermissionError(),
    )
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_approve_reply_permission_error(
        self,
        mock_redirect_to,
        mock_commit,
        _mock_approve,
        mock_flash_error,
        mock_check_org_role,
        mock_get_resource,
        current_user,
        admin_context,
        sysadmin,
    ):
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj
        g.userobj = user_obj

        mock_check_org_role.return_value = None

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        with patch(
            'ckanext.feedback.controllers.resource.request.form.get', return_value='rid'
        ):
            ResourceController.approve_reply('rid_res')

        mock_flash_error.assert_called_once()
        mock_commit.assert_not_called()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='rid_res'
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._check_organization_admin_role'  # noqa: E501
    )
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.approve_reply',
        side_effect=ValueError(),
    )
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_approve_reply_value_error(
        self,
        mock_redirect_to,
        mock_commit,
        _mock_approve,
        mock_abort,
        mock_check_org_role,
        mock_get_resource,
        current_user,
        admin_context,
        sysadmin,
    ):
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj
        g.userobj = user_obj

        mock_check_org_role.return_value = None

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        mock_abort.side_effect = Exception('abort')
        with patch(
            'ckanext.feedback.controllers.resource.request.form.get', return_value='rid'
        ):
            with pytest.raises(Exception):
                ResourceController.approve_reply('rid_res')

        mock_abort.assert_called_once_with(404)
        mock_commit.assert_not_called()
        mock_redirect_to.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.create_reply')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_admin_bypass_success(
        self,
        mock_redirect_to,
        mock_commit,
        mock_create_reply,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        current_user,
        admin_context,
        sysadmin,
    ):
        current_user.return_value = model.User.get(sysadmin['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = True
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'reply content']
            ResourceController.reply('res-id')

        mock_create_reply.assert_called_once()
        mock_commit.assert_called_once()
        mock_redirect_to.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.create_reply')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_reply_open_is_enable_raises_then_proceed_as_admin(
        self,
        mock_redirect_to,
        mock_commit,
        mock_create_reply,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        current_user,
        sysadmin,
    ):
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.side_effect = Exception('err')
        MockFeedbackConfig.return_value = cfg

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'reply content']
            ResourceController.reply('res-id')

        mock_create_reply.assert_called_once()
        mock_commit.assert_called_once()
        mock_redirect_to.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified',
        return_value=False,
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_bad_recaptcha_flashes_error(
        self,
        mock_redirect_to,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        mock_flash_error,
        current_user,
        user_context,
        user,
    ):

        current_user.return_value = model.User.get(user['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = True
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'reply content']
            ResourceController.reply('res-id')

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='res-id'
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_validation_error_flashes_error(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        current_user,
        sysadmin,
    ):
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = True
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        long_content = 'x' * 1001
        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', long_content]
            ResourceController.reply('res-id')

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='res-id'
        )

    @patch('flask_login.utils._get_user')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController.'
        '_check_organization_admin_role'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.resource.request.form.get')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reactions_missing_comment_id_redirects(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_form_get,
        _mock_check_org,
        current_user,
        sysadmin,
    ):
        current_user.return_value = model.User.get(sysadmin['id'])
        g.userobj = current_user

        from ckanext.feedback.models.types import ResourceCommentResponseStatus

        mock_form_get.side_effect = [
            '   ',
            ResourceCommentResponseStatus.STATUS_NONE.name,
            False,
        ]

        ResourceController.reactions('res-id')
        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment',
            resource_id='res-id',
        )

    @patch('flask_login.utils._get_user')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController.'
        '_check_organization_admin_role'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.resource.request.form.get')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_resource_comment',
        return_value=None,
    )
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reactions_comment_not_found_redirects(
        self,
        mock_redirect_to,
        mock_flash_error,
        _mock_get_comment,
        mock_form_get,
        _mock_check_org,
        current_user,
        admin_context,
        sysadmin,
    ):
        _mock_check_org.return_value = None
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj
        g.userobj = user_obj

        from ckanext.feedback.models.types import ResourceCommentResponseStatus

        mock_form_get.side_effect = [
            'cid',
            ResourceCommentResponseStatus.STATUS_NONE.name,
            False,
        ]

        ResourceController.reactions('res-id')
        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='res-id'
        )

    @patch('flask_login.utils._get_user')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController.'
        '_check_organization_admin_role'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.resource.request.form.get')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource_comment')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reactions_invalid_response_status_redirects(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_get_comment,
        mock_form_get,
        _mock_check_org,
        current_user,
        admin_context,
        sysadmin,
    ):
        _mock_check_org.return_value = None
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj
        g.userobj = user_obj

        mock_comment = MagicMock()
        mock_comment.id = 'cid'
        mock_get_comment.return_value = mock_comment
        mock_form_get.side_effect = ['cid', 'invalid-status', False]

        ResourceController.reactions('res-id')
        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='res-id'
        )

    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_check_comment_get_redirects(self, mock_redirect_to, app):
        resource_id = 'rid'
        with app.flask_app.test_request_context('/', method='GET'):
            ResourceController.check_comment(resource_id)
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    # fmt: off
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.get_authorized_package')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.'
        'get_resource_comment_categories'
    )
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    # fmt: on
    def test_check_comment_admin_bypass_normal_renders(
        self,
        mock_render,
        mock_get_categories,
        mock_get_authorized_package,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        current_user,
        app,
        sysadmin,
    ):
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.moral_keeper_ai.is_enable.return_value = False
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        res_obj.package_id = 'pkg-id'
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_res.organization_name = 'org'
        mock_get_resource.return_value = mock_res

        mock_get_categories.return_value = ['REQUEST']

        mock_get_authorized_package.return_value = {
            'id': 'pkg-id',
            'name': 'test-package',
        }

        with app.flask_app.test_request_context(
            '/',
            method='POST',
            data={'comment-content': 'ok', 'category': 'REQUEST'},
            content_type='application/x-www-form-urlencoded',
        ):
            ResourceController.check_comment('res-id')

        mock_render.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._check_organization_admin_role'  # noqa: E501
    )
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_approve_reply_missing_id_aborts_400(
        self,
        mock_abort,
        mock_check_org_role,
        mock_get_resource,
        current_user,
        sysadmin,
    ):
        user_obj = model.User.get(sysadmin['id'])
        current_user.return_value = user_obj
        g.userobj = user_obj

        mock_check_org_role.return_value = None

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        mock_abort.side_effect = Exception('abort')
        with patch(
            'ckanext.feedback.controllers.resource.request.form.get', return_value=None
        ):
            with pytest.raises(Exception):
                ResourceController.approve_reply('rid_res')
        mock_abort.assert_called_once_with(400)

    @patch('flask_login.utils._get_user', return_value=None)
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_unauthenticated_restricted_redirects(
        self,
        mock_redirect_to,
        mock_flash_error,
        MockFeedbackConfig,
        _current_user,
    ):
        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = False
        MockFeedbackConfig.return_value = cfg

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'content']
            ResourceController.reply('res-id')

        mock_flash_error.assert_called_once()
        # fmt: off
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment',
            resource_id='res-id',
        )

    @patch('flask_login.utils._get_user')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController.'
        '_check_organization_admin_role'
    )
    # fmt: on
    @patch('ckanext.feedback.controllers.resource.request.form.get')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reactions_comment_id_none_redirects(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_form_get,
        _mock_check_org,
        current_user,
        admin_context,
        sysadmin,
    ):

        current_user.return_value = model.User.get(sysadmin['id'])

        from ckanext.feedback.models.types import ResourceCommentResponseStatus

        mock_form_get.side_effect = [
            None,
            ResourceCommentResponseStatus.STATUS_NONE.name,
            False,
        ]

        ResourceController.reactions('res-id')
        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='res-id'
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._upload_image',
        return_value='reply.png',
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.create_reply')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_with_image_success(
        self,
        mock_redirect_to,
        mock_commit,
        mock_create_reply,
        _mock_upload_image,
        mock_files_get,
        mock_get_resource,
        _mock_is_recaptcha,
        MockFeedbackConfig,
        current_user,
        sysadmin,
        admin_context,
        user,
    ):
        current_user.return_value = model.User.get(sysadmin['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = True
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        mock_file = MagicMock()
        mock_files_get.return_value = mock_file

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'reply content']
            ResourceController.reply('res-id')

        mock_create_reply.assert_called_once_with(
            'cid', 'reply content', sysadmin['id'], 'reply.png'
        )
        mock_commit.assert_called_once()
        mock_redirect_to.assert_called_once()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._upload_image',
        side_effect=toolkit.ValidationError({'upload': ['invalid']}),
    )
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.comment_service.create_reply')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_with_image_validation_error(
        self,
        mock_redirect_to,
        _mock_create_reply,
        mock_flash_error,
        _mock_upload_image,
        mock_files_get,
        mock_get_resource,
        _mock_is_recaptcha,
        MockFeedbackConfig,
        current_user,
        sysadmin,
        admin_context,
        user,
    ):
        current_user.return_value = model.User.get(user['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = True
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        mock_files_get.return_value = MagicMock()

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'reply content']
            ResourceController.reply('res-id')

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once()
        _mock_create_reply.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch(
        'ckanext.feedback.controllers.resource.ResourceController._upload_image',
        side_effect=Exception('boom'),
    )
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_reply_with_image_exception(
        self,
        mock_abort,
        _mock_upload_image,
        mock_files_get,
        mock_get_resource,
        _mock_is_recaptcha,
        MockFeedbackConfig,
        current_user,
        sysadmin,
        admin_context,
        user,
    ):

        current_user.return_value = model.User.get(user['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = True
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        mock_files_get.return_value = MagicMock()

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'reply content']
            mock_abort.side_effect = Exception('abort')
            with pytest.raises(Exception):
                ResourceController.reply('res-id')

        mock_abort.assert_called_once_with(500)

    @patch('flask_login.utils._get_user')
    @patch(
        'ckanext.feedback.controllers.resource.has_organization_admin_role',
        return_value=True,
    )
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.request.files.get', return_value=None)
    @patch('ckanext.feedback.controllers.resource.comment_service.create_reply')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_is_admin_org_admin_path(
        self,
        mock_redirect_to,
        mock_commit,
        mock_create_reply,
        _mock_files_get,
        mock_get_resource,
        _mock_is_recaptcha,
        MockFeedbackConfig,
        _mock_has_org_admin,
        current_user,
        sysadmin,
        admin_context,
        user,
    ):
        current_user.return_value = model.User.get(user['id'])

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        cfg.resource_comment.reply_open.is_enable.return_value = False
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.return_value = mock_res

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'reply content']
            ResourceController.reply('res-id')

        mock_create_reply.assert_called_once_with(
            'cid', 'reply content', user['id'], None
        )
        mock_commit.assert_called_once()
        mock_redirect_to.assert_called_once()

    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource._session')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path',
        return_value='p',
    )
    @patch('ckanext.feedback.controllers.resource.os.path.exists', return_value=True)
    @patch('ckanext.feedback.controllers.resource.send_file', return_value='resp')
    def test_reply_attached_image_ok(
        self,
        mock_send_file,
        _mock_exists,
        _mock_get_path,
        mock_session,
        mock_get_resource,
    ):
        mock_get_resource.return_value = MagicMock()

        reply_obj = MagicMock()
        reply_obj.attached_image_filename = 'f.png'
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = reply_obj
        mock_session.query.return_value = mock_q

        resp = ResourceController.reply_attached_image('rid', 'rpyid', 'f.png')
        assert resp == 'resp'
        mock_send_file.assert_called_once_with('p')

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_resource',
        return_value=MagicMock(),
    )
    @patch('ckanext.feedback.controllers.resource._session')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_reply_attached_image_not_found(
        self,
        mock_abort,
        mock_session,
        _mock_get_resource,
    ):
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = None
        mock_session.query.return_value = mock_q

        ResourceController.reply_attached_image('rid', 'rpyid', 'f.png')
        mock_abort.assert_called_once_with(404)

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_resource',
        return_value=MagicMock(),
    )
    @patch('ckanext.feedback.controllers.resource._session')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path',
        return_value='p',
    )
    @patch('ckanext.feedback.controllers.resource.os.path.exists', return_value=False)
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_reply_attached_image_file_missing(
        self,
        mock_abort,
        _mock_exists,
        _mock_get_path,
        mock_session,
        _mock_get_resource,
    ):
        reply_obj = MagicMock()
        reply_obj.attached_image_filename = 'f.png'
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = reply_obj
        mock_session.query.return_value = mock_q

        ResourceController.reply_attached_image('rid', 'rpyid', 'f.png')
        mock_abort.assert_called_once_with(404)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.has_organization_admin_role')
    @patch('ckanext.feedback.controllers.resource.FeedbackConfig')
    @patch(
        'ckanext.feedback.controllers.resource.is_recaptcha_verified', return_value=True
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.create_reply')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_is_admin_block_with_res_none(
        self,
        mock_redirect_to,
        mock_flash_error,
        mock_session_commit,
        mock_create_reply,
        mock_get_resource,
        _mock_is_recaptcha,
        MockFeedbackConfig,
        mock_has_org_admin,
        current_user,
        user,
    ):
        current_user.return_value = model.User.get(user['id'])

        mock_get_resource.side_effect = Exception('boom')

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        MockFeedbackConfig.return_value = cfg

        with patch('ckanext.feedback.controllers.resource.request.form.get') as gf:
            gf.side_effect = ['cid', 'reply content']
            ResourceController.reply('res-id')

        mock_has_org_admin.assert_not_called()
        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='res-id'
        )

    @patch('flask_login.utils._get_user')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_resource',
        return_value=MagicMock(),
    )
    @patch('ckanext.feedback.controllers.resource._session')
    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_attached_image_path',
        return_value='p',
    )
    @patch('ckanext.feedback.controllers.resource.os.path.exists', return_value=True)
    @patch('ckanext.feedback.controllers.resource.send_file', return_value='resp')
    def test_reply_attached_image_ok_sysadmin(
        self,
        mock_send_file,
        _mock_exists,
        _mock_get_path,
        mock_session,
        _mock_get_resource,
        current_user,
        sysadmin,
    ):
        current_user.return_value = model.User.get(sysadmin['id'])
        reply_obj = MagicMock()
        reply_obj.attached_image_filename = 'f.png'
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = reply_obj
        mock_session.query.return_value = mock_q

        resp = ResourceController.reply_attached_image('rid', 'rpyid', 'f.png')
        assert resp == 'resp'
        mock_send_file.assert_called_once_with('p')

    @patch(
        'ckanext.feedback.controllers.resource.comment_service.get_resource',
        return_value=None,
    )
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_reply_attached_image_without_resource(
        self, mock_abort, _mock_get_resource
    ):
        mock_abort.side_effect = Exception('abort')
        with pytest.raises(Exception):
            ResourceController.reply_attached_image('rid', 'rpyid', 'f.png')
        mock_abort.assert_called_once_with(404)
