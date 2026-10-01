## 2026-09-30T13:29:22Z
You are teamwork_preview_worker_m1_1.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_worker_m1_1
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md

Explorer Blueprints to implement:
- Models & Packaging: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_1\models_plan.md
- Pure Formulas: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_2\formulas_plan.md
- Unit Tests Strategy: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_3\unit_tests_plan.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (You exclusively own and will write these files):
- `c:\Users\cjose\antigravity project\ampy\pyproject.toml`
- `c:\Users\cjose\antigravity project\ampy\src\ampy\__init__.py`
- `c:\Users\cjose\antigravity project\ampy\src\ampy\py.typed`
- `c:\Users\cjose\antigravity project\ampy\src\ampy\core\__init__.py`
- `c:\Users\cjose\antigravity project\ampy\src\ampy\core\models.py`
- `c:\Users\cjose\antigravity project\ampy\src\ampy\core\formulas.py`
- `c:\Users\cjose\antigravity project\ampy\tests\unit\__init__.py`
- `c:\Users\cjose\antigravity project\ampy\tests\unit\test_models.py`
- `c:\Users\cjose\antigravity project\ampy\tests\unit\test_formulas.py`

Task:
1. Implement `pyproject.toml` with setuptools build backend, dependencies (`pydantic>=2.0`, `typer>=0.12`, `rich>=13.0`, `pyyaml>=6.0`), and dev dependencies (`pytest>=8.0`, `pytest-cov>=4.0`).
2. Implement `src/ampy/core/models.py` with all Pydantic v2 schemas, Enums with coercion hooks, strict field validation, and JSON serialization as specified in `models_plan.md`.
3. Implement `src/ampy/core/formulas.py` with all pure calculation functions (`calculate_ib`, `calculate_voltage_drop`, `calculate_thermal_stress_min_section`, `calculate_k3_temp_factor`, helpers) conforming strictly to NF C 15-100 and UTE C 15-105 §5.3 as specified in `formulas_plan.md`.
4. Implement `tests/unit/test_models.py` and `tests/unit/test_formulas.py` covering all positive, boundary, and invalidation cases specified in `unit_tests_plan.md`.
5. Install the package in editable mode (`pip install -e .`) and run `pytest tests/unit/ -v`. Verify that 100% of unit tests pass with exit code 0.
6. Write a comprehensive `handoff.md` in your working directory documenting the files created, build/test commands executed, exact results, and verification method. Communicate via send_message to parent when complete.
