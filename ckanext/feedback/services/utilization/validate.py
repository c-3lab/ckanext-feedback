import ckan.logic.validators as validators


def validate_url(url):
    errors = {'key': []}
    context = {}
    validators.url_validator('key', {'key': url}, errors, context)
    if errors['key']:
        return 'Please provide a valid URL'

    if 2048 < len(url):
        return 'Please keep the URL length below 2048'
    return


def validate_title(title):
    if 50 < len(title):
        return 'Please keep the title length below 50'
    return


def validate_description(description):
    if 2000 < len(description):
        return 'Please keep the description length below 2000'
    return


def validate_comment(comment):
    if 1000 < len(comment):
        return 'Please keep the comment length below 1000'
    return
