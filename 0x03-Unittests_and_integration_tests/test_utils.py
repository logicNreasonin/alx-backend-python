#!/usr/bin/env python3
"""
This module contains unit tests for utility functions in the `utils` module.
It includes tests for `access_nested_map` covering normal access and
exception handling, tests for `get_json` which involve mocking HTTP calls,
and tests for the `memoize` decorator.
"""

import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized
from typing import Mapping, Sequence, Any, Dict

# Assuming utils.py is in the same directory or accessible in PYTHONPATH
from utils import access_nested_map, get_json, memoize


class TestAccessNestedMap(unittest.TestCase):
    """
    Test suite for the `access_nested_map` function from the `utils` module.
    This class implements tests to ensure that `access_nested_map` correctly
    retrieves values from nested dictionaries (or other mappings) using a
    sequence of keys representing the path to the desired value. It also
    tests its behavior when `KeyError` exceptions are expected due to invalid
    paths.
    """

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(
            self,
            nested_map: Mapping,
            path: Sequence,
            expected: Any
    ) -> None:
        """
        Tests `access_nested_map` for returning expected values.
        (Task 0)
        """
        self.assertEqual(access_nested_map(nested_map, path), expected)

    @parameterized.expand([
        ({}, ("a",), "'a'"),
        ({"a": 1}, ("a", "b"), "'b'")
    ])
    def test_access_nested_map_exception(
            self,
            nested_map: Mapping,
            path: Sequence,
            expected_message: str
    ) -> None:
        """
        Tests that `access_nested_map` raises KeyError with expected message.
        (Task 1)
        """
        with self.assertRaises(KeyError) as cm:
            access_nested_map(nested_map, path)
        self.assertEqual(str(cm.exception), expected_message)


class TestGetJson(unittest.TestCase):
    """
    Test suite for the `get_json` function from the `utils` module.
    This class tests the `get_json` function's ability to fetch JSON data
    from a URL, using mocks to simulate HTTP requests and responses.
    (Task 2)
    """

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    @patch('utils.requests.get')
    def test_get_json(
            self,
            test_url: str,
            test_payload: Dict,
            mock_requests_get: Mock
    ) -> None:
        """
        Tests `get_json` ensuring `requests.get` is called correctly
        and the payload is returned.
        """
        mock_response = Mock()
        mock_response.json.return_value = test_payload
        mock_requests_get.return_value = mock_response

        result = get_json(test_url)

        mock_requests_get.assert_called_once_with(test_url)
        self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """
    Test suite for the `memoize` decorator from the `utils` module.
    This class tests that the `memoize` decorator correctly caches the result
    of a method, ensuring the underlying method is called only once.
    (Task 3)
    """

    class TestClass:
        """
        A test class to demonstrate the behavior of the memoize decorator.
        """
        def a_method(self) -> int:
            """A sample method that returns a fixed integer value."""
            return 42

        @memoize
        def a_property(self) -> int:
            """A memoized property that calls `a_method`."""
            return self.a_method()

    def test_memoize(self) -> None:
        """
        Tests that a memoized property calls its underlying method only once.
        """
        test_object = self.TestClass()

        # Corrected line 124: Broken into multiple lines for readability and length
        with patch.object(
            test_object, 'a_method', return_value=42
        ) as mock_a_method:
            result1 = test_object.a_property
            result2 = test_object.a_property

            self.assertEqual(result1, 42)
            self.assertEqual(result2, 42)
            mock_a_method.assert_called_once()


if __name__ == '__main__':
    unittest.main()
# Added a newline character at the end of the file to fix W292