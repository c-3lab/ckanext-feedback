from unittest.mock import patch

from ckanext.feedback.controllers.api.package_show import package_show


@patch("ckanext.feedback.controllers.api.package_show.model.Package.get")
@patch("ckanext.feedback.controllers.api.package_show.core_package_show")
def test_package_show_package_not_found(
    mock_core_package_show,
    mock_package_get,
):
    package_dict = {
        "id": "test-package-id",
        "extras": [],
    }

    mock_core_package_show.return_value = package_dict
    mock_package_get.return_value = None

    result = package_show({}, {})

    assert result == package_dict
