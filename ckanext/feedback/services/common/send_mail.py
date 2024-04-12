import logging

import ckan.lib.mailer
import ckan.plugins.toolkit as toolkit
from jinja2 import Environment, FileSystemLoader

log = logging.getLogger(__name__)
DEFAULT_TEMPLATE_DIR = (
    '/srv/app'
    + '/src_extensions/ckanext-feedback/ckanext/feedback/templates/email_notification'
)


def send_email(action, organization_id, target_name, content_title, content, url):
    template_name = 'email_template.text'
    subject = 'New Submission Notification'
    email_body = (
        Environment(loader=FileSystemLoader(DEFAULT_TEMPLATE_DIR))
        .get_template(template_name)
        .render(
            {
                'action': action,
                'target': target_name,
                'content_title': content_title,
                'content': content,
                'url': url,
            }
        )
    )

    # Retrieving organization administrators and sending emails
    get_members = toolkit.get_action('member_list')
    show_user = toolkit.get_action('user_show')

    condition = {'id': organization_id, 'object_type': 'user', 'capacity': 'admin'}
    users = [show_user(None, {'id': id}) for (id, _, _) in get_members(None, condition)]

    for user in users:
        try:
            ckan.lib.mailer.mail_recipient(
                recipient_name=user['name'],
                recipient_email=user['email'],
                subject=subject,
                body=email_body,
            )
        except Exception:
            log.exception(
                'To:%s[%s]',
                user['name'],
                user['email'],
            )
