# BRIEFING — 2026-09-30T13:11:00Z

## Mission
Explore and design the software architecture, Python modular packaging, Pydantic schemas, and Typer/Rich CLI interface for the `ampy` electrical sizing calculation engine.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: explorer, software_architect, api_designer
- Working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2
- Original parent: 776386d9-70f0-46fd-896e-befc19ccbade
- Milestone: Survey Phase (Architecture & CLI Design)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement production source code
- Strictly follow NF C 15-100 & UTE C 15-105 standards
- All files written only in own working directory (.agents/teamwork_preview_explorer_survey_2/)
- Must produce architecture.md, handoff.md, and send_message to parent

## Current Parent
- Conversation ID: 776386d9-70f0-46fd-896e-befc19ccbade
- Updated: 2026-09-30T13:11:00Z

## Investigation State
- **Explored paths**:
  - `c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md` (lines 1-46)
  - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_orchestrator_1\BRIEFING.md`
  - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\DISPATCH.md`
  - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\DISPATCH.md`
  - Python runtime environment: Python 3.13.5 with Pydantic 2.11.7 installed; Typer, Rich, PyYAML, and pytest to be installed via `pip install -e .` with dependencies in pyproject.toml.
- **Key findings**: Complete modern src-layout architecture designed with pure calculation functions (`ampy.core.formulas`), normative lookup tables (`ampy.core.tables`), Pydantic v2 schemas (`ampy.core.models`), multi-constraint solver (`ampy.core.engine`), Typer/Rich CLI (`ampy.cli`), and top-level export API.
- **Unexplored areas**: Production implementation of code and tests (reserved for Worker agent in implementation milestones).

## Key Decisions Made
- Architecture uses PEP 517/518/621 `src/ampy/` layout with `pyproject.toml` based on `setuptools` (already present in environment).
- Pydantic v2 domain schemas (`ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `CircuitDefinition`, `SizingResult`, etc.) with strict field validators.
- Functional mathematical core (`calculate_ib`, `calculate_voltage_drop`, `calculate_thermal_stress`) completely decoupled from tables and orchestration.
- `SizingEngine` implements multi-constraint iterative section incrementation (Iz -> dU -> thermal stress).
- Rich terminal interface with stylized cards, result badges, and normative calculation audit tables.

## Artifact Index
- c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\DISPATCH.md — Dispatch log
- c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\BRIEFING.md — Situational awareness
- c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\progress.md — Liveness heartbeat
- c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md — Complete architectural specification
- c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\handoff.md — 5-component handoff report
