from unittest.mock import MagicMock, patch

import pytest
import six
from ckan import model
from ckan.logic import get_action
from ckan.model import Resource, Session, User
from ckan.plugins import toolkit
from ckan.tests import factories
from flask import Flask, g

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
)
from ckanext.feedback.controllers.utilization import UtilizationController
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization, UtilizationComment


def register_utilization(id, resource_id, title, description, approval):
    utilization = Utilization(
        id=id,
        resource_id=resource_id,
        title=title,
        description=description,
        approval=approval,
    )
    session.add(utilization)


def get_registered_utilization(resource_id):
    return (
        session.query(
            Utilization.id,
            Utilization.approval,
            Utilization.approved,
            Utilization.approval_user_id,
        )
        .filter(Utilization.resource_id == resource_id)
        .first()
    )


def register_utilization_comment(
    id, utilization_id, category, content, created, approval, approved, approval_user_id
):
    utilization_comment = UtilizationComment(
        id=id,
        utilization_id=utilization_id,
        category=category,
        content=content,
        created=created,
        approval=approval,
        approved=approved,
        approval_user_id=approval_user_id,
    )
    session.add(utilization_comment)


def get_registered_utilization_comment(utilization_id):
    return (
        session.query(
            UtilizationComment.id,
            UtilizationComment.utilization_id,
            UtilizationComment.category,
            UtilizationComment.content,
            UtilizationComment.approval,
            UtilizationComment.approved,
            UtilizationComment.approval_user_id,
        )
        .filter(UtilizationComment.utilization_id == utilization_id)
        .all()
    )


def convert_utilization_comment_to_tuple(utilization_comment):
    return (
        utilization_comment.utilization_id,
        utilization_comment.category,
        utilization_comment.content,
        utilization_comment.approval,
        utilization_comment.approved,
        utilization_comment.approval_user_id,
    )


