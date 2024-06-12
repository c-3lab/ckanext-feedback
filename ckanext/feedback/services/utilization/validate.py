import ckan.logic.validators as validators


def validate_url(url):
    errors = {'key': []}
    context = {}
    validators.url_validator('key', {'key': url}, errors, context)
    return errors['key']
