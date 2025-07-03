"""Main plugin implementation for pytest-brightest."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console

from .constants import (
    DEFAULT_FILE_ENCODING,
    DEFAULT_PYTEST_JSON_REPORT_PATH,
    NEWLINE,
    NODEID,
)
from .reorder import TestReorderer, setup_json_report_plugin
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
        self.reorderer: Optional[TestReorderer] = None
        self.brightest_json_file: Optional[str] = None

    def configure(self, config) -> None:
        """Configure the plugin based on command-line options."""
        self.enabled = config.getoption("--brightest", False)
        if not self.enabled:
            return
        self.brightest_json_file = DEFAULT_PYTEST_JSON_REPORT_PATH
        json_setup_success = setup_json_report_plugin(config)
        if not json_setup_success:
            console.print(
                ":high_brightness: pytest-brightest: pytest-json-report setup failed, reordering features disabled"
            )
        self.technique = config.getoption("--reorder-by-technique")
        self.focus = config.getoption("--reorder-by-focus")
        self.direction = config.getoption("--reorder-in-direction")
        if self.technique == "shuffle":
            self.shuffle_enabled = True
            self.shuffle_by = self.focus
            seed_option = config.getoption("--seed", None)
            if seed_option is not None:
                self.seed = int(seed_option)
            else:
                self.seed = generate_random_seed()
            self.shuffler = ShufflerOfTests(self.seed)
            console.print(
                f":flashlight: pytest-brightest: Shuffling tests by {self.shuffle_by} with seed {self.seed}"
            )
        elif self.technique in ["name", "cost"]:
            self.reorder_enabled = True
            self.reorder_by = self.technique
            self.reorder = self.direction
            if json_setup_success and self.brightest_json_file:
                self.reorderer = TestReorderer(self.brightest_json_file)
            console.print(
                f":flashlight: pytest-brightest: Reordering tests by {self.reorder_by} in {self.reorder} order with focus {self.focus}"
            )

    def shuffle_tests(self, items: List) -> None:
        """Shuffle test items if shuffling is enabled."""
        if self.shuffle_enabled and self.shuffler and items:
            if self.shuffle_by == "tests-across-modules":
                self.shuffler.shuffle_items_in_place(items)
            elif self.shuffle_by == "tests-within-module":
                self.shuffler.shuffle_items_by_file_in_place(items)
            elif self.shuffle_by == "modules-within-suite":
                self.shuffler.shuffle_files_in_place(items)

    def reorder_tests(self, items: List) -> None:
        """Reorder test items if reordering is enabled."""
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


# Global plugin instance
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
        choices=["shuffle", "name", "cost"],
        default=None,
        help="Reorder tests by shuffling, name, or cost",
    )
    group.addoption(
        "--reorder-by-focus",
        choices=[
            "modules-within-suite",
            "tests-within-module",
            "tests-across-modules",
        ],
        default="tests-across-modules",
        help="Reorder modules, tests within modules, or tests across modules",
    )
    group.addoption(
        "--reorder-in-direction",
        choices=["ascending", "descending"],
        default="ascending",
        help="Reordered tests in ascending or descending order",
    )


def pytest_configure(config):
    """Configure the plugin when pytest starts."""
    _plugin.configure(config)


def pytest_collection_modifyitems(config, items):
    """Modify the collected test items by applying reordering and shuffling."""
    # indicate that config parameter is not used
    _ = config
    if _plugin.enabled:
        # apply reordering first (based on previous test performance)
        if _plugin.reorder_enabled:
            _plugin.reorder_tests(items)
        # apply shuffling second (randomizes the reordered or original test order)
        if _plugin.shuffle_enabled:
            _plugin.shuffle_tests(items)


def pytest_sessionfinish(session, exitstatus):
    """Check if JSON file from pytest-json-report exists after test session completes."""
    if _plugin.enabled and _plugin.brightest_json_file:
        json_file = Path(_plugin.brightest_json_file)
        if json_file.exists():
            with json_file.open("r+", encoding=DEFAULT_FILE_ENCODING) as f:
                data = json.load(f)
                brightest_data = {
                    "timestamp": datetime.now().isoformat(),
                    "technique": _plugin.technique,
                    "focus": _plugin.focus,
                    "direction": _plugin.direction,
                    "seed": _plugin.seed,
                }
                if _plugin.technique == "cost" and _plugin.reorderer:
                    module_costs: Dict[str, float] = {}
                    test_costs: Dict[str, float] = {}
                    for item in session.items:
                        nodeid = getattr(item, NODEID, "")
                        if nodeid:
                            module_path = nodeid.split("::")[0]
                            cost = _plugin.reorderer.get_test_total_duration(item)
                            module_costs[module_path] = (
                                module_costs.get(module_path, 0.0) + cost
                            )
                            test_costs[nodeid] = cost
                    brightest_data["module_costs"] = module_costs
                    brightest_data["test_costs"] = test_costs
                data["brightest"] = brightest_data
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
