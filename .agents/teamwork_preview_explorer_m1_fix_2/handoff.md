# Handoff Report — Technical Remediation Specification for `src/ampy/core/formulas.py`

**Agent**: `teamwork_preview_explorer_m1_fix_2`  
**Roles**: `explorer`  
**Working Directory**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_2`  
**Target Milestone**: Milestone 1 Remediation (`m1_fix`)  
**Specification File**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_2\formulas_fix_plan.md`  
**Handoff Type**: Hard (Task Complete)  
**Date**: 2026-09-30  

---

## 1. Observation

### 1.1 Direct Source Code Observations
1. **System Identifier Slicing Defect in `calculate_ib` & `calculate_voltage_drop`**:
   - `src/ampy/core/formulas.py:147-151`:
     ```python
     sys_str = system.value if hasattr(system, "value") else str(system).upper()
     sys_str = str(sys_str).upper()
     is_single = "SINGLE" in sys_str or sys_str == "1"
     is_three = "THREE" in sys_str or sys_str == "3"
     is_dc = "DC" in sys_str
     ```
   - When `"1P"` or `"3P"` is provided, `"SINGLE"` and `"THREE"` are absent, and `"1P" != "1"`, `"3P" != "3"`.
   - Command:
     ```powershell
     python -c "from ampy.core.formulas import calculate_ib; print(calculate_ib(system='1P', voltage_v=230, power_w=2300))"
     ```
     Verbatim Error:
     ```
     ValueError: Unsupported system type: 1P
     ```
   - Same defect present in `calculate_voltage_drop` (`src/ampy/core/formulas.py:359-364`).

2. **Material String Coercion Defect in `calculate_thermal_stress_min_section` & `calculate_thermal_stress`**:
   - `src/ampy/core/formulas.py:447-455`:
     ```python
     mat_str = material.value if hasattr(material, "value") else str(material)
     mat_str = mat_str.strip().capitalize()
     ...
     key = (mat_str, ins_str)
     if key not in K_THERMAL_FACTORS:
         raise ValueError(f"Unknown material/insulation combination: {key}")
     ```
   - `K_THERMAL_FACTORS` keys are `("Cu", "PVC")`, `("Cu", "XLPE")`, `("Al", "PVC")`, `("Al", "XLPE")`.
   - Calling with `material="copper"` produces `mat_str = "Copper"`.
   - Command:
     ```powershell
     python -c "from ampy.core.formulas import calculate_thermal_stress_min_section; calculate_thermal_stress_min_section(5000.0, 0.1, material='copper', insulation='PVC')"
     ```
     Verbatim Error:
     ```
     ValueError: Unknown material/insulation combination: ('Copper', 'PVC')
     ```

3. **Missing Voltage Guards in `calculate_voltage_drop`**:
   - `src/ampy/core/formulas.py:350-358` validates `length_m >= 0`, `section_mm2 > 0`, `ib_a >= 0`, `cos_phi in (0, 1]`, but omits `voltage_v` and `u_ref`.
   - Lines 365-374 set `ref_voltage = u_ref if u_ref is not None else default_u_ref`. If `voltage_v=0.0`, `ref_voltage=0.0`.
   - Line 394: `du_percent = (du_volts / ref_voltage) * 100.0`
   - Command:
     ```powershell
     python -c "from ampy.core.formulas import calculate_voltage_drop; from ampy.core.models import PhaseSystem; calculate_voltage_drop(system=PhaseSystem.SINGLE_PHASE, length_m=10.0, section_mm2=4.0, ib_a=10.0, voltage_v=0.0)"
     ```
     Verbatim Error:
     ```
     ZeroDivisionError: float division by zero
     ```
   - When `voltage_v = -230.0`: computes `du_percent = -0.5%` and silently returns `is_compliant=True`.

4. **Dead Code / Unused Parameters in `get_conductor_resistivity`**:
   - `src/ampy/core/formulas.py:244-248`:
     ```python
     def get_conductor_resistivity(
         material: ConductorMaterial | str,
         operating_temp_c: float | None = None,
         insulation: InsulationType | str | None = None,
     ) -> float:
     ```
   - `insulation` is accepted in the signature and forwarded at line 387 by `calculate_voltage_drop`, but is never referenced or used inside `get_conductor_resistivity`.
   - In `calculate_voltage_drop`, DC circuits include AC reactance and use power factor when `cos_phi < 1.0`.

---

## 2. Logic Chain

