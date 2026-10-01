## 2026-09-30T13:22:15Z

<USER_REQUEST>
You are teamwork_preview_explorer_m1_1.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_1
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md
Architecture survey: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md
Normative specs: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md

You MUST first read ORIGINAL_REQUEST.md, PROJECT.md, and the survey documents.

Task:
Produce a detailed implementation blueprint for Milestone 1 (M1) components:
1. `pyproject.toml`:
   - Project metadata (`name = "ampy"`, version, description, python >= 3.10).
   - Dependencies: `pydantic>=2.0`, `typer>=0.12`, `rich>=13.0`, `pyyaml>=6.0`.
   - Optional dev dependencies: `pytest>=8.0`, `pytest-cov>=4.0`.
   - Entry point: `[project.scripts] ampy = "ampy.cli.main:app"`.
   - Build system: setuptools (already present in Python 3.13 environment).
2. `src/ampy/core/models.py`:
   - Enums: `PhaseSystem` (SINGLE_PHASE, THREE_PHASE, DC), `ConductorMaterial` (CU, AL), `InsulationType` (PVC, XLPE), `InstallationMethod` (B, C, E, F), `LimitingConstraint` (AMPACITY, VOLTAGE_DROP, THERMAL_STRESS).
   - Pydantic models: `ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `CircuitDefinition`, `VoltageDropResult`, `IntermediateFactors`, `SizingResult`.
   - Strict field validations, mutual exclusivity for load inputs (`power_kw`, `apparent_power_kva`, `current_a`).
   - Units, docstrings, JSON schema export support.

Write your blueprint to `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_1\models_plan.md` and deliver `handoff.md`. Communicate via send_message to parent when complete.
</USER_REQUEST>
