"""i18n utilities for ckanext-feedback"""

import polib


def filter_ckan_msgids():
    """Exclude CKAN core msgids from the feedback pot file"""
    ckan_pot = polib.pofile('ckanext/feedback/i18n/ckan.pot')
    ckan_msgids = {e.msgid for e in ckan_pot if e.msgid}

    feedback_pot = polib.pofile('ckanext/feedback/i18n/ckanext-feedback.pot')
    to_remove = [e for e in feedback_pot if e.msgid in ckan_msgids]

    for e in to_remove:
        feedback_pot.remove(e)

    feedback_pot.save()
    print(f"Removed {len(to_remove)} CKAN core msgids from feedback pot")


if __name__ == '__main__':
    filter_ckan_msgids()
