## 2026-09-30T13:45:41Z
You are teamwork_preview_explorer_m1_fix_2.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_2
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md
Reviewer 2 feedback: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_reviewer_m1_2\handoff.md
Challenger 1 feedback: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_challenger_m1_1\handoff.md

You MUST first read ORIGINAL_REQUEST.md, PROJECT.md, and the feedback from Reviewer 2 and Challenger 1.

Task:
Formulate an exact remediation specification for `src/ampy/core/formulas.py`:
1. Coerce system strings in `calculate_ib` and `calculate_voltage_drop`:
   - If `isinstance(system, str)`: normalize via `PhaseSystem(system)` so that inputs like `"1P"`, `"3P"`, `"DC"`, `"single_phase"`, `"three_phase"` work seamlessly without raising `ValueError: Unsupported system type`.
2. Material string coercion in `calculate_thermal_stress_min_section`:
   - Normalize string aliases like `"copper"`, `"cu"`, `"aluminium"`, `"al"` to standard `ConductorMaterial` or uppercase keys (`"Cu"`, `"Al"`).
3. Defensive handling in `calculate_voltage_drop`:
   - Validate `voltage_v > 0.0` and `u_ref > 0.0` to prevent `ZeroDivisionError` or negative percentages if zero/negative voltages are passed.
4. Clean up any dead code / unused parameters.

Write your plan to `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_2\formulas_fix_plan.md` and deliver `handoff.md`. Communicate via send_message to parent when complete.
