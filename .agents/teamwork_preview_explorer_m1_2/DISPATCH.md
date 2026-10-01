## 2026-09-30T13:22:15Z

<USER_REQUEST>
You are teamwork_preview_explorer_m1_2.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_2
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md
Architecture survey: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md
Normative specs: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md

You MUST first read ORIGINAL_REQUEST.md, PROJECT.md, and the survey documents.

Task:
Produce a detailed implementation blueprint for Milestone 1 (M1) pure mathematical calculation functions in `src/ampy/core/formulas.py`:
1. `calculate_ib(...)`:
   - Single-phase 230V: P / (V * cos_phi) or S / V or direct I.
   - Three-phase 400V: P / (sqrt(3) * U * cos_phi) or S / (sqrt(3) * U) or direct I.
   - DC: P / U or direct I.
   - Third harmonic derating factor per Table E.52.1.
2. `calculate_voltage_drop(...)`:
   - dU = b * (rho1 * (L / S) * cos_phi + lambda * L * sin_phi) * Ib
   - b = 2 for single-phase, b = 1 for three-phase.
   - rho1 = 0.023 ohm.mm2/m (Cu), 0.037 ohm.mm2/m (Al) or temp-adjusted.
   - lambda = 0.08 mOhm/m (0.00008 ohm/m) for S > 16 mm2, 0.0 for S <= 16 mm2.
   - dU_pct = 100 * dU / U_ref (230V or 400V).
3. `calculate_thermal_stress_min_section(ik_a, time_s, material, insulation)`:
   - S_min = sqrt(ik_a^2 * time_s) / k.
   - k = 115 (Cu/PVC), 143 (Cu/XLPE), 76 (Al/PVC), 94 (Al/XLPE).
4. `calculate_k3_temp_factor(insulation, temp_c)`:
   - Analytical square root formula and exact lookup equivalence.

Write your blueprint to `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_2\formulas_plan.md` and deliver `handoff.md`. Communicate via send_message to parent when complete.
</USER_REQUEST>
