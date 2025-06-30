from unittest.mock import MagicMock, Mock, patch

import pytest
from ckan import model
from ckan.common import _, config
from ckan.logic import get_action
from ckan.model import User
from ckan.tests import factories
from flask import Flask, g

import ckanext.feedback.services.resource.comment as comment_service
from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_like_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.resource import ResourceController
from ckanext.feedback.models.resource_comment import ResourceCommentCategory
from ckanext.feedback.models.session import session

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
    # mock current_user
    current_user.return_value = user_obj


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_resource_like_tables(engine)
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_comment_with_sysadmin(
        self,
        mock_request,
        mock_render,
        mock_page,
        mock_pagination,
        current_user,
        app,
        sysadmin_env,
    ):
        user_dict = factories.Sysadmin()
        mock_current_user(current_user, user_dict)

        organization_dict = factories.Organization(
            name='org_name',
        )
        package = factories.Dataset(owner_org=organization_dict['id'])
        resource = factories.Resource(package_id=package['id'])
        resource['package'] = package
        # session.commit()
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
        cookie = comment_service.get_cookie(resource_id)
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

        assert g.pkg_dict["organization"]['name'] == 'org_name'
        mock_render.assert_called_once_with(
            'resource/comment.html',
            {
                'resource': resource.Resource,
                'pkg_dict': package,
                'categories': categories,
                'cookie': cookie,
                'selected_category': 'REQUEST',
                'content': '',
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_comment_with_user(
        self,
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
        cookie = comment_service.get_cookie(resource_id)
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
                'cookie': cookie,
                'selected_category': 'REQUEST',
                'content': '',
                'page': 'mock_page',
            },
        )

    @patch('flask_login.utils._get_user')
    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_comment_question_with_user(
        self,
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
        cookie = comment_service.get_cookie(resource_id)
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
                'cookie': cookie,
                'selected_category': 'QUESTION',
                'content': '',
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.utilization.get_pagination_value')
    @patch('ckanext.feedback.controllers.utilization.helpers.Page')
    @patch('ckanext.feedback.controllers.resource.toolkit.render')
    @patch('ckanext.feedback.controllers.resource.request')
    def test_comment_without_user(
        self, mock_request, mock_render, mock_page, mock_pagination, app
    ):
        owner_org = factories.Organization()
        dataset = factories.Dataset(owner_org=owner_org['id'])
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

        with app.get(url='/'):
            g.userobj = None
            ResourceController.comment(resource_id)

        approval = False
        resource = comment_service.get_resource(resource_id)
        comments, total_count = comment_service.get_resource_comments(
            resource_id,
            approval,
            limit=limit,
            offset=offset,
        )
        categories = comment_service.get_resource_comment_categories()
        cookie = comment_service.get_cookie(resource_id)
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
                'cookie': cookie,
                'selected_category': 'REQUEST',
                'content': '',
                'page': 'mock_page',
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.summary_service')
    @patch('ckanext.feedback.controllers.resource.comment_service')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_success')
    @patch('ckanext.feedback.controllers.resource.session.commit')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.toolkit.url_for')
    @patch('ckanext.feedback.controllers.resource.make_response')
    @patch('ckanext.feedback.controllers.resource.send_email')
    def test_create_comment(
        self,
        mock_send_email,
        mock_make_response,
        mock_url_for,
        mock_redirect_to,
        mock_session_commit,
        mock_flash_success,
        mock_comment_service,
        mock_summary_service,
        mock_form,
    ):
        resource_id = 'resource id'
        category = ResourceCommentCategory.REQUEST.name
        comment_content = 'content'
        rating = '1'
        package_name = 'ota'
        mock_form.get.side_effect = lambda x, default: {
            'package_name': package_name,
            'comment-content': comment_content,
            'category': category,
            'rating': rating,
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)

        mock_send_email.side_effect = Exception("Mock Exception")
        mock_url_for.return_value = 'resource comment'
        resp = ResourceController.create_comment(resource_id)

        mock_comment_service.create_resource_comment.assert_called_once_with(
            resource_id, category, comment_content, int(rating)
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
        resp.set_cookie.assert_called_once_with(resource_id, 'alreadyPosted')

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
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    def test_create_comment_without_comment_length(
        self,
        mock_flash_flash_error,
        mock_redirect_to,
        mock_comment,
        mock_form,
    ):
        resource_id = 'resource id'
        category = ResourceCommentCategory.REQUEST.name
        content = 'ex'
        while True:
            content += content
            if 1000 < len(content):
                break

        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)

        ResourceController.create_comment(resource_id)

        mock_flash_flash_error.assert_called_once_with(
            'Please keep the comment length below 1000',
            allow_html=True,
        )
        mock_comment.assert_called_once_with(resource_id, category, content)

    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.ResourceController.comment')
    @patch('ckanext.feedback.controllers.resource.is_recaptcha_verified')
    @patch('ckanext.feedback.controllers.resource.helpers.flash_error')
    def test_create_comment_without_bad_recaptcha(
        self,
        mock_flash_error,
        mock_is_recaptcha_verified,
        mock_comment,
        mock_form,
    ):
        resource_id = 'resource_id'
        comment_content = 'comment_content'
        category = ResourceCommentCategory.REQUEST.name
        package_name = 'ota'
        mock_form.get.side_effect = lambda x, default: {
            'package_name': package_name,
            'comment-content': comment_content,
            'category': category,
            'comment-suggested': True,
            'comment-checked': True,
        }.get(x, default)

        mock_is_recaptcha_verified.return_value = False
        ResourceController.create_comment(resource_id)
        mock_comment.assert_called_once_with(resource_id, category, comment_content)

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
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.form')
    @patch('ckanext.feedback.controllers.resource.toolkit.redirect_to')
    def test_check_comment_GET(
        self,
        mock_redirect_to,
        mock_form,
    ):
        resource_id = 'resource_id'

        mock_form.return_value = 'GET'

        ResourceController.check_comment(resource_id)
        mock_redirect_to.assert_called_once_with(
            'resource_comment.comment', resource_id=resource_id
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
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
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'

        config['ckan.feedback.moral_keeper_ai.enable'] = False

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'comment-suggested': False,
        }.get(x, default)

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
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
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
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        judgement = True

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'comment-suggested': False,
        }.get(x, default)

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
            },
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
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
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'
        judgement = False

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'comment-suggested': False,
        }.get(x, default)

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
        )

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
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
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'comment-suggested': True,
        }.get(x, default)

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
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        rating = '3'

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'comment-suggested': True,
        }.get(x, default)

        mock_is_recaptcha_verified.return_value = False

        ResourceController.check_comment(resource_id)
        mock_flash_error.assert_called_once_with(
            'Bad Captcha. Please try again.', allow_html=True
        )
        mock_comment.assert_called_once_with(resource_id, category, content)

    @patch('ckanext.feedback.controllers.resource.request.method')
    @patch('ckanext.feedback.controllers.resource.request.form')
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
        mock_form,
        mock_method,
    ):
        resource_id = 'resource_id'
        category = 'category'
        content = 'comment_content'
        while len(content) < 1000:
            content += content
        rating = '3'

        config['ckan.feedback.moral_keeper_ai.enable'] = True

        mock_method.return_value = 'POST'
        mock_form.get.side_effect = lambda x, default: {
            'comment-content': content,
            'category': category,
            'rating': rating,
            'comment-suggested': True,
        }.get(x, default)

        mock_is_recaptcha_verified.return_value = True

        ResourceController.check_comment(resource_id)
        mock_flash_error.assert_called_once_with(
            'Please keep the comment length below 1000',
            allow_html=True,
        )
        mock_comment.assert_called_once_with(resource_id, category, content)

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
    @patch('ckanext.feedback.controllers.resource.toolkit.abort')
    def test_reply_with_user(self, mock_toolkit_abort, current_user):
        resource_id = 'resource id'

        user_dict = factories.User()
        mock_current_user(current_user, user_dict)
        g.userobj = current_user

        ResourceController.reply(resource_id)
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
    def test_reply_with_other_organization_admin_user(
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

        ResourceController.reply(resource['id'])
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

        ResourceController.reply(resource_id)
        mock_toolkit_abort.assert_called_once_with(400)

    @patch('ckanext.feedback.controllers.resource.comment_service.get_cookie')
    def test_like_status_return_True(self, mock_get_cookie):
        mock_get_cookie.return_value = 'True'
        resource_id = 'resource id'

        result = ResourceController.like_status(resource_id)
        assert result == 'True'

    @patch('ckanext.feedback.controllers.resource.comment_service.get_cookie')
    def test_like_status_return_False(self, mock_get_cookie):
        mock_get_cookie.return_value = 'False'
        resource_id = 'resource id'

        result = ResourceController.like_status(resource_id)
        assert result == 'False'

    @patch('ckanext.feedback.controllers.resource.comment_service.get_cookie')
    def test_like_status_none(self, mock_get_cookie):
        mock_get_cookie.return_value = None
        resource_id = 'resource id'

        result = ResourceController.like_status(resource_id)
        assert result == 'False'

    @patch('ckanext.feedback.controllers.resource.request.get_json')
    @patch('ckanext.feedback.controllers.resource.Response')
    def test_like_toggle_True(
        self,
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

        resp = ResourceController.like_toggle(package['name'], resource['id'])

        assert resp.data.decode() == "OK"
        assert resp.status_code == 200
        assert resp.mimetype == 'text/plain'
        assert resp == mock_resp

    @patch('ckanext.feedback.controllers.resource.request.get_json')
    @patch('ckanext.feedback.controllers.resource.Response')
    def test_like_toggle_False(
        self,
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

        resp = ResourceController.like_toggle(package['name'], resource['id'])

        assert resp.data.decode() == "OK"
        assert resp.status_code == 200
        assert resp.mimetype == 'text/plain'
        assert resp == mock_resp
