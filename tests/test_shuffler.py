"""Test the test shuffling functionality for pytest-brightest."""

import random
from pathlib import Path

from pytest_brightest.shuffler import ShufflerOfTests, create_shuffler

from .utils import MockTestItem


class TestShufflerOfTests:
    """Test the ShufflerOfTests class."""

    def test_init_with_seed(self):
        """Test that the shuffler can be initialized with a seed."""
        shuffler = ShufflerOfTests(seed=42)
        assert shuffler.get_seed() == 42

    def test_init_without_seed(self):
        """Test that the shuffler can be initialized without a seed."""
        shuffler = ShufflerOfTests()
        assert shuffler.get_seed() is None

    def test_set_seed(self):
        """Test that the seed can be set."""
        shuffler = ShufflerOfTests()
        shuffler.set_seed(42)
        assert shuffler.get_seed() == 42

    def test_shuffle_tests(self):
        """Test that the shuffler can shuffle tests."""
        shuffler = ShufflerOfTests(seed=42)
        items = [MockTestItem("one"), MockTestItem("two"), MockTestItem("three")]
        shuffled_items = shuffler.shuffle_tests(items)
        assert [item.name for item in shuffled_items] == ["two", "one", "three"]

    def test_shuffle_items_in_place(self):
        """Test that the shuffler can shuffle items in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = [MockTestItem("one"), MockTestItem("two"), MockTestItem("three")]
        shuffler.shuffle_items_in_place(items)
        assert [item.name for item in items] == ["two", "one", "three"]

    def test_shuffle_items_by_file_in_place(self):
        """Test that the shuffler can shuffle items by file in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = [
            MockTestItem("file1_test1"),
            MockTestItem("file1_test2"),
            MockTestItem("file2_test1"),
            MockTestItem("file2_test2"),
        ]
        # Mock the fspath attribute
        for item in items:
            if "file1" in item.name:
                item.fspath = "/path/to/file1.py"
            else:
                item.fspath = "/path/to/file2.py"

        shuffler.shuffle_items_by_file_in_place(items)
        assert [item.name for item in items] == [
            "file1_test2",
            "file1_test1",
            "file2_test2",
            "file2_test1",
        ]

    def test_shuffle_files_in_place(self):
        """Test that the shuffler can shuffle files in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = [
            MockTestItem("file1_test1"),
            MockTestItem("file1_test2"),
            MockTestItem("file2_test1"),
            MockTestItem("file2_test2"),
        ]
        # Mock the fspath attribute
        for item in items:
            if "file1" in item.name:
                item.fspath = "/path/to/file1.py"
            else:
                item.fspath = "/path/to/file2.py"

        shuffler.shuffle_files_in_place(items)
        assert [item.name for item in items] == [
            "file2_test1",
            "file2_test2",
            "file1_test1",
            "file1_test2",
        ]


def test_create_shuffler():
    """Test the create_shuffler function."""
    shuffler = create_shuffler(seed=42)
    assert isinstance(shuffler, ShufflerOfTests)
    assert shuffler.get_seed() == 42
