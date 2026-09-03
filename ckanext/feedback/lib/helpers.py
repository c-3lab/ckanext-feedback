"""Helper functions for feedback visualization."""

from collections import OrderedDict

from ckan.common import _
from ckan.plugins import toolkit

# Order matters: this defines the display order of feedback fields in the
# "Additional Information" table on the resource detail page.
# Maps the language-independent API field name (feedback_*) to a function
# that lazily returns the translated base label (evaluated per request, so
# that the current locale is always respected).
RESOURCE_FEEDBACK_KEYS = frozenset(
    [
        'feedback_like_count',
        'feedback_comments',
        'feedback_downloads',
        'feedback_utilizations',
        'feedback_issue_resolutions',
        'feedback_rating',
    ]
)

_FEEDBACK_FIELD_LABEL_GETTERS = OrderedDict(
    [
        ('feedback_like_count', lambda: _('Number of Likes')),
        ('feedback_comments', lambda: _('Comments')),
        ('feedback_downloads', lambda: _('Downloads')),
        ('feedback_utilizations', lambda: _('Utilizations')),
        ('feedback_issue_resolutions', lambda: _('Issue Resolutions')),
        ('feedback_rating', lambda: _('Rating')),
        # Dataset
        ('feedback_total_like_count', lambda: _('Total Likes')),
        ('feedback_total_comments', lambda: _('Total Comments')),
        ('feedback_total_downloads', lambda: _('Total Downloads')),
        ('feedback_total_utilizations', lambda: _('Total Utilizations')),
        ('feedback_total_issue_resolutions', lambda: _('Total Issue Resolutions')),
        ('feedback_average_rating', lambda: _('Average Rating')),
    ]
)

# CKAN core and themes (e.g. bodik_theme) render dataset extras as
# `{{ _(key) }}` and never reach get_feedback_field_label(), so each raw key
# needs a catalog entry of its own. Written as `_()` literals so that
# `pybabel extract` keeps them in the pot -- babel-clean
# (msgattrib --no-obsolete) deletes any entry the pot does not list.
_EXTRAS_KEY_LABEL_GETTERS = OrderedDict(
    [
        ('feedback_total_like_count', lambda: _('feedback_total_like_count')),
        ('feedback_total_comments', lambda: _('feedback_total_comments')),
        ('feedback_total_downloads', lambda: _('feedback_total_downloads')),
        (
            'feedback_total_utilizations',
            lambda: _('feedback_total_utilizations'),
        ),
        (
            'feedback_total_issue_resolutions',
            lambda: _('feedback_total_issue_resolutions'),
        ),
        ('feedback_average_rating', lambda: _('feedback_average_rating')),
    ]
)


def should_hide_resource_field(field_key):
    """Return True when a resource field should not appear in Additional Information."""

    if field_key in RESOURCE_FEEDBACK_KEYS or field_key.startswith('feedback_'):
        return True

    from ckanext.feedback.controllers.api.package_show import LEGACY_FEEDBACK_KEYS

    return field_key in LEGACY_FEEDBACK_KEYS


def get_feedback_field_label(field_key):
    """
    Convert a feedback_* field name into a display label.

    Args:
        field_key: A field name in the feedback_* format.

    Returns:
        A display label prefixed with "Feedback_"
        (or "フィードバック_" in multilingual environments).
    """

    # Prefer the raw-key entry so that this helper and a theme rendering
    # `{{ _(key) }}` produce the same label. Falls through when the catalog has
    # no entry for the key (the getter returns the msgid unchanged).
    extras_getter = _EXTRAS_KEY_LABEL_GETTERS.get(field_key)
    if extras_getter:
        label = extras_getter()
        if label != field_key:
            return label

    label_getter = _FEEDBACK_FIELD_LABEL_GETTERS.get(field_key)
    base_label = label_getter() if label_getter else field_key

    return '{} {}'.format(_('Feedback'), base_label)


def get_feedback_fields(resource):
    """
    Extract feedback-related fields from a resource.

    Args:
        resource: A resource dictionary.

    Returns:
        A dictionary where the keys are display labels
        and the values are the corresponding field values.
        (The field order follows the definition order of _FEEDBACK_FIELD_LABEL_GETTERS.)
    """

    fields = OrderedDict()
    for field_key in _FEEDBACK_FIELD_LABEL_GETTERS:
        if field_key in resource:
            fields[get_feedback_field_label(field_key)] = resource[field_key]

    return fields


@toolkit.chained_helper
def format_resource_items(next_helper, items):
    """Translate feedback_* resource field names before core formats them.

    A theme may override package/resource_read.html and render resource fields
    through this core helper, which never calls gettext -- it only does
    `key.replace('_', ' ')`. Translating the keys here keeps the labels correct
    whichever template wins the block.
    """

    return next_helper(
        [
            (
                (
                    get_feedback_field_label(key)
                    if key in _FEEDBACK_FIELD_LABEL_GETTERS
                    else key
                ),
                value,
            )
            for key, value in items
        ]
    )
