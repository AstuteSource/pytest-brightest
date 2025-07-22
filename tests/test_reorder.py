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


def test_tie_breaking_with_inverse_cost(mock_test_item):
    """Test that tie-breaking works with inverse-cost (expensive tests first)."""
    reorderer = ReordererOfTests()
    # Create mock items with equal ratios but different costs
    items = [
        mock_test_item("test_cheap.py::test_function"),
        mock_test_item("test_expensive.py::test_function"),
        mock_test_item("test_medium.py::test_function"),
    ]

    # Mock the methods to return equal ratios but different costs
    def mock_get_ratio(item):
        return 0.5  # all have equal ratio

    def mock_get_cost(item):
        costs = {
            "test_cheap.py::test_function": 0.1,
            "test_medium.py::test_function": 0.5,
            "test_expensive.py::test_function": 2.0,
        }
        return costs.get(item.nodeid, 0.0)

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio  # type: ignore[method-assign]
    reorderer.get_test_total_duration = mock_get_cost  # type: ignore[method-assign]
    # test tie-breaking with inverse-cost (expensive tests first when ascending)
    items_copy = items.copy()
    reorderer.reorder_tests_across_modules(
        items_copy, "ratio", True, "inverse-cost"
    )
    # with mathematical inverse: expensive(1/2.0=0.5) first, medium(1/0.5=2.0), cheap(1/0.1=10.0) last
    # when ascending=True, smallest inverse values come first
    expected_order = [
        "test_expensive.py::test_function",
        "test_medium.py::test_function",
        "test_cheap.py::test_function",
    ]
    actual_order = [item.nodeid for item in items_copy]
    assert actual_order == expected_order


def test_tie_breaking_with_inverse_failure(mock_test_item):
    """Test that tie-breaking works with inverse-failure (high failure tests first)."""
    reorderer = ReordererOfTests()
    # Create mock items with equal ratios but different failure counts
    items = [
        mock_test_item("test_stable.py::test_function"),
        mock_test_item("test_flaky.py::test_function"),
        mock_test_item("test_broken.py::test_function"),
    ]

    # Mock the methods to return equal ratios but different failure counts
    def mock_get_ratio(item):
        return 1.0  # all have equal ratio

    def mock_get_failure(item):
        failures = {
            "test_stable.py::test_function": 0,
            "test_flaky.py::test_function": 2,
            "test_broken.py::test_function": 10,
        }
        return failures.get(item.nodeid, 0)

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio  # type: ignore[method-assign]
    reorderer.get_test_failure_count = mock_get_failure  # type: ignore[method-assign]
    # Test tie-breaking with inverse-failure (high failure tests first when ascending)
    items_copy = items.copy()
    reorderer.reorder_tests_across_modules(
        items_copy, "ratio", True, "inverse-failure"
    )
    # With mathematical inverse: broken(1/10=0.1) first, flaky(1/2=0.5), stable(0→∞) last
    # When ascending=True, smallest inverse values come first
    expected_order = [
        "test_broken.py::test_function",
        "test_flaky.py::test_function",
        "test_stable.py::test_function",
    ]
    actual_order = [item.nodeid for item in items_copy]
    assert actual_order == expected_order


