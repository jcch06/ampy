## 2026-09-30T13:45:41Z

You are teamwork_preview_explorer_m1_fix_3.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_3
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md
Challenger 2 harness: c:\Users\cjose\antigravity project\ampy\tests\adversarial_challenge_models.py
Existing unit tests: c:\Users\cjose\antigravity project\ampy\tests\unit\

You MUST first read ORIGINAL_REQUEST.md, PROJECT.md, and the test files.

Task:
Formulate an exact test suite hardening plan for Milestone 1:
1. Converting `tests/adversarial_challenge_models.py` into a formal pytest module:
   - Create plan for `tests/boundary/test_models_adversarial.py` so that all 51 adversarial vectors run automatically under `pytest`.
2. Adding dedicated unit tests for:
   - Enum hashability (verifying `hash(PhaseSystem.SINGLE_PHASE)`, dict indexing `{PhaseSystem.SINGLE_PHASE: 'foo'}`, sets, and ensuring `PhaseSystem.SINGLE_PHASE != True`).
   - String inputs to `calculate_ib("1P", ...)` and `calculate_voltage_drop("3P", ...)`.
   - Material string aliases to `calculate_thermal_stress_min_section("copper", ...)`.
3. Ensuring zero regression on existing 182 unit tests and 39 boundary tests.

Write your plan to `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_3\test_hardening_plan.md` and deliver `handoff.md`. Communicate via send_message to parent when complete.
