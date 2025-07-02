"""Main plugin implementation for pytest-brightest."""

from pathlib import Path
from typing import List, Optional

from rich.console import Console

from .constants import DEFAULT_PYTEST_JSON_REPORT_PATH, NEWLINE
from .reorder import (
    TestReorderer,
    setup_json_report_plugin,
)
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
        # extract the configuration option for reordering and configure shuffling
        reorder_by_option = config.getoption("--reorder-by", None)
        # these are the options for --reorder-by:
        # --reorder-by shuffle
        # --reorder-by cost
        # --reorder-by failure
        # --> reordering should take place through the use of shuffling
        if reorder_by_option == "shuffle":
            # indicate that shuffling is enabled
            self.shuffle_enabled = True
            # since shuffling is enabled, determine whether or not to shuffle
            # by suite, file, or files and set the seed for shuffling
            shuffle_by_option = config.getoption("--shuffle-by", "suite")
            self.shuffle_by = shuffle_by_option
            # determine the seed for shuffling, which is either specified
            # on the command-line or generated randomly
            seed_option = config.getoption("--seed", "suite")
            if seed_option is not None:
                self.seed = int(seed_option)
            elif self.shuffle_enabled:
                self.seed = generate_random_seed()
        # shuffling is disabled
        else:
            self.shuffle_enabled = False
        # finish the configuration of shuffling if requested
        # and display the configuration details for pytest-brightest
        if self.shuffle_enabled:
            self.shuffler = ShufflerOfTests(self.seed)
            console.print(
                f":flashlight: pytest-brightest: Shuffling the test cases by {self.shuffle_by}"
            )
            console.print(
                f":flashlight: pytest-brightest: Shuffling with the random seed {self.seed}"
            )

    def shuffle_tests(self, items: List) -> None:
        """Shuffle test items if shuffling is enabled."""
        if self.shuffle_enabled and self.shuffler and items:
            if self.shuffle_by == "suite":
                self.shuffler.shuffle_items_in_place(items)
            elif self.shuffle_by == "file":
                self.shuffler.shuffle_items_by_file_in_place(items)
            elif self.shuffle_by == "files":
                self.shuffler.shuffle_files_and_tests_in_place(items)

    def reorder_tests(self, items: List) -> None:
        """Reorder test items if reordering is enabled."""
        if self.reorder_enabled and self.reorderer and items:
            self.reorderer.reorder_tests_in_place(
                items, self.reorder_by, self.reorder
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
        "--reorder-by",
        choices=["shuffle", "cost", "failure"],
        default="shuffle",
        help="Reorder tests by shuffling, cost, or failures",
    )
    group.addoption(
        "--reorder-direction",
        choices=["ascending", "descending"],
        default="ascending",
        help="Reordered tests in ascending or descending order",
    )
    group.addoption(
        "--shuffle-by",
        choices=["suite", "file", "files"],
        default="ascending",
        help="Shuffle tests by suite (all tests), file (tests in each file), or files (file order and tests within files)",
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
    # indicate that these parameters are not used
    # in this definition of the pytest hook
    _ = session
    _ = exitstatus
    # the plugin was enabled and this means that we can display a final
    # message about the behavior of the pytest-brightest plugin
    if _plugin.enabled:
        # there is no JSON file to check
        if _plugin.brightest_json_file is None:
            return None
        # the JSON file exists and we can display a message about it
        json_file = Path(_plugin.brightest_json_file)
        if json_file.exists():
            console.print(NEWLINE)
            console.print(
                f":flashlight: pytest-brightest: pytest-json-report detected at {json_file}"
            )
            console.print(
                f":flashlight: pytest-brightest: pytest-json-report created a JSON file of size: {json_file.stat().st_size} bytes"
            )
        # the is no JSON file from the pytest-json-report plugin and the
        # person using the pytest-brightest plugin may want to know how
        # to create it, so give an extra diagnostic message about this
        else:
            console.print(NEWLINE)
            console.print(
                ":high_brightness: pytest-brightest: There is no JSON file created by pytest-json-report"
            )
            console.print(
                ":high_brightness: pytest-brightest: Use --json-report from pytest-json-report to create the JSON file"
            )
