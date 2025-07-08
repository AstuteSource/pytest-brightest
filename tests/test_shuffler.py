"""Test the test shuffling functionality for pytest-brightest."""


def test_shuffle_files_in_place_noop():
    """Test shuffle_files_in_place with empty list does nothing."""
    from pytest_brightest.shuffler import ShufflerOfTests

    shuffler = ShufflerOfTests(seed=42)
    items = []
    shuffler.shuffle_files_in_place(items)
    assert items == []


def test_shuffler_init_and_repr():
    from pytest_brightest.shuffler import ShufflerOfTests

    s = ShufflerOfTests()
    assert s.seed is None
    assert hasattr(s, "_random")
    s2 = ShufflerOfTests(123)
    assert s2.seed == 123
    assert hasattr(s2, "_random")


def test_shuffle_tests_none_and_empty():
    from pytest_brightest.shuffler import ShufflerOfTests

    s = ShufflerOfTests()
    assert s.shuffle_tests([]) == []


def test_get_set_seed():
    from pytest_brightest.shuffler import ShufflerOfTests

    s = ShufflerOfTests()
    assert s.get_seed() is None
    s.set_seed(99)
    assert s.get_seed() == 99
    s.set_seed(None)
    assert s.get_seed() is None


def test_shuffle_items_in_place_branch():
    from pytest_brightest.shuffler import ShufflerOfTests

    s = ShufflerOfTests()
    # branch where items is not empty
    items = [1, 2, 3]
    s.shuffle_items_in_place(items)
    assert set(items) == {1, 2, 3}


def test_shuffle_items_by_file_in_place_branch():
    from pytest_brightest.shuffler import ShufflerOfTests

    class Dummy:
        def __init__(self, name):
            self.name = name
            self.fspath = name

    items = [Dummy("a"), Dummy("b")]
    s = ShufflerOfTests()
    s.shuffle_items_by_file_in_place(items)
    assert sorted([i.name for i in items]) == ["a", "b"]


def test_shuffle_files_in_place_branch():
    from pytest_brightest.shuffler import ShufflerOfTests

    class Dummy:
        def __init__(self, name):
            self.name = name
            self.fspath = name

    items = [Dummy("a"), Dummy("b")]
    s = ShufflerOfTests()
    s.shuffle_files_in_place(items)
    assert sorted([i.name for i in items]) == ["a", "b"]


def test_create_shuffler_no_seed():
    from pytest_brightest.shuffler import create_shuffler

    s = create_shuffler()
    assert s.get_seed() is None


def test_shuffler_full_init_and_methods():
    from pytest_brightest.shuffler import ShufflerOfTests

    s = ShufflerOfTests()
    # __init__ with None, with int
    s2 = ShufflerOfTests(123)
    assert s2.seed == 123
    # shuffle_tests with non-empty
    items = [1, 2, 3]
    shuffled = s2.shuffle_tests(items)
    assert set(shuffled) == {1, 2, 3}
    # get_seed/set_seed
    assert s2.get_seed() == 123
    s2.set_seed(456)
    assert s2.get_seed() == 456
    # shuffle_items_in_place with non-empty
    s2.shuffle_items_in_place(items)
    assert set(items) == {1, 2, 3}

    # shuffle_items_by_file_in_place with fallback
    class Dummy:
        def __init__(self, name):
            self.name = name
            self.path = name

    dummies = [Dummy("a"), Dummy("b")]
    s2.shuffle_items_by_file_in_place(dummies)
    assert sorted([d.name for d in dummies]) == ["a", "b"]
    # shuffle_files_in_place with fallback
    s2.shuffle_files_in_place(dummies)
    assert sorted([d.name for d in dummies]) == ["a", "b"]


def test_generate_random_seed_range():
    from pytest_brightest.shuffler import generate_random_seed

    for _ in range(10):
        seed = generate_random_seed()
        assert 1 <= seed <= 2**31 - 1

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
    from pytest_brightest.shuffler import create_shuffler, ShufflerOfTests

    shuffler = create_shuffler(seed=42)
    assert isinstance(shuffler, ShufflerOfTests)
    assert shuffler.get_seed() == 42


def test_generate_random_seed():
    """Test the generate_random_seed function returns an int in range."""
    from pytest_brightest.shuffler import generate_random_seed

    seed = generate_random_seed()
    assert isinstance(seed, int)
    assert 1 <= seed <= 2**31 - 1


def test_shuffle_items_by_file_in_place_path_fallback(mock_test_item):
    """Test shuffle_items_by_file_in_place fallback to PATH/UNKNOWN."""
    from pytest_brightest.shuffler import ShufflerOfTests

    class Dummy:
        def __init__(self, name):
            self.name = name
            self.path = f"/dummy/{name}.py"

    items = [Dummy("a"), Dummy("b")]
    shuffler = ShufflerOfTests(seed=42)
    shuffler.shuffle_items_by_file_in_place(items)
    assert sorted([item.name for item in items]) == ["a", "b"]


def test_shuffle_files_in_place_path_fallback(mock_test_item):
    """Test shuffle_files_in_place fallback to PATH/UNKNOWN."""
    from pytest_brightest.shuffler import ShufflerOfTests

    class Dummy:
        def __init__(self, name):
            self.name = name
            self.path = f"/dummy/{name}.py"

    items = [Dummy("a"), Dummy("b")]
    shuffler = ShufflerOfTests(seed=42)
    shuffler.shuffle_files_in_place(items)
    assert sorted([item.name for item in items]) == ["a", "b"]


def test_shuffle_items_in_place_noop():
    """Test shuffle_items_in_place with empty list does nothing."""
    from pytest_brightest.shuffler import ShufflerOfTests

    shuffler = ShufflerOfTests(seed=42)
    items = []
    shuffler.shuffle_items_in_place(items)
    assert items == []


def test_shuffle_items_by_file_in_place_noop():
    """Test shuffle_items_by_file_in_place with empty list does nothing."""
    from pytest_brightest.shuffler import ShufflerOfTests

    shuffler = ShufflerOfTests(seed=42)
    items = []
    shuffler.shuffle_items_by_file_in_place(items)
    assert items == []


def test_shuffle_files_in_place_noop():
    """Test shuffle_files_in_place with empty list does nothing."""
    from pytest_brightest.shuffler import ShufflerOfTests

    shuffler = ShufflerOfTests(seed=42)
    items = []
    shuffler.shuffle_files_in_place(items)
    assert items == []
