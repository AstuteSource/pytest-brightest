"""Test reordering functionality based on previous test performance."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pytest_jsonreport.plugin import JSONReport


class TestReorderer:
    """Handles test reordering based on previous test performance data."""

    def __init__(self, json_report_path: Optional[str] = None):
        """Initialize the reorderer with optional JSON report path."""
        self.json_report_path = (
            json_report_path or ".pytest_cache/pytest-json-report.json"
        )
        self.test_data: Dict[str, Dict[str, Any]] = {}
        self.load_test_data()

    def load_test_data(self) -> None:
        """Load test performance data from the JSON report file."""
        report_path = Path(self.json_report_path)
        if not report_path.exists():
            return
        try:
            with report_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if "tests" in data:
                    for test in data["tests"]:
                        node_id = test.get("nodeid", "")
                        if node_id:
                            setup_duration = test.get("setup", {}).get(
                                "duration", 0.0
                            )
                            call_duration = test.get("call", {}).get(
                                "duration", 0.0
                            )
                            teardown_duration = test.get("teardown", {}).get(
                                "duration", 0.0
                            )
                            total_duration = (
                                setup_duration
                                + call_duration
                                + teardown_duration
                            )
                            self.test_data[node_id] = {
                                "total_duration": total_duration,
                                "outcome": test.get("outcome", "unknown"),
                                "setup_duration": setup_duration,
                                "call_duration": call_duration,
                                "teardown_duration": teardown_duration,
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
    """Set up pytest-json-report plugin to generate JSON reports automatically."""
    try:

        plugin_manager = config.pluginmanager
        if not plugin_manager.has_plugin("pytest_jsonreport"):
            json_plugin = JSONReport()
            plugin_manager.register(json_plugin, "pytest_jsonreport")
            print("pytest-brightest: Registered pytest-json-report plugin")
        else:
            print(
                "pytest-brightest: pytest-json-report plugin already registered"
            )
        cache_dir = Path(".pytest_cache")
        cache_dir.mkdir(exist_ok=True)
        json_report_file = ".pytest_cache/pytest-json-report.json"
        if not hasattr(config.option, "json_report_file"):
            config.option.json_report_file = json_report_file
        else:
            config.option.json_report_file = json_report_file
        print(f"pytest-brightest: Set JSON report file to {json_report_file}")
        return True
    except ImportError as e:
        print(
            f"pytest-brightest: Warning - pytest-json-report not available: {e}"
        )
        print(
            "pytest-brightest: Install with: pip install pytest-json-report>=1.5.0"
        )
        return False
    except Exception as e:
        print(f"pytest-brightest: Error setting up JSON report plugin: {e}")
        return False
