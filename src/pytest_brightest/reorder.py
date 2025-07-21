"""Test reordering functionality based on previous test behavior."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from rich.console import Console

from .constants import (
    ASCENDING,
    BRIGHTEST,
    CALL,
    CALL_DURATION,
    COST,
    DEFAULT_FILE_ENCODING,
    DEFAULT_PYTEST_JSON_REPORT_PATH,
    DURATION,
    EMPTY_STRING,
    ERROR,
    FAILED,
    FAILURE,
    FLASHLIGHT_PREFIX,
    HIGH_BRIGHTNESS_PREFIX,
    INDENT,
    JSON_REPORT_FILE,
    MODULE_FAILURE_COUNTS,
    MODULE_ORDER,
    MODULE_TESTS,
    MODULES_WITHIN_SUITE,
    NAME,
    NODEID,
    NODEID_SEPARATOR,
    OUTCOME,
    PYTEST_CACHE_DIR,
    PYTEST_JSON_REPORT_PLUGIN_NAME,
    REPORT_JSON,
    SETUP,
    SETUP_DURATION,
    TEARDOWN,
    TEARDOWN_DURATION,
    TEST_CASE_COSTS,
    TEST_MODULE_COSTS,
    TEST_ORDER,
    TESTS,
    TESTS_WITHIN_MODULE,
    TESTS_WITHIN_SUITE,
    TOTAL_DURATION,
    UNKNOWN,
    ZERO_COST,
)

if TYPE_CHECKING:
    from _pytest.nodes import Item  # type: ignore


# create a default console
console = Console()


class ReordererOfTests:
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
        self.last_module_failure_counts: Optional[Dict[str, int]] = None
        self.brightest_data: Optional[Dict[str, Any]] = None
        # extract the data from the pytest-json-report that was found
        # and store it in the dictionary called test_data
        self.load_test_data()

    def load_test_data(self) -> None:
        """Load test execution data from the pytest-json-report report file."""
        # create a pathlib Path object for the JSON report file; remember
        # that pytest-brightest does not have its own mechanism for collecting
        # data about test execution as it instead relies on the pytest-json-report
        # plugin to generate a JSON report file that contains the test data
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
                # store the brightest data if it exists for historical information
                brightest_raw = data.get(BRIGHTEST, {})
                if isinstance(brightest_raw, list):
                    # new format: list of runs
                    self.brightest_data = (
                        brightest_raw[-1] if brightest_raw else {}
                    )
                else:
                    # legacy format: single object
                    self.brightest_data = brightest_raw
                # there is data about test cases
                # that were executed in the list of test information
                if TESTS in data:
                    # iterate through each test in the JSON data that
                    # is its own dictionary in a list of the test dictionaries
                    for test in data[TESTS]:
                        # extract the node ID for the test case
                        node_id = test.get(NODEID, EMPTY_STRING)
                        # if the node ID is not empty then it is okay to extract
                        # the setup, call, and teardown durations for the test case
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
        # something went wrong while reading the JSON file
        except (json.JSONDecodeError, KeyError, OSError):
            # if there is an error reading the JSON file, then do not
            # attempt to load any data from it and instead just return
            pass

    def get_test_total_duration(self, item: "Item") -> float:
        """Get the total duration of a test item from previous run(s)."""
        # a pytest item has a nodeid attribute that uniquely identifies it
        node_id = getattr(item, NODEID, EMPTY_STRING)
        # retrieve the test information from the test_data dictionary
        test_info = self.test_data.get(node_id, {})
        # return the total duration of the test, or zero if it is not available
        return test_info.get(TOTAL_DURATION, ZERO_COST)

    def get_test_outcome(self, item: "Item") -> str:
        """Get the outcome of a test item from previous run(s)."""
        # a pytest item has a nodeid attribute that uniquely identifies it
        node_id = getattr(item, NODEID, EMPTY_STRING)
        # retrieve the test information from the test_data dictionary
        test_info = self.test_data.get(node_id, {})
        # return the outcome of the test, or unknown if it is not available
        return test_info.get(OUTCOME, UNKNOWN)

    def get_test_failure_count(self, item: "Item") -> int:
        """Get the failure count of a test item from previous run(s)."""
        node_id = getattr(item, NODEID, EMPTY_STRING)
        if self.brightest_data and "data" in self.brightest_data:
            test_case_failures = self.brightest_data["data"].get(
                "test_case_failures", {}
            )
            return test_case_failures.get(node_id, 0)
        return 0

    def classify_tests_by_outcome(
        self, items: List["Item"]
    ) -> Tuple[List["Item"], List["Item"]]:
        """Classify tests into passing and failing based on previous outcomes."""
        passing_tests = []
        failing_tests = []
        # iterate over each item and classify it as passing or failing
        for item in items:
            outcome = self.get_test_outcome(item)
            # the outcome is a string that can be "passed", "failed", or "error"
            if outcome in [FAILED, ERROR]:
                failing_tests.append(item)
            else:
                passing_tests.append(item)
        return passing_tests, failing_tests

    def sort_tests_by_total_duration(
        self, items: List["Item"], ascending: bool = True
    ) -> List["Item"]:
        """Sort tests by total duration in ascending or descending order."""
        # use the sorted function to sort the items by their total duration
        return sorted(
            items, key=self.get_test_total_duration, reverse=not ascending
        )

    def get_prior_data_for_reordering(  # noqa: PLR0912, PLR0915
        self, items: List["Item"], technique: str, focus: str
    ) -> Dict[str, Any]:
        """Get the prior data that was used for reordering during this session."""
        prior_data: Dict[str, Any] = {}
        if technique == COST:
            module_costs: Dict[str, float] = {}
            test_costs: Dict[str, float] = {}
            for item in items:
                nodeid = getattr(item, NODEID, EMPTY_STRING)
                if nodeid:
                    cost = self.get_test_total_duration(item)
                    module_path = nodeid.split(NODEID_SEPARATOR)[0]
                    module_costs[module_path] = (
                        module_costs.get(module_path, 0.0) + cost
                    )
                    test_costs[nodeid] = cost
            if focus == MODULES_WITHIN_SUITE:
                prior_data[TEST_MODULE_COSTS] = module_costs
            elif focus == TESTS_WITHIN_MODULE:
                prior_data[TEST_MODULE_COSTS] = module_costs
                prior_data[TEST_CASE_COSTS] = test_costs
            elif focus == TESTS_WITHIN_SUITE:
                prior_data[TEST_CASE_COSTS] = test_costs
        elif technique == NAME:
            if focus == MODULES_WITHIN_SUITE:
                module_order = []
                for item in items:
                    nodeid = getattr(item, NODEID, "")
                    if nodeid:
                        module_path = nodeid.split("::")[0]
                        if module_path not in module_order:
                            module_order.append(module_path)
                prior_data[MODULE_ORDER] = module_order
            elif focus == TESTS_WITHIN_SUITE:
                prior_data[TEST_ORDER] = [
                    getattr(item, NODEID, "") for item in items
                ]
            elif focus == TESTS_WITHIN_MODULE:
                module_tests: Dict[str, List[str]] = {}
                for item in items:
                    nodeid = getattr(item, NODEID, NODEID_SEPARATOR)
                    if nodeid:
                        module_path = nodeid.split(NODEID_SEPARATOR)[0]
                        if module_path not in module_tests:
                            module_tests[module_path] = []
                        module_tests[module_path].append(nodeid)
                prior_data[MODULE_TESTS] = module_tests
        elif technique == FAILURE:
            module_failure_counts: Dict[str, int] = {}
            test_case_failures: Dict[str, int] = {}
            for item in items:
                nodeid = getattr(item, NODEID, EMPTY_STRING)
                if nodeid:
                    module_path = nodeid.split(NODEID_SEPARATOR)[0]
                    if module_path not in module_failure_counts:
                        module_failure_counts[module_path] = 0
                    failure_count = self.get_test_failure_count(item)
                    if failure_count > 0:
                        module_failure_counts[module_path] += 1
                    test_case_failures[nodeid] = failure_count
            if focus == MODULES_WITHIN_SUITE:
                prior_data[MODULE_FAILURE_COUNTS] = module_failure_counts
            elif focus == TESTS_WITHIN_MODULE:
                prior_data[MODULE_FAILURE_COUNTS] = module_failure_counts
                prior_data["test_case_failures"] = test_case_failures
            elif focus == TESTS_WITHIN_SUITE:
                prior_data["test_case_failures"] = test_case_failures
        return prior_data

    def reorder_modules_by_cost(
        self, items: List["Item"], ascending: bool = True
    ) -> None:
        """Reorder test modules by their cumulative cost."""
        module_costs: Dict[str, float] = {}
        module_items: Dict[str, List["Item"]] = {}
        # iterate over each item and calculate the cumulative cost of each module
        for item in items:
            nodeid = getattr(item, NODEID, EMPTY_STRING)
            if nodeid:
                # the module path is the part of the nodeid before the "::"
                module_path = nodeid.split(NODEID_SEPARATOR)[0]
                cost = self.get_test_total_duration(item)
                module_costs[module_path] = (
                    module_costs.get(module_path, ZERO_COST) + cost
                )
                if module_path not in module_items:
                    module_items[module_path] = []
                module_items[module_path].append(item)
        # sort the modules by their cumulative cost
        sorted_modules = sorted(
            module_costs.keys(),
            key=lambda m: module_costs[m],
            reverse=not ascending,
        )
        reordered_items = []
        # if there are sorted modules, then add an extra newline
        # to separate the diagnostic output from what appeared before
        if sorted_modules:
            console.print()
        # iterate over the sorted modules and add their items to the reordered list
        for module in sorted_modules:
            # print out the cost of the module using no more than 5 fixed
            # decimal places for the execution time of the test case
            console.print(
                f"{FLASHLIGHT_PREFIX} Module {module} contains tests with overall cost {module_costs[module]:.5f}"
            )
            reordered_items.extend(module_items[module])
        # replace the original list of items with the reordered list
        items[:] = reordered_items

    def reorder_modules_by_name(
        self, items: List["Item"], ascending: bool = True
    ) -> None:
        """Reorder test modules by their name."""
        module_items: Dict[str, List["Item"]] = {}
        # iterate over each item and group them by module
        for item in items:
            nodeid = getattr(item, NODEID, EMPTY_STRING)
            if nodeid:
                module_path = nodeid.split(NODEID_SEPARATOR)[0]
                if module_path not in module_items:
                    module_items[module_path] = []
                module_items[module_path].append(item)
        # sort the modules by their name
        sorted_modules = sorted(module_items.keys(), reverse=not ascending)
        reordered_items = []
        # if there are sorted modules, then add an extra newline
        # to separate the diagnostic output from what appeared before
        if sorted_modules:
            console.print()
        # iterate over the sorted modules and add their items to the reordered list
        for module in sorted_modules:
            console.print(
                f"{FLASHLIGHT_PREFIX} Module {module} is in the reordered suite"
            )
            reordered_items.extend(module_items[module])
        # replace the original list of items with the reordered list
        items[:] = reordered_items

    def reorder_modules_by_failure(
        self, items: List["Item"], ascending: bool = True
    ) -> None:
        """Reorder test modules by their number of failing tests from previous runs."""
        module_failure_counts: Dict[str, int] = {}
        module_items: Dict[str, List["Item"]] = {}
        # iterate over each item and group them by module
        for item in items:
            nodeid = getattr(item, NODEID, EMPTY_STRING)
            if nodeid:
                module_path = nodeid.split(NODEID_SEPARATOR)[0]
                if module_path not in module_failure_counts:
                    module_failure_counts[module_path] = 0
                    module_items[module_path] = []
                # get the test outcome from previous run data
                if self.get_test_outcome(item) in [FAILED, ERROR]:
                    module_failure_counts[module_path] += 1
                module_items[module_path].append(item)
        # store the failure counts for potential use in reporting
        self.last_module_failure_counts = module_failure_counts
        # sort the modules by their failure count
        sorted_modules = sorted(
            module_failure_counts.keys(),
            key=lambda m: module_failure_counts[m],
            reverse=not ascending,
        )
        reordered_items = []
        # if there are sorted modules, then add an extra newline
        # to separate the diagnostic output from what appeared before
        if sorted_modules:
            console.print()
        # iterate over the sorted modules and add their items to the reordered list
        for module in sorted_modules:
            console.print(
                f"{FLASHLIGHT_PREFIX} Module {module} contains {module_failure_counts[module]} failing tests from previous run"
            )
            reordered_items.extend(module_items[module])
        # replace the original list of items with the reordered list
        items[:] = reordered_items

    def reorder_tests_within_module(
        self, items: List["Item"], reorder_by: str, ascending: bool = True
    ) -> None:
        """Reorder tests within each module by the specified technique."""
        module_items: Dict[str, List["Item"]] = {}
        module_order: List[str] = []
        for item in items:
            nodeid = getattr(item, NODEID, EMPTY_STRING)
            if nodeid:
                module_path = nodeid.split(NODEID_SEPARATOR)[0]
                if module_path not in module_items:
                    module_items[module_path] = []
                    module_order.append(module_path)
                module_items[module_path].append(item)
        reordered_items = []
        if module_order:
            console.print()
        for module in module_order:
            console.print(
                f"{FLASHLIGHT_PREFIX} Reordering tests in module {module}"
            )
            if reorder_by == COST:
                self._reorder_module_by_cost(module_items[module], ascending)
            elif reorder_by == NAME:
                self._reorder_module_by_name(module_items[module], ascending)
            elif reorder_by == FAILURE:
                self._reorder_module_by_failure(
                    module_items[module], ascending
                )
            reordered_items.extend(module_items[module])
        items[:] = reordered_items

    def _reorder_module_by_cost(
        self, module_items: List["Item"], ascending: bool
    ) -> None:
        """Reorder a module's tests by cost."""
        module_items.sort(
            key=self.get_test_total_duration, reverse=not ascending
        )
        if module_items:
            cheapest_test = module_items[0]
            console.print(
                f"{INDENT} First test is {getattr(cheapest_test, NODEID, EMPTY_STRING)}"
            )
            most_expensive_test = module_items[-1]
            console.print(
                f"{INDENT} Last test is {getattr(most_expensive_test, NODEID, EMPTY_STRING)}"
            )

    def _reorder_module_by_name(
        self, module_items: List["Item"], ascending: bool
    ) -> None:
        """Reorder a module's tests by name."""
        module_items.sort(
            key=lambda item: getattr(item, NODEID, EMPTY_STRING),
            reverse=not ascending,
        )
        if module_items:
            first_test = module_items[0]
            console.print(
                f"{INDENT} First by-name test is {getattr(first_test, NODEID, EMPTY_STRING)}"
            )
            last_test = module_items[-1]
            console.print(
                f"{INDENT} Last by-name test is {getattr(last_test, NODEID, EMPTY_STRING)}"
            )

    def _reorder_module_by_failure(
        self, module_items: List["Item"], ascending: bool
    ) -> None:
        """Reorder a module's tests by failure."""
        module_items.sort(
            key=self.get_test_failure_count, reverse=not ascending
        )
        if module_items:
            first_test = module_items[0]
            console.print(
                f"{INDENT} First by-failure test is {getattr(first_test, NODEID, EMPTY_STRING)}"
            )
            last_test = module_items[-1]
            console.print(
                f"{INDENT} Last by-failure test is {getattr(last_test, NODEID, EMPTY_STRING)}"
            )

    def reorder_tests_in_place(
        self, items: List["Item"], reorder_by: str, reorder: str, focus: str
    ) -> None:
        """Reorder tests in place based on the specified criteria."""
        # it is not possible to reorder an empty list of items
        if not items:
            return
        # the reorder direction is either ascending or descending
        ascending = reorder == ASCENDING
        # reorder the modules within the suite by their cumulative cost
        if focus == MODULES_WITHIN_SUITE:
            if reorder_by == COST:
                self.reorder_modules_by_cost(items, ascending)
            elif reorder_by == NAME:
                self.reorder_modules_by_name(items, ascending)
            elif reorder_by == FAILURE:
                self.reorder_modules_by_failure(items, ascending)
        # reordering tests within a module
        elif focus == TESTS_WITHIN_MODULE:
            self.reorder_tests_within_module(items, reorder_by, ascending)
        # reorder the tests across all modules in the suite
        # elif focus == TESTS_ACROSS_MODULES:
        elif focus == TESTS_WITHIN_SUITE:
            self.reorder_tests_across_modules(items, reorder_by, ascending)

    def reorder_tests_across_modules(
        self, items: List["Item"], reorder_by: str, ascending: bool = True
    ) -> None:
        """Reorder tests across all modules by the specified technique."""
        # note that reordering all of the test cases across the modules
        # is like treating all of the test cases as being inside of one
        # big test suite, regardless of how they are grouped inside of
        # the modules (i.e., the individual files in the test suite)
        if reorder_by == COST:
            items.sort(key=self.get_test_total_duration, reverse=not ascending)
        elif reorder_by == NAME:
            items.sort(
                key=lambda item: getattr(item, NAME, EMPTY_STRING),
                reverse=not ascending,
            )
        elif reorder_by == FAILURE:
            items.sort(key=self.get_test_failure_count, reverse=not ascending)

    def has_test_data(self) -> bool:
        """Check if test performance data is available."""
        return bool(self.test_data)


