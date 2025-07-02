"""Test reordering functionality based on previous test performance."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

from .constants import (
    CALL,
    CALL_DURATION,
    DEFAULT_FILE_ENCODING,
    DEFAULT_PYTEST_JSON_REPORT_PATH,
    DURATION,
    NODEID,
    OUTCOME,
    PYTEST_CACHE_DIR,
    PYTEST_JSON_REPORT_PLUGIN_NAME,
    SETUP,
    SETUP_DURATION,
    TEARDOWN,
    TEARDOWN_DURATION,
    TESTS,
    TOTAL_DURATION,
    UNKNOWN,
)

# create a default console
console = Console()


class TestReorderer:
    """Handle test reordering based on previous test performance data."""

    def __init__(self, json_report_path: Optional[str] = None):
        """Initialize the reorderer with optional JSON report path."""
        # the pytest-json-report is a JSON file that contains
        # all of the details about the prior run of a pytest test suite
        self.json_report_path = (
            json_report_path or DEFAULT_PYTEST_JSON_REPORT_PATH
        )
        # the test_data dictionary stores details about the test cases
        # that enables them to be reordered; for instance, it stores
        # information about the cumulative execution time of a test
        self.test_data: Dict[str, Dict[str, Any]] = {}
        # extract the data from the pytest-json-report that was found
        # and store it in the dictionary called test_data
        self.load_test_data()

    def load_test_data(self) -> None:
        """Load test execution data from the pytest-json-report report file."""
        # create a pathlib Path object for the JSON report file
        report_path = Path(self.json_report_path)
        # if the report does not exist in the default location then
        # the data from it cannot be extracted and thus the loading
        # function can return early without doing anything
        if not report_path.exists():
            return
        # attempt to read the JSON file and parse it to extract the data
        try:
            with report_path.open("r", encoding=DEFAULT_FILE_ENCODING) as file:
                # load the JSON data from the file
                data = json.load(file)
                if "tests" in data:
                    for test in data[TESTS]:
                        node_id = test.get(NODEID, "")
                        if node_id:
                            setup_duration = test.get(SETUP, {}).get(
                                DURATION, 0.0
                            )
                            call_duration = test.get(CALL, {}).get(
                                DURATION, 0.0
                            )
                            teardown_duration = test.get(TEARDOWN, {}).get(
                                DURATION, 0.0
                            )
                            # calculate the total duration (i.e., the cumulative
                            # execution time for the test case) that will include
                            # the reported costs for these three test stages:
                            # --> setup, call, and teardown
                            total_duration = (
                                setup_duration
                                + call_duration
                                + teardown_duration
                            )
                            # store the test data in the dictionary
                            self.test_data[node_id] = {
                                TOTAL_DURATION: total_duration,
                                OUTCOME: test.get(OUTCOME, UNKNOWN),
                                SETUP_DURATION: setup_duration,
                                CALL_DURATION: call_duration,
                                TEARDOWN_DURATION: teardown_duration,
                            }
        except (json.JSONDecodeError, KeyError, OSError):
            pass

    def get_test_total_duration(self, item: Any) -> float:
        """Get the total duration of a test item from previous runs."""
        node_id = getattr(item, "nodeid", "")
        test_info = self.test_data.get(node_id, {})
        return test_info.get("total_duration", 0.0)

    def get_test_outcome(self, item: Any) -> str:
        """Get the outcome of a test item from previous runs."""
        node_id = getattr(item, "nodeid", "")
        test_info = self.test_data.get(node_id, {})
        return test_info.get("outcome", "unknown")

    def classify_tests_by_outcome(
        self, items: List[Any]
    ) -> Tuple[List[Any], List[Any]]:
        """Classify tests into passing and failing based on previous outcomes."""
        passing_tests = []
        failing_tests = []
        for item in items:
            outcome = self.get_test_outcome(item)
            if outcome in ["failed", "error"]:
                failing_tests.append(item)
            else:
                passing_tests.append(item)
        return passing_tests, failing_tests

    def sort_tests_by_total_duration(
        self, items: List[Any], ascending: bool = True
    ) -> List[Any]:
        """Sort tests by total duration in ascending or descending order."""
        return sorted(
            items, key=self.get_test_total_duration, reverse=not ascending
        )

    def reorder_tests_in_place(
        self, items: List[Any], reorder_by: str, reorder: str
    ) -> None:
        """Reorder tests in place based on the specified criteria."""
        if not items or reorder_by not in ["fast", "slow", "fail", "pass"]:
            return
        if reorder_by == "fast":
            # Sort by total duration, fastest first
            fast_tests = self.sort_tests_by_total_duration(
                items, ascending=True
            )
            items.clear()
            if reorder == "first":
                items.extend(fast_tests)
            else:
                items.extend(fast_tests)
        elif reorder_by == "slow":
            # Sort by total duration, slowest first
            slow_tests = self.sort_tests_by_total_duration(
                items, ascending=False
            )
            items.clear()
            if reorder == "first":
                items.extend(slow_tests)
            else:
                items.extend(slow_tests)
        elif reorder_by in ["fail", "pass"]:
            passing_tests, failing_tests = self.classify_tests_by_outcome(
                items
            )
            if reorder_by == "fail":
                target_tests = failing_tests
                other_tests = passing_tests
            else:
                target_tests = passing_tests
                other_tests = failing_tests
            items.clear()
            if reorder == "first":
                items.extend(target_tests)
                items.extend(other_tests)
            else:
                items.extend(other_tests)
                items.extend(target_tests)

    def has_test_data(self) -> bool:
        """Check if test performance data is available."""
        return bool(self.test_data)

    def get_test_count_by_outcome(self) -> Dict[str, int]:
        """Get count of tests by outcome from previous runs."""
        outcome_counts: Dict[str, int] = {}
        for test_info in self.test_data.values():
            outcome = test_info.get("outcome", "unknown")
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        return outcome_counts

    def get_duration_statistics(self) -> Dict[str, float]:
        """Get duration statistics from previous test runs."""
        durations = [
            test_info.get("total_duration", 0.0)
            for test_info in self.test_data.values()
        ]
        valid_durations = [d for d in durations if d > 0]
        if not valid_durations:
            return {"min": 0.0, "max": 0.0, "median": 0.0, "mean": 0.0}
        valid_durations.sort()
        return {
            "min": valid_durations[0],
            "max": valid_durations[-1],
            "median": valid_durations[len(valid_durations) // 2],
            "mean": sum(valid_durations) / len(valid_durations),
        }

    def get_test_details(self, item: Any) -> Dict[str, Any]:
        """Get detailed test information including all duration components."""
        node_id = getattr(item, "nodeid", "")
        test_info = self.test_data.get(node_id, {})
        return {
            "node_id": node_id,
            "total_duration": test_info.get("total_duration", 0.0),
            "setup_duration": test_info.get("setup_duration", 0.0),
            "call_duration": test_info.get("call_duration", 0.0),
            "teardown_duration": test_info.get("teardown_duration", 0.0),
            "outcome": test_info.get("outcome", "unknown"),
        }


def create_reorderer(json_report_path: Optional[str] = None) -> TestReorderer:
    """Create a TestReorderer instance."""
    return TestReorderer(json_report_path)


def setup_json_report_plugin(config) -> bool:
    """Configure pytest-json-report plugin to generate JSON reports automatically."""
    # attempt to configure the pytest-json-report plugin if needed
    try:
        # determine whether or not the pytest-json-report plugin is available
        # and display a suitable diagnostic message before running test suite
        plugin_manager = config.pluginmanager
        if plugin_manager.has_plugin(PYTEST_JSON_REPORT_PLUGIN_NAME):
            console.print(
                ":flashlight: pytest-brightest: pytest-json-report plugin available"
            )
        else:
            console.print(
                ":flashlight: pytest-brightest: pytest-json-report plugin not available"
            )
        # configure the directory where the pytest-json-report plugin will
        # store its JSON report file used by pytest-brightest for certain
        # tasks like test reordering according to cumulative execution time
        cache_dir = Path(PYTEST_CACHE_DIR)
        cache_dir.mkdir(exist_ok=True)
        json_report_file = DEFAULT_PYTEST_JSON_REPORT_PATH
        # if a JSON report location was already specified by the user through
        # a command-line argument for the pytest-json-report plugin, alert them
        # to the fact that we are storing it internally to manage history better
        if (
            hasattr(config.option, "json_report_file")
            and config.option.json_report_file == ".report.json"
        ):
            console.print(
                f":flashlight: pytest-brightest: Not using pytest-json-report in {config.option.json_report_file}"
            )
        # set the JSON report file location for pytest-json-report plugin
        # to be the default location that is used by the pytest-brightest plugin
        config.option.json_report_file = json_report_file
        console.print(
            f":flashlight: pytest-brightest: Using pytest-json-report with name like {json_report_file}"
        )
        return True
    # was not able to import pytest_jsonreport's plugin which means that it cannot
    # be extract to support certain types of prioritization enabled by pytest-brightest
    except ImportError as e:
        console.print(
            f":high_brightness: pytest-brightest: pytest-json-report not available: {e}"
        )
        return False
    # some other problem occurred and the pytest-brightest plugin cannot use
    # the pytest-json-report plugin
    except Exception as e:
        console.print(
            f":high_brightness: pytest-brightest: pytest-json report not setup: {e}"
        )
        return False
