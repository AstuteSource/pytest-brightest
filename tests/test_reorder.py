"""Test the TestReorderer class."""

import json

import pytest

from pytest_brightest.reorder import ReordererOfTests


class TestReordererOfTests:
    """Test the TestReorderer class."""

    def test_init_with_default_path(self, tmp_path):
        """Test that the TestReorderer can be initialized with a default path."""
        reorderer = ReordererOfTests()
        assert reorderer.json_report_path == ".pytest_cache/pytest-json-report.json"

    def test_init_with_custom_path(self, tmp_path):
        """Test that the TestReorderer can be initialized with a custom path."""
        json_path = tmp_path / "report.json"
        reorderer = ReordererOfTests(str(json_path))
        assert reorderer.json_report_path == str(json_path)

    def test_load_test_data_file_not_found(self, tmp_path):
        """Test that the TestReorderer can handle a missing JSON report."""
        json_path = tmp_path / "non_existent_report.json"
        reorderer = ReordererOfTests(str(json_path))
        assert not reorderer.has_test_data()

    def test_load_test_data_invalid_json(self, tmp_path):
        """Test that the TestReorderer can handle an invalid JSON report."""
        json_path = tmp_path / "report.json"
        json_path.write_text("invalid json")
        reorderer = ReordererOfTests(str(json_path))
        assert not reorderer.has_test_data()

    def test_load_test_data_success(self, tmp_path, mock_test_item):
        """Test that the ReordererOfTests can load test data from a JSON report."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {
                    "nodeid": "test_one",
                    "setup": {"duration": 0.1},
                    "call": {"duration": 0.2},
                    "teardown": {"duration": 0.3},
                    "outcome": "passed",
                }
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        assert reorderer.has_test_data()
        assert reorderer.get_test_total_duration(mock_test_item("test_one")) == pytest.approx(0.6)
        assert reorderer.get_test_outcome(mock_test_item("test_one")) == "passed"

    def test_get_test_total_duration_not_found(self, tmp_path, mock_test_item):
        """Test that the ReordererOfTests returns 0 for a test not in the report."""
        reorderer = ReordererOfTests()
        assert reorderer.get_test_total_duration(mock_test_item("not_found")) == 0.0

    def test_get_test_outcome_not_found(self, tmp_path, mock_test_item):
        """Test that the ReordererOfTests returns 'unknown' for a test not in the report."""
        reorderer = ReordererOfTests()
        assert reorderer.get_test_outcome(mock_test_item("not_found")) == "unknown"

    def test_classify_tests_by_outcome(self, tmp_path, mock_test_item):
        """Test that the ReordererOfTests can classify tests by outcome."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {"nodeid": "test_pass", "outcome": "passed"},
                {"nodeid": "test_fail", "outcome": "failed"},
                {"nodeid": "test_error", "outcome": "error"},
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [
            mock_test_item("test_pass"),
            mock_test_item("test_fail"),
            mock_test_item("test_error"),
        ]
        passing, failing = reorderer.classify_tests_by_outcome(items)
        assert [item.name for item in passing] == ["test_pass"]
        assert [item.name for item in failing] == ["test_fail", "test_error"]

    def test_sort_tests_by_total_duration(self, tmp_path, mock_test_item):
        """Test that the ReordererOfTests can sort tests by total duration."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {"nodeid": "test_fast", "setup": {"duration": 0.1}},
                {"nodeid": "test_slow", "setup": {"duration": 0.5}},
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [mock_test_item("test_slow"), mock_test_item("test_fast")]
        sorted_items = reorderer.sort_tests_by_total_duration(items)
        assert [item.name for item in sorted_items] == ["test_fast", "test_slow"]
        sorted_items = reorderer.sort_tests_by_total_duration(items, ascending=False)
        assert [item.name for item in sorted_items] == ["test_slow", "test_fast"]

