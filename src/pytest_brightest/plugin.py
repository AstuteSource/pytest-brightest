"""Main plugin implementation for pytest-brightest."""

from pathlib import Path
from typing import List, Optional

from .reorder import TestReorderer, setup_json_report_plugin
from .shuffler import ShufflerOfTests, generate_random_seed


class BrightestPlugin:
    """Main plugin class that handles pytest integration."""

    def __init__(self):
        """Initialize the plugin with default settings."""
        self.enabled = False
        self.shuffle_enabled = False
        self.shuffle_by = "suite"
        self.seed: Optional[int] = None
        self.shuffler: Optional[ShufflerOfTests] = None
        self.details = False
        self.reorder_enabled = False
        self.reorder_by = "fast"
        self.reorder = "first"
        self.reorderer: Optional[TestReorderer] = None
        self.brightest_json_file: Optional[str] = None

    def configure(self, config) -> None:  # noqa: PLR0912
        """Configure the plugin based on command line options."""
        self.enabled = config.getoption("--brightest", False)
        if not self.enabled:
            return
        # Always set up JSON reporting when brightest is enabled
        # This ensures we generate performance data for future reordering
        json_setup_success = setup_json_report_plugin(config)
        if not json_setup_success:
            print(
                "pytest-brightest: JSON report setup failed, reordering features disabled"
            )
        shuffle_option = config.getoption("--shuffle", None)
        no_shuffle_option = config.getoption("--no-shuffle", False)
        if no_shuffle_option:
            self.shuffle_enabled = False
        elif shuffle_option is not None:
            self.shuffle_enabled = shuffle_option
        else:
            self.shuffle_enabled = False
        shuffle_by_option = config.getoption("--shuffle-by", "suite")
        if shuffle_by_option in ["suite", "file", "files"]:
            self.shuffle_by = shuffle_by_option
        else:
            self.shuffle_by = "suite"
        seed_option = config.getoption("--seed", None)
        if seed_option is not None:
            self.seed = int(seed_option)
        elif self.shuffle_enabled:
            self.seed = generate_random_seed()
        details_option = config.getoption("--details", False)
        no_details_option = config.getoption("--no-details", False)
        if no_details_option:
            self.details = False
        elif details_option:
            self.details = True
        else:
            self.details = False
        reorder_by_option = config.getoption("--reorder-by", None)
        if reorder_by_option in ["fast", "slow", "fail", "pass"]:
            self.reorder_enabled = True
            self.reorder_by = reorder_by_option
        reorder_option = config.getoption("--reorder", "first")
        if reorder_option in ["first", "last"]:
            self.reorder = reorder_option
        self.brightest_json_file = config.getoption(
            "--brightest-json-file", ".pytest_cache/pytest-json-report.json"
        )
        # Show where we expect to find test data for reordering
        if json_setup_success:
            print(
                f"pytest-brightest: Will look for test data in {self.brightest_json_file}"
            )
        # Configure reordering if requested
        if self.reorder_enabled:
            if json_setup_success:
                self.reorderer = TestReorderer(self.brightest_json_file)
                if not self.reorderer.has_test_data():
                    print(
                        "pytest-brightest: No previous test data found for reordering"
                    )
                    print(
                        f"pytest-brightest: Run tests once to generate {self.brightest_json_file}"
                    )
                else:
                    print(
                        f"pytest-brightest: Reordering tests by {self.reorder_by} ({self.reorder})"
                    )
            else:
                print(
                    "pytest-brightest: Cannot enable reordering without JSON report plugin"
                )
                self.reorder_enabled = False
        # Configure shuffling if requested
        if self.shuffle_enabled:
            self.shuffler = ShufflerOfTests(self.seed)
            if self.seed is not None:
                print(f"pytest-brightest: Using random seed {self.seed}")
                print(f"pytest-brightest: Shuffling by {self.shuffle_by}")

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
        help="Enable pytest-brightest plugin",
    )
    group.addoption(
        "--shuffle",
        action="store_true",
        default=False,
        help="Shuffle the order of tests",
    )
    group.addoption(
        "--no-shuffle",
        action="store_true",
        default=False,
        help="Do not shuffle the order of tests",
    )
    group.addoption(
        "--shuffle-by",
        choices=["suite", "file", "files"],
        default="suite",
        help="Shuffle tests by suite (all tests), file (within each test file), or files (file order and tests within files)",
    )
    group.addoption(
        "--seed",
        type=int,
        default=None,
        help="Set the random seed for test shuffling",
    )
    group.addoption(
        "--details",
        action="store_true",
        default=False,
        help="Enable details display mode to print test names",
    )
    group.addoption(
        "--no-details",
        action="store_true",
        default=False,
        help="Disable details mode (default behavior)",
    )
    group.addoption(
        "--reorder-by",
        choices=["fast", "slow", "fail", "pass"],
        default=None,
        help="Reorder tests by speed (fast/slow) or outcome (fail/pass)",
    )
    group.addoption(
        "--reorder",
        choices=["first", "last"],
        default="first",
        help="Place reordered tests first or last in the test suite",
    )
    group.addoption(
        "--brightest-json-file",
        type=str,
        default=".pytest_cache/pytest-json-report.json",
        help="Path to JSON report file used for test reordering",
    )


def pytest_configure(config):
    """Configure the plugin when pytest starts."""
    _plugin.configure(config)


def pytest_collection_modifyitems(config, items):
    """Modify the collected test items by applying reordering and shuffling."""
    if _plugin.enabled:
        # Apply reordering first (based on previous test performance)
        if _plugin.reorder_enabled:
            _plugin.reorder_tests(items)
        # Apply shuffling second (randomizes the reordered or original test order)
        if _plugin.shuffle_enabled:
            _plugin.shuffle_tests(items)


def pytest_sessionfinish(session, exitstatus):
    """Check if JSON report was generated after test session completes."""
    if _plugin.enabled:

        json_file = Path(_plugin.brightest_json_file)
        if json_file.exists():
            print(f"pytest-brightest: JSON report generated at {json_file}")
            print(
                f"pytest-brightest: File size: {json_file.stat().st_size} bytes"
            )
        else:
            print(
                f"pytest-brightest: WARNING - JSON report not found at {json_file}"
            )
            print(
                "pytest-brightest: Check if pytest-json-report is properly configured"
            )


def pytest_runtest_makereport(item, call):
    """Print test outcome and duration when a test is executed."""
    if _plugin.enabled and _plugin.details:
        if call.when == "call":
            outcome = call.excinfo
            try:
                test_outcome = "failed" if outcome else "passed"
                test_duration = call.duration
                test_id = item.nodeid
                print(f"Test: {test_id}")
                print(f"Test Outcome: {test_outcome}")
                print(f"Test Duration: {test_duration:.5f} seconds")
            except Exception as e:
                print("ERROR:", e)
