import logging

import requests
from ckan.common import config
from ckan.types import Request

from ckanext.feedback.services.common.config import FeedbackConfig

logger = logging.getLogger(__name__)


class CaptchaError(ValueError):
    pass


def _check_recaptcha_v3_base(request: Request) -> None:
    '''Check a user's recaptcha submission is valid, and raise CaptchaError
    on failure using discreet data'''
    client_ip_address = request.remote_addr or 'Unknown IP Address'
    recaptcha_response = request.form.get('g-recaptcha-response', '')
    if not recaptcha_response:
        logger.warning('not recaptcha_response')
        raise CaptchaError()

    recaptcha_private_key = FeedbackConfig().recaptcha.privatekey.get()
    if not recaptcha_private_key:
        logger.warning('not recaptcha_private_key')
        raise CaptchaError()

    # reCAPTCHA v3
    recaptcha_server_name = 'https://www.google.com/recaptcha/api/siteverify'

    # recaptcha_response_field will be unicode if there are foreign chars in
    # the user input. So we need to encode it as utf8 before urlencoding or
    # we get an exception.
    params = {
        'secret': recaptcha_private_key,
        'remoteip': client_ip_address,
        'response': recaptcha_response.encode('utf8'),
    }

    timeout = config.get('ckan.requests.timeout')

    data = requests.get(recaptcha_server_name, params, timeout=timeout).json()
    score_threshold = float(FeedbackConfig().recaptcha.score_threshold.get())

    try:
        if not data['success']:
            logger.warning(f'not success:{data}')
            raise CaptchaError()
        if data['score'] < score_threshold:
            logger.warning(
                f'Score is below the threshold:{data}:score_threshold={score_threshold}'
            )
            raise CaptchaError()
    except KeyError:
        # Something weird with recaptcha response
        logger.error("KeyError")
        raise CaptchaError()

    logger.info(f'reCAPTCHA verification passed successfully:{data}')


def is_recaptcha_verified(request: Request):
    if FeedbackConfig().recaptcha.is_enable():
        try:
            _check_recaptcha_v3_base(request)
        except CaptchaError:
            return False
    return True
