# BRIEFING — 2026-09-30T13:28:45Z

## Mission
Implement the foundational E2E test cases and test harness for the ampy electrical cable sizing engine, including conftest.py, tolerance comparison helpers, and the 5 canonical UTE C 15-105 worked benchmark scenarios.

## 🔒 My Identity
- Archetype: specialist, qa (Test Writer)
- Roles: specialist, qa
- Working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_test_writer_e2e_1
- Original parent: 776386d9-70f0-46fd-896e-befc19ccbade
- Milestone: E2E Test Suite Creation

## 🔒 Key Constraints
- Write and modify TEST code only — never implementation code. Escalate implementation bugs to the implementing agent.
- Progressive testability: Tests must import public API gracefully or use `pytest.importorskip("ampy")` so test files are fully valid and executable at any stage.
- Discrete results (S mm², In A, constraint enum) must match exactly; continuous variables (dU, Ib, Iz) match within specified tolerances (<=0.5% rel_tol, etc.).
- Independent tests: self-contained and isolated.
- Authoritative derivation: Derived strictly from NF C 15-100, UTE C 15-105, and benchmarks specification.

## Current Parent
- Conversation ID: 776386d9-70f0-46fd-896e-befc19ccbade
- Updated: not yet

## Task Summary
- **What to build**:
  1. `tests/__init__.py` and `tests/conftest.py` with standard fixtures and tolerance comparison helpers.
  2. `tests/e2e/__init__.py` and `tests/e2e/test_ute_benchmarks.py` with the 5 canonical UTE C 15-105 benchmark scenarios (BENCH-01 to BENCH-05).
  3. `tests/test_harness_fixtures.py` ensuring self-testing of the test harness itself.
- **Success criteria**:
  - Test files are syntactically valid and pass compilation.
  - Comprehensive coverage of discrete and continuous benchmark assertions.
  - Passes ruff linting with 0 errors.
  - Pytest runs cleanly with exit code 0.
  - `handoff.md` and message sent to parent.
- **Interface contracts**: PROJECT.md § Interface Contracts
- **Code layout**: PROJECT.md § Code Layout

## Key Decisions Made
- Standardized tolerance assertions helper `assert_sizing_result_matches_benchmark(...)` in `conftest.py` to test discrete exact matches ($S$, $I_n$, constraint), continuous physical quantities ($I_b$, $I_z$, $\Delta U\text{ V}$, $\Delta U\%$, $k_{\text{total}}$), and normative inequalities ($I_b \le I_n \le I_z$ and $\Delta U\% \le \Delta U_{\max}\%$).
- Implemented flexible field extraction (`extract_result_fields`) supporting both direct properties (`result.voltage_drop_v`) and nested sub-objects (`result.voltage_drop.delta_u_v`) as well as naming aliases (`protective_device_in`, `in_a`).
- Guarded `test_ute_benchmarks.py` with `pytest.importorskip("ampy")` and fallback to `ampy.core.models`, enabling progressive testability where pytest passes with 0 failures prior to and after ampy engine implementation.
- Created `tests/test_harness_fixtures.py` to verify test harness integrity, fixture data, and intentional failure detection without needing production code.

## Artifact Index
- `tests/__init__.py` — Package root for tests
- `tests/conftest.py` — Pytest fixtures, tolerance comparison helpers, and circuit specifications
- `tests/e2e/__init__.py` — Package root for e2e tests
- `tests/e2e/test_ute_benchmarks.py` — 5 canonical UTE C 15-105 worked benchmark scenarios (12 tests)
- `tests/test_harness_fixtures.py` — Integrity tests for fixtures, helpers, and negative test cases (6 tests)

## Loaded Skills
- None required.

## Quality Status
- **Build/test result**: PASS (pytest: 6 passed, 1 skipped awaiting ampy engine; 12/12 passed when engine simulated)
- **Lint status**: 0 errors (ruff check tests/ -> All checks passed!)
- **Tests added/modified**: 18 test cases across `tests/e2e/test_ute_benchmarks.py` and `tests/test_harness_fixtures.py`
