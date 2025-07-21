"""Test the TestReorderer class."""

import json

import pytest

from pytest_brightest.reorder import (
    ReordererOfTests,
    create_reorderer,
    setup_json_report_plugin,
)


def test_create_reorderer():
    """Test the create_reorderer function."""
    reorderer = create_reorderer()
    assert isinstance(reorderer, ReordererOfTests)
    assert (
        reorderer.json_report_path == ".pytest_cache/pytest-json-report.json"
    )
    reorderer = create_reorderer("custom.json")
    assert isinstance(reorderer, ReordererOfTests)
    assert reorderer.json_report_path == "custom.json"


def test_load_test_data_json_decode_error(tmp_path):
    """Test loading test data with JSON decode error."""
    json_path = tmp_path / "bad.json"
    json_path.write_text("{bad json}")
    reorderer = ReordererOfTests(str(json_path))
    assert not reorderer.has_test_data()


def test_get_prior_data_for_reordering_all_branches(tmp_path, mock_test_item):
    """Test getting prior data for all reordering branches."""
    json_path = tmp_path / "report.json"
    data = {
        "tests": [
            {
                "nodeid": "mod1::t1",
                "call": {"duration": 1.0},
                "outcome": "passed",
            },
            {
                "nodeid": "mod1::t2",
                "call": {"duration": 2.0},
                "outcome": "failed",
            },
            {
                "nodeid": "mod2::t3",
                "call": {"duration": 3.0},
                "outcome": "error",
            },
        ]
    }
    json_path.write_text(json.dumps(data))
    reorderer = ReordererOfTests(str(json_path))
    items = [
        mock_test_item("mod1::t1"),
        mock_test_item("mod1::t2"),
        mock_test_item("mod2::t3"),
    ]
    # COST, MODULES_WITHIN_SUITE
    d = reorderer.get_prior_data_for_reordering(
        items, "cost", "modules-within-suite"
    )
    assert "test_module_costs" in d
    # COST, TESTS_WITHIN_MODULE
    d = reorderer.get_prior_data_for_reordering(
        items, "cost", "tests-within-module"
    )
    assert "test_case_costs" in d
    # COST, TESTS_ACROSS_MODULES
    d = reorderer.get_prior_data_for_reordering(
        items, "cost", "tests-within-suite"
    )
    assert "test_case_costs" in d
    # NAME, MODULES_WITHIN_SUITE
    d = reorderer.get_prior_data_for_reordering(
        items, "name", "modules-within-suite"
    )
    assert "module_order" in d
    # NAME, TESTS_WITHIN_SUITE
    d = reorderer.get_prior_data_for_reordering(
        items, "name", "tests-within-suite"
    )
    assert "test_order" in d
    # NAME, TESTS_WITHIN_MODULE
    d = reorderer.get_prior_data_for_reordering(
        items, "name", "tests-within-module"
    )
    assert "module_tests" in d
    # FAILURE, MODULES_WITHIN_SUITE
    d = reorderer.get_prior_data_for_reordering(
        items, "failure", "modules-within-suite"
    )
    assert "module_failure_counts" in d
    # FAILURE, TESTS_WITHIN_MODULE
    d = reorderer.get_prior_data_for_reordering(
        items, "failure", "tests-within-module"
    )
    assert "module_failure_counts" in d
    assert "test_case_failures" in d
    # FAILURE, TESTS_WITHIN_SUITE
    d = reorderer.get_prior_data_for_reordering(
        items, "failure", "tests-within-suite"
    )
    assert "test_case_failures" in d


def test_reorder_tests_in_place_empty():
    """Test reordering with empty items list."""
    reorderer = ReordererOfTests()
    items = []
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "modules-within-suite"
    )
    assert items == []


def test_reorder_tests_in_place_all_branches(tmp_path, mock_test_item, mocker):
    """Test reordering tests in place for all branches."""
    json_path = tmp_path / "report.json"
    data = {
        "tests": [
            {
                "nodeid": "mod1::t1",
                "call": {"duration": 1.0},
                "outcome": "passed",
            },
            {
                "nodeid": "mod1::t2",
                "call": {"duration": 2.0},
                "outcome": "failed",
            },
        ]
    }
    json_path.write_text(json.dumps(data))
    reorderer = ReordererOfTests(str(json_path))
    items = [mock_test_item("mod1::t1"), mock_test_item("mod1::t2")]
    mocker.patch("pytest_brightest.reorder.console.print")
    # modules-within-suite, cost
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "modules-within-suite"
    )
    # modules-within-suite, name
    reorderer.reorder_tests_in_place(
        items, "name", "ascending", "modules-within-suite"
    )
    # modules-within-suite, failure
    reorderer.reorder_tests_in_place(
        items, "failure", "ascending", "modules-within-suite"
    )
    # tests-within-module
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "tests-within-module"
    )
    # tests-across-modules
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "tests-within-suite"
    )

    # modules-within-suite, name
    reorderer.reorder_tests_in_place(
        items, "name", "ascending", "modules-within-suite"
    )
    # modules-within-suite, failure
    reorderer.reorder_tests_in_place(
        items, "failure", "ascending", "modules-within-suite"
    )
    # tests-within-module
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "tests-within-module"
    )
    # tests-within-suite
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "tests-within-suite"
    )


