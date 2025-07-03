"""Test shuffling functionality for pytest-brightest."""

import random
from typing import Any, Dict, List, Optional


class ShufflerOfTests:
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

    def shuffle_items_by_file_in_place(self, items: List[Any]) -> None:
        """Shuffle test items within each file while preserving file order."""
        if not items:
            return
        file_groups: Dict[str, List[Any]] = {}
        file_order = []
        for item in items:
            file_path = getattr(
                item, "fspath", str(getattr(item, "path", "unknown"))
            )
            file_path_str = str(file_path)
            if file_path_str not in file_groups:
                file_groups[file_path_str] = []
                file_order.append(file_path_str)
            file_groups[file_path_str].append(item)
        items.clear()
        for file_path in file_order:
            file_items = file_groups[file_path]
            self._random.shuffle(file_items)
            items.extend(file_items)

    def shuffle_files_in_place(self, items: List[Any]) -> None:
        """Shuffle the order of files while preserving test order within each file."""
        if not items:
            return
        file_groups: Dict[str, List[Any]] = {}
        file_order = []
        for item in items:
            file_path = getattr(
                item, "fspath", str(getattr(item, "path", "unknown"))
            )
            file_path_str = str(file_path)
            if file_path_str not in file_groups:
                file_groups[file_path_str] = []
                file_order.append(file_path_str)
            file_groups[file_path_str].append(item)
        self._random.shuffle(file_order)
        items.clear()
        for file_path in file_order:
            items.extend(file_groups[file_path])


def create_shuffler(seed: Optional[int] = None) -> ShufflerOfTests:
    """Define a factory function to create a TestItemShuffler instance."""
    return ShufflerOfTests(seed)


def generate_random_seed() -> int:
    """Generate a random seed for test shuffling."""
    return random.randint(1, 2**31 - 1)
