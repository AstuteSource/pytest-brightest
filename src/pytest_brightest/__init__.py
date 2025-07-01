"""Default package for pytest-brightest."""

from .plugin import BrightestPlugin
from .shuffler import TestShuffler

__version__ = "0.1.0"
__all__ = ["BrightestPlugin", "TestShuffler"]