def test_setup_json_report_plugin_branches(mocker):
    """Test setup_json_report_plugin for all branches and exceptions."""

    class DummyConfig:
        class Option:
            json_report_file = ".report.json"

        option = Option()

        class PluginManager:
            def has_plugin(self, name):
                return name == "pytest_jsonreport"

        pluginmanager = PluginManager()

    config = DummyConfig()
    mocker.patch("pytest_brightest.reorder.console.print")
    assert setup_json_report_plugin(config) is True

    # test ImportError
    def raise_import_error(*args, **kwargs):
        _ = args
        _ = kwargs
        raise ImportError("fail")

    mocker.patch.object(
        config.pluginmanager, "has_plugin", side_effect=raise_import_error
    )
    assert setup_json_report_plugin(config) is False

    # test Exception
    def raise_exception(*args, **kwargs):
        _ = args
        _ = kwargs
        raise Exception("fail")

    mocker.patch.object(
        config.pluginmanager, "has_plugin", side_effect=raise_exception
    )
    assert setup_json_report_plugin(config) is False


def test_load_test_data_key_error(tmp_path):
    """Test loading test data with a KeyError."""
    json_path = tmp_path / "bad.json"
    json_path.write_text('{"tests": [{}]}')  # Missing 'nodeid'
    reorderer = ReordererOfTests(str(json_path))
    assert not reorderer.has_test_data()


