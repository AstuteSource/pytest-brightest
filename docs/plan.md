# pytest-brightest Plan

## Documentation Requirements

All documentation should follow these standards:

- README files should use clear section headers with emoji prefixes for visual organization.
- Code examples in documentation should be complete and runnable.
- All command-line examples should include the `$` prompt prefix to indicate terminal commands.
- Documentation should specify exact file paths when referencing project files.
- All URLs in documentation should be complete and functional.
- Source code examples should be as realistic as possible, reflecting actual usage patterns.
- All documentation should be written in Markdown format and visible on GitHub.
- A special version of the documentation in the README.md file is always
maintained in the file called `README_PYTHON.md`. The purpose of this file is to
contain all the same content in the `README.md` file, excepting the fact that it
should not contain emojis or graphics or other elements that do not appear on PyPI.

## Project Structure Requirements

The project should maintain this structure:

- Source code should be in `src/pytest-brightest/` directory.
- Tests should be in `tests/` directory with matching structure to source.
- Documentation should be in `docs/` directory.
- Configuration files should be in the project root.
- GitHub Actions workflows should be in `.github/workflows/` directory.

## Infrastructure Requirements

- Use `uv` for managing the dependencies, virtual environments, and task running.
- System should be written so that they work on MacOS, Linux, and Windows.
- System should support Python 3.11, 3.12, and 3.13.
- The `pyproject.toml` file should be used to manage dependencies and encoded project metadata.

## Code Requirements

All the Python code should follow these standards:

- Function bodies should not have any blank lines in them. This means that
function bodies should be contiguous blocks of code without any blank lines.
- Every function should have a docstring that starts with a capital letter and
ends with a period.
- Every function should have a docstring that is a single line.
- All other comments should start with a lowercase letter.
- If there are already comments in the source code and it must be revised,
extended, or refactored in some way, do not delete the comments unless the code
that is going along with the comments is deleted. If the original source code
is refactored such that it no longer goes along with the comments, then it is
permissible to delete and/or revise the comments in a suitable fashion.

## Test Requirements

All test cases should follow these standards:

- Since a test case is a Python function, it should always follow the code
requirements above in the subsection called "Code Requirements".
- Test cases should have a descriptive name that starts with `test_`.
- Test cases should be grouped by the function they are testing.
- Test cases should be ordered in a way that makes sense to the reader.
- Test cases should be independent of each other so that they can be run in a
random order without affecting the results or each other.
- Test cases must work both on a local machine and in a CI environment, meaning
that they should work on a laptop and in GitHub Actions.
- Test cases should aim to achieve full function, statement, and branch coverage
so as to ensure that the function in the program is thoroughly tested.

## Code Generation Guidelines

When generating new code or test cases, follow these specific patterns:

### Function and Class Patterns

- All functions must have type hints for parameters and return values.
- Use `Path` from `pathlib` for all file system operations, never string paths.
- Rich console output should use the existing `rich` patterns in the codebase.
- Error handling should use specific exception types, not generic `Exception`.
- If a function contains comments inside of it and the function is going
to be refactored, never remove those comments that are still relevant to
the new implementation of the function. Only delete comments or remove all
the comments from a function subject to refactoring if it is absolutely needed.

### Import Organization

- Group imports in this order: standard library, third-party, local imports.
- Use absolute imports for all local modules (`from pytest_brightest.module import ...`).
- Import only what is needed, avoid wildcard imports.
- Follow the existing import patterns seen in the codebase.
- Unless there is a good reason not to do so, place all imports at the top
of a file and thus, for instance, avoid imports inside of functions.

### Naming Conventions

- Use snake_case for all functions, variables, and module names.
- Use PascalCase for class names.
- Constants should be UPPER_SNAKE_CASE.
- Private functions should start with underscore.

### Testing Patterns

- Test files should mirror the source structure (e.g., `tests/test_main.py` for
`src/pytest_brightest/main.py`).
- Use descriptive test names that explain what is being tested.
- Group related tests in the same file and use clear organization.
- Mock external dependencies (GitHub API, file system) in tests.
- Use pytest fixtures for common test setup.
- Include both positive and negative test cases.
- Test edge cases and error conditions.
- Write property-based test cases using Hypothesis where applicable. Make sure
that all the property-based are marked with the decorator called `@pytest.mark.property`
so that they can be run separately from the other tests when needed.

