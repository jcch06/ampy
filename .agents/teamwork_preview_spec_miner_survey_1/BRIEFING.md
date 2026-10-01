# BRIEFING — 2026-09-30T13:08:45Z

## Mission
Extract and document exhaustive normative specifications, formulas, tables, and rules for NF C 15-100 Part 5-52 and UTE C 15-105 for the ampy cable sizing calculation engine.

## 🔒 My Identity
- Archetype: teamwork_preview_spec_miner
- Roles: spec_miner
- Working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1
- Original parent: 776386d9-70f0-46fd-896e-befc19ccbade
- Milestone: survey

## 🔒 Key Constraints
- READ-ONLY / SPEC MINER ONLY: Do NOT implement code, strictly extract and document authoritative specifications.
- Prioritize authoritative French electrical standards: NF C 15-100 (Part 5-52) / IEC 60364-5-52 and practical calculation guide UTE C 15-105.
- Provide exhaustive numerical tables and rigorous mathematical formulas with exact units and definitions.
- Write findings to normative_specs.md and self-contained handoff.md.

## Current Parent
- Conversation ID: 776386d9-70f0-46fd-896e-befc19ccbade
- Updated: 2026-09-30T13:08:45Z

## Task Summary
- **What to build**: Complete normative specification extraction document `normative_specs.md` covering Ib formulas, installation methods B/C/E/F, derating factors k1, k2, k3, k4, kn, permissible current Iz and full reference table I0 (1.5 to 300 mm², Cu & Al, PVC & XLPE, 2 & 3 loaded conductors), voltage drop dU, and short-circuit thermal withstand (I²t <= k²S²).
- **Success criteria**: Detailed, accurate, self-contained documentation with edge cases and tabular specifications ready for engine implementation and testing.
- **Interface contracts**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md`
- **Code layout**: Specification metadata in `.agents/teamwork_preview_spec_miner_survey_1/`

## Key Decisions Made
- Structuring `normative_specs.md` to cover all 7 requested domains plus standard protective device ratings In series.
- Tabulating exact normative I0 reference currents from NF C 15-100 Table 52C / UTE C 15-105 Table BJ.
- Completed comprehensive extraction and validation against IEC 60364-5-52 and UTE C 15-105. All 16 standard cross-sections tabulated for Cu and Al, PVC and XLPE, 2 and 3 loaded conductors, Methods B, C, E, F.
- Handled check-in message from parent orchestrator.

## Artifact Index
- `c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md` — Original user request
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\DISPATCH.md` — Dispatch log
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\BRIEFING.md` — Persistent briefing
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\progress.md` — Liveness & progress tracking
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md` — Normative specification document (Complete)
- `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\handoff.md` — Self-contained handoff report (Complete)

## Loaded Skills
- None

