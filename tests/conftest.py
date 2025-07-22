"""Shared test fixtures and utilities."""

import pytest


class MockTestItem:
    """Mock test item for testing purposes."""

    def __init__(
        self,
        name: str,
        file_path: str = "test_file.py",
        outcome: str = "passed",
    ):
        """Initialize mock test item with a name and file path."""
        self.name = name
        self.fspath = file_path
        self.nodeid = name
        self.outcome = outcome

    def __str__(self) -> str:
        """Return string representation of the test item."""
        return f"MockTestItem({self.name})"

    def __repr__(self) -> str:
        """Return detailed representation of the test item."""
        return f"MockTestItem({self.name})"

    def __eq__(self, other) -> bool:
        """Check equality based on name and file path."""
        if not isinstance(other, MockTestItem):
            return False
        return self.name == other.name and self.fspath == other.fspath

    def __hash__(self) -> int:
        """Make the object hashable based on name and file path."""
        return hash((self.name, self.fspath))


class MockConfig:
    """A mock config object."""

    def __init__(self, options=None):
        """Initialize the mock config."""
        self.options = options or {}

    def getoption(self, name, default=None):
        """Get an option from the mock config."""
        # provide default values for repeat options if not specified
        defaults = {
            "--repeat": 1,
            "--repeat-failed": 0,
            "--reorder-by-technique": None,
            "--reorder-by-focus": None,
            "--reorder-in-direction": None,
        }
        if name in defaults and name not in self.options:
            return defaults[name]
        return self.options.get(name, default)


@pytest.fixture
def mock_test_item():
    """Provide a MockTestItem instance as a fixture."""
    return MockTestItem


@pytest.fixture
def mock_config():
    """Provide a MockConfig instance as a fixture."""
    return MockConfig


@pytest.fixture
def sample_test_items():
    """Provide a list of sample test items for testing."""
    return [
        MockTestItem("gamma"),
        MockTestItem("beta"),
        MockTestItem("delta"),
        MockTestItem("alpha"),
    ]


@pytest.fixture
def multi_file_test_items():
    """Provide test items from multiple files for testing file-based shuffling."""
    return [
        MockTestItem("test_a1", "test_file_a.py"),
        MockTestItem("test_a2", "test_file_a.py"),
        MockTestItem("test_a3", "test_file_a.py"),
        MockTestItem("test_b1", "test_file_b.py"),
        MockTestItem("test_b2", "test_file_b.py"),
        MockTestItem("test_c1", "test_file_c.py"),
        MockTestItem("test_c2", "test_file_c.py"),
        MockTestItem("test_c3", "test_file_c.py"),
        MockTestItem("test_c4", "test_file_c.py"),
    ]
