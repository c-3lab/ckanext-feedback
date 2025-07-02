import logging
import os

import ckan.lib.mailer
import ckan.plugins.toolkit as toolkit
from ckan.common import config
from jinja2 import Environment, FileSystemLoader

from ckanext.feedback.services.common.config import FeedbackConfig

log = logging.getLogger(__name__)


def send_email(template_name, organization_id, subject, **kwargs):
    if not FeedbackConfig().notice_email.is_enable():
        log.info('email notification is disabled.')
        return

    # settings email_template and subject from [feedback_config.json > ckan.ini]
    template_dir = config.get(
        'ckan.feedback.notice.email.template_directory',
        FeedbackConfig().notice_email.template_directory.default,
    )

    if not os.path.isfile(f'{template_dir}/{template_name}'):
        log.error(
            'template_file error. %s/%s: No such file or directory',
            template_dir,
            template_name,
        )
        return

    log.info('use template. %s/%s', template_dir, template_name)

    if not subject:
        subject = 'New Submission Notification'
        log.info('use default_subject: [%s]', subject)

    email_body = (
        Environment(loader=FileSystemLoader(template_dir))
        .get_template(template_name)
        .render(kwargs)
    )

    # Retrieving organization administrators and sending emails
    context = {'ignore_auth': True, 'keep_email': True}

    get_members = toolkit.get_action('member_list')
    show_user = toolkit.get_action('user_show')

    condition = {'id': organization_id, 'object_type': 'user', 'capacity': 'admin'}
    users = [
        show_user(context, {'id': id}) for (id, _, _) in get_members(context, condition)
    ]

    for user in users:
        try:
            toolkit.enqueue_job(
                ckan.lib.mailer.mail_recipient,
                kwargs={
                    'recipient_name': user['name'],
                    'recipient_email': user['email'],
                    'subject': subject,
                    'body': email_body,
                },
            )
        except Exception:
            log.exception(f'user: {user}')
