from unittest.mock import MagicMock, Mock, patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.logic import get_action
from ckan.model import User
from ckan.plugins import toolkit
from ckan.tests import factories
from flask import Flask, g
from werkzeug.exceptions import NotFound

import ckanext.feedback.services.resource.comment as comment_service
from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.resource import ResourceController
from ckanext.feedback.models.resource_comment import ResourceCommentCategory
from ckanext.feedback.models.session import session
from ckanext.feedback.models.types import ResourceCommentResponseStatus

engine = model.repo.session.get_bind()


@pytest.fixture
def sysadmin_env():
    user = factories.SysadminWithToken()
    env = {'Authorization': user['token']}
    return env


@pytest.fixture
def user_env():
    user = factories.UserWithToken()
    env = {'Authorization': user['token']}
    return env


def mock_current_user(current_user, user):
    user_obj = model.User.get(user['name'])
    current_user.return_value = user_obj


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

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
        app,
        sysadmin_env,
    ):
        mock_get_repeat_post_limit_cookie.return_value = 'mock_cookie'
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        organization_dict = factories.Organization(
            name='org_name',
        )
        package = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=package['id'])
        resource['package'] = package
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

        with app.get(url='/', environ_base=sysadmin_env):
            g.userobj = current_user
            ResourceController.comment(resource_id)

        approval = None
        resource = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()

        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )
        g.pkg_dict = package
        assert g.pkg_dict["organization"]['name'] == 'org_name'

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': resource.Resource,
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
        current_user,
        app,
        user_env,
    ):
        mock_get_repeat_post_limit_cookie.return_value = 'mock_cookie'
        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        organization_dict = factories.Organization(
            name='org_name',
        )
        package = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=package['id'])
        resource['package'] = package
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

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            ResourceController.comment(resource_id)

        approval = True
        resource = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()

        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )

        g.pkg_dict = package
        assert g.pkg_dict["organization"]['name'] == 'org_name'

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': resource.Resource,
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
        current_user,
        app,
        user_env,
    ):
        user_dict = factories.User()
        owner_org = factories.Organization()
        dataset = factories.Dataset(owner_org=owner_org['id'])
        mock_current_user(current_user, user_dict)
        resource = factories.Resource(package_id=dataset['id'])
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

        with app.get(url='/', environ_base=user_env):
            g.userobj = current_user
            ResourceController.comment(resource_id, category='QUESTION')

        approval = True
        resource = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
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
                'resource': resource.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': 'mock_cookie',
                'selected_category': 'QUESTION',
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
        app,
    ):
        organization_dict = factories.Organization(
            name='org_name',
        )
        dataset = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=dataset['id'])
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
        with app.get(url='/'):
            g.userobj = None
            ResourceController.comment(resource_id)

        approval = True
        resource = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()
        context = {'model': model, 'session': session, 'for_view': True}
        package = get_action('package_show')(
            context, {'id': resource.Resource.package_id}
        )

        mock_page.assert_called_once_with(
            collection=comments,
            page=page,
            item_count=total_count,
            items_per_page=limit,
        )

        g.pkg_dict = package
        assert g.pkg_dict["organization"]['name'] == 'org_name'

        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': resource.Resource,
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
    ):
        resource_id = 'resource id'
        mock_form.get.side_effect = lambda x, default: {
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)
        mock_validate_comment.return_value = None

        ResourceController.create_comment(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    def test_create_comment_with_bad_image(
        self,
        mock_comment,
        mock_flash_error,
        mock_upload_image,
        mock_files,
        mock_form,
    ):
        resource_id = 'resource id'
        package_name = 'package_name'
        comment_content = 'content'
        category = 'category'
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
        mock_file.filename = 'bad_image.txt'
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = toolkit.ValidationError(
            {'upload': ['Invalid image file type']}
        )

        ResourceController.create_comment(resource_id)

        mock_flash_error.assert_called_once_with(
            {'Upload': 'Invalid image file type'}, allow_html=True
        )
        mock_comment.assert_called_once_with(resource_id, category, comment_content)

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

        mock_upload_image.side_effect = Exception('Unexpected error')

        mock_abort.side_effect = Exception('abort')
        with pytest.raises(Exception):
            ResourceController.create_comment(resource_id)

        mock_upload_image.assert_called_once_with(mock_file)
        mock_abort.assert_called_once_with(500)

    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    def test_create_comment_without_comment_length(
        self,
        mock_flash_flash_error,
        mock_redirect_to,
        mock_is_recaptcha_verified,
        mock_comment,
        mock_files,
        mock_form,
    ):
        resource_id = 'resource id'
        category = ResourceCommentCategory.REQUEST.name
        content = 'ex'
        while True:
            content += content
            if 1000 < len(content):
                break
        attached_image_filename = None

        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)

        mock_files.return_value = None
        mock_is_recaptcha_verified.return_value = True

        ResourceController.create_comment(resource_id)

        mock_flash_flash_error.assert_called_once_with(
            'Please keep the comment length below 1000',
            allow_html=True,
        )
        mock_comment.assert_called_once_with(
            resource_id, category, content, attached_image_filename
        )

    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    def test_create_comment_without_bad_recaptcha(
        self,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_comment,
        mock_files,
        mock_form,
    ):
        resource_id = 'resource_id'
        package_name = 'package_name'
        comment_content = 'comment_content'
        category = ResourceCommentCategory.REQUEST.name
        attached_image_filename = None
        mock_form.get.side_effect = lambda x, default: {
            'package_name': package_name,
            'comment-content': comment_content,
            'category': category,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)

        mock_files.return_value = None

        mock_is_recaptcha_verified.return_value = False
        ResourceController.create_comment(resource_id)
        mock_comment.assert_called_once_with(
            resource_id, category, comment_content, attached_image_filename
        )

    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.get_action')
    @patch('ckanext.feedback.controllers.resource.suggest_ai_comment')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    def test_suggested_comment(
        self,
        mock_get_resource,
        mock_suggest_ai_comment,
        mock_get_action,
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
        mock_get_action.return_value = mock_package_show

        ResourceController.suggested_comment(resource_id, category, content, rating)
        mock_render.assert_called_once_with(
            'resource/suggestion.html',
            {
                'resource': mock_resource.Resource,
                'pkg_dict': mock_package,
                'selected_category': category,
                'rating': rating,
                'content': content,
                'softened': softened,
                'attached_image_filename': attached_image_filename,
            },
        )

    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.get_action')
    @patch('ckanext.feedback.controllers.resource.suggest_ai_comment')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    def test_suggested_comment_is_None(
        self,
        mock_get_resource,
        mock_suggest_ai_comment,
        mock_get_action,
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
        mock_get_action.return_value = mock_package_show

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
    @patch('ckanext.feedback.controllers.resource.get_action')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    def test_check_comment_POST_moral_keeper_ai_disable(
        self,
        mock_render,
        mock_get_action,
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
            'comment-suggested': False,
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
        mock_get_action.return_value = mock_package_show

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
    @patch('ckanext.feedback.controllers.resource.get_action')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    def test_check_comment_POST_judgement_True(
        self,
        mock_render,
        mock_get_action,
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
        mock_get_action.return_value = mock_package_show

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
    @patch('ckanext.feedback.controllers.resource.ResourceController.suggested_comment')
    @patch(
        'ckanext.feedback.controllers.resource.'
        'comment_service.get_resource_comment_categories'
    )
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.get_action')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    def test_check_comment_POST_judgement_False(
        self,
        mock_render,
        mock_get_action,
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
        mock_get_action.return_value = mock_package_show

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
    @patch('ckanext.feedback.controllers.resource.get_action')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    def test_check_comment_POST_suggested(
        self,
        mock_render,
        mock_get_action,
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
            'comment-suggested': True,
        }.get(x, default)

        mock_files.return_value = None

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'mock_package_id'
        mock_get_resource.return_value = mock_resource

        mock_package = 'mock_package'
        mock_package_show = MagicMock()
        mock_package_show.return_value = mock_package
        mock_get_action.return_value = mock_package_show

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

        mock_MoralKeeperAI = MagicMock()
        mock_MoralKeeperAI.return_value = None

        ResourceController.check_comment(resource_id)
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    def test_check_comment_with_bad_image(
        self,
        mock_comment,
        mock_flash_error,
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

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': True,
        }.get(x, default)

        mock_file = MagicMock()
        mock_file.filename = 'bad_image.txt'
        mock_files.return_value = mock_file

        mock_upload_image.side_effect = toolkit.ValidationError(
            {'upload': ['Invalid image file type']}
        )

        ResourceController.check_comment(resource_id)

        mock_flash_error.assert_called_once_with(
            {'Upload': 'Invalid image file type'}, allow_html=True
        )
        mock_comment.assert_called_once_with(resource_id, category, content)

    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.get_action')
    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.ResourceController._upload_image')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    def test_check_comment_with_bad_image_exception(
        self,
        mock_comment_service,
        mock_abort,
        mock_upload_image,
        mock_files,
        mock_form,
        mock_method,
        mock_get_action,
        mock_render,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        attached_image_filename = 'attached_image_filename'

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

        mock_upload_image.side_effect = Exception('Unexpected error')

        mock_resource = MagicMock()
        mock_resource.Resource.package_id = 'dummy_package_id'
        mock_comment_service.get_resource.return_value = mock_resource
        ResourceController.check_comment(resource_id)

        mock_package_show = MagicMock()
        mock_package_show.return_value = {'id': 'dummy_package_id'}
        mock_get_action.return_value = mock_package_show

        mock_render.return_value = 'mock_render'

        mock_upload_image.assert_called_once_with(mock_file)
        mock_abort.assert_called_once_with(500)

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    def test_check_comment_without_bad_recaptcha(
        self,
        mock_comment,
        mock_flash_error,
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
            'comment-suggested': True,
        }.get(x, default)

        mock_files.return_value = None

        mock_is_recaptcha_verified.return_value = False

        ResourceController.check_comment(resource_id)
        mock_flash_error.assert_called_once_with(
            'Bad Captcha. Please try again.', allow_html=True
        )
        mock_comment.assert_called_once_with(
            resource_id, category, content, attached_image_filename
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.request.files.get')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    def test_check_comment_without_comment_validation(
        self,
        mock_comment,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_redirect_to,
        mock_files,
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        while len(content) < 1000:
            content += content
        rating = '3'
        attached_image_filename = None

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'attached_image_filename': attached_image_filename,
            'comment-suggested': True,
        }.get(x, default)

        mock_files.return_value = None

        mock_is_recaptcha_verified.return_value = True

        ResourceController.check_comment(resource_id)
        mock_flash_error.assert_called_once_with(
            'Please keep the comment length below 1000',
            allow_html=True,
        )
        mock_comment.assert_called_once_with(
            resource_id, category, content, attached_image_filename
        )

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
        current_user,
    ):
        resource_id = 'resource id'
        resource_comment_id = 'resource comment id'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        mock_form.get.side_effect = [resource_comment_id]

        mock_redirect_to.return_value = 'resource comment url'
        ResourceController.approve_comment(resource_id)

        mock_comment_service.approve_resource_comment.assert_called_once_with(
            resource_comment_id, user_dict['id']
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
    def test_approve_comment_with_user(self, mock_toolkit_abort, current_user):
        resource_id = 'resource id'

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        ResourceController.approve_comment(resource_id)
        mock_toolkit_abort.assert_called_once_with(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_approve_comment_with_other_organization_admin_user(
        self,
        mock_redirect_to,
        mock_comment_service,
        mock_toolkit_abort,
        current_user,
    ):
        organization_dict = factories.Organization()
        package = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=package['id'])

        dummy_organization_dict = factories.Organization()
        dummy_organization = model.Group.get(dummy_organization_dict['id'])

        user_dict = factories.User()
        user = User.get(user_dict['id'])
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        member = model.Member(
            group=dummy_organization,
            group_id=dummy_organization_dict['id'],
            table_id=user.id,
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        mock_toolkit_abort.side_effect = Exception('abort')
        with pytest.raises(Exception):
            ResourceController.approve_comment(resource['id'])

        mock_toolkit_abort.assert_any_call(
            404,
            _(
                'The requested URL was not found on the server. If you entered the URL'
                ' manually please check your spelling and try again.'
            ),
        )

    @patch('flask_login.utils._get_user')
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
        current_user,
    ):
        resource_id = 'resource id'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        mock_form.get.side_effect = [None]

        ResourceController.approve_comment(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)

    @patch('flask_login.utils._get_user')
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
        current_user,
    ):
        resource_id = 'resource id'
        resource_comment_id = 'resource comment id'
        reply_content = 'reply content'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        mock_form.get.side_effect = [
            resource_comment_id,
            reply_content,
        ]

        mock_redirect_to.return_value = 'resource comment url'
        ResourceController.reply(resource_id)

        mock_comment_service.create_reply.assert_called_once_with(
            resource_comment_id, reply_content, user_dict['id']
        )
        mock_session_commit.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.request.form')
    def test_reply_with_user(
        self,
        mock_comment_service,
        mock_form,
        mock_toolkit_abort,
        mock_redirect_to,
        mock_flash_error,
        current_user,
    ):
        resource_id = 'resource id'

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        mock_form.get.side_effect = ['resource_comment_id', 'reply_content']

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = 'org-id'
        mock_comment_service.get_resource.return_value = mock_resource
        ResourceController.reply(resource_id)

        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )
        mock_toolkit_abort.assert_not_called()

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_reply_with_other_organization_admin_user(
        self,
        mock_redirect_to,
        mock_form,
        mock_comment_service,
        mock_flash_error,
        current_user,
    ):
        organization_dict = factories.Organization()
        package = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=package['id'])

        dummy_organization_dict = factories.Organization()
        dummy_organization = model.Group.get(dummy_organization_dict['id'])

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        member = model.Member(
            group=dummy_organization,
            group_id=dummy_organization_dict['id'],
            table_id=user_dict['id'],
            table_name='user',
            capacity='admin',
        )
        model.Session.add(member)
        model.Session.commit()

        mock_resource = MagicMock()
        mock_resource.Resource.package.owner_org = organization_dict['id']
        mock_comment_service.get_resource.return_value = mock_resource

        mock_form.get.side_effect = ['resource_comment_id', 'reply_content']

        ResourceController.reply(resource['id'])
        mock_comment_service.create_reply.assert_not_called()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource['id']
        )

    @patch('flask_login.utils._get_user')
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
        current_user,
    ):
        resource_id = 'resource id'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

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
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)
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
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
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
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
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
    ):
        resource_id = 'resource_id'
        comment_id = 'comment_id'
        attached_image_filename = 'attached_image_filename'

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
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
    ):
        organization_dict = factories.Organization()
        package = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=package['id'])

        mock_get_json.return_value = {'likeStatus': True}

        mock_resp = Mock()
        mock_resp.data = b"OK"
        mock_resp.status_code = 200
        mock_resp.mimetype = 'text/plain'
        mock_response.return_value = mock_resp

        mock_set_like_status_cookie.return_value = mock_resp
        resp = ResourceController.like_toggle(package['name'], resource['id'])

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
    ):
        organization_dict = factories.Organization()
        package = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=package['id'])

        mock_get_json.return_value = {'likeStatus': False}

        mock_resp = Mock()
        mock_resp.data = b"OK"
        mock_resp.status_code = 200
        mock_resp.mimetype = 'text/plain'
        mock_response.return_value = mock_resp

        mock_set_like_status_cookie.return_value = mock_resp
        resp = ResourceController.like_toggle(package['name'], resource['id'])

        mock_decrement.assert_called_once_with(resource['id'])
        mock_decrement_monthly.assert_called_once_with(resource['id'])

        assert resp.data.decode() == "OK"
        assert resp.status_code == 200
        assert resp.mimetype == 'text/plain'
        assert resp == mock_resp


