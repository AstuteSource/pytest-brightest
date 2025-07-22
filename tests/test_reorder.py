"""Test the TestReorderer class."""

import json

import pytest

from pytest_brightest.reorder import (
    ReordererOfTests,
    create_reorderer,
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
                "nodeid": "test_pass",
                "call": {"duration": 1.0},
                "outcome": "passed",
            },
            {
                "nodeid": "test_fail",
                "call": {"duration": 2.0},
                "outcome": "failed",
            },
            {
                "nodeid": "test_error",
                "call": {"duration": 1.5},
                "outcome": "error",
            },
            {
                "nodeid": "test_unknown",
                "call": {"duration": 0.5},
                "outcome": "unknown",
            },
        ]
    }
    json_path.write_text(json.dumps(data))
    reorderer = ReordererOfTests(str(json_path))
    items = [
        mock_test_item("test_pass"),
        mock_test_item("test_fail"),
        mock_test_item("test_error"),
        mock_test_item("test_unknown"),
    ]
    passing, failing = reorderer.classify_tests_by_outcome(items)
    assert [item.name for item in passing] == ["test_pass", "test_unknown"]
    assert [item.name for item in failing] == ["test_fail", "test_error"]


class TestReordererOfTests:
    """Test the ReordererOfTests class."""

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

    def test_get_test_failure_to_cost_ratio_zero_failures(
        self, mock_test_item
    ):
        """Test failure-to-cost ratio calculation for tests with no failures."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {"test_one": {"total_duration": 2.0}}
        reorderer.brightest_data = {
            "data": {"test_case_failures": {"test_one": 0}}
        }
        item = mock_test_item("test_one")
        ratio = reorderer.get_test_failure_to_cost_ratio(item)
        # simple ratio: 0 failures / 2.0 cost = 0.0
        assert ratio == pytest.approx(0.0)

    def test_get_test_failure_to_cost_ratio_with_failures(
        self, mock_test_item
    ):
        """Test failure-to-cost ratio calculation for tests with failures."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {"test_one": {"total_duration": 1.0}}
        reorderer.brightest_data = {
            "data": {"test_case_failures": {"test_one": 3}}
        }
        item = mock_test_item("test_one")
        ratio = reorderer.get_test_failure_to_cost_ratio(item)
        # simple ratio: 3 failures / 1.0 cost = 3.0
        assert ratio == pytest.approx(3.0)

    def test_get_test_failure_to_cost_ratio_zero_cost(self, mock_test_item):
        """Test failure-to-cost ratio calculation for tests with zero cost."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {"test_one": {"total_duration": 0.0}}
        reorderer.brightest_data = {
            "data": {"test_case_failures": {"test_one": 2}}
        }
        item = mock_test_item("test_one")
        ratio = reorderer.get_test_failure_to_cost_ratio(item)
        # simple ratio: 2 failures / 0.00001 (min threshold) = 200000.0
        assert ratio == pytest.approx(2 / 0.00001)

    def test_get_test_failure_to_cost_ratio_no_data(self, mock_test_item):
        """Test failure-to-cost ratio calculation for tests with no data."""
        reorderer = ReordererOfTests()
        item = mock_test_item("test_one")
        ratio = reorderer.get_test_failure_to_cost_ratio(item)
        # simple ratio: 0 failures / 0.00001 (min threshold) = 0.0
        assert ratio == pytest.approx(0.0)

    def test_reorder_modules_by_ratio(self, mock_test_item, mocker):
        """Test reordering modules by failure-to-cost ratio."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test1": {"total_duration": 1.0},
            "mod1::test2": {"total_duration": 2.0},
            "mod2::test3": {"total_duration": 0.5},
        }
        reorderer.brightest_data = {
            "data": {
                "test_case_failures": {
                    "mod1::test1": 2,  # ratio: (10+2*10)/1.0 = 30.0
                    "mod1::test2": 0,  # ratio: 10/2.0 = 5.0
                    "mod2::test3": 1,  # ratio: (10+1*10)/0.5 = 40.0
                }
            }
        }
        items = [
            mock_test_item("mod1::test1"),
            mock_test_item("mod1::test2"),
            mock_test_item("mod2::test3"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_modules_by_ratio(items, ascending=True)
        assert [item.name for item in items] == [
            "mod1::test1",
            "mod1::test2",
            "mod2::test3",
        ]

    def test_reorder_tests_across_modules_by_ratio(self, mock_test_item):
        """Test reordering tests across modules by failure-to-cost ratio."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test_fast": {"total_duration": 0.5},
            "mod2::test_slow": {"total_duration": 2.0},
            "mod1::test_medium": {"total_duration": 1.0},
        }
        reorderer.brightest_data = {
            "data": {
                "test_case_failures": {
                    "mod1::test_fast": 1,  # ratio: (1+1)/0.5 = 4.0
                    "mod2::test_slow": 0,  # ratio: 1/2.0 = 0.5
                    "mod1::test_medium": 2,  # ratio: (2+1)/1.0 = 3.0
                }
            }
        }
        items = [
            mock_test_item("mod1::test_fast"),
            mock_test_item("mod2::test_slow"),
            mock_test_item("mod1::test_medium"),
        ]
        reorderer.reorder_tests_across_modules(items, "ratio", ascending=False)
        assert [item.name for item in items] == [
            "mod1::test_fast",
            "mod1::test_medium",
            "mod2::test_slow",
        ]

    def test_reorder_tests_within_module_by_ratio(
        self, mock_test_item, mocker
    ):
        """Test reordering tests within modules by failure-to-cost ratio."""
        reorderer = ReordererOfTests()
        reorderer.test_data = {
            "mod1::test1": {"total_duration": 1.0},
            "mod1::test2": {"total_duration": 0.5},
            "mod2::test3": {"total_duration": 2.0},
        }
        reorderer.brightest_data = {
            "data": {
                "test_case_failures": {
                    "mod1::test1": 0,  # ratio: 10/1.0 = 10.0
                    "mod1::test2": 1,  # ratio: (10+1*10)/0.5 = 40.0
                    "mod2::test3": 2,  # ratio: (10+2*10)/2.0 = 15.0
                }
            }
        }
        items = [
            mock_test_item("mod1::test1"),
            mock_test_item("mod1::test2"),
            mock_test_item("mod2::test3"),
        ]
        mocker.patch("pytest_brightest.reorder.console.print")
        reorderer.reorder_tests_within_module(items, "ratio", ascending=True)
        assert [item.name for item in items] == [
            "mod1::test1",
            "mod1::test2",
            "mod2::test3",
        ]

    def test_get_prior_data_for_reordering_ratio_all_branches(
        self, tmp_path, mock_test_item
    ):
        """Test getting prior data for ratio reordering for all branches."""
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
                    "call": {"duration": 0.5},
                    "outcome": "error",
                },
            ],
            "brightest": {
                "data": {
                    "test_case_failures": {
                        "mod1::t1": 0,
                        "mod1::t2": 2,
                        "mod2::t3": 1,
                    }
                }
            },
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [
            mock_test_item("mod1::t1"),
            mock_test_item("mod1::t2"),
            mock_test_item("mod2::t3"),
        ]
        # RATIO, MODULES_WITHIN_SUITE - now collects ALL ratio data
        d = reorderer.get_prior_data_for_reordering(
            items, "ratio", "modules-within-suite"
        )
        assert "test_module_ratios" in d
        assert "test_case_ratios" in d  # now always included
        expected_modules = 2
        assert len(d["test_module_ratios"]) == expected_modules
        expected_tests = 3
        assert len(d["test_case_ratios"]) == expected_tests
        # RATIO, TESTS_WITHIN_MODULE - collects ALL ratio data
        d = reorderer.get_prior_data_for_reordering(
            items, "ratio", "tests-within-module"
        )
        assert "test_module_ratios" in d
        assert "test_case_ratios" in d
        assert len(d["test_case_ratios"]) == expected_tests
        assert len(d["test_module_ratios"]) == expected_modules
        # RATIO, TESTS_WITHIN_SUITE - collects ALL ratio data
        d = reorderer.get_prior_data_for_reordering(
            items, "ratio", "tests-within-suite"
        )
        assert "test_module_ratios" in d  # now always included
        assert "test_case_ratios" in d
        assert len(d["test_case_ratios"]) == expected_tests
        assert len(d["test_module_ratios"]) == expected_modules

    def test_reorder_tests_in_place_ratio_all_branches(
        self, tmp_path, mock_test_item, mocker
    ):
        """Test reordering tests in place by ratio for all branches."""
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
            ],
            "brightest": {
                "data": {
                    "test_case_failures": {
                        "mod1::t1": 0,
                        "mod1::t2": 3,
                    }
                }
            },
        }
        json_path.write_text(json.dumps(data))
        reorderer = ReordererOfTests(str(json_path))
        items = [mock_test_item("mod1::t1"), mock_test_item("mod1::t2")]
        mocker.patch("pytest_brightest.reorder.console.print")
        # modules-within-suite, ratio
        reorderer.reorder_tests_in_place(
            items, "ratio", "ascending", "modules-within-suite"
        )
        # tests-within-module, ratio
        reorderer.reorder_tests_in_place(
            items, "ratio", "ascending", "tests-within-module"
        )
        # tests-within-suite, ratio
        reorderer.reorder_tests_in_place(
            items, "ratio", "ascending", "tests-within-suite"
        )


def test_tie_breaking_with_equal_ratios(mock_test_item, mocker):
    """Test that tie-breaking works when tests have equal primary metric values."""
    # Create a reorderer
    reorderer = ReordererOfTests()

    # Create mock items with equal ratios but different costs
    items = [
        mock_test_item("test_fast.py::test_function"),
        mock_test_item("test_medium.py::test_function"),
        mock_test_item("test_slow.py::test_function"),
    ]

    # Mock the methods to return equal ratios but different costs
    def mock_get_ratio(item):
        return 0.0  # All have equal ratio (no failures)

    def mock_get_cost(item):
        costs = {
            "test_fast.py::test_function": 0.1,
            "test_medium.py::test_function": 0.5,
            "test_slow.py::test_function": 1.0,
        }
        return costs.get(item.nodeid, 0.0)

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio
    reorderer.get_test_total_duration = mock_get_cost

    # Test tie-breaking with cost (ascending - fast tests first)
    items_copy = items.copy()
    reorderer.reorder_tests_across_modules(items_copy, "ratio", True, ["cost"])

    # Should be ordered by cost: fast(0.1), medium(0.5), slow(1.0)
    expected_order = [
        "test_fast.py::test_function",
        "test_medium.py::test_function",
        "test_slow.py::test_function",
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

    reorderer.get_test_failure_to_cost_ratio = mock_get_ratio
    reorderer.get_test_total_duration = mock_get_cost

    # Test primary sort by ratio (ascending)
    items_copy = items.copy()
    reorderer.reorder_tests_across_modules(items_copy, "ratio", True, ["cost"])

    # Should be ordered by ratio: low(1.0), high(5.0)
    expected_order = [
        "test_low.py::test_function",
        "test_high.py::test_function",
    ]
    actual_order = [item.nodeid for item in items_copy]
    assert actual_order == expected_order
