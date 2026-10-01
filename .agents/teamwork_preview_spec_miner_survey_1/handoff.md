# Handoff Report: Normative Specification Extraction for NF C 15-100 & UTE C 15-105

**Agent**: `teamwork_preview_spec_miner_survey_1`  
**Milestone**: Phase 0 Survey  
**Deliverable**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md`

---

## 1. Observation
- Dispatch instructions requested comprehensive extraction of NF C 15-100 (Part 5-52) and UTE C 15-105 formulas and reference tables covering:
  1. Operating current $I_b$ (Single-phase 230V, Three-phase 400V, DC, neutral harmonics).
  2. Installation methods B, C, E, F (conduits, trays, free air, embedded) mapped to standard codes (Table 52C / 52G / Table BB/BC).
  3. Correction factors $k_1$ (mode of installation), $k_2$ (grouping Table 52N), $k_3$ (ambient temperature Table 52K), $k_4$ (soil resistivity Table 52M), and $k_h$ (third harmonics Table E.52.1).
  4. Permissible reference current table $I_0$ across all 16 standard cross-sections (1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300 mm²) for Copper and Aluminium, PVC and XLPE, 2 and 3 loaded conductors, for methods B, C, E, F.
  5. Sizing coordination conditions ($I_b \le I_n \le I_z$ and $I'_z = I_n / \prod k_i \le I_0$).
  6. Voltage drop calculation ($\Delta U = b \cdot (\rho_1 \frac{L}{S} \cos\varphi + \lambda L \sin\varphi) \cdot I_b$, $\rho_1(\text{Cu}) = 0.023\ \Omega\cdot\text{mm}^2/\text{m}$, $\rho_1(\text{Al}) = 0.037\ \Omega\cdot\text{mm}^2/\text{m}$, $\lambda = 0.08\ \text{m}\Omega/\text{m}$).
  7. Thermal short-circuit withstand ($I^2 t \le k^2 S^2$, with $k = 115, 143, 76, 94$).
- Web search verification against authoritative international and French standard databases (IEC 60364-5-52 Tables B.52.2 to B.52.12, NF C 15-100 Table 52H, UTE C 15-105 Tables BD, BE, BF, BJ, Schneider Electric Electrical Installation Guide) confirmed exact numerical tables and formulas.
- Python 3.13.5 environment confirmed available in `c:\Users\cjose\antigravity project\ampy`.

---

## 2. Logic Chain
1. Sizing an electrical conductor in accordance with NF C 15-100 and UTE C 15-105 requires satisfying three independent, simultaneous normative criteria: thermal capacity under continuous load ($I_b \le I_n \le I_z$), voltage drop limits ($\Delta U\% \le \Delta U_{\max}$), and short-circuit thermal withstand ($I^2 t \le k^2 S^2$).
2. Continuous load sizing starts by calculating the design operating current $I_b$ from active power $P$, apparent power $S$, or direct current $I$, with appropriate single-phase ($V=230\text{V}$) or three-phase ($U=400\text{V}, \sqrt{3}$) relations. In circuits with third-harmonic content exceeding 15% (per Table E.52.1), neutral sizing and harmonic derating $k_h$ ($0.86$ or neutral-current sizing) must be applied.
3. The cable's actual continuous current capacity $I_z$ is obtained by applying environmental derating factors $\prod k_i = k_1 \cdot k_2 \cdot k_3 \cdot k_4 \cdot k_h$ to the reference current $I_0$. Conversely, the required fictitious current $I'_z = I_n / \prod k_i$ enables direct lookup in the reference table $I_0$.
4. Reference current $I_0$ values are strictly governed by conductor material (Cu / Al), insulation material (PVC max 70°C / XLPE max 90°C), number of loaded conductors (2 for single-phase, 3 for three-phase), and installation reference method (B, C, E, F). All values for sections 1.5 to 300 mm² have been tabulated into `normative_specs.md`.
5. Voltage drop calculation per UTE C 15-105 §5.3 accounts for hot resistance $\rho_1 = 1.25 \times \rho_{20}$ and reactance $\lambda = 0.08\ \text{m}\Omega/\text{m}$, with circuit factor $b=2$ (single-phase) or $b=1$ (three-phase). If the section selected for thermal capacity exceeds $\Delta U_{\max}$ (typically 3% or 5%), the engine must iterate upwards through the standard cross-section series until the constraint is met.
6. The adiabatic withstand criterion $S \ge \frac{\sqrt{I^2 t}}{k}$ sets a hard lower bound on cross-section during short-circuit faults, using verified constants $k \in \{115, 143, 76, 94\}$.
7. The resulting documentation in `normative_specs.md` provides all formulas, lookup tables, boundary conditions, and edge cases necessary for the implementation track and benchmark test harness.

---

## 3. Caveats
- Underground installations (Method D / Table 52J / Table BE) use a ground reference temperature of 20°C and default soil thermal resistivity of $1.0\ \text{K}\cdot\text{m/W}$ (NF C 15-100) or $2.5\ \text{K}\cdot\text{m/W}$ (IEC). Method D is documented in Section 2 & 3 but secondary to above-ground methods B, C, E, F in core engine requirements.
- For Aluminium conductors, NF C 15-100 residential limits minimum cross-section to 10 mm², while industrial networks standardly use Al for $S \ge 16\text{ mm}^2$.
- Circuit breaker trip curves (B, C, D) govern instantaneous magnetic trip thresholds ($3-5 I_n, 5-10 I_n, 10-14 I_n$) for fault clearing time verification; for durations $t < 0.1\text{ s}$, manufacturer energy limitation $(I^2 t)_{\max}$ curves govern rather than $I_{cc}^2 \times t$.

---

## 4. Conclusion
Normative extraction is complete, fully verified, and documented in:
`c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md`

The document covers:
1. Complete mathematical formulas for $I_b$ across 1-phase, 3-phase, DC, and neutral harmonics.
2. Complete classification of installation methods B, C, E, F and standard codes.
3. Complete derating factors $k_1, k_2, k_3, k_4, k_h, k_p$ with formulas and lookup tables.
4. Complete $I_0$ reference current tables for all 16 standard cross-sections (1.5 to 300 mm²), Cu and Al, PVC and XLPE, 2 and 3 loaded conductors, for methods B, C, E, F.
5. Exact voltage drop formulation per UTE C 15-105 §5.3 with resistivity $\rho_1$ and reactance $\lambda$.
6. Adiabatic short-circuit withstand formulation ($I^2 t \le k^2 S^2$) with all $k$ constants.
7. Step-by-step sizing algorithm, discovered feature catalog, and edge cases matrix.

---

## 5. Verification Method
1. Inspect deliverable file:
   `view_file(AbsolutePath="c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md")`
2. Cross-reference values:
   - Operating current for $10\text{ kW}$, 3-phase 400V, $\cos\varphi = 0.8$:
     $I_b = \frac{10000}{\sqrt{3} \times 400 \times 0.8} = 18.04\text{ A}$.
   - Reference current for 2.5 mm² Cu XLPE 3-loaded on tray (Method E): $I_0 = 36\text{ A}$.
   - Voltage drop for 25 m, 2.5 mm² Cu ($I_b = 18.04\text{ A}$, $\cos\varphi = 0.8, \sin\varphi = 0.6$, 3-phase $b=1$, $\lambda=0$):
     $\Delta U = 1 \times (0.023 \times \frac{25}{2.5} \times 0.8) \times 18.04 = 0.184 \times 18.04 = 3.32\text{ V}$ ($0.83\% < 5\%$).
   - Short-circuit withstand for $I_{cc} = 3\text{ kA}, t = 0.05\text{ s}$ on Cu/XLPE ($k=143$):
     $S_{\min} = \frac{\sqrt{3000^2 \times 0.05}}{143} = \frac{670.82}{143} = 4.69\text{ mm}^2 \implies 6\text{ mm}^2$.
