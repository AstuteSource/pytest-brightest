"""Shared test fixtures and utilities."""

import pytest


class MockTestItem:
    """Mock test item for testing purposes."""

    def __init__(self, name: str):
        """Initialize mock test item with a name."""
        self.name = name

    def __str__(self) -> str:
        """Return string representation of the test item."""
        return f"MockTestItem({self.name})"

    def __repr__(self) -> str:
        """Return detailed representation of the test item."""
        return f"MockTestItem({self.name})"

    def __eq__(self, other) -> bool:
        """Check equality based on name."""
        if not isinstance(other, MockTestItem):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        """Make the object hashable based on name."""
        return hash(self.name)


@pytest.fixture
def sample_test_items():
    """Provide a list of sample test items for testing."""
    return [
        MockTestItem("gamma"),
        MockTestItem("beta"),
        MockTestItem("delta"),
        MockTestItem("alpha"),
    ]
