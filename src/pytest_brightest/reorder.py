"""Test reordering functionality based on previous test performance."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
        print(report_path)
        if not report_path.exists():
            return
        try:
            with report_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if "tests" in data:
                    for test in data["tests"]:
                        node_id = test.get("nodeid", "")
                        if node_id:
                            self.test_data[node_id] = {
                                "duration": test.get("duration", 0.0),
                                "outcome": test.get("outcome", "unknown"),
                                "call_duration": test.get("call", {}).get(
                                    "duration", 0.0
                                ),
                            }
        except (json.JSONDecodeError, KeyError, OSError):
            pass

    def get_test_duration(self, item: Any) -> float:
        """Get the duration of a test item from previous runs."""
        node_id = getattr(item, "nodeid", "")
        test_info = self.test_data.get(node_id, {})
        return test_info.get("call_duration", test_info.get("duration", 0.0))

    def get_test_outcome(self, item: Any) -> str:
        """Get the outcome of a test item from previous runs."""
        node_id = getattr(item, "nodeid", "")
        test_info = self.test_data.get(node_id, {})
        return test_info.get("outcome", "unknown")

    def classify_tests_by_speed(
        self, items: List[Any]
    ) -> Tuple[List[Any], List[Any]]:
        """Classify tests into fast and slow based on median duration."""
        if not items:
            return [], []
        durations = [self.get_test_duration(item) for item in items]
        valid_durations = [d for d in durations if d > 0]
        if not valid_durations:
            return items, []
        median_duration = sorted(valid_durations)[len(valid_durations) // 2]
        fast_tests = []
        slow_tests = []
        for item in items:
            duration = self.get_test_duration(item)
            if duration == 0.0:
                slow_tests.append(item)
            elif duration <= median_duration:
                fast_tests.append(item)
            else:
                slow_tests.append(item)
        return fast_tests, slow_tests

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

    def sort_tests_by_duration(
        self, items: List[Any], ascending: bool = True
    ) -> List[Any]:
        """Sort tests by duration in ascending or descending order."""
        return sorted(items, key=self.get_test_duration, reverse=not ascending)

    def reorder_tests_in_place(
        self, items: List[Any], reorder_by: str, reorder: str
    ) -> None:
        """Reorder tests in place based on the specified criteria."""
        if not items or reorder_by not in ["fast", "slow", "fail", "pass"]:
            return
        if reorder_by in ["fast", "slow"]:
            fast_tests, slow_tests = self.classify_tests_by_speed(items)
            fast_tests = self.sort_tests_by_duration(
                fast_tests, ascending=True
            )
            slow_tests = self.sort_tests_by_duration(
                slow_tests, ascending=False
            )
            if reorder_by == "fast":
                target_tests = fast_tests
                other_tests = slow_tests
            else:
                target_tests = slow_tests
                other_tests = fast_tests
        else:
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
            test_info.get("call_duration", test_info.get("duration", 0.0))
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


def create_reorderer(json_report_path: Optional[str] = None) -> TestReorderer:
    """Factory function to create a TestReorderer instance."""
    return TestReorderer(json_report_path)


def setup_json_report_plugin(config) -> bool:
    """Check if pytest-json-report plugin is available and configure it."""
    try:
        import pytest_jsonreport

        if not config.getoption("--json-report", None):
            config.option.json_report = ".pytest_cache/pytest-json-report.json"
            config.option.json_report_file = (
                ".pytest_cache/pytest-json-report.json"
            )
        return True
    except ImportError:
        return False
