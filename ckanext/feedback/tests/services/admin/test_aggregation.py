from unittest.mock import MagicMock, patch

import pytest
from ckan.common import config
from ckan.tests import factories
from sqlalchemy.sql import column

from ckanext.feedback.services.admin import aggregation


@pytest.mark.db_test
class TestFeedbacks:

    def test_get_resource_details(
        self,
    ):
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        resource = factories.Resource(package_id=dataset['id'])

        site_url = config.get('ckan.site_url', '')

        group_title, package_title, resource_name, resource_link = (
            aggregation.get_resource_details(resource['id'])
        )

        assert group_title == organization['title']
        assert package_title == dataset['title']
        assert resource_name == resource['name']
        assert (
            resource_link
            == f'{site_url}/dataset/{dataset["name"]}/resource/{resource["id"]}'
        )

    @patch('ckanext.feedback.services.admin.aggregation.session.query')
    def test_create_resource_report_query(self, mock_query):
        # Mock organization data (no need for actual DB entry)
        organization = {'name': 'test-org', 'title': 'Test Organization'}

        mock_session = MagicMock()
        mock_query.return_value = mock_session

        download_subquery = MagicMock()
        download_subquery.c.download_count = column("download_count")
        download_subquery.c.resource_id = column("resource_id")

        resource_comment_subquery = MagicMock()
        resource_comment_subquery.c.comment_count = column("comment_count")
        resource_comment_subquery.c.resource_id = column("resource_id")

        utilization_subquery = MagicMock()
        utilization_subquery.c.utilization_count = column("utilization_count")
        utilization_subquery.c.resource_id = column("resource_id")

        utilization_comment_subquery = MagicMock()
        utilization_comment_subquery.c.utilization_comment_count = column(
            "utilization_comment_count"
        )
        utilization_comment_subquery.c.resource_id = column("resource_id")

        issue_resolution_subquery = MagicMock()
        issue_resolution_subquery.c.issue_resolution_count = column(
            "issue_resolution_count"
        )
        issue_resolution_subquery.c.resource_id = column("resource_id")

        like_subquery = MagicMock()
        like_subquery.c.like_count = column("like_count")
        like_subquery.c.resource_id = column("resource_id")

        rating_subquery = MagicMock()
        rating_subquery.c.average_rating = column("average_rating")
        rating_subquery.c.resource_id = column("resource_id")

        result_query = aggregation.create_resource_report_query(
            download_subquery,
            resource_comment_subquery,
            utilization_subquery,
            utilization_comment_subquery,
            issue_resolution_subquery,
            like_subquery,
            rating_subquery,
            organization['name'],
        )

        assert result_query is not None

    @patch('ckanext.feedback.services.admin.aggregation.create_resource_report_query')
    def test_get_monthly_data(self, mock_create_query):
        organization = factories.Organization()

        select_month = '2024-03'

        mock_create_query.return_value = "final_query"

        result = aggregation.get_monthly_data(organization['name'], select_month)

        assert result == "final_query"

    @patch('ckanext.feedback.services.admin.aggregation.create_resource_report_query')
    def test_get_yearly_data(self, mock_create_query):
        organization = factories.Organization()

        select_year = '2024'

        mock_create_query.return_value = "final_query"

        result = aggregation.get_yearly_data(organization['name'], select_year)

        assert result == "final_query"

    @patch('ckanext.feedback.services.admin.aggregation.create_resource_report_query')
    def test_get_all_time_data(self, mock_create_query):
        organization = factories.Organization()

        mock_create_query.return_value = "final_query"

        result = aggregation.get_all_time_data(organization['name'])

        assert result == "final_query"
