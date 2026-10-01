# BRIEFING — 2026-09-30T13:17:30Z

## Mission
Explore, catalog, and document the automated test suite design, pytest structure, official UTE C 15-105 worked benchmark scenarios, and corner cases for verifying the `ampy` calculation engine.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: benchmark_specialist, test_architect, normative_verifier
- Working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3
- Original parent: 776386d9-70f0-46fd-896e-befc19ccbade
- Milestone: survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Output reports to c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\benchmarks.md and handoff.md
- Adhere strictly to NF C 15-100 and UTE C 15-105 standards
- Use send_message to communicate back to parent

## Current Parent
- Conversation ID: 776386d9-70f0-46fd-896e-befc19ccbade
- Updated: 2026-09-30T13:17:30Z

## Investigation State
- **Explored paths**:
  - `c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md`
  - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_orchestrator_1\BRIEFING.md`
  - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md`
  - NF C 15-100 Part 5-52 and UTE C 15-105 calculation rules and tables.
- **Key findings**:
  - Identified and mathematically verified 5 official worked benchmark scenarios covering 3P motor, 1P lighting, long-run feeder (voltage drop dominated), multi-cable grouping (N=6 touching), and high ambient temperature (50°C).
  - Designed the complete 4-tier test pyramid: Tier 1 (isolated formulas & table lookups), Tier 2 (boundary & corner cases), Tier 3 (32 pairwise method x material x insulation x phase combinations), Tier 4 (UTE C 15-105 acceptance benchmarks & CLI).
  - Established floating-point precision rules: exact match for discrete values ($S, I_n$), 0.5% relative tolerance on $\Delta U$, 0.05% absolute tolerance on $\Delta U\%$.
- **Unexplored areas**:
  - Multi-conductor parallel runs per phase (outside standard baseline scope).
  - Buried cable direct soil thermal resistivity (Method D / Table 52J), which is an optional future extension.

## Key Decisions Made
- Standardized all 5 benchmark test vectors with exact intermediate values and short-circuit adiabatic limits ($I^2 t \le k^2 S^2$).
- Aligned test architecture directly with `ampy` Pydantic models from explorer_survey_2 (`CircuitDefinition`, `ElectricalLoad`, `CableSpecs`, `InstallationConditions`).
- Completed `benchmarks.md` containing exhaustive specifications.

## Artifact Index
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\DISPATCH.md` — Dispatch log
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\BRIEFING.md` — Persistent briefing
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\progress.md` — Progress & heartbeat
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\benchmarks.md` — Exhaustive benchmark scenarios & 4-tier test architecture
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\handoff.md` — 5-component handoff report
