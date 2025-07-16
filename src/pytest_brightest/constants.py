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
NODEID_SEPARATOR = "::"

# define constants for test outcomes
TOTAL_DURATION = "total_duration"
OUTCOME = "outcome"
UNKNOWN = "unknown"
SETUP_DURATION = "setup_duration"
CALL_DURATION = "call_duration"
TEARDOWN_DURATION = "teardown_duration"
FAILED = "failed"
ERROR = "error"

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
# MODULE_COSTS = "module_costs"
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

# define constants for reporting
MODULE_ORDER = "module_order"
TEST_ORDER = "test_order"
MODULE_TESTS = "module_tests"
MODULE_FAILURE_COUNTS = "module_failure_counts"
MODULE_ORDER_CURRENT = "module_order_current"
TEST_ORDER_CURRENT = "test_order_current"
MODULE_TESTS_CURRENT = "module_tests_current"
CURRENT_MODULE_COSTS = "current_module_costs"
CURRENT_TEST_COSTS = "current_test_costs"
CURRENT_MODULE_FAILURE_COUNTS = "current_module_failure_counts"
CURRENT_MODULE_ORDER = "current_module_order"
CURRENT_TEST_ORDER = "current_test_order"
CURRENT_MODULE_TESTS = "current_module_tests"

# diagnostic message prefixes
FLASHLIGHT_PREFIX = ":flashlight: pytest-brightest:"
HIGH_BRIGHTNESS_PREFIX = ":high_brightness: pytest-brightest:"

# define constants for structured data logging
RUNCOUNT = "runcount"
DATA = "data"
TESTCASES = "testcases"
MAX_RUNS = 25

# define constants for test cost and failure data
TEST_CASE_COSTS = "test_case_costs"
TEST_MODULE_COSTS = "test_module_costs"
TEST_CASE_FAILURES = "test_case_failures"
TEST_MODULE_FAILURES = "test_module_failures"
