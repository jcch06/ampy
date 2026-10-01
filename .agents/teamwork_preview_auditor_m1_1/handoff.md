# Forensic Audit Report — Milestone 1 (M1 Foundation)

**Work Product**: Milestone 1 Deliverables (`src/ampy/core/models.py`, `src/ampy/core/formulas.py`, `tests/unit/test_models.py`, `tests/unit/test_formulas.py`)
**Profile**: General Project (Integrity Forensics)
**Integrity Mode**: Development (per `ORIGINAL_REQUEST.md`)
**Verdict**: **CLEAN**

---

### Phase Results

| Forensic Check | Status | Evidentiary Findings |
|---|:---:|---|
| **1. Hardcoded Output Detection** | **PASS** | 0 hardcoded test results, expected outputs, or test-specific lookup branches found in `src/ampy/core/formulas.py` or `models.py`. |
| **2. Facade Implementation Detection** | **PASS** | 0 dummy, stub, or facade methods found. All functions implement authentic physical, mathematical, and normative logic. |
| **3. Pre-populated Artifact Detection** | **PASS** | 0 pre-existing `.log`, `*result*`, or `*output*` files in workspace. |
| **4. Physical Formulation Integrity** | **PASS** | All physical equations ($P / (\sqrt{3} U \cos\varphi)$, $\Delta U = b (\rho \frac{L}{S} \cos\varphi + \lambda L \sin\varphi) I_b$, $\sqrt{I_k^2 t}/k$, $k_3 = \sqrt{(\theta_{\max} - \theta) / (\theta_{\max} - \theta_0)}$) faithfully compute continuous equations without shortcuts. |
| **5. Test Assertion Genuineness** | **PASS** | 0 tautological or trivial assertions (`assert True`) found in test suite. 182 unit tests assert specific numerical boundaries, tolerances, and exception conditions. |
| **6. Execution Delegation / Dependency Audit** | **PASS** | No third-party electrical calculation libraries imported or wrapped. Core logic uses only Python standard library (`math`, `dataclasses`, `enum`) and Pydantic v2 schemas. |
| **7. Adversarial Stress & Boundary Testing** | **PASS** | Tested arbitrary non-test inputs, extreme power factor ($\cos\varphi = 0.001$), adiabatic duration limits ($t \le 5.0\text{s}$), and thermal temperature limits. All tests and runtime traces pass with exact mathematical precision. |

---

# 5-Component Handoff Report

## 1. Observation

### A. Static Code Inspection
1. **`src/ampy/core/formulas.py`**:
   - Lines 28-48: Physical & normative constants are strictly standard values:
     - `RHO1_CU = 0.023` $\Omega\cdot\text{mm}^2/\text{m}$ (UTE C 15-105 §5.3)
     - `RHO1_AL = 0.037` $\Omega\cdot\text{mm}^2/\text{m}$ (UTE C 15-105 §5.3)
     - `REACTANCE_LARGE_SECTION = 0.00008` $\Omega/\text{m}$ ($0.08\text{ m}\Omega/\text{m}$ for $S > 16\text{ mm}^2$)
     - `REACTANCE_SMALL_SECTION = 0.0`
     - `K_THERMAL_FACTORS`: `("Cu", "PVC"): 115.0`, `("Cu", "XLPE"): 143.0`, `("Al", "PVC"): 76.0`, `("Al", "XLPE"): 94.0` (NF C 15-100 Table 43A)
     - `MAX_OPERATING_TEMP_C`: `PVC: 70.0`, `XLPE: 90.0`
   - Lines 68-179: `calculate_ib` executes genuine electrical power calculations:
     - Direct current: `return round(float(current_a), 3)`
     - DC active power: `ib = power_w / voltage_v`
     - 1-phase AC active power: `ib = power_w / (voltage_v * cos_phi)`
     - 1-phase AC apparent power: `ib = apparent_power_va / voltage_v`
     - 3-phase AC active power: `ib = power_w / (sqrt(3) * voltage_v * cos_phi)`
     - 3-phase AC apparent power: `ib = apparent_power_va / (sqrt(3) * voltage_v)`
   - Lines 181-229: `calculate_harmonic_derating` applies exact IEC 60364-5-52 Table E.52.1 neutral sizing thresholds ($\le 15\%$, $\le 33\%$, $\le 45\%$, $> 45\%$).
   - Lines 235-242: `calculate_sin_phi` applies $\sin\varphi = \sqrt{\max(0, 1 - \cos^2\varphi)}$.
   - Lines 244-275: `get_conductor_resistivity` applies linear temperature adjustment $\rho(\theta) = \rho_{20} [1 + \alpha_{20}(\theta - 20)]$.
   - Lines 288-406: `calculate_voltage_drop` computes $\Delta U = b [\rho_1 \frac{L}{S}\cos\varphi + \lambda L \sin\varphi] I_b$ with $b=1$ for 3-phase and $b=2$ for 1-phase/DC, and relative $\Delta U\% = (\Delta U / V_{\text{ref}}) \times 100$.
   - Lines 411-460: `calculate_thermal_stress_min_section` computes $S_{\min} = (I_k \sqrt{t}) / k$ enforcing adiabatic limit $t \le 5.0\text{s}$.
   - Lines 506-562: `calculate_k3_temp_factor` computes $k_3 = \sqrt{\frac{\theta_{\max} - \theta}{\theta_{\max} - \theta_0}}$ rejecting $\theta \ge \theta_{\max}$.