class TestReordererOfTests:
    """Test the ReordererOfTests class."""

    def test_load_test_data_no_file(self):
        """Test loading test data when the file does not exist."""
        reorderer = ReordererOfTests("non_existent.json")
        assert not reorderer.has_test_data()

    def test_load_test_data_with_file(self, tmp_path):
        """Test loading test data from a valid JSON file."""
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
        assert "test_one" in reorderer.test_data
        assert reorderer.test_data["test_one"][
            "total_duration"
        ] == pytest.approx(0.6)
        assert reorderer.test_data["test_one"]["outcome"] == "passed"

    def test_get_test_total_duration(self, mock_test_item):
        """Test getting the total duration of a test."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "test_one": {"total_duration": 1.23, "outcome": "passed"}
        }
        item = mock_test_item("test_one")
        assert reorderer.get_test_total_duration(item) == 1.23  # noqa: PLR2004
        item = mock_test_item("test_two")
        assert reorderer.get_test_total_duration(item) == 0.0

    def test_get_test_outcome(self, mock_test_item):
        """Test getting the outcome of a test."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "test_one": {"total_duration": 1.23, "outcome": "failed"}
        }
        item = mock_test_item("test_one")
        assert reorderer.get_test_outcome(item) == "failed"
        item = mock_test_item("test_two")
        assert reorderer.get_test_outcome(item) == "unknown"

    def test_classify_tests_by_outcome(self, mock_test_item):
        """Test classifying tests by their outcome."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "test_pass": {"total_duration": 1, "outcome": "passed"},
            "test_fail": {"total_duration": 1, "outcome": "failed"},
            "test_error": {"total_duration": 1, "outcome": "error"},
        }
        items = [
            mock_test_item("test_pass"),
            mock_test_item("test_fail"),
            mock_test_item("test_error"),
            mock_test_item("test_unknown"),
        ]
        passing, failing = reorderer.classify_tests_by_outcome(items)
        assert [item.name for item in passing] == ["test_pass", "test_unknown"]
        assert [item.name for item in failing] == ["test_fail", "test_error"]

    def test_sort_tests_by_total_duration(self, mock_test_item):
        """Test sorting tests by their total duration."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "test_slow": {"total_duration": 2.0, "outcome": "passed"},
            "test_fast": {"total_duration": 1.0, "outcome": "passed"},
        }
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

    def test_reorder_modules_by_cost(self, mock_test_item, mocker):
        """Test reordering modules by their cumulative cost."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test1": {"total_duration": 1.0, "outcome": "passed"},
            "mod1::test2": {"total_duration": 2.0, "outcome": "passed"},
            "mod2::test1": {"total_duration": 4.0, "outcome": "passed"},
        }
        items = [
            mock_test_item("mod1::test1"),
            mock_test_item("mod1::test2"),
            mock_test_item("mod2::test1"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_modules_by_cost(items)
        assert [item.name for item in items] == [
            "mod1::test1",
            "mod1::test2",
            "mod2::test1",
        ]
        reorderer.reorder_modules_by_cost(items, ascending=False)
        assert [item.name for item in items] == [
            "mod2::test1",
            "mod1::test1",
            "mod1::test2",
        ]

    def test_reorder_modules_by_name(self, mock_test_item, mocker):
        """Test reordering modules by their name."""
        reorderer = ReordererOfTests()
        items = [
            mock_test_item("mod_b::test1"),
            mock_test_item("mod_a::test1"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_modules_by_name(items)
        assert [item.name for item in items] == [
            "mod_a::test1",
            "mod_b::test1",
        ]
        reorderer.reorder_modules_by_name(items, ascending=False)
        assert [item.name for item in items] == [
            "mod_b::test1",
            "mod_a::test1",
        ]

    def test_reorder_modules_by_failure(self, mock_test_item, mocker):
        """Test reordering modules by their failure count."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod_a::test1": {"total_duration": 1, "outcome": "failed"},
            "mod_b::test1": {"total_duration": 1, "outcome": "passed"},
            "mod_b::test2": {"total_duration": 1, "outcome": "failed"},
            "mod_b::test3": {"total_duration": 1, "outcome": "failed"},
        }
        items = [
            mock_test_item("mod_a::test1"),
            mock_test_item("mod_b::test1"),
            mock_test_item("mod_b::test2"),
            mock_test_item("mod_b::test3"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_modules_by_failure(items)
        assert [item.name for item in items] == [
            "mod_a::test1",
            "mod_b::test1",
            "mod_b::test2",
            "mod_b::test3",
        ]
        reorderer.reorder_modules_by_failure(items, ascending=False)
        assert [item.name for item in items] == [
            "mod_b::test1",
            "mod_b::test2",
            "mod_b::test3",
            "mod_a::test1",
        ]

    def test_reorder_tests_within_module(self, mock_test_item, mocker):
        """Test reordering tests within each module."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test_slow": {"total_duration": 2.0, "outcome": "passed"},
            "mod1::test_fast": {"total_duration": 1.0, "outcome": "passed"},
        }
        items = [
            mock_test_item("mod1::test_slow"),
            mock_test_item("mod1::test_fast"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_tests_within_module(items, "cost")
        assert [item.name for item in items] == [
            "mod1::test_fast",
            "mod1::test_slow",
        ]
        reorderer.reorder_tests_within_module(items, "name", ascending=False)
        assert [item.name for item in items] == [
            "mod1::test_slow",
            "mod1::test_fast",
        ]
        reorderer.reorder_tests_within_module(items, "name", ascending=True)
        assert [item.name for item in items] == [
            "mod1::test_fast",
            "mod1::test_slow",
        ]

    def test_reorder_tests_within_module_by_failure(
        self, mock_test_item, mocker
    ):
        """Test reordering tests within each module by failure."""
        reorderer = ReordererOfTests()
        reorderer.brightest_data = {
            "data": {
                "test_case_failures": {
                    "mod1::test_pass": 0,
                    "mod1::test_fail": 1,
                }
            }
        }
        items = [
            mock_test_item("mod1::test_pass"),
            mock_test_item("mod1::test_fail"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_tests_within_module(
            items, "failure", ascending=False
        )
        assert [item.name for item in items] == [
            "mod1::test_fail",
            "mod1::test_pass",
        ]
        reorderer.reorder_tests_within_module(items, "failure", ascending=True)
        assert [item.name for item in items] == [
            "mod1::test_pass",
            "mod1::test_fail",
        ]

    def test_get_test_failure_count(self, mock_test_item):
        """Test getting the failure count of a test."""
        reorderer = ReordererOfTests()
        reorderer.brightest_data = {
            "data": {"test_case_failures": {"test_one": 1}}
        }
        item = mock_test_item("test_one")
        assert reorderer.get_test_failure_count(item) == 1
        item = mock_test_item("test_two")
        assert reorderer.get_test_failure_count(item) == 0

    def test_reorder_tests_across_modules_by_failure_history(
        self, mock_test_item
    ):
        """Test reordering tests across modules by historical failure."""
        reorderer = ReordererOfTests()
        reorderer.brightest_data = {
            "data": {
                "test_case_failures": {
                    "mod2::test_slow": 0,
                    "mod1::test_fast": 1,
                    "mod1::test_fail": 0,
                }
            }
        }
        items = [
            mock_test_item("mod2::test_slow"),
            mock_test_item("mod1::test_fast"),
            mock_test_item("mod1::test_fail"),
        ]
        reorderer.reorder_tests_across_modules(
            items, "failure", ascending=False
        )
        assert [item.name for item in items] == [
            "mod1::test_fast",
            "mod2::test_slow",
            "mod1::test_fail",
        ]
        reorderer.reorder_tests_across_modules(
            items, "failure", ascending=True
        )
        assert [item.name for item in items] == [
            "mod2::test_slow",
            "mod1::test_fail",
            "mod1::test_fast",
        ]