def test_tie_breaking_without_ties(mock_test_item, mocker):
    """Test that tie-breaking doesn't interfere when there are no ties."""
    # Create a reorderer
    reorderer = ReordererOfTests()
    # Create mock items with different ratios
    items = [
        mock_test_item("test_low.py::test_function"),
        mock_test_item("test_high.py::test_function"),
    ]

    # Mock the methods to return different ratios
    def mock_get_ratio(item):
        ratios = {
            "test_low.py::test_function": 1.0,  # Lower ratio
            "test_high.py::test_function": 5.0,  # Higher ratio
        }
        return ratios.get(item.nodeid, 0.0)

    def mock_get_cost(item):
        return 0.5  # Equal costs

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio  # type: ignore[method-assign]
    reorderer.get_test_total_duration = mock_get_cost  # type: ignore[method-assign]

    # Test primary sort by ratio (ascending)
    items_copy = items.copy()
    reorderer.reorder_tests_across_modules(items_copy, "ratio", True, "cost")

    # Should be ordered by ratio: low(1.0), high(5.0)
    expected_order = [
        "test_low.py::test_function",
        "test_high.py::test_function",
    ]
    actual_order = [item.nodeid for item in items_copy]
    assert actual_order == expected_order


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

    def test_modules_within_suite_tie_breaking_with_shuffle(
        self, mock_test_item, mocker
    ):
        """Test modules-within-suite focus with shuffle tie-breaker."""
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test1": {"total_duration": 0.0, "outcome": "passed"},
            "mod2::test2": {"total_duration": 0.0, "outcome": "passed"},
            "mod3::test3": {"total_duration": 0.0, "outcome": "passed"},
        }

        items = [
            mock_test_item("mod1::test1"),
            mock_test_item("mod2::test2"),
            mock_test_item("mod3::test3"),
        ]

        # Test with cost technique - all modules have 0.0 cost, should use shuffle tie-breaker
        original_order = [item.name for item in items]
        reorderer.reorder_tests_in_place(
            items, "cost", "descending", "modules-within-suite", "shuffle"
        )

        # The order might be different due to shuffling, but all items should still be present
        final_order = [item.name for item in items]
        assert len(final_order) == len(original_order)
        assert set(final_order) == set(original_order)

    def test_modules_within_suite_tie_breaking_with_name(
        self, mock_test_item, mocker
    ):
        """Test modules-within-suite focus with name tie-breaker."""
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod_c::test1": {"total_duration": 0.0, "outcome": "passed"},
            "mod_a::test2": {"total_duration": 0.0, "outcome": "passed"},
            "mod_b::test3": {"total_duration": 0.0, "outcome": "passed"},
        }

        items = [
            mock_test_item("mod_c::test1"),
            mock_test_item("mod_a::test2"),
            mock_test_item("mod_b::test3"),
        ]

        # Test with ratio technique - all modules have 0.0 ratio, should use name tie-breaker (ascending)
        reorderer.reorder_tests_in_place(
            items, "ratio", "descending", "modules-within-suite", "name"
        )

        # Should be ordered by module name: mod_c, mod_b, mod_a (descending)
        # Since main sort is descending, tie-breaker also follows descending
        assert [item.name for item in items] == [
            "mod_c::test1",
            "mod_b::test3",
            "mod_a::test2",
        ]

    def test_modules_within_suite_tie_breaking_with_cost(
        self, mock_test_item, mocker
    ):
        """Test modules-within-suite focus with cost tie-breaker."""
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test1": {"total_duration": 2.0, "outcome": "passed"},
            "mod1::test2": {"total_duration": 1.0, "outcome": "passed"},
            "mod2::test3": {"total_duration": 1.5, "outcome": "passed"},
            "mod2::test4": {"total_duration": 1.5, "outcome": "passed"},
            "mod3::test5": {"total_duration": 0.5, "outcome": "passed"},
            "mod3::test6": {"total_duration": 2.5, "outcome": "passed"},
        }

        # Module costs: mod1=3.0, mod2=3.0 (tie), mod3=3.0 (tie)
        items = [
            mock_test_item("mod1::test1"),
            mock_test_item("mod1::test2"),
            mock_test_item("mod2::test3"),
            mock_test_item("mod2::test4"),
            mock_test_item("mod3::test5"),
            mock_test_item("mod3::test6"),
        ]

        # Test with failure technique - all modules have same failure count (0)
        # Should use cost tie-breaker
        reorderer.reorder_tests_in_place(
            items, "failure", "descending", "modules-within-suite", "cost"
        )

        # All modules have 0 failures, so tie-breaker by cost should be used
        # Since descending, higher cost modules should come first
        actual_modules = []
        for item in items:
            module = item.name.split("::")[0]
            if module not in actual_modules:
                actual_modules.append(module)

        # Since all modules have same cost (3.0), the order may vary
        # but all modules should be present
        expected_module_count = 3
        assert len(actual_modules) == expected_module_count
        assert set(actual_modules) == {"mod1", "mod2", "mod3"}

    def test_tests_within_module_tie_breaking_with_shuffle(
        self, mock_test_item, mocker
    ):
        """Test tests-within-module focus with shuffle tie-breaker."""
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test1": {"total_duration": 1.0, "outcome": "passed"},
            "mod1::test2": {
                "total_duration": 1.0,
                "outcome": "passed",
            },  # Same cost
            "mod1::test3": {
                "total_duration": 1.0,
                "outcome": "passed",
            },  # Same cost
        }

        items = [
            mock_test_item("mod1::test1"),
            mock_test_item("mod1::test2"),
            mock_test_item("mod1::test3"),
        ]

        # Test with cost technique - all tests have same cost, should use shuffle tie-breaker
        original_order = [item.name for item in items]
        reorderer.reorder_tests_in_place(
            items, "cost", "ascending", "tests-within-module", "shuffle"
        )

        # Order might be different due to shuffling, but all items should be present
        final_order = [item.name for item in items]
        assert len(final_order) == len(original_order)
        assert set(final_order) == set(original_order)

    def test_tests_within_module_tie_breaking_with_name(
        self, mock_test_item, mocker
    ):
        """Test tests-within-module focus with name tie-breaker."""
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test_c": {"total_duration": 1.0, "outcome": "passed"},
            "mod1::test_a": {"total_duration": 1.0, "outcome": "passed"},
            "mod1::test_b": {"total_duration": 1.0, "outcome": "passed"},
        }

        items = [
            mock_test_item("mod1::test_c"),
            mock_test_item("mod1::test_a"),
            mock_test_item("mod1::test_b"),
        ]

        # Test with ratio technique - all tests have same ratio (0), should use name tie-breaker
        reorderer.reorder_tests_in_place(
            items, "ratio", "ascending", "tests-within-module", "name"
        )

        # Should be ordered by test name: test_a, test_b, test_c
        assert [item.name for item in items] == [
            "mod1::test_a",
            "mod1::test_b",
            "mod1::test_c",
        ]

    def test_tests_within_module_tie_breaking_with_failure(
        self, mock_test_item, mocker
    ):
        """Test tests-within-module focus with failure tie-breaker."""
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test1": {"total_duration": 1.0, "outcome": "passed"},
            "mod1::test2": {"total_duration": 1.0, "outcome": "passed"},
            "mod1::test3": {
                "total_duration": 1.0,
                "outcome": "failed",
            },  # Different failure
        }
        reorderer.brightest_data = {
            "data": {
                "test_case_failures": {
                    "mod1::test1": 0,
                    "mod1::test2": 0,  # Same failure count as test1
                    "mod1::test3": 1,  # Different failure count
                }
            }
        }

        items = [
            mock_test_item("mod1::test1"),
            mock_test_item("mod1::test2"),
            mock_test_item("mod1::test3"),
        ]

        # Test with cost technique - test1 and test2 have same cost, should use failure tie-breaker
        reorderer.reorder_tests_in_place(
            items, "cost", "descending", "tests-within-module", "failure"
        )

        # All have same cost, so tie-breaker by failure (descending) should put test3 first
        # then test1 and test2 (both have 0 failures, order may vary)
        final_order = [item.name for item in items]
        assert (
            final_order[0] == "mod1::test3"
        )  # Highest failure count should be first
        assert "mod1::test1" in final_order
        assert "mod1::test2" in final_order

    def test_get_test_failure_to_cost_ratio(self, mock_test_item):
        """Test getting the failure to cost ratio of a test."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "test_one": {"total_duration": 2.0, "outcome": "passed"}
        }
        reorderer.brightest_data = {
            "data": {"test_case_failures": {"test_one": 4}}
        }
        item = mock_test_item("test_one")
        # Ratio should be failures / cost = 4 / 2.0 = 2.0
        assert reorderer.get_test_failure_to_cost_ratio(item) == pytest.approx(
            2.0
        )
        item = mock_test_item("test_unknown")
        # Unknown test should return 0.0
        assert reorderer.get_test_failure_to_cost_ratio(item) == 0.0

    def test_get_test_failure_to_cost_ratio_zero_cost(self, mock_test_item):
        """Test getting the failure to cost ratio when cost is zero."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "test_zero_cost": {"total_duration": 0.0, "outcome": "passed"}
        }
        reorderer.brightest_data = {
            "data": {"test_case_failures": {"test_zero_cost": 5}}
        }
        item = mock_test_item("test_zero_cost")
        # When cost is 0, uses MIN_COST_THRESHOLD = 0.00001, so ratio = 5/0.00001 = 500000
        ratio = reorderer.get_test_failure_to_cost_ratio(item)
        assert ratio == pytest.approx(500000.0)

    def test_get_module_failure_to_cost_ratio(self):
        """Test getting the failure to cost ratio of a module."""
        reorderer = ReordererOfTests()
        reorderer.brightest_data = {
            "data": {"test_module_ratios": {"test_module.py": 1.0}}
        }
        # Should return the saved ratio directly
        ratio = reorderer.get_module_failure_to_cost_ratio("test_module.py")
        assert ratio == 1.0

    def test_get_module_failure_to_cost_ratio_zero_cost(self):
        """Test getting module ratio when no saved data exists."""
        reorderer = ReordererOfTests()
        reorderer.brightest_data = {"data": {}}  # No saved ratios
        ratio = reorderer.get_module_failure_to_cost_ratio("test_module.py")
        assert ratio == 0.0

    def test_load_test_data_success(self, tmp_path):
        """Test successful loading of test data."""
        json_path = tmp_path / "report.json"
        data = {
            "tests": [
                {
                    "nodeid": "test_example",
                    "setup": {"duration": 0.1},
                    "call": {"duration": 0.5},
                    "teardown": {"duration": 0.2},
                    "outcome": "passed",
                }
            ]
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        # Data should be loaded automatically in __init__
        assert reorderer.has_test_data()
        assert "test_example" in reorderer.test_data
        assert reorderer.test_data["test_example"][
            "total_duration"
        ] == pytest.approx(0.8)

    def test_reorder_modules_by_ratio(self, mock_test_item, mocker):
        """Test reordering modules by their failure-to-cost ratio."""
        reorderer = ReordererOfTests()
        reorderer.brightest_data = {
            "data": {
                "test_module_ratios": {
                    "mod1": 1.0,  # Higher ratio
                    "mod2": 0.5,  # Lower ratio
                }
            }
        }
        items = [
            mock_test_item("mod1::test1"),
            mock_test_item("mod2::test1"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        # Test ascending order (lower ratios first)
        reorderer.reorder_modules_by_ratio(items, ascending=True)
        assert [item.name for item in items] == [
            "mod2::test1",  # ratio 0.5
            "mod1::test1",  # ratio 1.0
        ]
        # Test descending order (higher ratios first)
        reorderer.reorder_modules_by_ratio(items, ascending=False)
        assert [item.name for item in items] == [
            "mod1::test1",  # ratio 1.0
            "mod2::test1",  # ratio 0.5
        ]


def test_tie_breaking_with_name_tie_breaker(mock_test_item):
    """Test tie-breaking using name as the tie-breaker."""
    reorderer = ReordererOfTests()
    items = [
        mock_test_item("test_zebra.py::test_function"),
        mock_test_item("test_alpha.py::test_function"),
        mock_test_item("test_beta.py::test_function"),
    ]

    # Mock methods to return equal primary values
    def mock_get_ratio(item):
        return 1.0  # All equal

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio  # type: ignore[method-assign]

    # Test tie-breaking with name
    items_copy = items.copy()
    reorderer.reorder_tests_across_modules(items_copy, "ratio", True, "name")

    # Should be sorted by name alphabetically
    expected_order = [
        "test_alpha.py::test_function",
        "test_beta.py::test_function",
        "test_zebra.py::test_function",
    ]
    actual_order = [item.nodeid for item in items_copy]
    assert actual_order == expected_order


def test_tie_breaking_with_shuffle(mock_test_item, mocker):
    """Test tie-breaking using shuffle as the tie-breaker."""
    reorderer = ReordererOfTests()
    items = [
        mock_test_item("test_a.py::test_function"),
        mock_test_item("test_b.py::test_function"),
        mock_test_item("test_c.py::test_function"),
    ]

    # Mock methods to return equal primary values
    def mock_get_ratio(item):
        return 1.0  # All equal

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio  # type: ignore[method-assign]

    # Mock random.shuffle to control the order
    mock_shuffle = mocker.patch("pytest_brightest.reorder.random.shuffle")

    items_copy = items.copy()
    reorderer.reorder_tests_across_modules(
        items_copy, "ratio", True, "shuffle"
    )

    # Verify shuffle was called
    mock_shuffle.assert_called_once()


def test_tie_breaking_no_ties(mock_test_item):
    """Test that tie-breaking is not needed when there are no ties."""
    reorderer = ReordererOfTests()
    items = [
        mock_test_item("test_low.py::test_function"),
        mock_test_item("test_high.py::test_function"),
    ]

    # Mock methods to return different primary values (no ties)
    def mock_get_ratio(item):
        ratios = {
            "test_low.py::test_function": 1.0,
            "test_high.py::test_function": 2.0,
        }
        return ratios.get(item.nodeid, 0.0)

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio  # type: ignore[method-assign]

    items_copy = items.copy()
    reorderer.reorder_tests_across_modules(items_copy, "ratio", True, "name")

    # Should be ordered by primary key (ratio) since no ties
    expected_order = [
        "test_low.py::test_function",  # ratio 1.0
        "test_high.py::test_function",  # ratio 2.0
    ]
    actual_order = [item.nodeid for item in items_copy]
    assert actual_order == expected_order


def test_reorder_tests_across_modules_with_ratio(mock_test_item):
    """Test reordering tests across modules by ratio with tie-breaking."""
    reorderer = ReordererOfTests()

    # Mock the ratio calculation method
    def mock_get_ratio(item):
        ratios = {
            "test_a.py::test_function": 3.0,  # highest
            "test_b.py::test_function": 1.0,  # lowest
            "test_c.py::test_function": 2.0,  # middle
        }
        return ratios.get(item.nodeid, 0.0)

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio  # type: ignore[method-assign]

    items = [
        mock_test_item("test_a.py::test_function"),
        mock_test_item("test_b.py::test_function"),
        mock_test_item("test_c.py::test_function"),
    ]

    # Test ascending order (lowest ratio first)
    reorderer.reorder_tests_across_modules(items, "ratio", ascending=True)
    expected_order = [
        "test_b.py::test_function",  # ratio 1.0
        "test_c.py::test_function",  # ratio 2.0
        "test_a.py::test_function",  # ratio 3.0
    ]
    actual_order = [item.nodeid for item in items]
    assert actual_order == expected_order
