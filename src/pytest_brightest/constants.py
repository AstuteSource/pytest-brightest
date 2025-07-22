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
INDENT = "  "
NEWLINE = "\n"
ZERO_COST = 0.0
BRIGHTEST = "brightest"
TIMESTAMP = "timestamp"
TECHNIQUE = "technique"
FAILURE = "failure"
FOCUS = "focus"
DIRECTION = "direction"
SEED = "seed"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
PYTEST_BRIGHTEST_OUT = "pytest-brightest-output"
PYTEST_BRIGHTEST_OUT_JSON = "pytest-brightest-output.json"

# define constants for reordering techniques
SHUFFLE = "shuffle"
NAME = "name"
COST = "cost"
RATIO = "ratio"

# define constants for tie-breaking
TIE_BREAK_BY = "tie_break_by"
DEFAULT_TIE_BREAKERS = []

# define constants for reordering focus
MODULES_WITHIN_SUITE = "modules-within-suite"
TESTS_WITHIN_MODULE = "tests-within-module"
TESTS_WITHIN_SUITE = "tests-within-suite"
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
TEST_CASE_RATIOS = "test_case_ratios"
TEST_MODULE_RATIOS = "test_module_ratios"

# define constants for ratio calculation
FAILURE_BASE_WEIGHT = 1
FAILURE_MULTIPLIER = 10
MIN_COST_THRESHOLD = 0.00001

# define constants for command-line arguments in JSON report
REPEAT_COUNT = "repeat_count"
REPEAT_FAILED_COUNT = "repeat_failed_count"
