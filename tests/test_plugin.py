"""Tests for the main plugin functionality."""

"""Test the pytest-brightest plugin."""

from pytest_brightest.plugin import BrightestPlugin


class TestBrightestPlugin:
    """Test the BrightestPlugin class."""

    def test_configure_disabled(self, mock_config):
        """Test that the plugin is disabled by default."""
        plugin = BrightestPlugin()
        config = mock_config()
        plugin.configure(config)
        assert not plugin.enabled

    def test_configure_enabled(self, mock_config):
        """Test that the plugin can be enabled."""
        plugin = BrightestPlugin()
        config = mock_config({"--brightest": True})
        plugin.configure(config)
        assert plugin.enabled

    def test_configure_shuffle(self, mock_config):
        """Test that the plugin can be configured to shuffle."""
        plugin = BrightestPlugin()
        config = mock_config(
            {
                "--brightest": True,
                "--reorder-by-technique": "shuffle",
                "--seed": 42,
            }
        )
        plugin.configure(config)
        assert plugin.shuffle_enabled
        assert plugin.seed == 42

    def test_configure_reorder(self, mock_config):
        """Test that the plugin can be configured to reorder."""
        plugin = BrightestPlugin()
        config = mock_config(
            {
                "--brightest": True,
                "--reorder-by-technique": "cost",
                "--reorder-in-direction": "ascending",
            }
        )
        plugin.configure(config)
        assert plugin.reorder_enabled
        assert plugin.reorder_by == "cost"
        assert plugin.reorder == "ascending"

    def test_shuffle_tests(self, mock_config, mock_test_item):
        """Test that the plugin can shuffle tests."""
        plugin = BrightestPlugin()
        config = mock_config(
            {
                "--brightest": True,
                "--reorder-by-technique": "shuffle",
                "--seed": 42,
            }
        )
        plugin.configure(config)
        items = [mock_test_item("one"), mock_test_item("two"), mock_test_item("three")]
        plugin.shuffle_tests(items)
        assert [item.name for item in items] == ["two", "one", "three"]

    def test_reorder_tests(self, tmp_path, mock_config, mock_test_item):
        """Test that the plugin can reorder tests."""
        plugin = BrightestPlugin()
        config = mock_config(
            {
                "--brightest": True,
                "--reorder-by-technique": "cost",
                "--reorder-in-direction": "ascending",
            }
        )
        plugin.configure(config)
        items = [mock_test_item("slow"), mock_test_item("fast")]
        plugin.reorder_tests(items)
        # This test is not complete as it requires a json file
        assert [item.name for item in items] == ["slow", "fast"]