@pytest.mark.usefixtures('with_request_context')
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

        mock_current_user(current_user, sysadmin)
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
        current_user,
        sysadmin,
        resource_comment,
    ):
        resource_id = resource_comment.resource_id
        comment_id = resource_comment.id
        response_status = 'completed'
        admin_liked = False

        mock_current_user(current_user, sysadmin)
        g.userobj = current_user

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

        mock_current_user(current_user, user)
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
    @patch('ckanext.feedback.controllers.resource.get_uploader')
    def test_upload_image(
        self,
        mock_get_uploader,
        mock_get_upload_destination,
    ):
        mock_image = MagicMock()
        mock_image.filename = 'test.png'

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
        app,
    ):
        user = factories.Sysadmin()
        user_obj = model.User.get(user['id'])
        current_user.return_value = user_obj

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
    def test_create_comment_admin_bypass_exception_then_proceed(
        self,
        mock_redirect_to,
        mock_flash_success,
        mock_session_commit,
        mock_create_summary,
        mock_create_comment,
        mock_get_resource,
        MockFeedbackConfig,
        current_user,
        app,
    ):
        user = factories.Sysadmin()
        user_obj = model.User.get(user['id'])
        current_user.return_value = user_obj

        cfg = MagicMock()
        cfg.recaptcha.force_all.get.return_value = False
        MockFeedbackConfig.return_value = cfg

        pkg = MagicMock()
        pkg.owner_org = 'org-x'
        res_obj = MagicMock()
        res_obj.package = pkg
        mock_res = MagicMock()
        mock_res.Resource = res_obj
        mock_get_resource.side_effect = [Exception('boom'), mock_res]

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
    # fmt: off
    @patch('ckanext.feedback.controllers.resource.get_action')
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
        mock_get_action,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        current_user,
        app,
    ):
        user = factories.Sysadmin()
        user_obj = model.User.get(user['id'])
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
        mock_res.organization_name = 'orgname'

        mock_get_resource.side_effect = [Exception('boom'), mock_res]
        mock_get_categories.return_value = ['REQUEST']
        mock_package_show = MagicMock()
        mock_package_show.return_value = 'pkg_dict'
        mock_get_action.return_value = mock_package_show

        with app.flask_app.test_request_context(
            '/',
            method='POST',
            data={'comment-content': 'ok', 'category': 'REQUEST'},
            content_type='application/x-www-form-urlencoded',
        ):
            ResourceController.check_comment('res-id')

        mock_render.assert_called_once_with(
            'resource/comment_check.html',
            {
                'resource': mock_res.Resource,
                'pkg_dict': 'pkg_dict',
                'categories': ['REQUEST'],
                'selected_category': 'REQUEST',
                'rating': '',
                'content': 'ok',
                'attached_image_filename': None,
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.resource.comment_service.get_resource')
    @patch('ckanext.feedback.controllers.resource.comment_service.approve_reply')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_approve_reply_success(
        self,
        mock_redirect_to,
        mock_commit,
        mock_approve,
        mock_get_resource,
        current_user,
    ):
        user = factories.Sysadmin()
        mock_current_user(current_user, user)
        g.userobj = current_user

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
        mock_get_resource,
        current_user,
    ):
        user = factories.Sysadmin()
        mock_current_user(current_user, user)
        g.userobj = current_user

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
        mock_get_resource,
        current_user,
    ):
        user = factories.Sysadmin()
        mock_current_user(current_user, user)
        g.userobj = current_user

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
    ):
        user = factories.Sysadmin()
        user_obj = model.User.get(user['id'])
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
    def test_reply_admin_bypass_exception_then_proceed(
        self,
        mock_redirect_to,
        mock_commit,
        mock_create_reply,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        current_user,
    ):
        user = factories.Sysadmin()
        user_obj = model.User.get(user['id'])
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
        mock_get_resource.side_effect = [Exception('boom'), mock_res]

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
    ):
        user = factories.Sysadmin()
        user_obj = model.User.get(user['id'])
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
    ):
        user = factories.User()
        user_obj = model.User.get(user['id'])
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
    ):
        user = factories.Sysadmin()
        user_obj = model.User.get(user['id'])
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
    ):
        user = factories.Sysadmin()
        mock_current_user(current_user, user)
        g.userobj = current_user

        mock_form_get.side_effect = ['   ', 'status-none', False]

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
    ):
        user = factories.Sysadmin()
        mock_current_user(current_user, user)
        g.userobj = current_user

        mock_form_get.side_effect = ['cid', 'status-none', False]

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
    ):
        user = factories.Sysadmin()
        mock_current_user(current_user, user)
        g.userobj = current_user

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
    @patch('ckanext.feedback.controllers.resource.get_action')
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
        mock_get_action,
        mock_get_resource,
        _mock_recaptcha,
        MockFeedbackConfig,
        current_user,
        app,
    ):
        user = factories.Sysadmin()
        user_obj = model.User.get(user['id'])
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
        pkg_show = MagicMock()
        pkg_show.return_value = 'pkg_dict'
        mock_get_action.return_value = pkg_show

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
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_approve_reply_missing_id_aborts_400(
        self,
        mock_abort,
        mock_get_resource,
        current_user,
    ):
        user = factories.Sysadmin()
        mock_current_user(current_user, user)
        g.userobj = current_user

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
    ):
        user = factories.Sysadmin()
        mock_current_user(current_user, user)
        g.userobj = current_user

        mock_form_get.side_effect = [None, 'status-none', False]

        ResourceController.reactions('res-id')
        mock_flash_error.assert_called_once()
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id='res-id'
        )
