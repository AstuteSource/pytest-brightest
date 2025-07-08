"""Test the TestReorderer class."""


def test_create_reorderer():
    """Test the create_reorderer function."""
    from pytest_brightest.reorder import create_reorderer, ReordererOfTests

    reorderer = create_reorderer()
    assert isinstance(reorderer, ReordererOfTests)
    assert (
        reorderer.json_report_path == ".pytest_cache/pytest-json-report.json"
    )
    reorderer = create_reorderer("custom.json")
    assert isinstance(reorderer, ReordererOfTests)
    assert reorderer.json_report_path == "custom.json"


def test_load_test_data_json_decode_error(tmp_path, mocker):
    from pytest_brightest.reorder import ReordererOfTests

    json_path = tmp_path / "bad.json"
    json_path.write_text("{bad json}")
    reorderer = ReordererOfTests(str(json_path))
    assert not reorderer.has_test_data()


def test_get_prior_data_for_reordering_all_branches(tmp_path, mock_test_item):
    from pytest_brightest.reorder import ReordererOfTests
    import json

    json_path = tmp_path / "report.json"
    data = {
        "tests": [
            {
                "nodeid": "mod1::t1",
                "call": {"duration": 1.0},
                "outcome": "passed",
            },
            {
                "nodeid": "mod1::t2",
                "call": {"duration": 2.0},
                "outcome": "failed",
            },
            {
                "nodeid": "mod2::t3",
                "call": {"duration": 3.0},
                "outcome": "error",
            },
        ]
    }
    json_path.write_text(json.dumps(data))
    reorderer = ReordererOfTests(str(json_path))
    items = [
        mock_test_item("mod1::t1"),
        mock_test_item("mod1::t2"),
        mock_test_item("mod2::t3"),
    ]
    # COST, MODULES_WITHIN_SUITE
    d = reorderer.get_prior_data_for_reordering(
        items, "cost", "modules-within-suite"
    )
    assert "prior_module_costs" in d
    # COST, TESTS_WITHIN_MODULE
    d = reorderer.get_prior_data_for_reordering(
        items, "cost", "tests-within-module"
    )
    assert "prior_test_costs" in d
    # COST, TESTS_ACROSS_MODULES
    d = reorderer.get_prior_data_for_reordering(
        items, "cost", "tests-across-modules"
    )
    assert "prior_test_costs" in d
    # NAME, MODULES_WITHIN_SUITE
    d = reorderer.get_prior_data_for_reordering(
        items, "name", "modules-within-suite"
    )
    assert "prior_module_order" in d
    # NAME, TESTS_ACROSS_MODULES
    d = reorderer.get_prior_data_for_reordering(
        items, "name", "tests-across-modules"
    )
    assert "prior_test_order" in d
    # NAME, TESTS_WITHIN_MODULE
    d = reorderer.get_prior_data_for_reordering(
        items, "name", "tests-within-module"
    )
    assert "prior_module_tests" in d
    # FAILURE, MODULES_WITHIN_SUITE
    d = reorderer.get_prior_data_for_reordering(
        items, "failure", "modules-within-suite"
    )
    assert "prior_module_failure_counts" in d


def test_reorder_tests_in_place_empty():
    from pytest_brightest.reorder import ReordererOfTests

    reorderer = ReordererOfTests()
    items = []
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "modules-within-suite"
    )
    assert items == []


def test_reorder_tests_in_place_all_branches(tmp_path, mock_test_item, mocker):
    from pytest_brightest.reorder import ReordererOfTests
    import json

    json_path = tmp_path / "report.json"
    data = {
        "tests": [
            {
                "nodeid": "mod1::t1",
                "call": {"duration": 1.0},
                "outcome": "passed",
            },
            {
                "nodeid": "mod1::t2",
                "call": {"duration": 2.0},
                "outcome": "failed",
            },
        ]
    }
    json_path.write_text(json.dumps(data))
    reorderer = ReordererOfTests(str(json_path))
    items = [mock_test_item("mod1::t1"), mock_test_item("mod1::t2")]
    mocker.patch("pytest_brightest.reorder.console.print")
    # modules-within-suite, cost
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "modules-within-suite"
    )
    # modules-within-suite, name
    reorderer.reorder_tests_in_place(
        items, "name", "ascending", "modules-within-suite"
    )
    # modules-within-suite, failure
    reorderer.reorder_tests_in_place(
        items, "failure", "ascending", "modules-within-suite"
    )
    # tests-within-module
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "tests-within-module"
    )
    # tests-across-modules
    reorderer.reorder_tests_in_place(
        items, "cost", "ascending", "tests-across-modules"
    )


def test_setup_json_report_plugin_branches(tmp_path, mocker):
    from pytest_brightest.reorder import setup_json_report_plugin

    class DummyConfig:
        class Option:
            json_report_file = ".report.json"

        option = Option()

        class PluginManager:
            def has_plugin(self, name):
                return name == "pytest_jsonreport"

        pluginmanager = PluginManager()

    config = DummyConfig()
    mocker.patch("pytest_brightest.reorder.console.print")
    assert setup_json_report_plugin(config) is True

    # test ImportError
    def raise_import_error(*a, **kw):
        raise ImportError("fail")

    mocker.patch.object(
        config.pluginmanager, "has_plugin", side_effect=raise_import_error
    )
    assert setup_json_report_plugin(config) is False

    # test Exception
    def raise_exception(*a, **kw):
        raise Exception("fail")

    mocker.patch.object(
        config.pluginmanager, "has_plugin", side_effect=raise_exception
    )
    assert setup_json_report_plugin(config) is False