1. **Root Cause Analysis of Enum and String Normalization**:
   - `PhaseSystem` and `ConductorMaterial` in `src/ampy/core/models.py` already define complete `_missing_` classmethods supporting all standard aliases (`"1P"`, `"3P"`, `"DC"`, `"single"`, `"three"`, `"copper"`, `"cuivre"`, `"aluminum"`, etc.).
   - The pure calculation functions in `formulas.py` were manually manipulating string tokens instead of delegating to these robust converters.
   - By coercing `system` via `PhaseSystem(system)` and `material` via `ConductorMaterial(material)` inside try-except blocks:
     - All aliases are mapped directly to canonical enum values.
     - Unrecognized values trigger clean, backward-compatible domain errors (`ValueError: Unsupported system type: {system}` and `ValueError: Unknown conductor material: {material}`).

2. **Defensive Validation Boundary**:
   - Validating `voltage_v > 0.0` and `u_ref > 0.0` at the very entry of `calculate_voltage_drop` guarantees that `ref_voltage` is strictly positive before any mathematical operations occur.
   - This eliminates both `ZeroDivisionError` and negative percentage anomalies, matching the defensive standard of `calculate_ib`.
   - Zero-frequency DC topology requires setting $\cos\varphi = 1.0$ and $\lambda = 0.0$, which correctly reflects physical behavior and addresses Challenger 1's Challenge 4.

3. **Dead Code Cleanup Rationale**:
   - In UTE C 15-105 §5.3, standard conventional resistivities are fixed at $\rho_{\text{Cu}} = 0.023\ \Omega\cdot\text{mm}^2/\text{m}$ and $\rho_{\text{Al}} = 0.037\ \Omega\cdot\text{mm}^2/\text{m}$ regardless of insulation type, unless real temperature `operating_temp_c` is explicitly specified.
   - Removing `insulation` from `get_conductor_resistivity` eliminates dead code without altering normative math.
   - Retaining `insulation: InsulationType | str | None = None` as an optional parameter in `calculate_voltage_drop` prevents breaking external callers.

---

## 3. Caveats

- **Scope Boundary**: This specification applies to `src/ampy/core/formulas.py` and its accompanying unit/boundary tests (`tests/unit/test_formulas.py` and `tests/boundary/test_boundaries.py`). Enum hashability and domain model changes in `src/ampy/core/models.py` belong to the concurrent models remediation track (`teamwork_preview_explorer_m1_fix_1`).
- **Test Alignment Required**: Challenger 1 wrote tests in `tests/boundary/test_boundaries.py` specifically expecting `ZeroDivisionError` and `ValueError` for `"copper"`. Implementing this specification requires updating those two tests to assert the remediated behavior (`ValueError` for `voltage_v=0.0` and success for `"copper"`).

---

## 4. Conclusion

A comprehensive, line-by-line remediation specification has been formulated and recorded in:
`c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_2\formulas_fix_plan.md`

The plan completely resolves:
1. System string normalization for `"1P"`, `"3P"`, `"DC"`, and aliases in `calculate_ib` and `calculate_voltage_drop`.
2. Material and insulation string normalization for `"copper"`, `"cu"`, `"aluminium"`, `"al"` in `calculate_thermal_stress_min_section`, `calculate_thermal_stress`, and `get_conductor_resistivity`.
3. Defensive entry guards for `voltage_v > 0.0`, `u_ref > 0.0`, and DC reactance elimination.
4. Elimination of dead code / unused parameters in `get_conductor_resistivity`.

---

## 5. Verification Method

Once implemented, the remediation can be verified independently using the following commands:

1. **Verify Unit Test Suite**:
   ```powershell
   pytest tests/unit/test_formulas.py -v
   ```
   *Expected Result*: All formula tests pass with exit code `0`.

2. **Verify Adversarial Stress Suite**:
   ```powershell
   python tests/boundary/test_boundaries.py
   pytest tests/boundary/test_boundaries.py -v
   ```
   *Expected Result*: All 39 adversarial boundary tests pass with `[PASS]`, exit code `0`.

3. **Verify Full Repository**:
   ```powershell
   pytest
   ```
   *Expected Result*: 100% test pass rate.

4. **Verify Ruff Linting**:
   ```powershell
   python -m ruff check src/ tests/unit/
   ```
   *Expected Result*: `All checks passed!`, exit code `0`.

5. **Direct Smoke Probes**:
   ```powershell
   python -c "from ampy.core.formulas import calculate_ib, calculate_voltage_drop, calculate_thermal_stress_min_section; assert calculate_ib('1P', 230, power_w=2300) == 10.0; assert calculate_voltage_drop('3P', 10, 4, 10).is_compliant; assert calculate_thermal_stress_min_section(5000, 0.1, 'copper', 'PVC') > 0; print('OK')"
   ```
   *Expected Result*: Prints `OK` with exit code `0`.
