"""Tests for the main plugin functionality."""

from pytest_brightest.plugin import (
    BrightestPlugin,
    _plugin,
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_configure,
)
from pytest_brightest.shuffler import ShufflerOfTests


class MockConfig:
    """Mock configuration object for testing."""

    def __init__(self, options=None):
        """Initialize mock config with options."""
        self.options = options or {}

    def getoption(self, name, default=None):
        """Get an option value from the mock configuration."""
        return self.options.get(name, default)


class TestBrightestPlugin:
    """Test cases for the BrightestPlugin class."""

    def test_init_default_state(self):
        """Test plugin initialization with default state."""
        plugin = BrightestPlugin()
        assert plugin.enabled is False
        assert plugin.shuffle_enabled is False
        assert plugin.seed is None
        assert plugin.shuffler is None

    def test_configure_plugin_disabled(self):
        """Test configuration when plugin is disabled."""
        plugin = BrightestPlugin()
        config = MockConfig({"--brightest": False})
        plugin.configure(config)
        assert plugin.enabled is False
        assert plugin.shuffle_enabled is False
        assert plugin.shuffler is None

    def test_configure_plugin_enabled_no_shuffle(self):
        """Test configuration when plugin is enabled but shuffle is disabled."""
        plugin = BrightestPlugin()
        config = MockConfig({"--brightest": True, "--shuffle": False})
        plugin.configure(config)
        assert plugin.enabled is True
        assert plugin.shuffle_enabled is False
        assert plugin.shuffler is None

    def test_configure_plugin_enabled_with_shuffle(self):
        """Test configuration when plugin is enabled with shuffle."""
        plugin = BrightestPlugin()
        config = MockConfig({"--brightest": True, "--shuffle": True})
        plugin.configure(config)
        assert plugin.enabled is True
        assert plugin.shuffle_enabled is True
        assert plugin.shuffler is not None
        assert plugin.seed is not None

    def test_configure_plugin_with_no_shuffle_option(self):
        """Test configuration with explicit no-shuffle option."""
        plugin = BrightestPlugin()
        config = MockConfig(
            {"--brightest": True, "--shuffle": True, "--no-shuffle": True}
        )
        plugin.configure(config)
        assert plugin.enabled is True
        assert plugin.shuffle_enabled is False
        assert plugin.shuffler is None

    def test_configure_plugin_with_custom_seed(self):
        """Test configuration with a custom seed."""
        plugin = BrightestPlugin()
        config = MockConfig(
            {"--brightest": True, "--shuffle": True, "--seed": 42}
        )
        plugin.configure(config)
        assert plugin.enabled is True
        assert plugin.shuffle_enabled is True
        assert plugin.seed == 42  # noqa: PLR2004
        assert plugin.shuffler is not None

    def test_shuffle_tests_when_disabled(self, sample_test_items):
        """Test that shuffle_tests does nothing when shuffling is disabled."""
        plugin = BrightestPlugin()
        plugin.enabled = True
        plugin.shuffle_enabled = False
        original_items = sample_test_items.copy()
        plugin.shuffle_tests(sample_test_items)
        assert sample_test_items == original_items

    def test_shuffle_tests_when_enabled(self, sample_test_items):
        """Test that shuffle_tests modifies items when shuffling is enabled."""
        plugin = BrightestPlugin()
        plugin.enabled = True
        plugin.shuffle_enabled = True
        plugin.shuffler = plugin.shuffler or ShufflerOfTests(42)
        original_items = sample_test_items.copy()
        plugin.shuffle_tests(sample_test_items)
        assert set(sample_test_items) == set(original_items)
        assert len(sample_test_items) == len(original_items)

    def test_shuffle_tests_empty_list(self):
        """Test shuffling an empty list of test items."""
        plugin = BrightestPlugin()
        plugin.enabled = True
        plugin.shuffle_enabled = True
        plugin.shuffler = ShufflerOfTests(42)
        items = []
        plugin.shuffle_tests(items)
        assert items == []


class TestPluginIntegration:
    """Test cases for pytest plugin integration."""

    def test_pytest_addoption_function_exists(self):
        """Test that pytest_addoption function is available."""
        assert callable(pytest_addoption)

    def test_pytest_configure_function_exists(self):
        """Test that pytest_configure function is available."""
        assert callable(pytest_configure)

    def test_pytest_collection_modifyitems_function_exists(self):
        """Test that pytest_collection_modifyitems function is available."""
        assert callable(pytest_collection_modifyitems)

    def test_global_plugin_instance_exists(self):
        """Test that global plugin instance is available."""
        assert _plugin is not None
        assert isinstance(_plugin, BrightestPlugin)
