"""Test the test shuffling functionality for pytest-brightest."""

# ruff: noqa: PLR2004

from pytest_brightest.shuffler import ShufflerOfTests, create_shuffler


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

    def test_shuffle_tests_empty_list(self):
        """Test that shuffling an empty list returns an empty list."""
        shuffler = ShufflerOfTests(seed=42)
        items = []
        shuffled_items = shuffler.shuffle_tests(items)
        assert shuffled_items == []

    def test_shuffle_tests(self, mock_test_item):
        """Test that the shuffler can shuffle tests."""
        shuffler = ShufflerOfTests(seed=42)
        items = [
            mock_test_item("one"),
            mock_test_item("two"),
            mock_test_item("three"),
        ]
        shuffled_items = shuffler.shuffle_tests(items)
        assert [item.name for item in shuffled_items] == [
            "two",
            "one",
            "three",
        ]

    def test_shuffle_items_in_place_empty_list(self):
        """Test that the shuffler can shuffle an empty list in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = []
        shuffler.shuffle_items_in_place(items)
        assert items == []

    def test_shuffle_items_in_place(self, mock_test_item):
        """Test that the shuffler can shuffle items in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = [
            mock_test_item("one"),
            mock_test_item("two"),
            mock_test_item("three"),
        ]
        shuffler.shuffle_items_in_place(items)
        assert [item.name for item in items] == ["two", "one", "three"]

    def test_shuffle_items_by_file_in_place_empty_list(self):
        """Test that the shuffler can shuffle an empty list by file in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = []
        shuffler.shuffle_items_by_file_in_place(items)
        assert items == []

    def test_shuffle_items_by_file_in_place_single_file(self, mock_test_item):
        """Test that the shuffler can shuffle a single file by file in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = [
            mock_test_item("file1_test1"),
            mock_test_item("file1_test2"),
        ]
        for item in items:
            item.fspath = "/path/to/file1.py"
        shuffler.shuffle_items_by_file_in_place(items)
        assert [item.name for item in items] == ["file1_test2", "file1_test1"]

    def test_shuffle_items_by_file_in_place(self, mock_test_item):
        """Test that the shuffler can shuffle items by file in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = [
            mock_test_item("file1_test1"),
            mock_test_item("file1_test2"),
            mock_test_item("file2_test1"),
            mock_test_item("file2_test2"),
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

    def test_shuffle_files_in_place_empty_list(self):
        """Test that the shuffler can shuffle an empty list of files in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = []
        shuffler.shuffle_files_in_place(items)
        assert items == []

    def test_shuffle_files_in_place_single_file(self, mock_test_item):
        """Test that the shuffler can shuffle a single file in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = [
            mock_test_item("file1_test1"),
            mock_test_item("file1_test2"),
        ]
        for item in items:
            item.fspath = "/path/to/file1.py"
        shuffler.shuffle_files_in_place(items)
        assert [item.name for item in items] == ["file1_test1", "file1_test2"]

    def test_shuffle_files_in_place(self, mock_test_item):
        """Test that the shuffler can shuffle files in place."""
        shuffler = ShufflerOfTests(seed=42)
        items = [
            mock_test_item("file1_test1"),
            mock_test_item("file1_test2"),
            mock_test_item("file2_test1"),
            mock_test_item("file2_test2"),
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
