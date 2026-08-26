"""Helper functions for feedback visualization."""

from collections import OrderedDict

from ckan.common import _

# Order matters: this defines the display order of feedback fields in the
# "Additional Information" table on the resource detail page.
# Maps the language-independent API field name (feedback_*) to a function
# that lazily returns the translated base label (evaluated per request, so
# that the current locale is always respected).
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


def get_feedback_field_label(field_key):
    """
    feedback_* フィールド名を表示用ラベルに変換する

    Args:
        field_key: feedback_* 形式のフィールド名

    Returns:
        「フィードバック_」（多言語環境では「Feedback_」）を接頭辞に持つ
        表示用ラベル
    """

    label_getter = _FEEDBACK_FIELD_LABEL_GETTERS.get(field_key)
    base_label = label_getter() if label_getter else field_key

    return '{} {}'.format(_('Feedback'), base_label)


def get_feedback_fields(resource):
    """
    リソースからフィードバック関連フィールドを抽出する

    Args:
        resource: リソース辞書

    Returns:
        表示用ラベルをキーとし、値を値とした辞書
        （フィールドの並び順は _FEEDBACK_FIELD_LABEL_GETTERS の定義順）
    """

    fields = OrderedDict()
    for field_key in _FEEDBACK_FIELD_LABEL_GETTERS:
        if field_key in resource:
            fields[get_feedback_field_label(field_key)] = resource[field_key]

    return fields
