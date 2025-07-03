"""Tests for the main plugin functionality."""

# ruff: noqa: PLR2004

from pytest_brightest.plugin import (
    BrightestPlugin,
    _plugin,
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_configure,
    pytest_sessionfinish,
)


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
        items = [
            mock_test_item("one"),
            mock_test_item("two"),
            mock_test_item("three"),
        ]
        plugin.shuffle_tests(items)
        assert [item.name for item in items] == ["two", "one", "three"]

    def test_reorder_tests(self, tmp_path, mock_config, mock_test_item):
        """Test that the plugin can reorder tests."""
        _ = tmp_path
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


class TestHooks:
    """A container for all the tests of the hooks."""

    def test_pytest_addoption(self, mocker):
        """Test that the command line options are added."""
        parser = mocker.MagicMock()
        parser.getgroup.return_value = mocker.MagicMock()

        pytest_addoption(parser)
        assert parser.getgroup.called
        assert parser.getgroup.return_value.addoption.call_count == 5

    def test_pytest_configure(self, mocker, mock_config):
        """Test that the plugin is configured."""
        mocker.patch.object(_plugin, "configure")
        config = mock_config({"--brightest": True})
        pytest_configure(config)
        _plugin.configure.assert_called_once_with(config)  # type: ignore

    def test_pytest_collection_modifyitems(
        self, mocker, mock_config, mock_test_item
    ):
        """Test that pytest_collection_modifyitems modifies the items."""
        # Mock the _plugin instance and its methods
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.reorder_enabled = True
        mock_plugin.shuffle_enabled = True


        config = mock_config()
        items = [mock_test_item("one"), mock_test_item("two")]
        pytest_collection_modifyitems(config, items)

        mock_plugin.reorder_tests.assert_called_once_with(items)
        mock_plugin.shuffle_tests.assert_called_once_with(items)

    def test_pytest_sessionfinish_no_json_file(self, mocker, mock_config):
        """Test that pytest_sessionfinish handles no JSON file."""
        _ = mock_config
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.brightest_json_file = "non_existent.json"

        mocker.patch("pathlib.Path.exists", return_value=False)
        mock_console_print = mocker.patch(
            "pytest_brightest.plugin.console.print"
        )


        pytest_sessionfinish(mocker.MagicMock(), 0)

        assert mock_console_print.call_count == 3
        mock_console_print.assert_any_call(
            ":high_brightness: pytest-brightest: There is no JSON file created by pytest-json-report"
        )

    def test_pytest_sessionfinish_with_json_file(self, mocker, mock_config):
        """Test that pytest_sessionfinish processes JSON file."""
        _ = mock_config
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.brightest_json_file = "existent.json"
        mock_plugin.technique = "cost"
        mock_plugin.focus = "tests-across-modules"
        mock_plugin.direction = "ascending"
        mock_plugin.seed = 123

        mock_path_exists = mocker.patch(
            "pathlib.Path.exists", return_value=True
        )
        mock_json_load = mocker.patch("json.load", return_value={"tests": []})
        mock_json_dump = mocker.patch("json.dump")
        mock_console_print = mocker.patch(
            "pytest_brightest.plugin.console.print"
        )

        mock_file_handle = mocker.MagicMock()
        mocker.patch("pathlib.Path.open", return_value=mock_file_handle)
        mocker.patch(
            "pathlib.Path.stat", return_value=mocker.MagicMock(st_size=100)
        )

        mock_session = mocker.MagicMock()
        mock_session.items = []


        pytest_sessionfinish(mock_session, 0)

        mock_path_exists.assert_called_once_with()
        mock_json_load.assert_called_once_with(
            mock_file_handle.__enter__.return_value
        )
        mock_json_dump.assert_called_once()
        assert mock_console_print.call_count == 3
        mock_console_print.assert_any_call(
            f":flashlight: pytest-brightest: pytest-json-report detected at {mock_plugin.brightest_json_file}"
        )
