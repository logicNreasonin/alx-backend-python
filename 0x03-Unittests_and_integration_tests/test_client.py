#!/usr/bin/env python3
"""
This module contains unit and integration tests for the `GithubOrgClient`
class from the `client` module. Unit tests mock dependencies heavily,
while integration tests use fixtures to simulate more realistic interactions.
"""

import unittest
from unittest.mock import patch, PropertyMock, Mock
from parameterized import parameterized, parameterized_class
from typing import Dict, List, Any

# Import the class to be tested and fixtures
from client import GithubOrgClient
from fixtures import TEST_PAYLOAD  # This is a list of tuples


class TestGithubOrgClient(unittest.TestCase):
    """
    Unit Test suite for the `GithubOrgClient` class.
    """

    @parameterized.expand([
        ("google", {"login": "google", "name": "Google Inc."}),
        ("abc", {"login": "abc", "name": "Alphabet Inc."}),
    ])
    @patch('client.get_json')
    def test_org(
            self,
            org_name: str,
            expected_org_payload: Dict,
            mock_get_json: Mock
    ) -> None:
        """
        Tests the `GithubOrgClient.org` property.
        Verifies `get_json` call and returned payload. (Task 4)
        """
        mock_get_json.return_value = expected_org_payload
        client = GithubOrgClient(org_name)
        # Access the .org property multiple times
        org_data1 = client.org
        org_data2 = client.org  # Should use cached value

        expected_url = GithubOrgClient.ORG_URL.format(org=org_name)
        # get_json should be called only once due to memoization of client.org
        mock_get_json.assert_called_once_with(expected_url)

        self.assertEqual(org_data1, expected_org_payload)
        self.assertEqual(org_data2, expected_org_payload)

    def test_public_repos_url(self) -> None:
        """
        Tests the `_public_repos_url` property.
        Verifies URL construction from mocked `org` payload. (Task 5)
        """
        # This is the payload that GithubOrgClient.org would return
        known_org_payload = {
            "repos_url": "https://api.github.com/orgs/testorg/repos"
        }
        with patch.object(GithubOrgClient,
                          'org',
                          new_callable=PropertyMock) as mock_org_property:
            mock_org_property.return_value = known_org_payload
            client = GithubOrgClient("testorg")
            public_repos_url = client._public_repos_url
            self.assertEqual(public_repos_url,
                             known_org_payload["repos_url"])
            mock_org_property.assert_called_once()

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json: Mock) -> None:
        """
        Tests `public_repos` without license filtering.
        Verifies processing of `get_json` payload and interactions
        with `_public_repos_url`. (Task 6)
        """
        # This is the payload that get_json(repos_url) would return
        repos_payload_fixture = [
            {"name": "repo1"}, {"name": "repo2"}, {"name": "repo3"}
        ]
        expected_repo_names = ["repo1", "repo2", "repo3"]
        mock_get_json.return_value = repos_payload_fixture

        # This is the URL that _public_repos_url property would return
        known_repos_url = "https://api.github.com/orgs/testorg/repos"
        with patch.object(GithubOrgClient,
                          '_public_repos_url',
                          new_callable=PropertyMock) as mock_public_repos_url_property:
            mock_public_repos_url_property.return_value = known_repos_url
            client = GithubOrgClient("testorg")

            # Access public_repos multiple times
            list_of_repo_names1 = client.public_repos()
            list_of_repo_names2 = client.public_repos()  # Should use cached

            self.assertEqual(list_of_repo_names1, expected_repo_names)
            self.assertEqual(list_of_repo_names2, expected_repo_names)

            mock_public_repos_url_property.assert_called_once()
            # get_json (for repos) should be called once
            mock_get_json.assert_called_once_with(known_repos_url)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
        ({"license": {"key": "my_license"}}, "other_license", False),
        ({"license": None}, "my_license", False),
        ({}, "my_license", False),
        ({"license": {"no_key_field": "value"}}, "my_license", False)
    ])
    def test_has_license(self,
                         repo: Dict[str, Any],
                         license_key: str,
                         expected: bool
                         ) -> None:
        """
        Tests the `GithubOrgClient.has_license` static method. (Task 7)
        """
        self.assertEqual(GithubOrgClient.has_license(repo, license_key),
                         expected)


@parameterized_class(
    ('org_payload', 'repos_payload', 'expected_repos', 'apache2_repos'),
    TEST_PAYLOAD
)
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """
    Integration Test suite for `GithubOrgClient.public_repos`.
    Uses fixtures from `fixtures.TEST_PAYLOAD`. (Task 8)
    """
    org_payload: Dict
    repos_payload: List[Dict]
    expected_repos: List[str]
    apache2_repos: List[str]

    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up class method to patch `requests.get` for all tests in this class.
        The mock for `requests.get` is configured with a side effect function
        that returns different mock responses based on the URL being requested,
        using data from the class's fixture attributes.
        """
        cls.org_name_for_fixture = "google"

        def mock_requests_get_side_effect(url: str) -> Mock:
            mock_response = Mock()
            expected_org_url = GithubOrgClient.ORG_URL.format(
                org=cls.org_name_for_fixture
            )
            expected_repos_url = cls.org_payload.get("repos_url")

            if url == expected_org_url:
                mock_response.json.return_value = cls.org_payload
            elif url == expected_repos_url:
                mock_response.json.return_value = cls.repos_payload
            else:
                mock_response.status_code = 404
                mock_response.json.return_value = {
                    "message": "Not Found", "url_called": url
                }
            return mock_response

        # Modified line: Patch 'requests.get' directly
        cls.get_patcher = patch('requests.get',
                                side_effect=mock_requests_get_side_effect)
        cls.mock_requests_get = cls.get_patcher.start()

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Tear down class method to stop the patcher for `requests.get`
        that was started in `setUpClass`.
        """
        cls.get_patcher.stop()

    def test_public_repos(self) -> None:
        """
        Integration test for `public_repos` without license filtering.
        """
        org_client = GithubOrgClient(self.org_name_for_fixture)
        actual_repos = org_client.public_repos()
        self.assertEqual(actual_repos, self.expected_repos)

    def test_public_repos_with_license(self) -> None:
        """
        Integration test for `public_repos` with "apache-2.0" license filtering.
        """
        org_client = GithubOrgClient(self.org_name_for_fixture)
        actual_repos = org_client.public_repos(license="apache-2.0")
        self.assertEqual(actual_repos, self.apache2_repos)


if __name__ == '__main__':
    unittest.main()