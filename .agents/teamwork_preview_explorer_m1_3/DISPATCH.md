## 2026-09-30T13:22:15Z
You are teamwork_preview_explorer_m1_3.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_3
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md
Architecture survey: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md
Benchmarks survey: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\benchmarks.md
Normative specs: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md

You MUST first read ORIGINAL_REQUEST.md, PROJECT.md, and the survey documents.

Task:
Produce a detailed test strategy and test case design blueprint for Milestone 1 unit tests:
1. `tests/unit/test_models.py`:
   - Valid instantiations of all models.
   - Invalid configurations (e.g. negative power, cos_phi > 1.0 or <= 0, mutually exclusive load inputs missing or conflicting).
   - Serialization to/from JSON and dict.
2. `tests/unit/test_formulas.py`:
   - Exact numerical assertions for Ib across 1P, 3P, DC, active kW, apparent kVA, current A.
   - Voltage drop dU and dU% assertions distinguishing single-phase (b=2) and three-phase (b=1) with exact 0.5% tolerance.
   - Thermal stress S_min calculations with all material/insulation combinations.
   - Temperature factor k3 formula assertions.

Write your blueprint to `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_3\unit_tests_plan.md` and deliver `handoff.md`. Communicate via send_message to parent when complete.