2. **`src/ampy/core/models.py`**:
   - Lines 18-185: Enums with custom coercion and equality helpers (`PhaseSystem`, `ConductorMaterial`, `InsulationType`, `InstallationMethod`, `LimitingConstraint`).
   - Lines 190-426: Strict Pydantic v2 models with `extra="forbid"`, `frozen=True`, and semantic validators (`validate_load_input`, `validate_insulation_temperature`).
   - Lines 432-576: Structured result schemas (`IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, `SizingResult`) with full backward-compatible property accessors.

3. **`tests/unit/test_models.py` & `tests/unit/test_formulas.py`**:
   - Zero occurrences of `assert True` or self-referential tautologies across the entire test codebase.
   - Comprehensive test assertions covering: input validation failures, boundary rejections, type coercions, JSON/dict roundtrips, tolerance-bounded floating-point matches against independent theoretical calculations.

### B. Empirical Tool Executions

1. **Pytest Test Suite Execution**:
   - Command: `pytest -v`
   - Output:
     ```
     ============================= test session starts =============================
     platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
     rootdir: C:\Users\cjose\antigravity project\ampy
     configfile: pyproject.toml
     testpaths: tests
     plugins: anyio-4.9.0, cov-7.1.0
     collected 188 items / 1 skipped

     tests\test_harness_fixtures.py ......                                    [  3%]
     tests\unit\test_formulas.py ............................................ [ 26%]
     .........................................................                [ 56%]
     tests\unit\test_models.py .............................................. [ 81%]
     ...................................                                      [100%]

     =========================== short test summary info ===========================
     SKIPPED [1] tests\e2e\test_ute_benchmarks.py:56: ampy public API / core engine not yet available: No module named 'ampy.core.engine'
     ======================= 188 passed, 1 skipped in 0.52s ========================
     ```

2. **Unit Test Coverage**:
   - Command: `pytest --cov=ampy.core --cov-report=term-missing tests/unit/`
   - Output:
     ```
     Name                        Stmts   Miss  Cover   Missing
     ---------------------------------------------------------
     src\ampy\core\__init__.py       3      0   100%
     src\ampy\core\formulas.py     203      0   100%
     src\ampy\core\models.py       282     14    95%   38, 41, 43, 45, 62, 64, 66, 135, 137, 139, 173, 175, 177, 421
     ---------------------------------------------------------
     TOTAL                         488     14    97%
     182 passed in 0.77s
     ```

3. **Empirical Arbitrary Runtime Tracing**:
   - Traced `formulas.py` with arbitrary non-test values:
     - $P = 73456.7\text{ W}$, $U = 398.2\text{ V}$, $\cos\varphi = 0.8123 \implies I_b = 131.115\text{ A}$ (diff: 0.0)
     - $L = 137.4\text{ m}$, $S = 35.0\text{ mm}^2$, $\text{Cu}$, $3\text{P} \implies \Delta U = 10.457\text{ V}$, $\Delta U\% = 4.547\%$ (diff: 0.0)
     - $I_k = 14321.0\text{ A}$, $t = 0.17\text{ s}$, $\text{Cu/XLPE} \implies S_{\min} = 41.29\text{ mm}^2$ (diff: 0.0)
     - $\theta = 42.7^\circ\text{C}$, $\text{XLPE} \implies k_3 = 0.88788$ (diff: 0.0)

4. **Adversarial Boundary Stress-Testing**:
   - Extreme $\cos\varphi = 0.001$: calculated $I_b = 1000.0\text{ A}$ without numeric instability.
   - Temperature adjusted $\rho$ for Cu and Al at $70^\circ\text{C}$: matches analytical values.
   - Adiabatic duration boundary: $t = 5.0\text{s}$ accepted; $t = 5.01\text{s}$ rejected with `ValueError`.
   - Ambient temperature boundary: $T = 69.9^\circ\text{C}$ accepted for PVC; $T \ge 70.0^\circ\text{C}$ rejected with `ValueError`.

---

## 2. Logic Chain

1. **Premise 1**: A work product exhibits an integrity violation if it utilizes hardcoded test outputs, returns fake constants, employs facade patterns, relies on pre-populated artifacts, or has self-certifying/trivial tests.
2. **Observation Step 1**: Static grep search across `src/ampy/core/formulas.py` for benchmark constants (`31.415`, `6.44`, `3.68`, `62.83`, `11.392`) returned 0 occurrences.
3. **Observation Step 2**: All mathematical operations in `formulas.py` were directly inspected and traced to authentic algebraic equations conforming to NF C 15-100 and UTE C 15-105 §5.3.
4. **Observation Step 3**: Runtime tracing with arbitrary floating-point inputs confirmed continuous calculation without branch shortcuts or lookup caches.
5. **Observation Step 4**: Grep search across `tests/` for `assert True` returned 0 occurrences. Inspection of `tests/unit/test_formulas.py` and `tests/unit/test_models.py` verified that assertions validate genuine numerical outputs and error boundaries.
6. **Observation Step 5**: Test execution executed 188 automated tests (182 unit + 6 fixture tests) in 0.52s with 100% statement coverage on `formulas.py` and 95% on `models.py`.
7. **Deductive Conclusion**: Since every forensic check passed without a single defect or suspicious pattern, the work product is authentic and free from integrity violations.

---

## 3. Caveats

- **No caveats.** The scope is strictly delimited to Milestone 1 (`src/ampy/core/models.py`, `src/ampy/core/formulas.py`, and their unit test suites). Downstream components (Milestone 2 `tables.py`, Milestone 3 `engine.py`, Milestone 4 `cli/`) are planned for subsequent milestones.

---

## 4. Conclusion

- **Definitive Verdict**: **`CLEAN`**
- Milestone 1 code and tests fully satisfy all forensic integrity requirements. The implementation delivers genuine, uncompromised mathematical calculations and robust Pydantic domain models in full compliance with NF C 15-100, UTE C 15-105, and `ORIGINAL_REQUEST.md`.

---

## 5. Verification Method

To independently reproduce this forensic audit:

1. **Run full unit test suite**:
   ```bash
   pytest -v tests/unit/
   ```
2. **Verify test coverage**:
   ```bash
   pytest --cov=ampy.core --cov-report=term-missing tests/unit/
   ```
3. **Run empirical arbitrary runtime trace**:
   ```bash
   python -c "from ampy.core.formulas import calculate_ib, calculate_voltage_drop; from ampy.core.models import PhaseSystem, ConductorMaterial; print(calculate_ib(system=PhaseSystem.THREE_PHASE, voltage_v=398.2, power_w=73456.7, cos_phi=0.8123)); print(calculate_voltage_drop(system=PhaseSystem.THREE_PHASE, length_m=137.4, section_mm2=35.0, ib_a=131.115, cos_phi=0.8123, material=ConductorMaterial.CU, voltage_v=398.2))"
   ```
4. **Invalidation condition**: Any change introducing static lookup dictionaries matching test cases, stubbed returns, or weakened test assertions constitutes an immediate integrity violation.
