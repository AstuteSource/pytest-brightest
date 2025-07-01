"""Tests for the test shuffling functionality."""

from pytest_brightest.shuffler import (
    TestShuffler,
    create_shuffler,
    generate_random_seed,
)


class TestTestShuffler:
    """Test cases for the TestShuffler class."""

    def test_init_with_no_seed(self):
        """Test TestShuffler initialization without a seed."""
        shuffler = TestShuffler()
        assert shuffler.get_seed() is None

    def test_init_with_seed(self):
        """Test TestShuffler initialization with a specific seed."""
        seed = 42
        shuffler = TestShuffler(seed)
        assert shuffler.get_seed() == seed

    def test_shuffle_tests_empty_list(self):
        """Test shuffling an empty list returns empty list."""
        shuffler = TestShuffler(42)
        result = shuffler.shuffle_tests([])
        assert result == []

    def test_shuffle_tests_single_item(self):
        """Test shuffling a single item returns the same item."""
        shuffler = TestShuffler(42)
        items = ["test1"]
        result = shuffler.shuffle_tests(items)
        assert result == ["test1"]
        assert result is not items

    def test_shuffle_tests_deterministic_with_seed(self):
        """Test that shuffling is deterministic when using the same seed."""
        items = ["test1", "test2", "test3", "test4"]
        shuffler1 = TestShuffler(42)
        shuffler2 = TestShuffler(42)
        result1 = shuffler1.shuffle_tests(items)
        result2 = shuffler2.shuffle_tests(items)
        assert result1 == result2
        assert set(result1) == set(items)

    def test_shuffle_tests_different_with_different_seeds(self):
        """Test that different seeds produce different shuffling results."""
        items = ["test1", "test2", "test3", "test4", "test5"]
        shuffler1 = TestShuffler(42)
        shuffler2 = TestShuffler(123)
        result1 = shuffler1.shuffle_tests(items)
        result2 = shuffler2.shuffle_tests(items)
        assert result1 != result2
        assert set(result1) == set(items)
        assert set(result2) == set(items)

    def test_set_seed_changes_behavior(self):
        """Test that setting a new seed changes shuffling behavior."""
        items = ["test1", "test2", "test3", "test4"]
        shuffler = TestShuffler(42)
        result1 = shuffler.shuffle_tests(items)
        shuffler.set_seed(123)
        result2 = shuffler.shuffle_tests(items)
        assert shuffler.get_seed() == 123  # noqa: PLR2004
        assert result1 != result2

    def test_shuffle_items_in_place_modifies_original(self, sample_test_items):
        """Test that in-place shuffling modifies the original list."""
        shuffler = TestShuffler(42)
        original_items = sample_test_items.copy()
        shuffler.shuffle_items_in_place(sample_test_items)
        assert set(sample_test_items) == set(original_items)
        assert len(sample_test_items) == len(original_items)

    def test_shuffle_items_in_place_empty_list(self):
        """Test in-place shuffling of empty list does nothing."""
        shuffler = TestShuffler(42)
        items = []
        shuffler.shuffle_items_in_place(items)
        assert items == []


class TestCreateShuffler:
    """Test cases for the create_shuffler factory function."""

    def test_create_shuffler_no_seed(self):
        """Test creating a shuffler without a seed."""
        shuffler = create_shuffler()
        assert isinstance(shuffler, TestShuffler)
        assert shuffler.get_seed() is None

    def test_create_shuffler_with_seed(self):
        """Test creating a shuffler with a specific seed."""
        seed = 42
        shuffler = create_shuffler(seed)
        assert isinstance(shuffler, TestShuffler)
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
