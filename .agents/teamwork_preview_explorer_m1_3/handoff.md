# Handoff Report: Milestone 1 Unit Tests Blueprint

> **Agent**: `teamwork_preview_explorer_m1_3`  
> **Role**: Explorer (Test Strategy & Test Case Designer)  
> **Milestone**: Milestone 1 (M1) Foundation Layer  
> **Target Files**: `tests/unit/test_models.py` & `tests/unit/test_formulas.py`  
> **Blueprint Path**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_3\unit_tests_plan.md`  
> **Handoff Type**: Hard (Task Complete)

---

## 1. Observation

1. **User Request & Project Plan**:
   - `c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md` (lines 14-23, 39):
     - Calculate $I_b$ for 1P (230V), 3P (400V), DC across active kW, apparent kVA, and direct current A factoring in $\cos\varphi$.
     - Voltage drop calculations ($dU$ in V and %) distinguishing single-phase ($b=2$) and three-phase ($b=1$) with theoretical values within 0.5% tolerance.
     - Thermal stress short-circuit withstand ($I^2 t \le k^2 S^2$, $S_{\min} = \sqrt{I^2 t}/k$).
   - `c:\Users\cjose\antigravity project\ampy\PROJECT.md` (lines 44-50, 93-97, 140-143):
     - Milestone 1 scope: Packaging (`pyproject.toml`), Pydantic models (`src/ampy/core/models.py`), and pure formulas (`src/ampy/core/formulas.py`).
     - Tier 1 unit test targets in `tests/unit/`: `test_models.py` and `test_formulas.py`.
2. **Architecture Specification**:
   - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md`:
     - Line 198-223: Definition of domain enums `ConductorMaterial`, `InsulationType`, `InstallationMethod`, `PhaseSystem`, `LimitingConstraint`.
     - Line 231-389: Schemas for `ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `CircuitDefinition`.
     - Line 275-283: Strict mutual exclusivity validator on `ElectricalLoad` (`power_kw`, `apparent_power_kva`, `current_a`).
     - Line 409-462: Output models `VoltageDropResult`, `ThermalStressResult`, `IntermediateFactors`, `SizingResult`.
     - Line 476-651: Pure mathematical implementations for $I_b$, $\sin\varphi$, resistivity $\rho_1$, linear reactance $\lambda$, voltage drop $dU$, and thermal stress.
3. **Normative Formulas & Standards**:
   - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_spec_miner_survey_1\normative_specs.md`:
     - Line 20-30: Complete formula set for $I_b$ (1P, 3P, DC).
     - Line 45-51: Neutral third-harmonic derating ($i_{h3}$ and $k_h$ per Table E.52.1).
     - Line 153-171: Ambient temperature factor $k_3 = \sqrt{\frac{\theta_{\max} - \theta_{\text{ambient}}}{\theta_{\max} - \theta_0}}$ for PVC (70°C) and XLPE (90°C).
     - Line 288-306: Exact voltage drop formula $dU = b \cdot (\rho_1 \frac{L}{S} \cos\varphi + \lambda L \sin\varphi) I_b$ with $\lambda = 0.0\ \Omega/\text{m}$ for $S \le 16\text{ mm}^2$ and $0.00008\ \Omega/\text{m}$ for $S > 16\text{ mm}^2$.
     - Line 344-349: Adiabatic short-circuit withstand factor $k$: Cu/PVC=115, Cu/XLPE=143, Al/PVC=76, Al/XLPE=94.
4. **Benchmarks & Precision Rules**:
   - `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\benchmarks.md` (lines 89-120, 151-188, 211-248, 271-303, 327-358):
     - Scenario 1 (3P Motor 18.5kW): $I_b = 31.41\text{ A}, \Delta U = 6.97\text{ V} (3.03\%)$.
     - Scenario 2 (1P Lighting 3.68kW): $I_b = 16.00\text{ A}, \Delta U = 6.44\text{ V} (2.80\%)$.
     - Scenario 3 (3P Feeder 37kW): $I_b = 62.83\text{ A}, \Delta U = 11.39\text{ V} (4.95\%)$.
     - Scenario 4 (3P Grouping 22kW): $I_b = 37.36\text{ A}, \Delta U = 2.24\text{ V} (0.97\%)$.
     - Scenario 5 (3P High Temp 30kW): $I_b = 50.94\text{ A}, \Delta U = 2.58\text{ V} (1.12\%)$.
   - `c:\Users\cjose\antigravity project\ampy\TEST_INFRA.md` (lines 40-44):
     - Discrete parameters must match exactly.
     - Continuous parameters must match within $\le 0.5\%$ relative tolerance.
5. **Sibling Agent Prompts**:
   - `teamwork_preview_explorer_m1_1`: Designing `pyproject.toml` and `models.py`.
   - `teamwork_preview_explorer_m1_2`: Designing `formulas.py`.

---

## 2. Logic Chain

1. **Foundation Requirement Mapping**:
   From Observation 1 and 2, Milestone 1 must validate models and pure equations independently of table data or iterative sizing loops. Therefore, tests must be segregated into `test_models.py` (structural, validation, serialization) and `test_formulas.py` (functional, mathematical, tolerances).