def create_reorderer(
    json_report_path: Optional[str] = None,
) -> ReordererOfTests:
    """Create a TestReorderer instance."""
    # create a TestReorderer instance that
    # can be used to reorder based on
    # data about the tests from prior run(s)
    return ReordererOfTests(json_report_path)


def setup_json_report_plugin(config) -> bool:
    """Configure pytest-json-report plugin to generate JSON reports automatically."""
    # attempt to configure the pytest-json-report plugin since the data
    # that it produces is useful for certain reordering tasks like,
    # for instance, reordering tests by cumulative execution time
    try:
        # determine whether or not the pytest-json-report plugin is available
        # and display a suitable diagnostic message before running test suite
        plugin_manager = config.pluginmanager
        if plugin_manager.has_plugin(PYTEST_JSON_REPORT_PLUGIN_NAME):
            console.print(
                f"{FLASHLIGHT_PREFIX} Detected the pytest-json-report plugin"
            )
        else:
            console.print(
                f"{FLASHLIGHT_PREFIX} Did not detect pytest-json-report plugin"
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
            hasattr(config.option, JSON_REPORT_FILE)
            and config.option.json_report_file == REPORT_JSON
        ):
            console.print(
                f"{FLASHLIGHT_PREFIX} Not using the pytest-json-report in {config.option.json_report_file}"
            )
        # set the JSON report file location for pytest-json-report plugin
        # to be the default location that is used by the pytest-brightest plugin
        config.option.json_report_file = json_report_file
        console.print(
            f"{FLASHLIGHT_PREFIX} Using the pytest-json-report with name {json_report_file}"
        )
        return True
    # was not able to import pytest_jsonreport's plugin which means that it cannot
    # be extract to support certain types of prioritization enabled by pytest-brightest
    except ImportError as e:
        console.print(
            f"{HIGH_BRIGHTNESS_PREFIX} pytest-json-report not available: {e}"
        )
        return False
    # some other problem occurred and the pytest-brightest plugin cannot use
    # the pytest-json-report plugin
    except Exception as e:
        console.print(
            f"{HIGH_BRIGHTNESS_PREFIX} pytest-json report not setup: {e}"
        )
        return False
