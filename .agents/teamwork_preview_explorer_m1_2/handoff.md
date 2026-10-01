# Handoff Report: Milestone 1 Pure Mathematical Calculation Core (`src/ampy/core/formulas.py`)

**Agent**: `teamwork_preview_explorer_m1_2`  
**Milestone**: Milestone 1 (M1) — Foundation & Formulas Blueprint  
**Recipient**: `parent` (`776386d9-70f0-46fd-896e-befc19ccbade`)  
**Date**: 2026-09-30  
**Deliverable**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_2\formulas_plan.md`  

---

## 1. Observation

- **User Request & Scope**: Dispatch mandated a comprehensive implementation blueprint for pure mathematical calculation functions in `src/ampy/core/formulas.py`:
  1. `calculate_ib(...)`: Single-phase 230V ($P / (V \cos\varphi)$, $S / V$, direct $I$), Three-phase 400V ($P / (\sqrt{3} U \cos\varphi)$, $S / (\sqrt{3} U)$, direct $I$), DC ($P / U$, direct $I$), and third harmonic derating factor per Table E.52.1.
  2. `calculate_voltage_drop(...)`: $\Delta U = b \cdot (\rho_1 \frac{L}{S} \cos\varphi + \lambda L \sin\varphi) \cdot I_b$, with $b=2$ for 1P/DC, $b=1$ for 3P, $\rho_1 = 0.023\ \Omega\cdot\text{mm}^2/\text{m}$ (Cu) and $0.037\ \Omega\cdot\text{mm}^2/\text{m}$ (Al) or temp-adjusted, $\lambda = 0.08\ \text{m}\Omega/\text{m}$ for $S > 16\text{ mm}^2$ and $0.0$ for $S \le 16\text{ mm}^2$, and $\Delta U\% = 100 \cdot \Delta U / U_{\text{ref}}$.
  3. `calculate_thermal_stress_min_section(ik_a, time_s, material, insulation)`: $S_{\min} = \sqrt{I_k^2 t} / k$, with $k \in \{115, 143, 76, 94\}$.
  4. `calculate_k3_temp_factor(insulation, temp_c)`: Analytical square root formula $k_3 = \sqrt{\frac{\theta_{\max} - \theta_{\text{ambient}}}{\theta_{\max} - \theta_0}}$ and Table 52K lookup equivalence.
- **Reference Context Inspected**:
  - `c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md`: Sizing requirements R1, R2, R3.
  - `c:\Users\cjose\antigravity project\ampy\PROJECT.md`: Interface contracts between `formulas.py` and `models.py` (lines 93–97).
  - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md`: Normative extractions of NF C 15-100 Table 52K, Table E.52.1, Section 434.5.2, and UTE C 15-105 §5.3.
  - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\benchmarks.md`: The 5 official worked UTE C 15-105 benchmark scenarios (`BENCH-01` to `BENCH-05`).
- **Normative Specificity on Three-Phase Voltage Drop**:
  - In UTE C 15-105 §5.3, with $b=1$, $\Delta U$ represents the voltage drop across a single phase conductor ($\Delta V_{\text{ph}}$).
  - The relative drop $\Delta U\%$ is evaluated against phase-to-neutral voltage $V_n = 230\text{ V}$ (or $U_{\text{line}} / \sqrt{3}$).
  - Line-to-line drop $\Delta U_{\text{line}} = \sqrt{3} \times \Delta U$, yielding identical percentage: $\frac{\sqrt{3} \Delta U}{400} = \frac{\Delta U}{230.94} \approx \frac{\Delta U}{230}$.

---

## 2. Logic Chain

1. **Design Operating Current ($I_b$)**:
   - Single-phase AC load draws $I_b = \frac{P}{V \cos\varphi}$ or $\frac{S}{V}$ where $V$ is line-to-neutral voltage ($230\text{ V}$).
   - Three-phase balanced load draws $I_b = \frac{P}{\sqrt{3} U \cos\varphi}$ or $\frac{S}{\sqrt{3} U}$ where $U$ is line-to-line voltage ($400\text{ V}$).
   - Direct current circuit draws $I_b = \frac{P}{U_{\text{dc}}}$ or direct $I$.
   - Mutual exclusivity validation guarantees no conflicting or ambiguous inputs.
   - For non-linear loads with third harmonics, IEC 60364-5-52 Table E.52.1 mandates derating factor $k_h = 1.00$ ($i_{h3} \le 15\%$), $k_h = 0.86$ ($15\% < i_{h3} \le 33\%$ sized on phase $I_b$), $k_h = 0.86$ ($33\% < i_{h3} \le 45\%$ sized on neutral $I_N = 3 i_{h3} I_b$), and $k_h = 1.00$ ($i_{h3} > 45\%$ sized on neutral $I_N$).

2. **Voltage Drop ($\Delta U$ and $\Delta U\%$)**:
   - By Ohm's law and AC line impedance, the phase drop is $\Delta V = I_b \cdot (R \cos\varphi + X \sin\varphi)$ where $R = \rho_1 \frac{L}{S}$ and $X = \lambda L$.
   - In a balanced 3-phase system ($b=1$), neutral current is zero, so each phase experiences drop $\Delta V$. Sizing compares this to phase nominal voltage $V_n = 230\text{ V}$.
   - In a single-phase system ($b=2$), current flows forward through the phase conductor and returns through the neutral conductor, doubling the loop impedance ($\Delta U = 2 \Delta V$).
   - For small cross-sections ($S \le 16\text{ mm}^2$), internal inductance and cable spacing produce negligible reactance ($\lambda = 0.0$). For $S > 16\text{ mm}^2$, standard low-voltage multicore spacing sets $\lambda = 0.08\ \text{m}\Omega/\text{m} = 0.00008\ \Omega/\text{m}$.
   - Resistivity at operating temperature is standardized as $\rho_1 = 0.023\ \Omega\cdot\text{mm}^2/\text{m}$ for Copper and $0.037\ \Omega\cdot\text{mm}^2/\text{m}$ for Aluminium ($1.25 \times \rho_{20}$ convention). Optional temperature-adjustment formula $\rho(\theta) = \rho_{20} [1 + \alpha_{20}(\theta - 20)]$ is also provided.

3. **Conductor Thermal Stress Under Short-Circuit ($S_{\min}$)**:
   - For fault clearing times $t \le 5\text{ s}$, Joule heating is adiabatic: $I_k^2 t \le k^2 S^2 \implies S_{\min} = \frac{\sqrt{I_k^2 t}}{k} = \frac{I_k \sqrt{t}}{k}$.
   - Constant $k$ derived from heat capacity, conductivity, and allowable temperature delta ($\theta_i \to \theta_f$):
     - Cu / PVC ($70^\circ\text{C} \to 160^\circ\text{C}$): $k = 115$
     - Cu / XLPE ($90^\circ\text{C} \to 250^\circ\text{C}$): $k = 143$
     - Al / PVC ($70^\circ\text{C} \to 160^\circ\text{C}$): $k = 76$
     - Al / XLPE ($90^\circ\text{C} \to 250^\circ\text{C}$): $k = 94$
   - Fault times $t > 5.0\text{ s}$ breach the adiabatic regime and are rejected.

4. **Ambient Temperature Derating Factor ($k_3$)**:
   - The fundamental heat balance of a cable in steady state yields:
     $$\frac{I^2 R}{\Delta \theta} = \text{const} \implies k_3 = \sqrt{\frac{\theta_{\max} - \theta_{\text{ambient}}}{\theta_{\max} - \theta_0}}$$
   - Evaluating this analytical square root across $10^\circ\text{C}$ to $60^\circ\text{C}$ with $\theta_0 = 30^\circ\text{C}$ produces exact rounded values matching every single cell of NF C 15-100 Table 52K within $< 0.005$ delta.
   - Operating at or above $\theta_{\max}$ ($70^\circ\text{C}$ PVC, $90^\circ\text{C}$ XLPE) produces physical breakdown before current flows and is strictly rejected with `ValueError`.

---

## 3. Caveats

1. **Voltage Reference for Three-Phase Systems**: In UTE C 15-105 §5.3, with $b=1$, $\Delta U$ is the line-to-neutral drop ($\Delta V_{\text{ph}}$). When computing $\Delta U\% = 100 \cdot \Delta U / U_{\text{ref}}$, $U_{\text{ref}}$ must be $230\text{ V}$ (not $400\text{ V}$). The formula function automatically handles this by normalizing $U_{\text{ref}} = 230\text{ V}$ if $U_n \approx 400\text{ V}$ unless the user overrides `u_ref`.
2. **Boundary Threshold Equality in Floating Point**: In automated sizing engines, when $\Delta U\% = 5.00000000001\%$, strict IEEE-754 inequality `du_pct <= 5.0` would reject the section. The function implements tolerance-aware evaluation `du_percent <= (du_max_percent + 1e-9)` to guarantee numerical stability.
3. **Harmonic Cancellation**: In circuits with heavy 3rd harmonic content, neutral current can exceed phase current ($I_N > I_b$). In such cases, cable sizing must be based on $I_N$, and the neutral cross-section must never be reduced below the phase section.

---

## 4. Conclusion

The specification and reference code for `src/ampy/core/formulas.py` are complete, mathematically validated, and documented in:
`c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_2\formulas_plan.md`

All four core calculations and their supporting functions are fully specified:
1. `calculate_ib(system, voltage_v, power_w=None, apparent_power_va=None, current_a=None, cos_phi=1.0, power_kw=None, apparent_power_kva=None) -> float`
2. `calculate_harmonic_derating(ib_a: float, ih3_ratio: float) -> HarmonicResult`
3. `calculate_voltage_drop(system, length_m, section_mm2, ib_a, cos_phi, material, voltage_v=400.0, du_max_percent=5.0, operating_temp_c=None, u_ref=None) -> VoltageDropResult`
4. `calculate_thermal_stress_min_section(ik_a: float, time_s: float, material, insulation) -> float`
5. `calculate_k3_temp_factor(insulation, temp_c, in_ground=False, rounded=True) -> float`
6. Physical helper functions: `calculate_sin_phi`, `get_conductor_resistivity`, `get_linear_reactance`.

---

## 5. Verification Method

To independently verify the mathematical blueprint against standard values:

1. **Verify Deliverable Content**:
   `view_file(AbsolutePath="c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_2\formulas_plan.md")`

2. **Cross-Check with Worked UTE C 15-105 Benchmark Scenarios**:
   - **Scenario 1 (Three-phase motor $18.5\text{ kW}$, $400\text{ V}$, $\cos\varphi = 0.85$, $L = 45\text{ m}$, $S = 4\text{ mm}^2$ Cu)**:
     - $I_b = \frac{18500}{\sqrt{3} \times 400 \times 0.85} = 31.415\text{ A}$.
     - $\Delta U = 1 \times (0.023 \times \frac{45}{4} \times 0.85 + 0.0) \times 31.415 = 0.2199 \times 31.415 = 6.969\text{ V}$.
     - $\Delta U\% = \frac{6.969}{230} \times 100 = 3.03\% \le 5.0\%$.
   - **Scenario 2 (Single-phase lighting $3.68\text{ kW}$, $230\text{ V}$, $\cos\varphi = 1.0$, $L = 35\text{ m}$, $S = 4\text{ mm}^2$ Cu)**:
     - $I_b = \frac{3680}{230 \times 1.0} = 16.000\text{ A}$.
     - $\Delta U = 2 \times (0.023 \times \frac{35}{4} \times 1.0) \times 16.0 = 6.440\text{ V}$.
     - $\Delta U\% = \frac{6.440}{230} \times 100 = 2.80\% \le 3.0\%$.
   - **Scenario 3 (Three-phase long run $37.0\text{ kW}$, $400\text{ V}$, $\cos\varphi = 0.85$, $L = 220\text{ m}$, $S = 25\text{ mm}^2$ Cu)**:
     - $I_b = 62.829\text{ A}$.
     - $\lambda = 0.00008\ \Omega/\text{m}$, $\sin\varphi = \sqrt{1 - 0.85^2} = 0.52678$.
     - $\Delta U = 1 \times (0.023 \times \frac{220}{25} \times 0.85 + 0.00008 \times 220 \times 0.52678) \times 62.829 = 11.392\text{ V}$.
     - $\Delta U\% = \frac{11.392}{230} \times 100 = 4.95\% \le 5.0\%$.
   - **Short-Circuit Adiabatic Withstand ($I_k = 5000\text{ A}, t = 0.1\text{ s}$, Cu/XLPE $k = 143$)**:
     - $S_{\min} = \frac{5000 \times \sqrt{0.1}}{143} = \frac{1581.14}{143} = 11.06\text{ mm}^2$.
   - **Temperature Factor $k_3$ ($40^\circ\text{C}$ PVC)**:
     - $k_3 = \sqrt{\frac{70 - 40}{70 - 30}} = \sqrt{0.75} = 0.866 \to 0.87$ (matches Table 52K).
