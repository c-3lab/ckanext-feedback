import logging
import os

import ckan.lib.mailer
import ckan.plugins.toolkit as toolkit
from ckan.common import config
from jinja2 import Environment, FileSystemLoader

log = logging.getLogger(__name__)
DEFAULT_TEMPLATE_DIR = (
    '/srv/app'
    + '/src_extensions/ckanext-feedback/ckanext/feedback/templates/email_notification'
)


def send_email(template_name, organization_id, subject, **kwargs):
    if not toolkit.asbool(config.get('ckan.feedback.notice.email.enable', False)):
        log.info('email notification is disabled.')
        return

    # settings email_template and subject from [feedback_config.json > ckan.ini]
    template_dir = config.get('ckan.feedback.notice.email.template_directory')
    if not os.path.isfile(f'{template_dir}/{template_name}'):
        template_dir = DEFAULT_TEMPLATE_DIR

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
    get_members = toolkit.get_action('member_list')
    show_user = toolkit.get_action('user_show')

    condition = {'id': organization_id, 'object_type': 'user', 'capacity': 'admin'}
    users = [show_user(None, {'id': id}) for (id, _, _) in get_members(None, condition)]

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
