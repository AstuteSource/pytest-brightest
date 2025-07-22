# Command-Line Arguments Checklist

This document provides a checklist of valid and invalid command-line arguments
for `pytest-brightest`. It is intended to be used as a guide for manual and
automated testing.

## Valid Command-Line Arguments

### Reordering by Cost

- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --reorder-by-focus modules-within-suite --reorder-in-direction ascending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --reorder-by-focus modules-within-suite --reorder-in-direction descending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --reorder-by-focus tests-within-module --reorder-in-direction ascending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --reorder-by-focus tests-within-module --reorder-in-direction descending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --reorder-by-focus tests-across-modules --reorder-in-direction ascending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --reorder-by-focus tests-across-modules --reorder-in-direction descending`

### Reordering by Name

- [ ] `uv run pytest --json-report --brightest --reorder-by-technique name --reorder-by-focus modules-within-suite --reorder-in-direction ascending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique name --reorder-by-focus modules-within-suite --reorder-in-direction descending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique name --reorder-by-focus tests-within-module --reorder-in-direction ascending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique name --reorder-by-focus tests-within-module --reorder-in-direction descending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique name --reorder-by-focus tests-across-modules --reorder-in-direction ascending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique name --reorder-by-focus tests-across-modules --reorder-in-direction descending`

### Reordering by Failure

- [ ] `uv run pytest --json-report --brightest --reorder-by-technique failure --reorder-by-focus modules-within-suite --reorder-in-direction ascending`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique failure --reorder-by-focus modules-within-suite --reorder-in-direction descending`

### Shuffling

- [ ] `uv run pytest --json-report --brightest --reorder-by-technique shuffle --reorder-by-focus modules-within-suite`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique shuffle --reorder-by-focus tests-within-module`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique shuffle --reorder-by-focus tests-across-modules`
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique shuffle --seed 12345`

## Invalid Command-Line Arguments

### Missing `--brightest`

- [ ] `uv run pytest --json-report --reorder-by-technique cost` (Plugin should not activate)

### Invalid Technique

- [ ] `uv run pytest --json-report --brightest --reorder-by-technique invalid_technique` (Should raise an error)

### Invalid Focus

- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --reorder-by-focus invalid_focus` (Should raise an error)

### Invalid Direction

- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --reorder-in-direction invalid_direction` (Should raise an error)

### Conflicting Arguments

- [ ] `uv run pytest --json-report --brightest --reorder-by-technique shuffle --reorder-in-direction ascending` (Direction should be ignored)
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique cost --seed 12345` (Seed should be ignored)
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique failure --reorder-by-focus tests-within-module` (Not a valid combination)
- [ ] `uv run pytest --json-report --brightest --reorder-by-technique failure --reorder-by-focus tests-across-modules` (Not a valid combination)
