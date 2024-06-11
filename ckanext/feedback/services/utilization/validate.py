from ckan.logic import get_validator


def validate_url(url):
    errors = {'key': []}
    context = {}
    get_validator('url_validator')('key', {'key': url}, errors, context)
    if errors['key']:
        return False
    return True