### Error Handling Patterns

- Catch specific exceptions and provide meaningful error messages.
- Use early returns to avoid deep nesting.
- Log errors appropriately without exposing sensitive information.
- Provide actionable error messages to users.

### File Operations

- Use `pathlib.Path` for all file operations.
- Handle file permissions and access errors gracefully.
- Use context managers for file operations.
- Validate file paths and existence before operations.

## Context Requirements for GitHub Copilot

To generate the most accurate code, always provide:

### Essential Context

- The specific module or function being modified or extended.
- Related functions or classes that might be affected.
- Existing error handling patterns in similar functions.
- The expected input/output format for the new functionality.

### Testing Context

- Existing test patterns for similar functionality.
- Mock objects and fixtures already in use.
- Test data structures and formats.
- Integration test requirements vs unit test requirements.

### Integration Context

- How the new code fits into existing CLI commands.
- Dependencies on other modules or external services.
- Configuration requirements or environment variables.
- Backward compatibility requirements.

### Fenced Code Blocks

- Always use fenced code blocks with the language specified for syntax highlighting.
- Use triple backticks (```) for the fenced code blocks.
- Whenever the generated code for a file is less than 100 lines, always generate
a single code block for the entire file, making it easy to apply the code to a
contiguous region of the file.
- When the generated code for a file is more than 100 lines, always follow these rules:
    - Provide the fenced code blocks so that the first one generated is for the last
    block of code in the file being generated.
    - After providing the last block of code, work your way "up" the file for which code
    in being generated and provide each remaining fenced code block.
    - Make sure that the provided blocks of code are for contiguous sections of the file
    for which code is being generated.
    - The overall goal is that I should be able to start from the first code block
    that you generate and apply it to the bottom of the file and then continue to apply
    code blocks until the entire file is updated with the new code.
    - The reason for asking the code to be generated in this fashion is that it ensures
    that the line numbers in the code blocks match the line numbers in the file.

## Current Refactoring Instructions

1) The `pytest-brightest` plugin does not yet have a good way to save data in
the JSON report file. The data that it saves it not consistent and not suitable
for checking to confirm whether or not it is working correctly.

2) The refactored version of the plugin should save the following data in
the `brightest` section of the JSON report files in a list of entries:
    - `runcount`: The identifier for the run of the test suite.
    - `timestamp`: The timestamp when the test suite was run.
    - `technique`: The technique used for reordering the tests.
    - `focus`: The focus of the reordering.
    - `direction`: The direction of the reordering.
    - `seed`: The seed for the random number generator used for shuffling.
    - `data`: All calculated data about the test cases, test modules, etc.
    - `testcases`: A list of test `nodeids` in the order that the plugin
    executed them decided to run them according to the current configuration.

3) If one of these attributes is not needed for a specific configuration of the
plugin, it should still still be recorded, but with the value `null`.

4) The purpose of the `runcount` parameter is to allow the plugin to save up to a
maximum number of runs in the JSON report. For now, the tool can have a
hard-coded constant of `25` for the maximum number of runs that it will store in
the `brightest` section of the JSON report file. This means that the `runcount`
will start at `1` and increment by `1` for each run of the test suite with the
plugin being enabled. Then, all the data will be stored for that run and can be
used in subsequent runs of the test suite when the plugin is enabled.

5) The entire refactoring should not break the existing implementation. It
should all of this logging code so that the plugin's behavior is easier to check
and understand. If there are any inconsistencies in the description of the tool,
then the agent implementing this refactoring should check in with the designer
of the pytest-brightest plugin to clarify details.

6) An example of the `brightest` section of the JSON file would be:

```json
"brightest": [
    {
        "runcount": 1,
        "timestamp": "2025-07-15T22:03:39.926943",
        "technique": "cost",
        "focus": "modules-within-suite",
        "direction": "ascending",
        "seed": null,
        "data": {
            "test_case_costs": {
                "tests/test_actions.py::test_get_github_actions_status_no_runs": 0.0005024719866923988,
                "tests/test_actions.py::test_get_github_actions_status_success_with_runs": 0.0012274129840079695,
                < ... more test case cost data ... >
            }
            "test_module_costs": {
                "tests/test_models.py": 0.004262267902959138,
                "tests/test_user.py": 0.005330827989382669,
                "tests/test_actions.py": 0.0049656800692901015,
                "tests/test_find.py": 0.007323569996515289,
                "tests/test_constants.py": 0.007342756842263043,
                "tests/test_pullrequest.py": 0.00743798105395399,
                "tests/test_repository.py": 0.014911067992215976,
                "tests/test_status.py": 0.1593270179873798,
                "tests/test_main.py": 0.11824749677907676,
                "tests/test_util.py": 0.22743810291285627,
                "tests/test_discover.py": 0.2617855129938107
                < ... more test module cost data ... >
            }
            "test_case_failures": {
                "tests/test_actions.py::test_get_github_actions_status_no_runs": 0,
                "tests/test_actions.py::test_get_github_actions_status_success_with_runs": 0,
                < ... more test case failure data ... >
            },
            "test_module_failures": {
                "tests/test_models.py": 0,
                "tests/test_user.py": 0,
                "tests/test_actions.py": 0,
                "tests/test_find.py": 0,
                "tests/test_constants.py": 0,
                "tests/test_pullrequest.py": 0,
                "tests/test_repository.py": 0,
                "tests/test_status.py": 0,
                "tests/test_main.py": 0,
                "tests/test_util.py": 0,
                "tests/test_discover.py": 0
                < ... more test module failure data ... >
            }
        }
    }
    < more entries for follow-on runs of the test suite with pytest-brightest plugin ... >
]
```

## Finished Refactoring Instructions

1) Even though the command-line interface for the pytest-brightest plugin is
acceptable and there is evidence that it works when installed through an
editable install with uv in a project that uses Pytest and Pytest plugins, I
want to refactor it in the following ways:
    - Make a command-line argument called `--reorder-by-technique`, with these options:
        - `shuffle`: Shuffle the tests in a random order.
        - `name`: Order the tests by their names.
        - `cost`: Order the tests by their execution time.
    - Make a command-line argument called `--reorder-by-focus`, with these options:
        - `modules-within-suite`: Reorder the modules (i.e., the files) in the test
          suite, but do not actually change the order of the tests in the modules
        - `tests-within-module`: Reorder the tests within each module, but do not
          change the order of the modules in the test suite.
        - `tests-across-modules`: Reorder the tests across all modules in the test suite,
           mixing and matching tests from different modules into a complete new
           order
    - Make a command-line argument called `--reorder-in-direction` with these options:
        - `ascending`: Order the tests in ascending order.
        - `descending`: Order the tests in descending order.

2) The idea is that the person using the pytest-brightest plugin should have the
ability to pass these different command-line arguments to chose the technique by
which the reordering will take place (i.e., the first new command-line
argument), the focus of the reordering (i.e., the second new command-line
argument), and the direction in which the reordering will take place (i.e., the
third new command-line argument).

3) The entire refactoring should not break the existing implementation. It
should add these new command-line arguments and make the tool more
general-purpose and easier to use and understand. If there are any
inconsistencies in the description of the tool, then the agent implementing this
refactoring should check in with the designer of the pytest-brightest plugin to
clarify details.

## Additional Notes

Note: This section is for any additional notes or context that might be
useful for future software agents who work on this project.

## Current Plans

Note: A software agent can add details about their plan in this subsection.

### Implement --repeat feature (2025-07-21)

1. Add a new command-line argument `--repeat` to `pytest_addoption` in `src/pytest_brightest/plugin.py`. This argument will accept an integer value specifying the number of times each test should be repeated.
2. In the `BrightestPlugin.configure` method, read the value of the `--repeat` argument and store it in a new instance variable, e.g., `self.repeat_count`.
3. In `pytest_collection_modifyitems`, after the existing reordering and shuffling logic, check if `self.repeat_count` is greater than 1.
4. If it is, create a new list of items. For each item in the (potentially reordered) `items` list, add it to the new list `self.repeat_count` times.
5. Replace the original `items` list with this new list of repeated items.
6. Add a new test case in `tests/test_plugin.py` to verify that the `--repeat` functionality works as expected. This test should check that the number of items is correctly multiplied.
7. Run all linters and tests using `uv run task all` to ensure the changes are correct and follow project standards.

### Implement --repeat-failed feature (2025-07-21)

1. Add a new command-line argument `--repeat-failed` to `pytest_addoption` in `src/pytest_brightest/plugin.py`. This argument will accept an integer value specifying the number of times a failed test should be repeated.
2. In the `BrightestPlugin.configure` method, read the value of the `--repeat-failed` argument and store it in a new instance variable, e.g., `self.repeat_failed_count`.
3. Implement the `pytest_runtest_protocol` hook to create a custom test execution loop.
4. Inside the `pytest_runtest_protocol` hook, use `_pytest.runner.runtestprotocol` to run the test and get the reports.
5. If the test fails, loop and re-run it up to the specified number of times.
6. Log the final reports.
7. Add new test cases in `tests/test_plugin.py` to verify that the `--repeat-failed` functionality works as expected. This test should check that a failing test is re-run and that a passing test is not.
8. Run all linters and tests using `uv run task all` to ensure the changes are correct and follow project standards.

### Implement ratio-based reordering technique (2025-07-21)

**Goal**: Implement a new "ratio" reordering technique that uses both cost and failure data by calculating the ratio between failure counts and test execution costs.

**Problem to solve**: Current tool uses either cost OR failure data exclusively. The new technique will combine both by calculating failure-to-cost ratios for more informed test prioritization.

**Detailed Plan**:

1. **Add "ratio" constant and update command-line options**:
   - Add `RATIO = "ratio"` constant to `src/pytest_brightest/constants.py`
   - Update `--reorder-by-technique` choices in `src/pytest_brightest/plugin.py` to include "ratio"
   - Update validation logic in `BrightestPlugin.configure()` to handle "ratio" technique

2. **Implement ratio calculation logic in ReordererOfTests class**:
   - Add method `get_test_failure_to_cost_ratio(item: Item) -> float` that:
     - Gets failure count using existing `get_test_failure_count()`
     - Gets cost using existing `get_test_total_duration()`
     - Applies failure count adjustment: if failure_count == 0, set to 1; else use actual count + 1
     - Returns ratio as `adjusted_failure_count / max(cost, 0.001)` (avoid division by zero)
   - Add module-level ratio calculation methods for different focus areas
   - Add ratio-based reordering methods for all three focus types:
     - `reorder_modules_by_ratio()`: Calculate module ratios as sum of module test ratios
     - `reorder_tests_across_modules()`: Sort all tests by individual ratios
     - `reorder_tests_within_module()`: Sort tests within each module by ratios

3. **Update existing reordering infrastructure**:
   - Modify `reorder_tests_in_place()` to handle "ratio" technique
   - Update `get_prior_data_for_reordering()` to collect ratio data for reporting
   - Add ratio-specific helper methods following existing patterns

4. **Comprehensive testing**:
   - Create test fixtures with mock failure and cost data representing realistic scenarios
   - Test ratio calculations with edge cases (zero failures, zero costs, missing data)
   - Verify correct ordering for all three focus areas (modules-within-suite, tests-within-module, tests-within-suite)
   - Test integration with existing shuffling and other reordering techniques
   - Verify diagnostic output shows meaningful ratio information

5. **Data structure updates**:
   - Update `get_prior_data_for_reordering()` to include ratio calculations in saved data
   - Ensure ratio data is properly included in brightest JSON report output
   - Add appropriate constants for ratio-related data keys

6. **Documentation and validation**:
   - Run full test suite with `uv run task all` to ensure no regressions
   - Verify ratio technique works with all existing command-line combinations
   - Test with real test suites to validate meaningful reordering results

**Key technical considerations**:
- Failure count adjustment strategy: non-failed tests get count of 1, failed tests get actual_count + 1
- Cost normalization: use minimum threshold (0.001) to prevent division by zero for very fast tests
- Preserve existing behavior: all current reordering techniques must continue working unchanged
- Diagnostic output: provide clear information about calculated ratios during reordering
