"""Main plugin implementation for pytest-brightest."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console

from .constants import (
    ASCENDING,
    BRIGHTEST,
    COST,
    DEFAULT_FILE_ENCODING,
    DEFAULT_PYTEST_JSON_REPORT_PATH,
    DESCENDING,
    DIRECTION,
    FAILURE,
    FOCUS,
    MODULE_COSTS,
    MODULE_ORDER,
    MODULE_TESTS,
    MODULES_WITHIN_SUITE,
    NAME,
    NEWLINE,
    NODEID,
    SEED,
    SHUFFLE,
    TECHNIQUE,
    TEST_COSTS,
    TEST_ORDER,
    TESTS_ACROSS_MODULES,
    TESTS_WITHIN_MODULE,
    TIMESTAMP,
)
from .reorder import ReordererOfTests, setup_json_report_plugin
from .shuffler import ShufflerOfTests, generate_random_seed

# create a default console
console = Console()


class BrightestPlugin:
    """Main plugin class that handles pytest integration."""

    def __init__(self):
        """Initialize the plugin with default settings."""
        self.enabled = False
        self.shuffle_enabled = False
        self.shuffle_by = None
        self.seed: Optional[int] = None
        self.shuffler: Optional[ShufflerOfTests] = None
        self.details = False
        self.reorder_enabled = False
        self.reorder_by = None
        self.reorder = None
        self.reorderer: Optional[ReordererOfTests] = None
        self.brightest_json_file: Optional[str] = None

    def configure(self, config) -> None:
        """Configure the plugin based on command-line options."""
        # check if the plugin is enabled; if it is not
        # enabled then no further configuration steps are taken
        self.enabled = config.getoption("--brightest", False)
        if not self.enabled:
            return
        # configure the name of the file that will contain the
        # JSON file that contains the pytest-json-report data
        self.brightest_json_file = DEFAULT_PYTEST_JSON_REPORT_PATH
        # always set up JSON reporting when brightest is enabled;
        # this ensures generation of performance data for future reordering
        json_setup_success = setup_json_report_plugin(config)
        if not json_setup_success:
            console.print(
                ":high_brightness: pytest-brightest: pytest-json-report setup failed, reordering features disabled"
            )
        # extract the configuration options for reordering and shuffling
        self.technique = config.getoption("--reorder-by-technique")
        self.focus = config.getoption("--reorder-by-focus")
        self.direction = config.getoption("--reorder-in-direction")
        # if the shuffling technique is chosen, then configure the shuffler
        if self.technique == SHUFFLE:
            self.shuffle_enabled = True
            self.shuffle_by = self.focus
            if self.shuffle_by is None:
                self.shuffle_by = TESTS_ACROSS_MODULES
            seed_option = config.getoption("--seed", None)
            if seed_option is not None:
                self.seed = int(seed_option)
            else:
                self.seed = generate_random_seed()
            self.shuffler = ShufflerOfTests(self.seed)
            console.print(
                f":flashlight: pytest-brightest: Shuffling tests by {self.shuffle_by} with seed {self.seed}"
            )
            if self.direction is not None:
                console.print(
                    ":high_brightness: pytest-brightest: Warning: --reorder-in-direction is ignored when --reorder-by-technique is 'shuffle'"
                )
        # if the reordering technique is chosen, then configure the reorderer
        elif self.technique in [NAME, COST, FAILURE]:
            self.reorder_enabled = True
            self.reorder_by = self.technique
            self.reorder = self.direction
            if json_setup_success and self.brightest_json_file:
                self.reorderer = ReordererOfTests(self.brightest_json_file)
            console.print(
                f":flashlight: pytest-brightest: Reordering tests by {self.reorder_by} in {self.reorder} order with focus {self.focus}"
            )

    def shuffle_tests(self, items: List) -> None:
        """Shuffle test items if shuffling is enabled."""
        # if shuffling is enabled and there are items to shuffle, then
        # shuffle them according to the chosen focus
        if self.shuffle_enabled and self.shuffler and items:
            if self.shuffle_by == TESTS_ACROSS_MODULES:
                self.shuffler.shuffle_items_in_place(items)
            elif self.shuffle_by == TESTS_WITHIN_MODULE:
                self.shuffler.shuffle_items_by_file_in_place(items)
            elif self.shuffle_by == MODULES_WITHIN_SUITE:
                self.shuffler.shuffle_files_in_place(items)

    def reorder_tests(self, items: List) -> None:
        """Reorder test items if reordering is enabled."""
        # if reordering is enabled and there are items to reorder, then
        # reorder them according to the chosen technique, focus, and direction
        if (
            self.reorder_enabled
            and self.reorderer
            and items
            and self.reorder_by
            and self.reorder
        ):
            self.reorderer.reorder_tests_in_place(
                items, self.reorder_by, self.reorder, self.focus
            )


# create a global plugin instance that can be used by the pytest hooks
_plugin = BrightestPlugin()


def pytest_addoption(parser):
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
            TESTS_ACROSS_MODULES,
        ],
        default=TESTS_ACROSS_MODULES,
        help="Reorder modules, tests within modules, or tests across modules",
    )
    group.addoption(
        "--reorder-in-direction",
        choices=[ASCENDING, DESCENDING],
        default=None,
        help="Reordered tests in ascending or descending order",
    )


def pytest_configure(config):
    """Configure the plugin when pytest starts."""
    # configure the plugin using the command-line options
    _plugin.configure(config)


def pytest_collection_modifyitems(config, items):
    """Modify the collected test items by applying reordering and shuffling."""
    # indicate that config parameter is not used
    _ = config
    # if the plugin is enabled, then apply the reordering and shuffling
    if _plugin.enabled:
        # apply reordering first (based on previous test performance)
        if _plugin.reorder_enabled:
            _plugin.reorder_tests(items)
        # apply shuffling second (randomizes the reordered or original test order)
        if _plugin.shuffle_enabled:
            _plugin.shuffle_tests(items)


def pytest_sessionfinish(session, exitstatus):  # noqa: PLR0912
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
                brightest_data = {
                    TIMESTAMP: datetime.now().isoformat(),
                    TECHNIQUE: _plugin.technique,
                    FOCUS: _plugin.focus,
                    DIRECTION: _plugin.direction,
                    SEED: _plugin.seed,
                }
                # save the data about the cost-based reordering
                if _plugin.technique == COST and _plugin.reorderer:
                    module_costs: Dict[str, float] = {}
                    test_costs: Dict[str, float] = {}
                    for item in session.items:
                        nodeid = getattr(item, NODEID, "")
                        if nodeid:
                            module_path = nodeid.split("::")[0]
                            cost = _plugin.reorderer.get_test_total_duration(  # type: ignore
                                item
                            )
                            module_costs[module_path] = (
                                module_costs.get(module_path, 0.0) + cost
                            )
                            test_costs[nodeid] = cost
                    brightest_data[MODULE_COSTS] = module_costs
                    brightest_data[TEST_COSTS] = test_costs
                # save the data about the name-based reordering
                elif _plugin.technique == NAME:
                    if _plugin.focus == MODULES_WITHIN_SUITE:
                        module_order = []
                        for item in session.items:
                            nodeid = getattr(item, NODEID, "")
                            if nodeid:
                                module_path = nodeid.split("::")[0]
                                if module_path not in module_order:
                                    module_order.append(module_path)
                        brightest_data[MODULE_ORDER] = module_order
                    elif _plugin.focus == TESTS_ACROSS_MODULES:
                        brightest_data[TEST_ORDER] = [
                            getattr(item, NODEID, "") for item in session.items
                        ]
                    elif _plugin.focus == TESTS_WITHIN_MODULE:
                        module_tests: Dict[str, List[str]] = {}
                        for item in session.items:
                            nodeid = getattr(item, NODEID, "")
                            if nodeid:
                                module_path = nodeid.split("::")[0]
                                if module_path not in module_tests:
                                    module_tests[module_path] = []
                                module_tests[module_path].append(nodeid)
                        brightest_data[MODULE_TESTS] = module_tests
                data[BRIGHTEST] = brightest_data
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            console.print(NEWLINE)
            console.print(
                f":flashlight: pytest-brightest: pytest-json-report detected at {json_file}"
            )
            console.print(
                f":flashlight: pytest-brightest: pytest-json-report created a JSON file of size: {json_file.stat().st_size} bytes"
            )
        else:
            console.print(NEWLINE)
            console.print(
                ":high_brightness: pytest-brightest: There is no JSON file created by pytest-json-report"
            )
            console.print(
                ":high_brightness: pytest-brightest: Use --json-report from pytest-json-report to create the JSON file"
            )