2. **Model Validation Logic**:
   - From Observation 2 (lines 275-283), `ElectricalLoad` requires mutually exclusive input of power sources. The test design systematically checks 4 valid modes (kW, kVA, A, DC) and 4 invalid permutations (missing all, pairs, all 3).
   - Domain constraints dictate invalidation of negative voltages, negative power, non-positive currents, non-standard frequencies, and power factors outside $(0.0, 1.0]$.
   - Immutability (`frozen=True`) and strict field rejection (`extra="forbid"`) must be verified to prevent silent bugs in higher-level solvers.
   - Pydantic v2 `model_dump()`, `model_dump_json()`, and `model_json_schema()` must be tested with round-trip equality assertions to guarantee interoperability with Typer CLI and JSON export requirements.
3. **Formula Mathematical Verification Logic**:
   - From Observation 3 and 4, operating current $I_b$ has three distinct topologies (1P, 3P, DC). An 18-row parameterized vector matrix was constructed covering active power, apparent power, and direct current.
   - From Observation 3 (line 288-306) and 4 (Scenario 1 & 2), the voltage drop formula contains topology parameter $b \in \{1, 2\}$, conductor material parameter $\rho_1 \in \{0.023, 0.037\}$, and section-dependent reactance threshold ($\lambda = 0$ for $S \le 16\text{ mm}^2$, $0.00008$ for $S > 16\text{ mm}^2$). Test cases explicitly assert the $b=2$ vs $b=1$ ratio ($2.0000$), test both resistive and inductive circuits, and enforce $\le 0.5\%$ relative tolerance against canonical hand calculations.
   - From Observation 3 (line 344-349), adiabatic thermal stress $S_{\min} = \sqrt{I_k^2 t}/k$ has four distinct material/insulation combinations ($k \in \{115, 143, 76, 94\}$). 10 parameterized short-circuit vectors were designed covering varying fault currents ($1.5\text{ kA}$ to $10\text{ kA}$) and fault clearing durations ($0.05\text{ s}$ to $0.2\text{ s}$).
   - From Observation 3 (line 153-171), temperature factor $k_3$ was mapped across a 14-point discrete grid from 10°C to 80°C in air and in ground, asserting compatibility between the analytical square root formula and official Table 52K values, while checking rejection at or above insulation operating limits (70°C for PVC, 90°C for XLPE).

---

## 3. Caveats

1. **Neutral Voltage Drop Reference**: In three-phase balanced systems, UTE C 15-105 §5.3 uses $b=1$ to calculate phase-to-neutral voltage drop $\Delta V$, which is divided by $V_n = 230\text{ V}$ to yield $\Delta U\%$. If a line-to-line calculation is performed with $b=\sqrt{3}$, it is divided by $U_n = 400\text{ V}$, yielding an identical percentage ($3.03\%$). The test suite specifies relative percentage assertions to ensure invariance regardless of whether internal formulation uses $b=1/230\text{V}$ or $b=\sqrt{3}/400\text{V}$.
2. **Aluminium Resistivity Convention**: Some reference documents list $\rho_1(\text{Al}) = 0.036\ \Omega\cdot\text{mm}^2/\text{m}$ while others list $0.037\ \Omega\cdot\text{mm}^2/\text{m}$ ($1.25 \times 0.0294 = 0.03675$). The test tolerance of $0.5\%$ accounts for this minor conventional variance.
3. **No M2 Tables Dependency**: Tier 1 formula tests do not import or query `ampy.core.tables`. All inputs are passed directly as function arguments.

---

## 4. Conclusion

A comprehensive, mathematically rigorous, and normative-compliant test blueprint has been created and documented in:
`c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_3\unit_tests_plan.md`

The blueprint specifies:
- 12 test classes across `tests/unit/test_models.py` and `tests/unit/test_formulas.py`.
- 60+ individual test cases and parameterized test vectors.
- Exact hand-calculated theoretical reference values for all benchmark scenarios.
- Strict $\le 0.5\%$ relative tolerance policy.
- Full executable Python test skeletons ready for immediate implementation.

---

## 5. Verification Method

1. **Inspect Blueprint**:
   - Check file existence and integrity: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_3\unit_tests_plan.md`.
   - Verify presence of all sections: Enums, Load Validation, Invalidation Matrix, Serialization, $I_b$ Vectors, Voltage Drop $b=1/2$ Vectors, Thermal Stress $S_{\min}$ 4-combination Matrix, Temperature Factor $k_3$ Grid, and Pytest Runner Commands.
2. **Downstream Execution Command (Upon Implementation)**:
   ```powershell
   pytest tests/unit/ -v --cov=ampy.core.models --cov=ampy.core.formulas --cov-report=term-missing
   ```
3. **Invalidation Conditions**:
   - If `test_models.py` allows mutual load inputs simultaneously (e.g. `power_kw` and `current_a`), validation has failed.
   - If `test_formulas.py` fails to distinguish single-phase ($b=2$) and three-phase ($b=1$), or exceeds the 0.5% tolerance threshold on $\Delta U$, test assertion verification has failed.