engine = model.repo.session.get_bind()


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationController:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    def setup_method(self, method):
        self.app = Flask(__name__)

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request')
    def test_search(self, mock_request, mock_get_utilizations, mock_render, app):
        dataset = factories.Dataset()
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        resource = factories.Resource(package_id=dataset['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        mock_request.args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': 'test_keyword',
            'disable_keyword': 'test_disable_keyword',
        }.get(x, default)

        with app.flask_app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'], 'test_keyword', None
        )
        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': 'test_keyword',
                'disable_keyword': 'test_disable_keyword',
                'utilizations': mock_get_utilizations.return_value,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.search_service.get_utilizations')
    @patch('ckanext.feedback.controllers.utilization.request')
    def test_search_without_user(
        self, mock_request, mock_get_utilizations, mock_render, app
    ):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        mock_request.args.get.side_effect = lambda x, default: {
            'id': resource['id'],
            'keyword': 'test_keyword',
            'disable_keyword': 'test_disable_keyword',
        }.get(x, default)

        with app.flask_app.test_request_context(path='/'):
            g.userobj = None
            UtilizationController.search()

        mock_get_utilizations.assert_called_once_with(
            resource['id'], 'test_keyword', True
        )
        mock_render.assert_called_once_with(
            'utilization/search.html',
            {
                'keyword': 'test_keyword',
                'disable_keyword': 'test_disable_keyword',
                'utilizations': mock_get_utilizations.return_value,
            },
        )

    @patch('ckanext.feedback.controllers.utilization.toolkit.render')
    @patch('ckanext.feedback.controllers.utilization.registration_service.get_resource')
    @patch('ckanext.feedback.controllers.utilization.request')
    def test_new(self, mock_request, mock_get_resource, mock_render, app):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        user_dict = factories.User()
        user = User.get(user_dict['id'])
        user_env = {'REMOTE_USER': six.ensure_str(user.name)}

        mock_request.args.get.side_effect = lambda x, default: {
            'resource_id': resource['id'],
            'return_to_resource': True,
        }.get(x, default)

        # Create a Resource object with the same attributes as the resource dict
        resource_obj = Resource.get(resource['id'])
        mock_get_resource.return_value = resource_obj

        with app.flask_app.test_request_context(path='/', environ_base=user_env):
            g.userobj = user
            UtilizationController.new()

        context = {'model': model, 'session': Session, 'for_view': True}
        package = get_action('package_show')(context, {'id': dataset['id']})

        mock_render.assert_called_once_with(
            'utilization/new.html',
            {
                'pkg_dict': package,
                'return_to_resource': True,
                'resource': resource_obj,
            },
        )

    @patch("ckanext.feedback.controllers.utilization.request")
    @patch(
        "ckanext.feedback.controllers.utilization.registration_service.create_utilization"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.summary_service.create_utilization_summary"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.helpers.flash_success")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    def test_create_return_to_resource_true(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_create_utilization_summary,
        mock_create_utilization,
        mock_request,
    ):
        # Set up test data
        package_name = "test_package"
        resource_id = "test_resource_id"
        title = "test_title"
        description = "test_description"
        return_to_resource = True

        # Configure mock objects
        mock_request.form.get.side_effect = [
            package_name,
            resource_id,
            title,
            description,
            return_to_resource,
        ]
        mock_url_for.return_value = "resource_read_url"

        # Call the method
        UtilizationController.create()

        # Assert the expected behavior
        mock_create_utilization.assert_called_with(resource_id, title, description)
        mock_create_utilization_summary.assert_called_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            'resource.read', id=package_name, resource_id=resource_id
        )
        mock_redirect.assert_called_with("resource_read_url")

    @patch("ckanext.feedback.controllers.utilization.request")
    @patch(
        "ckanext.feedback.controllers.utilization.registration_service.create_utilization"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.summary_service.create_utilization_summary"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.helpers.flash_success")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    def test_create_return_to_resource_false(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_create_utilization_summary,
        mock_create_utilization,
        mock_request,
    ):
        # Set up test data
        package_name = "test_package"
        resource_id = "test_resource_id"
        title = "test_title"
        description = "test_description"
        return_to_resource = False

        # Configure mock objects
        mock_request.form.get.side_effect = [
            package_name,
            resource_id,
            title,
            description,
            return_to_resource,
        ]
        mock_url_for.return_value = "dataset_read_url"

        # Call the method
        UtilizationController.create()

        # Assert the expected behavior
        mock_create_utilization.assert_called_with(resource_id, title, description)
        mock_create_utilization_summary.assert_called_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with('dataset.read', id=package_name)
        mock_redirect.assert_called_with("dataset_read_url")

    @patch("ckanext.feedback.controllers.utilization.toolkit.abort")
    @patch("ckanext.feedback.controllers.utilization.request")
    @patch(
        "ckanext.feedback.controllers.utilization.registration_service.create_utilization"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.summary_service.create_utilization_summary"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.helpers.flash_success")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    def test_create_without_resource_id_title_description(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_create_utilization_summary,
        mock_create_utilization,
        mock_request,
        mock_toolkit_abort,
    ):
        # Set up test data
        package_name = "test_package"
        resource_id = ""
        title = ""
        description = ""
        return_to_resource = True

        # Configure mock objects
        mock_request.form.get.side_effect = [
            package_name,
            resource_id,
            title,
            description,
            return_to_resource,
        ]
        mock_url_for.return_value = "resource_read_url"

        # Call the method
        UtilizationController.create()

        mock_toolkit_abort.assert_called_once_with(400)

    @patch("ckanext.feedback.controllers.utilization.detail_service.get_utilization")
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.get_utilization_comments"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.get_utilization_comment_categories"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.get_issue_resolutions"
    )
    @patch("ckanext.feedback.controllers.utilization.toolkit.render")
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_details_approval_true(
        self,
        mock_c,
        mock_render,
        mock_get_issue_resolutions,
        mock_get_utilization_comment_categories,
        mock_get_utilization_comments,
        mock_get_utilization,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        mock_c.userobj = MagicMock(sysadmin=None)

        # Configure mock objects
        mock_get_utilization.return_value = "mock_utilization"
        mock_get_utilization_comments.return_value = "mock_comments"
        mock_get_utilization_comment_categories.return_value = "mock_categories"
        mock_get_issue_resolutions.return_value = "mock_issue_resolutions"

        # Call the method
        UtilizationController.details(utilization_id)

        # Assert the expected behavior
        mock_get_utilization.assert_called_once_with(utilization_id)
        mock_get_utilization_comments.assert_called_once_with(utilization_id, True)
        mock_get_utilization_comment_categories.assert_called_once()
        mock_get_issue_resolutions.assert_called_once_with(utilization_id)
        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': 'mock_utilization',
                'comments': 'mock_comments',
                'categories': 'mock_categories',
                'issue_resolutions': 'mock_issue_resolutions',
            },
        )
        mock_get_utilization_comments.assert_called_once_with(utilization_id, True)

    @patch("ckanext.feedback.controllers.utilization.detail_service.get_utilization")
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.get_utilization_comments"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.get_utilization_comment_categories"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.get_issue_resolutions"
    )
    @patch("ckanext.feedback.controllers.utilization.toolkit.render")
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_details_approval_false(
        self,
        mock_c,
        mock_render,
        mock_get_issue_resolutions,
        mock_get_utilization_comment_categories,
        mock_get_utilization_comments,
        mock_get_utilization,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        mock_c.userobj = MagicMock(sysadmin=True)

        # Configure mock objects
        mock_get_utilization.return_value = "mock_utilization"
        mock_get_utilization_comments.return_value = "mock_comments"
        mock_get_utilization_comment_categories.return_value = "mock_categories"
        mock_get_issue_resolutions.return_value = "mock_issue_resolutions"

        # Call the method
        UtilizationController.details(utilization_id)

        # Assert the expected behavior
        mock_get_utilization.assert_called_once_with(utilization_id)
        mock_get_utilization_comment_categories.assert_called_once()
        mock_get_issue_resolutions.assert_called_once_with(utilization_id)
        mock_render.assert_called_once_with(
            'utilization/details.html',
            {
                'utilization_id': utilization_id,
                'utilization': 'mock_utilization',
                'comments': 'mock_comments',
                'categories': 'mock_categories',
                'issue_resolutions': 'mock_issue_resolutions',
            },
        )
        mock_get_utilization_comments.assert_called_once_with(utilization_id, None)

    @patch("ckanext.feedback.controllers.utilization.detail_service.get_utilization")
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.approve_utilization"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.summary_service.refresh_utilization_summary"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_approve(
        self,
        mock_c,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_refresh_utilization_summary,
        mock_approve_utilization,
        mock_get_utilization,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        resource_id = "test_resource_id"
        user_id = "test_user_id"
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])

        # Configure mock objects
        mock_c.userobj = MagicMock(id=user_id)
        mock_get_utilization.return_value = MagicMock(resource_id=resource_id)
        mock_url_for.return_value = "utilization_details_url"

        # Call the method
        g.userobj = user
        UtilizationController.approve(utilization_id)

        # Assert the expected behavior
        mock_get_utilization.assert_called_once_with(utilization_id)
        mock_approve_utilization.assert_called_once_with(utilization_id, user_id)
        mock_refresh_utilization_summary.assert_called_once_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with("utilization_details_url")

    @patch("ckanext.feedback.controllers.utilization.request")
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.create_utilization_comment"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.helpers.flash_success")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    def test_create_comment(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_create_utilization_comment,
        mock_request,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        category = "test_category"
        content = "test_content"

        # Configure mock objects
        mock_request.form.get.side_effect = [category, content]
        mock_url_for.return_value = "utilization_details_url"

        # Call the method
        UtilizationController.create_comment(utilization_id)

        # Assert the expected behavior
        mock_create_utilization_comment.assert_called_once_with(
            utilization_id, category, content
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with("utilization_details_url")

    @patch("ckanext.feedback.controllers.utilization.toolkit.abort")
    @patch("ckanext.feedback.controllers.utilization.request")
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.create_utilization_comment"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.helpers.flash_success")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    def test_create_comment_without_category_content(
        self,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_create_utilization_comment,
        mock_request,
        mock_toolkit_abort,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        category = ""
        content = ""

        # Configure mock objects
        mock_request.form.get.side_effect = [category, content]
        mock_url_for.return_value = "utilization_details_url"

        # Call the method
        UtilizationController.create_comment(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.approve_utilization_comment"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.refresh_utilization_comments"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_approve_comment(
        self,
        mock_c,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_refresh_utilization_comments,
        mock_approve_utilization_comment,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        comment_id = "test_comment_id"
        user_id = "test_user_id"
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])

        # Configure mock objects
        mock_c.userobj = MagicMock(id=user_id)
        mock_url_for.return_value = "utilization_details_url"

        # Call the method
        g.userobj = user
        UtilizationController.approve_comment(utilization_id, comment_id)

        # Assert the expected behavior
        mock_approve_utilization_comment.assert_called_once_with(comment_id, user_id)
        mock_refresh_utilization_comments.assert_called_once_with(utilization_id)
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            'utilization.details', utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with("utilization_details_url")

    @patch("ckanext.feedback.controllers.utilization.toolkit.render")
    @patch("ckanext.feedback.controllers.utilization.edit_service.get_resource_details")
    @patch(
        "ckanext.feedback.controllers.utilization.edit_service.get_utilization_details"
    )
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_edit(
        self,
        mock_c,
        mock_get_utilization_details,
        mock_get_resource_details,
        mock_render,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        utilization_details = MagicMock()
        resource_details = MagicMock()
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])

        # Configure mock objects
        mock_get_utilization_details.return_value = utilization_details
        mock_get_resource_details.return_value = resource_details

        # Call the method
        g.userobj = user
        UtilizationController.edit(utilization_id)

        # Assert the expected behavior
        mock_get_utilization_details.assert_called_once_with(utilization_id)
        mock_get_resource_details.assert_called_once_with(
            utilization_details.resource_id
        )
        mock_render.assert_called_once_with(
            'utilization/edit.html',
            {
                'utilization_details': utilization_details,
                'resource_details': resource_details,
            },
        )

    @patch("ckanext.feedback.controllers.utilization.request")
    @patch("ckanext.feedback.controllers.utilization.edit_service.update_utilization")
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.helpers.flash_success")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_update(
        self,
        mock_c,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_update_utilization,
        mock_request,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        title = "test_title"
        description = "test_description"

        # Configure mock objects
        userobj = MagicMock()
        userobj.sysadmin = True
        mock_c.configure_mock(userobj=userobj)

        mock_request.form.get.side_effect = [title, description]
        mock_url_for.return_value = "utilization_details_url"

        # Call the method
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.update(utilization_id)

        # Assert the expected behavior
        mock_update_utilization.assert_called_once_with(
            utilization_id, title, description
        )
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with(
            "utilization.details", utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with("utilization_details_url")

    @patch("ckanext.feedback.controllers.utilization.toolkit.abort")
    @patch("ckanext.feedback.controllers.utilization.request")
    @patch("ckanext.feedback.controllers.utilization.edit_service.update_utilization")
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.helpers.flash_success")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_update_without_title_description(
        self,
        mock_c,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_update_utilization,
        mock_request,
        mock_toolkit_abort,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        title = ""
        description = ""

        # Configure mock objects
        userobj = MagicMock()
        userobj.sysadmin = True
        mock_c.configure_mock(userobj=userobj)

        mock_request.form.get.side_effect = [title, description]
        mock_url_for.return_value = "utilization_details_url"

        # Call the method
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.update(utilization_id)

        mock_toolkit_abort.assert_called_once_with(400)

    @patch("ckanext.feedback.controllers.utilization.detail_service.get_utilization")
    @patch("ckanext.feedback.controllers.utilization.edit_service.delete_utilization")
    @patch(
        "ckanext.feedback.controllers.utilization.summary_service.refresh_utilization_summary"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.helpers.flash_success")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_delete(
        self,
        mock_c,
        mock_redirect,
        mock_url_for,
        mock_flash_success,
        mock_session_commit,
        mock_refresh_utilization_summary,
        mock_delete_utilization,
        mock_get_utilization,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        resource_id = "test_resource_id"

        # Configure mock objects
        userobj = MagicMock()
        userobj.sysadmin = True
        mock_c.configure_mock(userobj=userobj)

        utilization = MagicMock()
        utilization.resource_id = resource_id
        mock_get_utilization.return_value = utilization

        mock_url_for.return_value = "utilization_search_url"

        # Call the method
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.delete(utilization_id)

        # Assert the expected behavior
        mock_get_utilization.assert_called_once_with(utilization_id)
        mock_delete_utilization.assert_called_once_with(utilization_id)
        mock_refresh_utilization_summary.assert_called_once_with(resource_id)
        mock_session_commit.assert_called_once()
        mock_flash_success.assert_called_once()
        mock_url_for.assert_called_once_with("utilization.search")
        mock_redirect.assert_called_once_with("utilization_search_url")

    @patch("ckanext.feedback.controllers.utilization.toolkit.render")
    def test_comment(self, mock_render):
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.comment()
        mock_render.assert_called_once_with('utilization/comment.html')

    @patch("ckanext.feedback.controllers.utilization.toolkit.render")
    def test_comment_approval(self, mock_render):
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.comment_approval()
        mock_render.assert_called_once_with('utilization/comment_approval.html')

    @patch("ckanext.feedback.controllers.utilization.request")
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.create_issue_resolution"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.summary_service.increment_issue_resolution_summary"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    def test_create_issue_resolution(
        self,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_increment_issue_resolution_summary,
        mock_create_issue_resolution,
        mock_request,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        description = "test_description"

        mock_request.form.get.return_value = description
        mock_url_for.return_value = "utilization_details_url"

        # Call the method
        user_dict = factories.Sysadmin()
        user = User.get(user_dict['id'])
        g.userobj = user
        UtilizationController.create_issue_resolution(utilization_id)

        # Assert the expected behavior
        mock_create_issue_resolution.assert_called_once_with(
            utilization_id, description, user.id
        )
        mock_increment_issue_resolution_summary.assert_called_once_with(utilization_id)
        mock_session_commit.assert_called_once()
        mock_url_for.assert_called_once_with(
            "utilization.details", utilization_id=utilization_id
        )
        mock_redirect.assert_called_once_with("utilization_details_url")

    @patch("ckanext.feedback.controllers.utilization.toolkit.abort")
    @patch("ckanext.feedback.controllers.utilization.request")
    @patch(
        "ckanext.feedback.controllers.utilization.detail_service.create_issue_resolution"
    )
    @patch(
        "ckanext.feedback.controllers.utilization.summary_service.increment_issue_resolution_summary"
    )
    @patch("ckanext.feedback.controllers.utilization.session.commit")
    @patch("ckanext.feedback.controllers.utilization.url_for")
    @patch("ckanext.feedback.controllers.utilization.redirect")
    @patch("ckanext.feedback.controllers.utilization.c")
    def test_create_issue_resolution_description_None(
        self,
        mock_c,
        mock_redirect,
        mock_url_for,
        mock_session_commit,
        mock_increment_issue_resolution_summary,
        mock_create_issue_resolution,
        mock_request,
        mock_abort,
    ):
        # Set up test data
        utilization_id = "test_utilization_id"
        description = ""

        # Configure mock objects
        userobj = MagicMock()
        userobj.sysadmin = True
        mock_c.configure_mock(userobj=userobj)

        mock_request.form.get.return_value = description
        mock_url_for.return_value = "utilization_details_url"

        # Call the method

        # Call the method
        with self.app.test_request_context():
            user_dict = factories.Sysadmin()
            user = User.get(user_dict['id'])
            g.userobj = user
            request = UtilizationController.create_issue_resolution(utilization_id)

        # Assert the expected behavior
        request.status == "400"
        mock_abort.assert_called_once_with(400)
