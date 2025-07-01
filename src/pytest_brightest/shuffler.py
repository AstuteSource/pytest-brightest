"""Test shuffling functionality for pytest-brightest."""

import random
from typing import Any, List, Optional


class TestShuffler:
    """Handles test shuffling with configurable random seeding."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the shuffler with an optional random seed."""
        self.seed = seed
        self._random = random.Random(seed)

    def shuffle_tests(self, items: List[Any]) -> List[Any]:
        """Shuffle a list of test items using the configured random seed."""
        if not items:
            return items
        shuffled_items = items.copy()
        self._random.shuffle(shuffled_items)
        return shuffled_items

    def get_seed(self) -> Optional[int]:
        """Get the current random seed."""
        return self.seed

    def set_seed(self, seed: Optional[int]) -> None:
        """Set a new random seed and reinitialize the random generator."""
        self.seed = seed
        self._random = random.Random(seed)

    def shuffle_items_in_place(self, items: List[Any]) -> None:
        """Shuffle a list of items in place using the configured random seed."""
        if items:
            self._random.shuffle(items)


def create_shuffler(seed: Optional[int] = None) -> TestShuffler:
    """Define a factory function to create a TestShuffler instance."""
    return TestShuffler(seed)


def generate_random_seed() -> int:
    """Generate a random seed for test shuffling."""
    return random.randint(1, 2**31 - 1)
