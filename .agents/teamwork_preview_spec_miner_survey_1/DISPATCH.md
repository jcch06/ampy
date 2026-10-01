# DISPATCH Log

## 2026-09-30T13:08:08Z

You are teamwork_preview_spec_miner_survey_1.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md

You MUST first read ORIGINAL_REQUEST.md.

Task:
Perform a comprehensive normative specification extraction for the French electrical installation standards NF C 15-100 (Part 5-52 / IEC 60364-5-52) and the practical calculation guide UTE C 15-105.

Investigate and thoroughly document in `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md`:
1. Design operating current Ib:
   - Single-phase (230V): Ib = P / (V * cos_phi) for active power P (kW); Ib = S / V for apparent power S (kVA); direct current Ib = I.
   - Three-phase (400V): Ib = P / (sqrt(3) * U * cos_phi) for P (kW); Ib = S / (sqrt(3) * U) for S (kVA); direct current Ib = I.
   - Neutral current, harmonic considerations (THD-N, k_H3 if applicable).
2. Reference installation methods (NF C 15-100 Table 52C / UTE C 15-105 Table BB/BC):
   - Installation method letters: B, C, E, F (conduits, cable trays, free air, embedded).
   - Standard reference method codes (e.g., methods 1, 2, 3... to letter mapping).
3. Correction / derating factors (Table 52E, 52G, 52H, 52I / UTE C 15-105 Tables BD, BE, BF):
   - k1: Installation method factor.
   - k2: Grouping factor (number of circuits/cables, laying on tray, touching, spaced).
   - k3: Ambient temperature factor for PVC (max 70°C) and XLPE / PR (max 90°C) across temperatures from 10°C to 60°C (reference 30°C in air, 20°C in ground).
   - Any additional factors (k4 for buried cables/soil thermal resistivity, kn for harmonics).
4. Permissible current Iz and coordination:
   - Complete reference current table I0 (Table 52J / 52C / UTE C 15-105 Table BJ) for standard cross-sections: 1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300 mm²; Copper (Cu) and Aluminium (Al); PVC and XLPE; 2 loaded conductors (single phase) and 3 loaded conductors (three phase); for letters B, C, E, F.
   - Permissible current formula: Iz = I0 * prod(ki).
   - Required rating condition: Ib <= In <= Iz (and fictive required current I'z = In / prod(ki) <= I0).
5. Standard cross-section series (1.5 to 300 mm²).
6. Voltage drop formula according to UTE C 15-105 §5.3 / NF C 15-100:
   - dU = b * (rho1 * (L / S) * cos_phi + lambda * L * sin_phi) * Ib
   - b = 2 for single-phase, b = 1 for three-phase.
   - Conductor resistivity rho1 at normal operating temperature:
     rho1 for Cu (0.023 ohm.mm²/m or 1.25 * 0.01851 at 70/90°C or UTE C 15-105 convention) and Al (0.036 or 0.037 ohm.mm²/m).
   - Conductor linear reactance lambda (typically 0.08 mOhm/m = 0.00008 ohm/m for cables, or 0 for small cross sections S <= 16mm²).
   - Relative voltage drop: dU% = 100 * dU / U0 (or U).
   - Standard limits dU_max (lighting 3% or 5%, other uses 5% or 8%).
7. Thermal stress limit / short-circuit withstand:
   - Adiabatic formula: I²t <= k² * S² => S_min = sqrt(I²t) / k.
   - Value of factor k for Cu/PVC (115), Cu/XLPE (143), Al/PVC (76), Al/XLPE (94).

## 2026-09-30T13:20:09Z

**Context**: Phase 0 Survey for NF C 15-100 / UTE C 15-105 normative specifications.
**Content**: Checking in on your progress compiling `normative_specs.md` and `handoff.md`. Explorer 2 (architecture) and Explorer 3 (benchmarks) have completed their deliverables. How is the table extraction proceeding?
**Action**: Please provide a quick status update or finalize `normative_specs.md` and deliver your handoff report.

