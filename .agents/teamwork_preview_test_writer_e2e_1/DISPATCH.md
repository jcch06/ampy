## 2026-09-30T13:22:15Z
You are teamwork_preview_test_writer_e2e_1.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_test_writer_e2e_1
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md
Test infra: c:\Users\cjose\antigravity project\ampy\TEST_INFRA.md
Benchmarks spec: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\benchmarks.md
Normative specs: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md

You MUST first read ORIGINAL_REQUEST.md, TEST_INFRA.md, and the benchmarks specification.

Task:
Implement the foundational E2E test cases and test harness for the project:
1. Create `tests/__init__.py` and `tests/conftest.py` with standard fixtures and tolerance comparison helpers.
2. Create `tests/e2e/__init__.py` and implement the 5 canonical UTE C 15-105 worked benchmark scenarios in `tests/e2e/test_ute_benchmarks.py`:
   - `BENCH-01`: Standard 3P Motor 18.5kW (Method E, XLPE, Cu, 45m) -> S=4.0mm², In=32A, dU=3.03%.
   - `BENCH-02`: 1P Commercial Lighting 3.68kW (Method B, PVC, Cu, 35m) -> S=4.0mm², In=16A, dU=2.80%.
   - `BENCH-03`: Long-Run Feeder Pumping 37kW (Method C, XLPE, Cu, 220m) -> S=25.0mm², In=63A, dU=4.95%.
   - `BENCH-04`: Multi-Cable Grouping N=6 touching (Method E, XLPE, Cu, 30m) -> S=10.0mm², In=40A, dU=0.97%.
   - `BENCH-05`: High Ambient Temp 50°C Plant (Method C, XLPE, Cu, 40m) -> S=16.0mm², In=63A, dU=1.12%.
   Ensure tests use public API (`from ampy import SizingEngine, CircuitDefinition, ...` or `pytest.importorskip("ampy")` so they are fully valid test files ready for execution once engine is implemented).
3. Document readiness in `handoff.md`. Communicate via send_message to parent when complete.
