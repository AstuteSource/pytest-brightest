"""Define constants used by pytest-brightest."""

# define default values associated with reordering
DEFAULT_PYTEST_JSON_REPORT_PATH = ".pytest_cache/pytest-json-report.json"
PYTEST_JSON_REPORT_PLUGIN_NAME = "pytest_jsonreport"
PYTEST_CACHE_DIR = ".pytest_cache"

# define details about the files
DEFAULT_FILE_ENCODING = "utf-8"

# define defaults about the tests
CALL = "call"
DURATION = "duration"
NODEID = "nodeid"
SETUP = "setup"
TEARDOWN = "teardown"
TESTS = "tests"

# define pytest-specific constants
FSPATH = "fspath"
PATH = "path"
NODEID = "nodeid"

# define constants for test outcomes
TOTAL_DURATION = "total_duration"
OUTCOME = "outcome"
UNKNOWN = "unknown"
SETUP_DURATION = "setup_duration"
CALL_DURATION = "call_duration"
TEARDOWN_DURATION = "teardown_duration"

# define constants for json report
JSON_REPORT_FILE = "json_report_file"
REPORT_JSON = ".report.json"

# define the empty string and starting constants
EMPTY_STRING = ""
NEWLINE = "\n"
ZERO_COST = 0.0
BRIGHTEST = "brightest"
TIMESTAMP = "timestamp"
TECHNIQUE = "technique"
FAILURE = "failure"
FOCUS = "focus"
DIRECTION = "direction"
SEED = "seed"
MODULE_COSTS = "module_costs"
TEST_COSTS = "test_costs"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
PYTEST_BRIGHTEST_OUT = "pytest-brightest-output"
PYTEST_BRIGHTEST_OUT_JSON = "pytest-brightest-output.json"

# define constants for reordering techniques
SHUFFLE = "shuffle"
NAME = "name"
COST = "cost"

# define constants for reordering focus
MODULES_WITHIN_SUITE = "modules-within-suite"
TESTS_WITHIN_MODULE = "tests-within-module"
TESTS_ACROSS_MODULES = "tests-across-modules"

# define constants for reordering direction
ASCENDING = "ascending"
DESCENDING = "descending"
