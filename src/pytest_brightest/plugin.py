"""Main plugin implementation for pytest-brightest."""

from typing import List, Optional

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

    def configure(self, config) -> None:
        """Configure the plugin based on command line options."""
        self.enabled = config.getoption("--brightest", False)
        if not self.enabled:
            return
        shuffle_option = config.getoption("--shuffle", None)
        no_shuffle_option = config.getoption("--no-shuffle", False)
        if no_shuffle_option:
            self.shuffle_enabled = False
        elif shuffle_option is not None:
            self.shuffle_enabled = shuffle_option
        else:
            self.shuffle_enabled = False
        shuffle_by_option = config.getoption("--shuffle-by", "suite")
        if shuffle_by_option in ["suite", "file"]:
            self.shuffle_by = shuffle_by_option
        else:
            self.shuffle_by = "suite"
        seed_option = config.getoption("--seed", None)
        if seed_option is not None:
            self.seed = int(seed_option)
        elif self.shuffle_enabled:
            self.seed = generate_random_seed()
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
        choices=["suite", "file"],
        default="suite",
        help="Shuffle tests by suite (all tests) or by file (within each test file)",
    )
    group.addoption(
        "--seed",
        type=int,
        default=None,
        help="Set the random seed for test shuffling",
    )


def pytest_configure(config):
    """Configure the plugin when pytest starts."""
    _plugin.configure(config)


def pytest_collection_modifyitems(config, items):
    """Modify the collected test items."""
    if _plugin.enabled:
        _plugin.shuffle_tests(items)
