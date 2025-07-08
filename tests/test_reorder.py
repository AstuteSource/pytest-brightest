"""Test the TestReorderer class."""

import json

import pytest

from pytest_brightest.reorder import ReordererOfTests, create_reorderer


class TestReordererOfTests:
    """Test the TestReorderer class."""

    def test_init_with_default_path(self, tmp_path):
        """Test that the TestReorderer can be initialized with a default path."""
        _ = tmp_path
        reorderer = ReordererOfTests()
        assert (
            reorderer.json_report_path
            == ".pytest_cache/pytest-json-report.json"
        )

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
        assert reorderer.get_test_total_duration(
            mock_test_item("test_one")
        ) == pytest.approx(0.6)
        assert (
            reorderer.get_test_outcome(mock_test_item("test_one")) == "passed"
        )

    def test_get_test_total_duration_not_found(self, tmp_path, mock_test_item):
        """Test that the ReordererOfTests returns 0 for a test not in the report."""
        _ = tmp_path
        reorderer = ReordererOfTests()
        assert (
            reorderer.get_test_total_duration(mock_test_item("not_found"))
            == 0.0
        )

    def test_get_test_outcome_not_found(self, tmp_path, mock_test_item):
        """Test that the ReordererOfTests returns 'unknown' for a test not in the report."""
        _ = tmp_path
        reorderer = ReordererOfTests()
        assert (
            reorderer.get_test_outcome(mock_test_item("not_found"))
            == "unknown"
        )

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
        assert [item.name for item in sorted_items] == [
            "test_fast",
            "test_slow",
        ]
        sorted_items = reorderer.sort_tests_by_total_duration(
            items, ascending=False
        )
        assert [item.name for item in sorted_items] == [
            "test_slow",
            "test_fast",
        ]

    def test_reorder_modules_by_failure(
        self, tmp_path, mock_test_item, mocker
    ):
        """Test reordering modules by failure count."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {"nodeid": "module_a.py::test_a1", "outcome": "passed"},
                {"nodeid": "module_a.py::test_a2", "outcome": "failed"},
                {"nodeid": "module_b.py::test_b1", "outcome": "passed"},
                {"nodeid": "module_b.py::test_b2", "outcome": "failed"},
                {"nodeid": "module_b.py::test_b3", "outcome": "failed"},
                {"nodeid": "module_c.py::test_c1", "outcome": "passed"},
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [
            mock_test_item("module_a.py::test_a1"),
            mock_test_item("module_a.py::test_a2"),
            mock_test_item("module_b.py::test_b1"),
            mock_test_item("module_b.py::test_b2"),
            mock_test_item("module_b.py::test_b3"),
            mock_test_item("module_c.py::test_c1"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_modules_by_failure(items, ascending=True)
        assert [item.name for item in items] == [
            "module_c.py::test_c1",
            "module_a.py::test_a1",
            "module_a.py::test_a2",
            "module_b.py::test_b1",
            "module_b.py::test_b2",
            "module_b.py::test_b3",
        ]

        items = [
            mock_test_item("module_a.py::test_a1"),
            mock_test_item("module_a.py::test_a2"),
            mock_test_item("module_b.py::test_b1"),
            mock_test_item("module_b.py::test_b2"),
            mock_test_item("module_b.py::test_b3"),
            mock_test_item("module_c.py::test_c1"),
        ]
        reorderer.reorder_modules_by_failure(items, ascending=False)
        assert [item.name for item in items] == [
            "module_b.py::test_b1",
            "module_b.py::test_b2",
            "module_b.py::test_b3",
            "module_a.py::test_a1",
            "module_a.py::test_a2",
            "module_c.py::test_c1",
        ]

    def test_reorder_modules_by_cost(self, tmp_path, mock_test_item, mocker):
        """Test reordering modules by cost."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {"nodeid": "module_a.py::test_a1", "call": {"duration": 0.5}},
                {"nodeid": "module_a.py::test_a2", "call": {"duration": 0.1}},
                {"nodeid": "module_b.py::test_b1", "call": {"duration": 1.0}},
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [
            mock_test_item("module_a.py::test_a1"),
            mock_test_item("module_b.py::test_b1"),
            mock_test_item("module_a.py::test_a2"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_modules_by_cost(items, ascending=True)
        assert [item.name for item in items] == [
            "module_a.py::test_a1",
            "module_a.py::test_a2",
            "module_b.py::test_b1",
        ]

        items = [
            mock_test_item("module_a.py::test_a1"),
            mock_test_item("module_b.py::test_b1"),
            mock_test_item("module_a.py::test_a2"),
        ]
        reorderer.reorder_modules_by_cost(items, ascending=False)
        assert [item.name for item in items] == [
            "module_b.py::test_b1",
            "module_a.py::test_a1",
            "module_a.py::test_a2",
        ]

    def test_reorder_modules_by_name(self, mock_test_item, mocker):
        """Test reordering modules by name."""
        reorderer = ReordererOfTests()
        items = [
            mock_test_item("module_b.py::test_b1"),
            mock_test_item("module_a.py::test_a1"),
            mock_test_item("module_c.py::test_c1"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_modules_by_name(items, ascending=True)
        assert [item.name for item in items] == [
            "module_a.py::test_a1",
            "module_b.py::test_b1",
            "module_c.py::test_c1",
        ]

        items = [
            mock_test_item("module_b.py::test_b1"),
            mock_test_item("module_a.py::test_a1"),
            mock_test_item("module_c.py::test_c1"),
        ]
        reorderer.reorder_modules_by_name(items, ascending=False)
        assert [item.name for item in items] == [
            "module_c.py::test_c1",
            "module_b.py::test_b1",
            "module_a.py::test_a1",
        ]

    def test_reorder_tests_within_module(
        self, tmp_path, mock_test_item, mocker
    ):
        """Test reordering tests within modules."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {
                    "nodeid": "module_a.py::test_a_slow",
                    "call": {"duration": 1.0},
                },
                {
                    "nodeid": "module_a.py::test_a_fast",
                    "call": {"duration": 0.1},
                },
                {
                    "nodeid": "module_b.py::test_b_slow",
                    "call": {"duration": 0.8},
                },
                {
                    "nodeid": "module_b.py::test_b_fast",
                    "call": {"duration": 0.2},
                },
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [
            mock_test_item("module_a.py::test_a_slow"),
            mock_test_item("module_a.py::test_a_fast"),
            mock_test_item("module_b.py::test_b_slow"),
            mock_test_item("module_b.py::test_b_fast"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_tests_within_module(items, "cost", ascending=True)
        assert [item.name for item in items] == [
            "module_a.py::test_a_fast",
            "module_a.py::test_a_slow",
            "module_b.py::test_b_fast",
            "module_b.py::test_b_slow",
        ]

        items = [
            mock_test_item("module_a.py::test_a_slow"),
            mock_test_item("module_a.py::test_a_fast"),
            mock_test_item("module_b.py::test_b_slow"),
            mock_test_item("module_b.py::test_b_fast"),
        ]
        reorderer.reorder_tests_within_module(items, "name", ascending=False)
        assert [item.name for item in items] == [
            "module_a.py::test_a_slow",
            "module_a.py::test_a_fast",
            "module_b.py::test_b_slow",
            "module_b.py::test_b_fast",
        ]

    def test_reorder_tests_across_modules(self, tmp_path, mock_test_item):
        """Test reordering tests across modules."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {
                    "nodeid": "module_a.py::test_a_slow",
                    "call": {"duration": 1.0},
                },
                {
                    "nodeid": "module_a.py::test_a_fast",
                    "call": {"duration": 0.1},
                },
                {
                    "nodeid": "module_b.py::test_b_slow",
                    "call": {"duration": 0.8},
                },
                {
                    "nodeid": "module_b.py::test_b_fast",
                    "call": {"duration": 0.2},
                },
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [
            mock_test_item("module_a.py::test_a_slow"),
            mock_test_item("module_a.py::test_a_fast"),
            mock_test_item("module_b.py::test_b_slow"),
            mock_test_item("module_b.py::test_b_fast"),
        ]
        reorderer.reorder_tests_across_modules(items, "cost", ascending=True)
        assert [item.name for item in items] == [
            "module_a.py::test_a_fast",
            "module_b.py::test_b_fast",
            "module_b.py::test_b_slow",
            "module_a.py::test_a_slow",
        ]

        items = [
            mock_test_item("module_a.py::test_a_slow"),
            mock_test_item("module_a.py::test_a_fast"),
            mock_test_item("module_b.py::test_b_slow"),
            mock_test_item("module_b.py::test_b_fast"),
        ]
        reorderer.reorder_tests_across_modules(items, "name", ascending=False)
        assert [item.name for item in items] == [
            "module_b.py::test_b_slow",
            "module_b.py::test_b_fast",
            "module_a.py::test_a_slow",
            "module_a.py::test_a_fast",
        ]

        items = [
            mock_test_item("module_a.py::test_a_pass"),
            mock_test_item("module_b.py::test_b_fail"),
            mock_test_item("module_c.py::test_c_pass"),
        ]
        # Create a JSON report with outcomes
        json_path_failure = tmp_path / "report_failure.json"
        data_failure = {
            "tests": [
                {"nodeid": "module_a.py::test_a_pass", "outcome": "passed"},
                {"nodeid": "module_b.py::test_b_fail", "outcome": "failed"},
                {"nodeid": "module_c.py::test_c_pass", "outcome": "passed"},
            ]
        }
        json_path_failure.write_text(json.dumps(data_failure))
        reorderer_failure = ReordererOfTests(str(json_path_failure))

        reorderer_failure.reorder_tests_across_modules(
            items, "failure", ascending=True
        )
        assert [item.name for item in items] == [
            "module_a.py::test_a_pass",
            "module_c.py::test_c_pass",
            "module_b.py::test_b_fail",
        ]

        items = [
            mock_test_item("module_a.py::test_a_pass"),
            mock_test_item("module_b.py::test_b_fail"),
            mock_test_item("module_c.py::test_c_pass"),
        ]
        reorderer_failure.reorder_tests_across_modules(
            items, "failure", ascending=False
        )
        assert [item.name for item in items] == [
            "module_b.py::test_b_fail",
            "module_a.py::test_a_pass",
            "module_c.py::test_c_pass",
        ]

    def test_reorder_tests_in_place(self, tmp_path, mock_test_item, mocker):
        """Test the main reordering function."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {
                    "nodeid": "module_a.py::test_a_slow",
                    "call": {"duration": 1.0},
                },
                {
                    "nodeid": "module_a.py::test_a_fast",
                    "call": {"duration": 0.1},
                },
                {
                    "nodeid": "module_b.py::test_b_slow",
                    "call": {"duration": 0.8},
                },
                {
                    "nodeid": "module_b.py::test_b_fast",
                    "call": {"duration": 0.2},
                },
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [
            mock_test_item("module_a.py::test_a_slow"),
            mock_test_item("module_a.py::test_a_fast"),
            mock_test_item("module_b.py::test_b_slow"),
            mock_test_item("module_b.py::test_b_fast"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_tests_in_place(
            items, "cost", "ascending", "tests-across-modules"
        )
        assert [item.name for item in items] == [
            "module_a.py::test_a_fast",
            "module_b.py::test_b_fast",
            "module_b.py::test_b_slow",
            "module_a.py::test_a_slow",
        ]

        items = [
            mock_test_item("module_b.py::test_b1"),
            mock_test_item("module_a.py::test_a1"),
        ]
        reorderer.reorder_tests_in_place(
            items, "name", "ascending", "modules-within-suite"
        )
        assert [item.name for item in items] == [
            "module_a.py::test_a1",
            "module_b.py::test_b1",
        ]

        items = [
            mock_test_item("module_a.py::test_a_slow"),
            mock_test_item("module_a.py::test_a_fast"),
        ]
        reorderer.reorder_tests_in_place(
            items, "cost", "ascending", "tests-within-module"
        )
        assert [item.name for item in items] == [
            "module_a.py::test_a_fast",
            "module_a.py::test_a_slow",
        ]

        items = []
        reorderer.reorder_tests_in_place(
            items, "cost", "ascending", "tests-across-modules"
        )
        assert items == []

    def test_create_reorderer(self):
        """Test the create_reorderer function."""
        reorderer = create_reorderer()
        assert isinstance(reorderer, ReordererOfTests)
        assert (
            reorderer.json_report_path
            == ".pytest_cache/pytest-json-report.json"
        )
        reorderer = create_reorderer("custom.json")
        assert isinstance(reorderer, ReordererOfTests)
        assert reorderer.json_report_path == "custom.json"
