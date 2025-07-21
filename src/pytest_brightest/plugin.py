"""Main plugin implementation for pytest-brightest."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

from _pytest.config import Config  # type: ignore
from _pytest.config.argparsing import Parser  # type: ignore
from _pytest.main import Session  # type: ignore
from _pytest.nodes import Item  # type: ignore
from _pytest.reports import TestReport  # type: ignore
from _pytest.runner import runtestprotocol  # type: ignore
from rich.console import Console

from .constants import (
    ASCENDING,
    BRIGHTEST,
    COST,
    DATA,
    DEFAULT_FILE_ENCODING,
    DEFAULT_PYTEST_JSON_REPORT_PATH,
    DESCENDING,
    DIRECTION,
    EMPTY_STRING,
    ERROR,
    FAILED,
    FAILURE,
    FLASHLIGHT_PREFIX,
    FOCUS,
    HIGH_BRIGHTNESS_PREFIX,
    MAX_RUNS,
    MODULES_WITHIN_SUITE,
    NAME,
    NEWLINE,
    NODEID,
    NODEID_SEPARATOR,
    REPEAT_COUNT,
    REPEAT_FAILED_COUNT,
    RUNCOUNT,
    SEED,
    SHUFFLE,
    TECHNIQUE,
    TEST_CASE_COSTS,
    TEST_CASE_FAILURES,
    TEST_MODULE_COSTS,
    TEST_MODULE_FAILURES,
    TESTCASES,
    TESTS_WITHIN_MODULE,
    TESTS_WITHIN_SUITE,
    TIMESTAMP,
)
from .reorder import ReordererOfTests, setup_json_report_plugin
from .shuffler import ShufflerOfTests, generate_random_seed

# create a default console
console = Console()


class BrightestPlugin:
    """Main plugin class that handles pytest integration."""

    def __init__(self) -> None:
        """Initialize the plugin with default settings."""
        self.enabled = False
        self.shuffle_enabled = False
        self.shuffle_by: Optional[str] = None
        self.seed: Optional[int] = None
        self.shuffler: Optional[ShufflerOfTests] = None
        self.details = False
        self.reorder_enabled = False
        self.reorder_by: Optional[str] = None
        self.reorder: Optional[str] = None
        self.reorderer: Optional[ReordererOfTests] = None
        self.brightest_json_file: Optional[str] = None
        self.current_session_failures: Dict[str, int] = {}
        self.session_items: List[Item] = []
        self.technique: Optional[str] = None
        self.focus: Optional[str] = None
        self.direction: Optional[str] = None
        self.historical_brightest_data: List[Dict[str, Any]] = []
        self.repeat_count = 1
        self.repeat_failed_count = 0

    def configure(self, config: Config) -> None:
        """Configure the plugin based on command-line options."""
        # check if the plugin is enabled; if it is not
        # enabled then no further configuration steps are taken
        self.enabled = config.getoption("--brightest", False)
        if not self.enabled:
            return
        # configure the name of the file that will contain the
        # JSON file that contains the pytest-json-report data
        self.brightest_json_file = DEFAULT_PYTEST_JSON_REPORT_PATH
        # preserve historical brightest data before pytest-json-report
        # overwrites it with the new data; this is a critical step because
        # this plugin stores and relies on historical data to perform
        # various types of optimizations to the regression testing process
        self._preserve_historical_brightest_data()
        # always set up JSON reporting when brightest is enabled;
        # this ensures generation of test execution data for future reordering
        json_setup_success = setup_json_report_plugin(config)
        # there was a problem configuring the pytest-json-report plugin,
        # display a diagnostic message and to indicate that certain features
        # will not be available during this run of the test suite
        if not json_setup_success:
            console.print(
                f"{HIGH_BRIGHTNESS_PREFIX} pytest-json-report setup failed, certain features disabled"
            )
        # create the reorderer of tests so that it is possible to
        # extract historical data about test execution; note that the
        # reorderer is now created in all modes of execution
        if json_setup_success and self.brightest_json_file:
            self.reorderer = ReordererOfTests(self.brightest_json_file)
        # extract the configuration options for reordering and shuffling
        self.technique = config.getoption("--reorder-by-technique")
        self.focus = config.getoption("--reorder-by-focus")
        self.direction = config.getoption("--reorder-in-direction")
        # if the shuffling technique is chosen, then configure the shuffler
        # and alert the person using the plugin if there is a misconfiguration
        if self.technique == SHUFFLE:
            # shuffling is enabled, so the tests will be randomly ordered
            # depending on the specific focus that was specified
            self.shuffle_enabled = True
            self.shuffle_by = self.focus
            # use a default focus if none was specified;
            # in this case, the shuffling will simply shuffle
            # all of the tests cases within the suite, not
            # considering the boundaries of the modules
            if self.shuffle_by is None:
                self.shuffle_by = TESTS_WITHIN_SUITE
            # use the specified see if it was given on the command-line;
            # otherwise, generate a random seed for test shuffling
            seed_option = config.getoption("--seed", None)
            if seed_option is not None:
                self.seed = int(seed_option)
            else:
                self.seed = generate_random_seed()
            # create the shuffler object with the specified seed
            self.shuffler = ShufflerOfTests(self.seed)
            console.print(
                f"{FLASHLIGHT_PREFIX} Shuffling tests by {self.shuffle_by} with seed {self.seed}"
            )
            # alert the person using this plugin to the fact that
            # they cannot specify a direction for shuffling as this
            # is not a valid configuration of a reordering technique
            if self.direction is not None:
                console.print(
                    f"{HIGH_BRIGHTNESS_PREFIX} Warning: --reorder-in-direction is ignored when --reorder-by-technique is 'shuffle'"
                )
        # if the reordering technique is chosen, then configure the reorderer
        elif self.technique in [NAME, COST, FAILURE]:
            self.reorder_enabled = True
            self.reorder_by = self.technique
            self.reorder = self.direction
            console.print(
                f"{FLASHLIGHT_PREFIX} Reordering tests by {self.reorder_by} in {self.reorder} order with focus {self.focus}"
            )
        self.repeat_count = config.getoption("--repeat")
        self.repeat_failed_count = config.getoption("--repeat-failed")

    def record_test_failure(self, nodeid: str) -> None:
        """Record a test failure for the current session."""
        if nodeid:
            module_path = nodeid.split(NODEID_SEPARATOR)[0]
            if module_path not in self.current_session_failures:
                self.current_session_failures[module_path] = 0
            self.current_session_failures[module_path] += 1

    def shuffle_tests(self, items: List[Item]) -> None:
        """Shuffle test items if shuffling is enabled."""
        # if shuffling is enabled and there are items to shuffle, then
        # shuffle them according to the chosen focus
        if self.shuffle_enabled and self.shuffler and items:
            if self.shuffle_by == TESTS_WITHIN_SUITE:
                self.shuffler.shuffle_items_in_place(items)
            elif self.shuffle_by == TESTS_WITHIN_MODULE:
                self.shuffler.shuffle_items_by_file_in_place(items)
            elif self.shuffle_by == MODULES_WITHIN_SUITE:
                self.shuffler.shuffle_files_in_place(items)

    def reorder_tests(self, items: List[Item]) -> None:
        """Reorder test items if reordering is enabled."""
        # if reordering is enabled and there are items to reorder, then
        # reorder them according to the chosen technique, focus, and direction
        if (
            self.reorder_enabled
            and self.reorderer
            and items
            and self.reorder_by
            and self.reorder
            and self.focus
        ):
            self.reorderer.reorder_tests_in_place(
                items, self.reorder_by, self.reorder, self.focus
            )

    def store_session_items(self, items: List[Item]) -> None:
        """Store the session items for later use in data collection."""
        self.session_items = items.copy()

    def _preserve_historical_brightest_data(self) -> None:
        """Preserve historical brightest data before pytest-json-report overwrites it."""
        if not self.brightest_json_file:
            return
        json_file = Path(self.brightest_json_file)
        if json_file.exists():
            try:
                with json_file.open("r", encoding=DEFAULT_FILE_ENCODING) as f:
                    data = json.load(f)
                    # extract existing brightest data
                    if BRIGHTEST in data:
                        if isinstance(data[BRIGHTEST], list):
                            self.historical_brightest_data = data[
                                BRIGHTEST
                            ].copy()
                        else:
                            # handle legacy format
                            self.historical_brightest_data = [data[BRIGHTEST]]
            except (json.JSONDecodeError, FileNotFoundError):
                # if there's an error reading the file, start with empty history
                self.historical_brightest_data = []


# create a global plugin instance that can be used by the pytest hooks
_plugin = BrightestPlugin()


def pytest_addoption(parser: Parser) -> None:
    """Add command line options for pytest-brightest."""
    group = parser.getgroup("brightest")
    group.addoption(
        "--brightest",
        action="store_true",
        default=False,
        help="Enable the pytest-brightest plugin",
    )
    group.addoption(
        "--seed",
        type=int,
        default=None,
        help="Set the random seed for test shuffling",
    )
    group.addoption(
        "--reorder-by-technique",
        choices=[SHUFFLE, NAME, COST, FAILURE],
        default=None,
        help="Reorder tests by shuffling, name, cost, or failure",
    )
    group.addoption(
        "--reorder-by-focus",
        choices=[
            MODULES_WITHIN_SUITE,
            TESTS_WITHIN_MODULE,
            TESTS_WITHIN_SUITE,
        ],
        default=TESTS_WITHIN_SUITE,
        help="Reorder modules within suite, tests within modules, or tests within suite",
    )
    group.addoption(
        "--reorder-in-direction",
        choices=[ASCENDING, DESCENDING],
        default=ASCENDING,
        help="Reordered tests in ascending or descending order",
    )
    group.addoption(
        "--repeat",
        type=int,
        default=1,
        help="Set the number of times to repeat each test",
    )
    group.addoption(
        "--repeat-failed",
        type=int,
        default=0,
        help="Set the number of times to repeat a failed test",
    )


def pytest_configure(config: Config) -> None:
    """Configure the plugin when pytest starts."""
    # configure the plugin using the command-line options
    _plugin.configure(config)


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    """Modify the collected test items by applying reordering and shuffling."""
    # indicate that config parameter is not used
    _ = config
    # if the plugin is enabled, then apply the reordering in one of the
    # specified techniques according to the command-line options
    if _plugin.enabled:
        # store the original items for later use in data collection
        _plugin.store_session_items(items)
        # notes about how to use the pytest-brightest plugin:
        # (a) the plugin allows for either the shuffling of the test
        # suite or the reordering of the test suite, but a person
        # using the plugin cannot use both techniques at the same time
        # (b) the plugin defaults to using one of the reordering
        # techniques as the default if both techniques are (accidentally)
        # specified on the command line by the person using the plugin
        # --> Use the reordering technique
        if _plugin.reorder_enabled:
            _plugin.reorder_tests(items)
        # --> Use the shuffling technique
        elif _plugin.shuffle_enabled:
            _plugin.shuffle_tests(items)
        # apply repeat functionality after reordering/shuffling
        if _plugin.repeat_count > 1:
            # create repeated items by duplicating the ordered/shuffled list
            repeated_items = []
            for _ in range(_plugin.repeat_count):
                repeated_items.extend(items.copy())
            # replace the items list with the repeated items
            items[:] = repeated_items


def pytest_runtest_protocol(
    item: Item, nextitem: Optional[Item]
) -> Optional[bool]:
    """Run the test protocol for a single item."""
    if _plugin.enabled and _plugin.repeat_failed_count > 0:
        # custom test execution loop for repeating failed tests
        reports = runtestprotocol(item, nextitem=nextitem, log=False)
        # check if the test failed in the call phase
        call_failed = any(
            report.when == "call" and report.failed for report in reports
        )
        if call_failed:
            # if the test fails, repeat it up to the specified number of times
            for i in range(_plugin.repeat_failed_count):
                console.print(
                    f"{FLASHLIGHT_PREFIX} Attempt {i + 2} at repeating failed test {item.nodeid}"
                )
                repeat_reports = runtestprotocol(
                    item, nextitem=nextitem, log=False
                )
                # check if the test passed on a retry
                call_passed = any(
                    report.when == "call" and not report.failed
                    for report in repeat_reports
                )
                if call_passed:
                    # use the passing reports for final outcome
                    reports = repeat_reports
                    console.print(
                        f"{FLASHLIGHT_PREFIX} Test {item.nodeid} passed on retry attempt {i + 2}"
                    )
                    break
                else:
                    # update with the latest failed reports
                    reports = repeat_reports
        # log the final reports to ensure proper test outcome recording
        for report in reports:
            item.config.hook.pytest_runtest_logreport(report=report)
        return True
    # default behavior
    return None


def pytest_runtest_logreport(report: TestReport) -> None:
    """Capture test failures during the current session."""
    if _plugin.enabled and _plugin.technique == FAILURE and report.failed:
        _plugin.record_test_failure(report.nodeid)


def _sort_dict_by_value(
    data_dict: Mapping[str, Union[int, float]], order: str
) -> Mapping[str, Union[int, float]]:
    """Create a new dictionary with keys sorted by their values in ascending or descending order."""
    reverse = order == DESCENDING
    sorted_dictionary = dict(
        sorted(data_dict.items(), key=lambda item: item[1], reverse=reverse)
    )
    return sorted_dictionary


def _get_brightest_data(session: Session) -> Dict[str, Any]:
    """Collect brightest data for the JSON report."""
    brightest_data: Dict[str, Any] = {
        TIMESTAMP: datetime.now().isoformat(),
        TECHNIQUE: _plugin.technique,
        FOCUS: _plugin.focus,
        DIRECTION: _plugin.direction,
        SEED: _plugin.seed,
        REPEAT_COUNT: _plugin.repeat_count,
        REPEAT_FAILED_COUNT: _plugin.repeat_failed_count,
        DATA: {},
        TESTCASES: [
            getattr(item, NODEID, EMPTY_STRING) for item in session.items
        ],
    }
    # collect test case costs and module costs
    test_case_costs: Dict[str, float] = {}
    test_module_costs: Dict[str, float] = {}
    test_case_failures: Dict[str, int] = {}
    test_module_failures: Dict[str, int] = {}
    # if reorderer is available, get test performance data
    if _plugin.reorderer:
        # reload the test data to get the current session's performance data
        # that was just written by pytest-json-report
        _plugin.reorderer.load_test_data()
        # use original session items (before repeat) for data collection
        # to avoid duplicate counting of repeated tests
        original_items = (
            _plugin.session_items if _plugin.session_items else session.items
        )
        # collect cost data for each test case
        for item in original_items:
            nodeid = getattr(item, NODEID, EMPTY_STRING)
            if nodeid:
                cost = _plugin.reorderer.get_test_total_duration(item)
                test_case_costs[nodeid] = cost
                # aggregate module costs
                module_path = nodeid.split(NODEID_SEPARATOR)[0]
                test_module_costs[module_path] = (
                    test_module_costs.get(module_path, 0.0) + cost
                )
                # collect failure data
                outcome = _plugin.reorderer.get_test_outcome(item)
                failure_count = 1 if outcome in [FAILED, ERROR] else 0
                test_case_failures[nodeid] = failure_count
                # aggregate module failures
                test_module_failures[module_path] = (
                    test_module_failures.get(module_path, 0) + failure_count
                )
    # add current session failure data if available
    if _plugin.current_session_failures:
        test_module_failures.update(_plugin.current_session_failures)
    # store the data in the target structure, placing it in sorted
    # order so that it is easier for the person who is inspecting
    # the logging output in the JSON file to understand the data
    brightest_data[DATA][TEST_CASE_COSTS] = _sort_dict_by_value(
        test_case_costs, str(_plugin.direction)
    )
    brightest_data[DATA][TEST_MODULE_COSTS] = _sort_dict_by_value(
        test_module_costs, str(_plugin.direction)
    )
    brightest_data[DATA][TEST_CASE_FAILURES] = _sort_dict_by_value(
        test_case_failures, str(_plugin.direction)
    )
    brightest_data[DATA][TEST_MODULE_FAILURES] = _sort_dict_by_value(
        test_module_failures, str(_plugin.direction)
    )
    # add prior data that was used for reordering this session
    if (
        _plugin.reorderer
        and _plugin.session_items
        and _plugin.technique
        and _plugin.focus
    ):
        prior_data = _plugin.reorderer.get_prior_data_for_reordering(
            _plugin.session_items, _plugin.technique, _plugin.focus
        )
        # merge prior data with current data, but don't overwrite the new structure
        for key, value in prior_data.items():
            if key not in brightest_data[DATA]:
                brightest_data[DATA][key] = value
    return brightest_data


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    """Check if JSON file from pytest-json-report exists after test session completes."""
    # indicate that these parameters are not used
    _ = exitstatus
    # if the plugin is enabled and a JSON file is specified, then
    # save the diagnostic data to the JSON file
    if _plugin.enabled and _plugin.brightest_json_file:
        json_file = Path(_plugin.brightest_json_file)
        if json_file.exists():
            with json_file.open("r+", encoding=DEFAULT_FILE_ENCODING) as f:
                data = json.load(f)
                # get the new brightest data for this run
                new_run_data = _get_brightest_data(session)
                # restore historical data and add the new run
                current_runs = _plugin.historical_brightest_data.copy()
                # add runcount to the new data
                if current_runs:
                    # get the highest runcount and increment by 1
                    max_runcount = max(
                        run.get(RUNCOUNT, 0) for run in current_runs
                    )
                    new_run_data[RUNCOUNT] = max_runcount + 1
                else:
                    new_run_data[RUNCOUNT] = 1
                # add the new run data
                current_runs.append(new_run_data)
                # keep only the most recent MAX_RUNS runs
                if len(current_runs) > MAX_RUNS:
                    current_runs[:] = current_runs[-MAX_RUNS:]
                # update the data
                data[BRIGHTEST] = current_runs
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            # display diagnostic messages to the console about the JSON file,
            # showing the name of the file and its size can help a person using
            # this plugin to confirm that the correct JSON report is in use and
            # (since the plugin adds to the report) confirm that the size is
            # increasing each time the tests are run with this plugin
            console.print(NEWLINE)
            console.print(
                f"{FLASHLIGHT_PREFIX} pytest-json-report detected at {json_file}"
            )
            console.print(
                f"{FLASHLIGHT_PREFIX} pytest-json-report created a JSON file of size: {json_file.stat().st_size} bytes"
            )
        # there was no JSON file and this means that several key
        # features of this plugin are disabled (e.g., it is not possible
        # to reorder the tests by cost if there is no JSON file that
        # contains the cost information); make sure to tell the person
        # using this plugin that they need to use pytest-json-report
        else:
            console.print(NEWLINE)
            console.print(
                f"{HIGH_BRIGHTNESS_PREFIX} There is no JSON file created by pytest-json-report"
            )
            console.print(
                f"{HIGH_BRIGHTNESS_PREFIX} Use --json-report from pytest-json-report to create the JSON file"
            )
