## 2026-09-30T13:52:21Z

You are teamwork_preview_worker_m1_2.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_worker_m1_2
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md

Remediation Blueprints to execute:
- Models Fix Plan: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_1\models_fix_plan.md
- Formulas Fix Plan: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_2\formulas_fix_plan.md
- Test Hardening Plan: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_3\test_hardening_plan.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (You exclusively own and will edit/create these files):
- `c:\Users\cjose\antigravity project\ampy\src\ampy\core\models.py`
- `c:\Users\cjose\antigravity project\ampy\src\ampy\core\formulas.py`
- `c:\Users\cjose\antigravity project\ampy\tests\adversarial_challenge_models.py`
- `c:\Users\cjose\antigravity project\ampy\tests\boundary\test_models_adversarial.py`
- `c:\Users\cjose\antigravity project\ampy\tests\boundary\test_boundaries.py`
- `c:\Users\cjose\antigravity project\ampy\tests\unit\test_models.py`
- `c:\Users\cjose\antigravity project\ampy\tests\unit\test_formulas.py`

Task:
1. Apply the exact changes from `models_fix_plan.md` to `src/ampy/core/models.py` and `tests/adversarial_challenge_models.py`:
   - Add `__hash__` and boolean guard to `PhaseSystem` and `LimitingConstraint`.
   - Add `allow_inf_nan=False` across all model configs.
   - Add `frozen=True` to `CircuitDefinition.model_config`.
   - Add `extra="forbid"` to output models.
   - Add boolean validator to `ElectricalLoad`.
2. Apply the exact changes from `formulas_fix_plan.md` to `src/ampy/core/formulas.py`:
   - System string coercion via `PhaseSystem(system)` in `calculate_ib` and `calculate_voltage_drop`.
   - Material string normalization (`"copper"`, `"cu"`, `"aluminium"`, `"al"`) in `calculate_thermal_stress_min_section`.
   - Zero/negative voltage validation in `calculate_voltage_drop`.
   - Dead code cleanup.
3. Apply the exact changes from `test_hardening_plan.md`:
   - Create `tests/boundary/test_models_adversarial.py` implementing all 51 adversarial vectors under pytest.
   - Reconcile `tests/boundary/test_boundaries.py` lines 471-503 to test the hardened behavior.
   - Add unit tests for enum hashability, dict indexing, string inputs in `tests/unit/test_models.py` and `tests/unit/test_formulas.py`.
4. Run verification:
   - `python tests/adversarial_challenge_models.py` -> verify 51/51 PASSED, 0 FAILED, exit code 0.
   - `pytest tests/ -v` -> verify 284+ passed, 0 failed, exit code 0.
   - `python -m ruff check src/ tests/` -> verify 0 violations.
5. Write your comprehensive report in `handoff.md` and send message to parent when complete.
