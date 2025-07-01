"""Tests for the test shuffling functionality."""

from pytest_brightest.shuffler import (
    ShufflerOfTests,
    create_shuffler,
    generate_random_seed,
)


class TestShufflerOfTests:
    """Test cases for the ShufflerOfTests class."""

    def test_init_with_no_seed(self):
        """Test ShufflerOfTests initialization without a seed."""
        shuffler = ShufflerOfTests()
        assert shuffler.get_seed() is None

    def test_init_with_seed(self):
        """Test ShufflerOfTests initialization with a specific seed."""
        seed = 42
        shuffler = ShufflerOfTests(seed)
        assert shuffler.get_seed() == seed

    def test_shuffle_tests_empty_list(self):
        """Test shuffling an empty list returns empty list."""
        shuffler = ShufflerOfTests(42)
        result = shuffler.shuffle_tests([])
        assert result == []

    def test_shuffle_tests_single_item(self):
        """Test shuffling a single item returns the same item."""
        shuffler = ShufflerOfTests(42)
        items = ["test1"]
        result = shuffler.shuffle_tests(items)
        assert result == ["test1"]
        assert result is not items

    def test_shuffle_tests_deterministic_with_seed(self):
        """Test that shuffling is deterministic when using the same seed."""
        items = ["test1", "test2", "test3", "test4"]
        shuffler1 = ShufflerOfTests(42)
        shuffler2 = ShufflerOfTests(42)
        result1 = shuffler1.shuffle_tests(items)
        result2 = shuffler2.shuffle_tests(items)
        assert result1 == result2
        assert set(result1) == set(items)

    def test_shuffle_tests_different_with_different_seeds(self):
        """Test that different seeds produce different shuffling results."""
        items = ["test1", "test2", "test3", "test4", "test5"]
        shuffler1 = ShufflerOfTests(42)
        shuffler2 = ShufflerOfTests(123)
        result1 = shuffler1.shuffle_tests(items)
        result2 = shuffler2.shuffle_tests(items)
        assert result1 != result2
        assert set(result1) == set(items)
        assert set(result2) == set(items)

    def test_set_seed_changes_behavior(self):
        """Test that setting a new seed changes shuffling behavior."""
        items = ["test1", "test2", "test3", "test4"]
        shuffler = ShufflerOfTests(42)
        result1 = shuffler.shuffle_tests(items)
        shuffler.set_seed(123)
        result2 = shuffler.shuffle_tests(items)
        assert shuffler.get_seed() == 123  # noqa: PLR2004
        assert result1 != result2

    def test_shuffle_items_in_place_modifies_original(self, sample_test_items):
        """Test that in-place shuffling modifies the original list."""
        shuffler = ShufflerOfTests(42)
        original_items = sample_test_items.copy()
        shuffler.shuffle_items_in_place(sample_test_items)
        assert set(sample_test_items) == set(original_items)
        assert len(sample_test_items) == len(original_items)

    def test_shuffle_items_in_place_empty_list(self):
        """Test in-place shuffling of empty list does nothing."""
        shuffler = ShufflerOfTests(42)
        items = []
        shuffler.shuffle_items_in_place(items)
        assert items == []

    def test_shuffle_items_by_file_in_place_empty_list(self):
        """Test file-based shuffling of empty list does nothing."""
        shuffler = ShufflerOfTests(42)
        items = []
        shuffler.shuffle_items_by_file_in_place(items)
        assert items == []

    def test_shuffle_items_by_file_in_place_single_file(self, sample_test_items):
        """Test file-based shuffling with items from a single file."""
        shuffler = ShufflerOfTests(42)
        original_items = sample_test_items.copy()
        shuffler.shuffle_items_by_file_in_place(sample_test_items)
        assert set(sample_test_items) == set(original_items)
        assert len(sample_test_items) == len(original_items)

    def test_shuffle_items_by_file_in_place_multiple_files(self, multi_file_test_items):
        """Test file-based shuffling with items from multiple files."""
        shuffler = ShufflerOfTests(42)
        original_items = multi_file_test_items.copy()
        shuffler.shuffle_items_by_file_in_place(multi_file_test_items)
        assert set(multi_file_test_items) == set(original_items)
        assert len(multi_file_test_items) == len(original_items)
        file_a_items = [item for item in multi_file_test_items if item.fspath == "test_file_a.py"]
        file_b_items = [item for item in multi_file_test_items if item.fspath == "test_file_b.py"]
        file_c_items = [item for item in multi_file_test_items if item.fspath == "test_file_c.py"]
        assert len(file_a_items) == 3  # noqa: PLR2004
        assert len(file_b_items) == 2  # noqa: PLR2004
        assert len(file_c_items) == 4  # noqa: PLR2004

    def test_shuffle_items_by_file_preserves_file_order(self, multi_file_test_items):
        """Test that file-based shuffling preserves the order of files."""
        shuffler = ShufflerOfTests(42)
        original_file_order = []
        current_file = None
        for item in multi_file_test_items:
            if item.fspath != current_file:
                current_file = item.fspath
                original_file_order.append(current_file)
        shuffler.shuffle_items_by_file_in_place(multi_file_test_items)
        shuffled_file_order = []
        current_file = None
        for item in multi_file_test_items:
            if item.fspath != current_file:
                current_file = item.fspath
                shuffled_file_order.append(current_file)
        assert shuffled_file_order == original_file_order

    def test_shuffle_items_by_file_deterministic_with_seed(self, multi_file_test_items):
        """Test that file-based shuffling is deterministic with the same seed."""
        items1 = multi_file_test_items.copy()
        items2 = multi_file_test_items.copy()
        shuffler1 = ShufflerOfTests(42)
        shuffler2 = ShufflerOfTests(42)
        shuffler1.shuffle_items_by_file_in_place(items1)
        shuffler2.shuffle_items_by_file_in_place(items2)
        assert items1 == items2


class TestCreateShuffler:
    """Test cases for the create_shuffler factory function."""

    def test_create_shuffler_no_seed(self):
        """Test creating a shuffler without a seed."""
        shuffler = create_shuffler()
        assert isinstance(shuffler, ShufflerOfTests)
        assert shuffler.get_seed() is None

    def test_create_shuffler_with_seed(self):
        """Test creating a shuffler with a specific seed."""
        seed = 42
        shuffler = create_shuffler(seed)
        assert isinstance(shuffler, ShufflerOfTests)
        assert shuffler.get_seed() == seed


class TestGenerateRandomSeed:
    """Test cases for the generate_random_seed function."""

    def test_generate_random_seed_returns_int(self):
        """Test that generate_random_seed returns an integer."""
        seed = generate_random_seed()
        assert isinstance(seed, int)
        assert 1 <= seed <= 2**31 - 1

    def test_generate_random_seed_different_values(self):
        """Test that multiple calls return different values."""
        seeds = [generate_random_seed() for _ in range(10)]
        assert len(set(seeds)) > 1
