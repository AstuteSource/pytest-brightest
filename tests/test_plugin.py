"""Tests for the main plugin functionality."""

# ruff: noqa: PLR2004

from pytest_brightest.plugin import (
    BrightestPlugin,
    _get_brightest_data,
    _plugin,
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_configure,
    pytest_generate_tests,
    pytest_runtest_logreport,
    pytest_runtest_protocol,
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

    def test_configure_enabled(self, mock_config, mocker):
        """Test that the plugin can be enabled."""
        mocker.patch("pytest_brightest.plugin.console.print")
        mocker.patch(
            "pytest_brightest.plugin.setup_json_report_plugin",
            return_value=True,
        )
        plugin = BrightestPlugin()
        config = mock_config({"--brightest": True})
        plugin.configure(config)
        assert plugin.enabled

    def test_configure_shuffle(self, mock_config, mocker):
        """Test that the plugin can be configured to shuffle."""
        mocker.patch("pytest_brightest.plugin.console.print")
        mocker.patch(
            "pytest_brightest.plugin.setup_json_report_plugin",
            return_value=True,
        )
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

    def test_configure_reorder(self, mock_config, mocker):
        """Test that the plugin can be configured to reorder."""
        mocker.patch("pytest_brightest.plugin.console.print")
        mocker.patch(
            "pytest_brightest.plugin.setup_json_report_plugin",
            return_value=True,
        )
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

    def test_shuffle_tests(self, mock_config, mock_test_item, mocker):
        """Test that the plugin can shuffle tests."""
        mocker.patch("pytest_brightest.plugin.console.print")
        mocker.patch(
            "pytest_brightest.plugin.setup_json_report_plugin",
            return_value=True,
        )
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

    def test_reorder_tests(
        self, tmp_path, mock_config, mock_test_item, mocker
    ):
        """Test that the plugin can reorder tests."""
        mocker.patch("pytest_brightest.plugin.console.print")
        mocker.patch(
            "pytest_brightest.plugin.setup_json_report_plugin",
            return_value=True,
        )
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
        # this test is not complete as it requires a json file
        assert [item.name for item in items] == ["slow", "fast"]

    def test_configure_shuffle_with_direction_warning(
        self, mock_config, mocker
    ):
        """Test that a warning is issued when shuffling with a direction."""
        mock_console_print = mocker.patch(
            "pytest_brightest.plugin.console.print"
        )
        mocker.patch(
            "pytest_brightest.plugin.setup_json_report_plugin",
            return_value=True,
        )
        plugin = BrightestPlugin()
        config = mock_config(
            {
                "--brightest": True,
                "--reorder-by-technique": "shuffle",
                "--reorder-in-direction": "descending",
            }
        )
        plugin.configure(config)
        mock_console_print.assert_any_call(
            ":high_brightness: pytest-brightest: Warning: --reorder-in-direction is ignored when --reorder-by-technique is 'shuffle'"
        )

    def test_configure_json_report_setup_fails(self, mock_config, mocker):
        """Test that a warning is issued when json report setup fails."""
        mock_console_print = mocker.patch(
            "pytest_brightest.plugin.console.print"
        )
        mocker.patch(
            "pytest_brightest.plugin.setup_json_report_plugin",
            return_value=False,
        )
        plugin = BrightestPlugin()
        config = mock_config({"--brightest": True})
        plugin.configure(config)
        mock_console_print.assert_any_call(
            ":high_brightness: pytest-brightest: pytest-json-report setup failed, certain features disabled"
        )


def test_brightestplugin_record_test_failure():
    """Test recording test failures in BrightestPlugin."""
    plugin = BrightestPlugin()
    plugin.record_test_failure("mod1::test1")
    assert plugin.current_session_failures["mod1"] == 1
    plugin.record_test_failure("mod1::test1")
    assert plugin.current_session_failures["mod1"] == 2
    plugin.record_test_failure("")
    # Should not raise


def test_brightestplugin_store_session_items(mock_test_item):
    """Test storing session items in BrightestPlugin."""
    plugin = BrightestPlugin()
    items = [mock_test_item("a"), mock_test_item("b")]
    plugin.store_session_items(items)
    assert plugin.session_items == items


class TestHooks:
    """A container for all the tests of the hooks."""

    def test_pytest_addoption(self, mocker):
        """Test that the command line options are added."""
        parser = mocker.MagicMock()
        parser.getgroup.return_value = mocker.MagicMock()
        pytest_addoption(parser)
        assert parser.getgroup.called
        assert parser.getgroup.return_value.addoption.call_count == 7

    def test_pytest_configure(self, mocker, mock_config):
        """Test that the plugin is configured."""
        mocker.patch.object(_plugin, "configure")
        config = mock_config({"--brightest": True})
        pytest_configure(config)
        _plugin.configure.assert_called_once_with(config)  # type: ignore

    def test_pytest_collection_modifyitems_first_strategy(
        self, mocker, mock_config, mock_test_item
    ):
        """Test that pytest_collection_modifyitems modifies the items."""
        # mock the _plugin instance and its methods
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.reorder_enabled = True
        mock_plugin.shuffle_enabled = False
        mock_plugin.technique = None
        config = mock_config()
        items = [mock_test_item("one"), mock_test_item("two")]
        pytest_collection_modifyitems(config, items)
        mock_plugin.reorder_tests.assert_called_once_with(items)

    def test_pytest_collection_modifyitems_second_strategy(
        self, mocker, mock_config, mock_test_item
    ):
        """Test that pytest_collection_modifyitems modifies the items."""
        # mock the _plugin instance and its methods
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.reorder_enabled = False
        mock_plugin.shuffle_enabled = True
        mock_plugin.technique = None
        config = mock_config()
        items = [mock_test_item("one"), mock_test_item("two")]
        pytest_collection_modifyitems(config, items)
        mock_plugin.shuffle_tests.assert_called_once_with(items)

    def test_pytest_collection_modifyitems_default_to_reorder(
        self, mocker, mock_config, mock_test_item
    ):
        """Test that pytest_collection_modifyitems modifies the items."""
        # mock the _plugin instance and its methods
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.reorder_enabled = True
        mock_plugin.shuffle_enabled = True
        mock_plugin.technique = None
        config = mock_config()
        items = [mock_test_item("one"), mock_test_item("two")]
        pytest_collection_modifyitems(config, items)
        mock_plugin.reorder_tests.assert_called_once_with(items)

    def test_pytest_collection_modifyitems_reorder_and_shuffle_prefers_reorder(
        self, mocker, mock_config, mock_test_item
    ):
        """Test that reordering is preferred when reordering and shuffling are enabled."""
        # mock the _plugin instance and its methods
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.reorder_enabled = True
        mock_plugin.shuffle_enabled = True
        mock_plugin.technique = None
        config = mock_config()
        items = [mock_test_item("one"), mock_test_item("two")]
        pytest_collection_modifyitems(config, items)
        mock_plugin.reorder_tests.assert_called_once_with(items)
        mock_plugin.shuffle_tests.assert_not_called()

    def test_pytest_runtest_logreport(self, mocker):
        """Test that pytest_runtest_logreport records failures."""
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.technique = "failure"
        report = mocker.MagicMock()
        report.failed = True
        report.when = "call"
        report.nodeid = "test_node"
        pytest_runtest_logreport(report)
        mock_plugin.record_test_failure.assert_called_once_with("test_node")

    def test_pytest_sessionfinish_no_json_file(self, mocker, mock_config):
        """Test that pytest_sessionfinish handles no JSON file."""
        _ = mock_config
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.technique = None
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
        mock_plugin.historical_brightest_data = []
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
        # mock _plugin.reorderer directly
        mock_plugin.reorderer = mocker.MagicMock()
        mock_plugin.reorderer.get_test_total_duration.return_value = (
            0.5  # example return value
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

    def test_pytest_sessionfinish_failure_module_counts(
        self, mocker, mock_config, tmp_path, mock_test_item
    ):
        """Test that pytest_sessionfinish saves module failure counts for failure reordering."""
        _ = mock_config
        mock_plugin = mocker.patch(
            "pytest_brightest.plugin._plugin", autospec=True
        )
        mock_plugin.enabled = True
        mock_plugin.brightest_json_file = str(tmp_path / "report.json")
        mock_plugin.technique = "failure"
        mock_plugin.focus = "modules-within-suite"
        mock_plugin.direction = "descending"
        mock_plugin.current_session_failures = {
            "module_a.py": 1,
            "module_b.py": 2,
            "module_c.py": 0,
        }
        mock_plugin.historical_brightest_data = []
        # mock _plugin.reorderer directly
        mock_plugin.reorderer = mocker.MagicMock()
        mock_plugin.reorderer.last_module_failure_counts = {
            "module_a.py": 1,
            "module_b.py": 2,
            "module_c.py": 0,
        }
        mock_plugin.reorderer.get_test_outcome.side_effect = lambda item: {
            "module_a.py::test_a1": "passed",
            "module_a.py::test_a2": "failed",
            "module_b.py::test_b1": "passed",
            "module_b.py::test_b2": "failed",
            "module_b.py::test_b3": "failed",
            "module_c.py::test_c1": "passed",
        }.get(item.nodeid, "passed")
        mock_plugin.reorderer.get_test_total_duration.return_value = (
            0.1  # example return value
        )
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("json.load", return_value={"tests": []})
        mock_json_dump = mocker.patch("json.dump")
        mocker.patch("pytest_brightest.plugin.console.print")
        mock_file_handle = mocker.MagicMock()
        mocker.patch("pathlib.Path.open", return_value=mock_file_handle)
        mocker.patch(
            "pathlib.Path.stat", return_value=mocker.MagicMock(st_size=100)
        )
        mock_session = mocker.MagicMock()
        mock_session.items = [
            mock_test_item("module_a.py::test_a1", outcome="passed"),
            mock_test_item("module_a.py::test_a2", outcome="failed"),
            mock_test_item("module_b.py::test_b1", outcome="passed"),
            mock_test_item("module_b.py::test_b2", outcome="failed"),
            mock_test_item("module_b.py::test_b3", outcome="failed"),
            mock_test_item("module_c.py::test_c1", outcome="passed"),
        ]
        pytest_sessionfinish(mock_session, 0)
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        _ = kwargs
        dumped_data = args[0]
        assert isinstance(dumped_data["brightest"], list)
        assert len(dumped_data["brightest"]) == 1
        run_data = dumped_data["brightest"][0]
        assert run_data["data"]["test_module_failures"] == {
            "module_a.py": 1,
            "module_b.py": 2,
            "module_c.py": 0,
        }


def test_get_brightest_data_all_branches(mocker, mock_test_item):
    """Test _get_brightest_data for all branches."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_session = mocker.MagicMock()
    # technique: cost, Focus: modules-within-suite
    mock_plugin.technique = "cost"
    mock_plugin.focus = "modules-within-suite"
    mock_plugin.reorderer = mocker.MagicMock()
    mock_plugin.reorderer.get_test_total_duration.return_value = 1.0
    mock_plugin.reorderer.get_test_outcome.return_value = "passed"
    mock_plugin.current_session_failures = {}
    mock_session.items = [mock_test_item("mod1::test1")]
    data = _get_brightest_data(mock_session)
    assert "data" in data
    assert "test_case_costs" in data["data"]
    assert "test_module_costs" in data["data"]
    assert "test_case_failures" in data["data"]
    assert "test_module_failures" in data["data"]
    # check that testcases list is present
    assert "testcases" in data
    assert data["testcases"] == ["mod1::test1"]


def test_get_brightest_data_structure(mocker, mock_test_item):
    """Test that _get_brightest_data creates proper structure with all required fields."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_session = mocker.MagicMock()
    mock_plugin.technique = "cost"
    mock_plugin.focus = "tests-across-modules"
    mock_plugin.direction = "ascending"
    mock_plugin.seed = 42
    mock_plugin.reorderer = mocker.MagicMock()
    mock_plugin.reorderer.get_test_total_duration.return_value = 1.5
    mock_plugin.reorderer.get_test_outcome.return_value = "passed"
    mock_plugin.current_session_failures = {}
    mock_session.items = [
        mock_test_item("mod1::test1"),
        mock_test_item("mod2::test2"),
    ]
    data = _get_brightest_data(mock_session)
    # check required fields
    assert "timestamp" in data
    assert "technique" in data
    assert "focus" in data
    assert "direction" in data
    assert "seed" in data
    assert "data" in data
    assert "testcases" in data
    # check data structure
    assert "test_case_costs" in data["data"]
    assert "test_module_costs" in data["data"]
    assert "test_case_failures" in data["data"]
    assert "test_module_failures" in data["data"]
    # check testcases field
    assert data["testcases"] == ["mod1::test1", "mod2::test2"]
    # check values
    assert data["technique"] == "cost"
    assert data["focus"] == "tests-across-modules"
    assert data["direction"] == "ascending"
    assert data["seed"] == 42


def test_pytest_sessionfinish_runcount_increment(mocker, mock_config):
    """Test that runcount increments correctly across multiple runs."""
    _ = mock_config
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = True
    mock_plugin.brightest_json_file = "test.json"
    mock_plugin.technique = "shuffle"
    mock_plugin.focus = "tests-across-modules"
    mock_plugin.direction = None
    mock_plugin.seed = 123
    mock_plugin.historical_brightest_data = [
        {
            "runcount": 1,
            "timestamp": "2025-01-01T00:00:00.000000",
            "technique": "cost",
            "focus": "tests-across-modules",
            "direction": "ascending",
            "seed": None,
            "data": {},
            "testcases": [],
        }
    ]
    # mock existing data with one run
    existing_data = {
        "tests": [],
        "brightest": [
            {
                "runcount": 1,
                "timestamp": "2025-01-01T00:00:00.000000",
                "technique": "cost",
                "focus": "tests-across-modules",
                "direction": "ascending",
                "seed": None,
                "data": {},
                "testcases": [],
            }
        ],
    }
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("json.load", return_value=existing_data)
    mock_json_dump = mocker.patch("json.dump")
    mocker.patch("pytest_brightest.plugin.console.print")

    mock_file_handle = mocker.MagicMock()
    mocker.patch("pathlib.Path.open", return_value=mock_file_handle)
    mocker.patch(
        "pathlib.Path.stat", return_value=mocker.MagicMock(st_size=100)
    )
    mock_session = mocker.MagicMock()
    mock_session.items = []
    pytest_sessionfinish(mock_session, 0)
    mock_json_dump.assert_called_once()
    args, _ = mock_json_dump.call_args
    dumped_data = args[0]
    # check that we have 2 runs now
    assert len(dumped_data["brightest"]) == 2
    # check that runcount incremented
    assert dumped_data["brightest"][0]["runcount"] == 1
    assert dumped_data["brightest"][1]["runcount"] == 2


def test_pytest_sessionfinish_max_runs_limit(mocker, mock_config):
    """Test that maximum 25 runs are kept in the brightest section."""
    _ = mock_config
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = True
    mock_plugin.brightest_json_file = "test.json"
    mock_plugin.technique = "shuffle"
    mock_plugin.focus = "tests-across-modules"
    mock_plugin.direction = None
    mock_plugin.seed = 123

    # create existing data with 25 runs
    existing_runs = []
    for i in range(25):
        existing_runs.append(
            {
                "runcount": i + 1,
                "timestamp": f"2025-01-01T00:00:0{i:02d}.000000",
                "technique": "cost",
                "focus": "tests-across-modules",
                "direction": "ascending",
                "seed": None,
                "data": {},
                "testcases": [],
            }
        )
    # set the historical data in the mock plugin
    mock_plugin.historical_brightest_data = existing_runs.copy()
    existing_data = {"tests": [], "brightest": existing_runs}
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("json.load", return_value=existing_data)
    mock_json_dump = mocker.patch("json.dump")
    mocker.patch("pytest_brightest.plugin.console.print")
    mock_file_handle = mocker.MagicMock()
    mocker.patch("pathlib.Path.open", return_value=mock_file_handle)
    mocker.patch(
        "pathlib.Path.stat", return_value=mocker.MagicMock(st_size=100)
    )
    mock_session = mocker.MagicMock()
    mock_session.items = []
    pytest_sessionfinish(mock_session, 0)
    mock_json_dump.assert_called_once()
    args, _ = mock_json_dump.call_args
    dumped_data = args[0]
    # check that we still have only 25 runs
    assert len(dumped_data["brightest"]) == 25
    # check that the oldest run was removed and new run was added
    assert (
        dumped_data["brightest"][0]["runcount"] == 2
    )  # first run was removed
    assert dumped_data["brightest"][-1]["runcount"] == 26  # new run added


def test_pytest_generate_tests(mocker):
    """Test that pytest_generate_tests parameterizes the test."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = True
    mock_plugin.repeat_count = 3
    metafunc = mocker.MagicMock()
    metafunc.fixturenames = []
    pytest_generate_tests(metafunc)
    assert "__pytest_repeat_step_number" in metafunc.fixturenames
    metafunc.parametrize.assert_called_once_with(
        "__pytest_repeat_step_number", range(3)
    )


def test_pytest_generate_tests_disabled(mocker):
    """Test that pytest_generate_tests does nothing when disabled."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = False
    mock_plugin.repeat_count = 3
    metafunc = mocker.MagicMock()
    pytest_generate_tests(metafunc)
    metafunc.parametrize.assert_not_called()


def test_pytest_runtest_protocol_disabled(mocker, mock_test_item):
    """Test that pytest_runtest_protocol returns None when plugin disabled."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = False
    mock_plugin.repeat_failed_count = 2
    item = mock_test_item("test_item")
    result = pytest_runtest_protocol(item, None)
    assert result is None


def test_pytest_runtest_protocol_no_repeat_failed(mocker, mock_test_item):
    """Test that pytest_runtest_protocol returns None when repeat_failed_count is 0."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = True
    mock_plugin.repeat_failed_count = 0
    item = mock_test_item("test_item")
    result = pytest_runtest_protocol(item, None)
    assert result is None


def test_pytest_runtest_protocol_passing_test(mocker, mock_test_item):
    """Test that pytest_runtest_protocol handles passing tests correctly."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = True
    mock_plugin.repeat_failed_count = 2

    # mock passing test reports
    mock_reports = [
        mocker.MagicMock(when="setup", failed=False),
        mocker.MagicMock(when="call", failed=False),
        mocker.MagicMock(when="teardown", failed=False),
    ]

    mock_runtestprotocol = mocker.patch(
        "pytest_brightest.plugin.runtestprotocol", return_value=mock_reports
    )

    item = mock_test_item("test_item")
    # mock the config and hook
    mock_config = mocker.MagicMock()
    mock_hook = mocker.MagicMock()
    mock_config.hook.pytest_runtest_logreport = mock_hook
    item.config = mock_config

    result = pytest_runtest_protocol(item, None)

    assert result is True
    # should only run once for passing test
    mock_runtestprotocol.assert_called_once_with(
        item, nextitem=None, log=False
    )
    # should log all reports
    assert mock_hook.call_count == 3


def test_pytest_runtest_protocol_failing_test_eventually_passes(
    mocker, mock_test_item
):
    """Test that pytest_runtest_protocol retries failed tests and stops when they pass."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = True
    mock_plugin.repeat_failed_count = 3

    # first run fails
    mock_failing_reports = [
        mocker.MagicMock(when="setup", failed=False),
        mocker.MagicMock(when="call", failed=True),
        mocker.MagicMock(when="teardown", failed=False),
    ]

    # second run passes
    mock_passing_reports = [
        mocker.MagicMock(when="setup", failed=False),
        mocker.MagicMock(when="call", failed=False),
        mocker.MagicMock(when="teardown", failed=False),
    ]

    mock_runtestprotocol = mocker.patch(
        "pytest_brightest.plugin.runtestprotocol",
        side_effect=[mock_failing_reports, mock_passing_reports],
    )

    mock_console_print = mocker.patch("pytest_brightest.plugin.console.print")

    item = mock_test_item("test_item")
    # mock the config and hook
    mock_config = mocker.MagicMock()
    mock_hook = mocker.MagicMock()
    mock_config.hook.pytest_runtest_logreport = mock_hook
    item.config = mock_config

    result = pytest_runtest_protocol(item, None)

    assert result is True
    # should run twice: initial run + one retry
    assert mock_runtestprotocol.call_count == 2
    # should print retry message once
    mock_console_print.assert_called_once_with(
        ":flashlight: pytest-brightest: Repeating failed test test_item (attempt 2)"
    )
    # should log the passing reports
    assert mock_hook.call_count == 3


def test_pytest_runtest_protocol_failing_test_exhausts_retries(
    mocker, mock_test_item
):
    """Test that pytest_runtest_protocol retries failed tests until exhausted."""
    mock_plugin = mocker.patch(
        "pytest_brightest.plugin._plugin", autospec=True
    )
    mock_plugin.enabled = True
    mock_plugin.repeat_failed_count = 2

    # all runs fail
    mock_failing_reports = [
        mocker.MagicMock(when="setup", failed=False),
        mocker.MagicMock(when="call", failed=True),
        mocker.MagicMock(when="teardown", failed=False),
    ]

    mock_runtestprotocol = mocker.patch(
        "pytest_brightest.plugin.runtestprotocol",
        return_value=mock_failing_reports,
    )

    mock_console_print = mocker.patch("pytest_brightest.plugin.console.print")

    item = mock_test_item("test_item")
    # mock the config and hook
    mock_config = mocker.MagicMock()
    mock_hook = mocker.MagicMock()
    mock_config.hook.pytest_runtest_logreport = mock_hook
    item.config = mock_config

    result = pytest_runtest_protocol(item, None)

    assert result is True
    # should run 3 times: initial run + 2 retries
    assert mock_runtestprotocol.call_count == 3
    # should print retry messages twice
    assert mock_console_print.call_count == 2
    mock_console_print.assert_any_call(
        ":flashlight: pytest-brightest: Repeating failed test test_item (attempt 2)"
    )
    mock_console_print.assert_any_call(
        ":flashlight: pytest-brightest: Repeating failed test test_item (attempt 3)"
    )
    # should log the final failing reports
    assert mock_hook.call_count == 3
