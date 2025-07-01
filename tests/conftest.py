"""Test configuration for pytest-brightest tests."""

import pytest


@pytest.fixture
def sample_test_items():
    """Create a list of sample test items for testing."""

    class MockTestItem:
        def __init__(self, name: str):
            self.name = name
            self.nodeid = f"test_{name}.py::test_{name}"

        def __repr__(self):
            return f"MockTestItem({self.name})"

        def __eq__(self, other):
            return isinstance(other, MockTestItem) and self.name == other.name

    return [
        MockTestItem("alpha"),
        MockTestItem("beta"),
        MockTestItem("gamma"),
        MockTestItem("delta"),
    ]
