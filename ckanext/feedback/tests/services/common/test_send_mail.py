import os
from unittest.mock import MagicMock, patch

import ckan.lib.mailer
import ckan.tests.factories as factories
import pytest
from ckan import model
from ckan.common import config
from jinja2 import Environment, FileSystemLoader

from ckanext.feedback.services.common.send_mail import send_email

engine = model.repo.session.get_bind()

template_dir = (
    '/srv/app/src_extensions/ckanext-feedback/ckanext/feedback/tests/services/common'
)
template_name = 'mail_template.txt'


def create_org_admin_user():
    user = factories.User()
    user_dict = user
    user_dict['name'] = 'test_user'
    user_dict['email'] = 'user@email.com'

    organization_dict = factories.Organization()
    organization = model.Group.get(organization_dict['id'])

    member = MagicMock()
    member.table_name = 'user'
    member.table_id = user['id']
    member.capacity = 'admin'
    member.group_id = organization.id
    member.group = organization
    return (user_dict, organization.id)


def mock_get_members(_, a):
    return [
        ('id', '_', '_'),
    ]


def mock_show_user(_, b):
    return {'name': 'test_user', 'email': 'user@email.com'}


@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestSendMail:
    @classmethod
    def setup_class(cls):
        model.repo.init_db()

    @patch('ckanext.feedback.services.common.send_mail.toolkit.get_action')
    @patch('ckanext.feedback.services.common.send_mail.toolkit.enqueue_job')
    def test_send_email(self, mock_enqueue_job, mock_get_action):
        (user, organization_id) = create_org_admin_user()
        config['ckan.feedback.notice.email.enable'] = True
        config['ckan.feedback.notice.email.template_directory'] = template_dir
        subject = 'test subject'

        mock_enqueue_job.side_effect = Exception("Mock Exception")
        mock_get_action.side_effect = [mock_get_members, mock_show_user]

        email_body = (
            Environment(loader=FileSystemLoader(template_dir))
            .get_template(template_name)
            .render()
        )

        send_email(template_name, organization_id, subject)

        mock_enqueue_job.assert_called_once_with(
            ckan.lib.mailer.mail_recipient,
            kwargs={
                'recipient_name': user['name'],
                'recipient_email': user['email'],
                'subject': subject,
                'body': email_body,
            },
        )

    @patch('ckanext.feedback.services.common.send_mail.log.info')
    def test_send_email_disable(self, mock_log_info):
        config['ckan.feedback.notice.email.enable'] = False
        send_email(template_name, '', '')
        mock_log_info.assert_called_once_with('email notification is disabled.')

    @patch('ckanext.feedback.services.common.send_mail.log.error')
    def test_send_email_no_template(self, mock_log_error):
        config['ckan.feedback.notice.email.enable'] = True

        email_template_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                '..',
                'templates',
                'email_notification',
            )
        )

        send_email('no_template.test', '', '')
        mock_log_error.assert_called_once_with(
            'template_file error. %s/%s: No such file or directory',
            email_template_dir,
            'no_template.test',
        )

    @patch('ckanext.feedback.services.common.send_mail.toolkit.get_action')
    @patch('ckanext.feedback.services.common.send_mail.toolkit.enqueue_job')
    def test_send_email_no_subject(self, mock_enqueue_job, mock_get_action):
        (user, organization_id) = create_org_admin_user()
        config['ckan.feedback.notice.email.enable'] = True
        config['ckan.feedback.notice.email.template_directory'] = template_dir

        mock_get_action.side_effect = [mock_get_members, mock_show_user]

        email_body = (
            Environment(loader=FileSystemLoader(template_dir))
            .get_template(template_name)
            .render()
        )

        send_email(template_name, organization_id, '')

        mock_enqueue_job.assert_called_once_with(
            ckan.lib.mailer.mail_recipient,
            kwargs={
                'recipient_name': user['name'],
                'recipient_email': user['email'],
                'subject': 'New Submission Notification',
                'body': email_body,
            },
        )
