"""Test shuffling functionality for pytest-brightest."""

import random
from typing import TYPE_CHECKING, Dict, List, Optional

from .constants import FSPATH, PATH, UNKNOWN

if TYPE_CHECKING:
    from _pytest.nodes import Item  # type: ignore


class ShufflerOfTests:
    """Handles test shuffling with configurable random seeding."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the shuffler with an optional random seed."""
        self.seed = seed
        # create a new random number generator to ensure that the shuffling
        # is independent of the global random number generator
        self._random = random.Random(seed)

    def shuffle_tests(self, items: List["Item"]) -> List["Item"]:
        """Shuffle a list of test items using the configured random seed."""
        # it is not possible to shuffle an empty list of items
        if not items:
            return items
        # create a copy of the list of items to avoid modifying the original
        shuffled_items = items.copy()
        # shuffle the list of items in place using the random number generator
        self._random.shuffle(shuffled_items)
        return shuffled_items

    def get_seed(self) -> Optional[int]:
        """Get the current random seed."""
        return self.seed

    def set_seed(self, seed: Optional[int]) -> None:
        """Set a new random seed and reinitialize the random generator."""
        self.seed = seed
        # create a new random number generator to ensure that the shuffling
        # is independent of the global random number generator
        self._random = random.Random(seed)

    def shuffle_items_in_place(self, items: List["Item"]) -> None:
        """Shuffle a list of items in place using the configured random seed."""
        # it is not possible to shuffle an empty list of items
        if items:
            # shuffle the list of items in place using the random number generator
            self._random.shuffle(items)

    def shuffle_items_by_file_in_place(self, items: List["Item"]) -> None:
        """Shuffle test items within each file while preserving file order."""
        # it is not possible to shuffle an empty list of items
        if not items:
            return
        # create a dictionary to group items by their file path
        file_groups: Dict[str, List["Item"]] = {}
        # create a list to maintain the order of the files
        file_order = []
        # iterate over each item and group it by its file path
        for item in items:
            # pytest items have an fspath attribute that contains the path to the file
            # and we can also use the path attribute as a fallback
            file_path = getattr(
                item, FSPATH, str(getattr(item, PATH, UNKNOWN))
            )
            file_path_str = str(file_path)
            # if the file path is not already in the file_groups dictionary,
            # add it and also add it to the file_order list
            if file_path_str not in file_groups:
                file_groups[file_path_str] = []
                file_order.append(file_path_str)
            # add the item to the list of items for the current file path
            file_groups[file_path_str].append(item)
        # clear the original list of items so that it can be repopulated
        items.clear()
        # iterate over the file_order list to preserve the original file order
        for file_path in file_order:
            # get the list of items for the current file path
            file_items = file_groups[file_path]
            # shuffle the list of items for the current file path in place
            self._random.shuffle(file_items)
            # add the shuffled items to the original list of items
            items.extend(file_items)

    def shuffle_files_in_place(self, items: List["Item"]) -> None:
        """Shuffle the order of files while preserving test order within each file."""
        # it is not possible to shuffle an empty list of items
        if not items:
            return
        # create a dictionary to group items by their file path
        file_groups: Dict[str, List["Item"]] = {}
        # create a list to maintain the order of the files
        file_order = []
        # iterate over each item and group it by its file path
        for item in items:
            # pytest items have an fspath attribute that contains the path to the file
            # and we can also use the path attribute as a fallback
            file_path = getattr(
                item, FSPATH, str(getattr(item, PATH, UNKNOWN))
            )
            file_path_str = str(file_path)
            # if the file path is not already in the file_groups dictionary,
            # add it and also add it to the file_order list
            if file_path_str not in file_groups:
                file_groups[file_path_str] = []
                file_order.append(file_path_str)
            # add the item to the list of items for the current file path
            file_groups[file_path_str].append(item)
        # shuffle the order of the files in place
        self._random.shuffle(file_order)
        # clear the original list of items so that it can be repopulated
        items.clear()
        # iterate over the shuffled file_order list
        for file_path in file_order:
            # add the items for the current file path to the original list
            items.extend(file_groups[file_path])


def create_shuffler(seed: Optional[int] = None) -> ShufflerOfTests:
    """Define a factory function to create a TestItemShuffler instance."""
    return ShufflerOfTests(seed)


def generate_random_seed() -> int:
    """Generate a random seed for test shuffling."""
    # the upper bound for the random seed is 2**31 - 1 because it is a
    # common value for the maximum value of a 32-bit signed integer
    return random.randint(1, 2**31 - 1)
