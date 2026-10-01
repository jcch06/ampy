# Handoff Report — Milestone 1 Review & Adversarial Quality Audit

**Reviewer Agent**: `teamwork_preview_reviewer_m1_2`  
**Roles**: `reviewer`, `critic`  
**Working Directory**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_reviewer_m1_2`  
**Target Milestone**: Milestone 1 (M1) — Foundation, Pydantic v2 Models & Pure Formulas  
**Worker Handoff Reviewed**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_worker_m1_1\handoff.md`  
**Date**: 2026-09-30  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### 1.1 Direct Tool Commands and Results

1. **Pytest Unit Test Suite & Coverage**:
   - Command:
     ```powershell
     pytest tests/unit/ --cov=ampy.core --cov-report=term-missing
     ```
   - Verbatim Output:
     ```
     ........................................................................ [ 39%]
     ........................................................................ [ 79%]
     ......................................                                   [100%]
     =============================== tests coverage ================================
     Name                        Stmts   Miss  Cover   Missing
     ---------------------------------------------------------
     src\ampy\core\__init__.py       3      0   100%
     src\ampy\core\formulas.py     203      0   100%
     src\ampy\core\models.py       282     14    95%   38, 41, 43, 45, 62, 64, 66, 135, 137, 139, 173, 175, 177, 421
     ---------------------------------------------------------
     TOTAL                         488     14    97%
     182 passed in 0.85s
     ```
   - Exit Code: `0`

2. **Ruff Linter**:
   - Command:
     ```powershell
     python -m ruff check src/ tests/unit/
     ```
   - Verbatim Output:
     ```
     All checks passed!
     ```
   - Exit Code: `0`

3. **Full Repository Test Suite Check**:
   - Command:
     ```powershell
     pytest tests/ -v
     ```
   - Verbatim Output:
     ```
     tests\test_harness_fixtures.py ......                                    [  3%]
     tests\unit\test_formulas.py ............................................ [ 26%]
     .........................................................                [ 56%]
     tests\unit\test_models.py .............................................. [ 81%]
     ...................................                                      [100%]
     SKIPPED [1] tests\e2e\test_ute_benchmarks.py:56: ampy public API / core engine not yet available: No module named 'ampy.core.engine'
     ======================= 188 passed, 1 skipped in 0.50s ========================
     ```
   - Exit Code: `0`

---

### 1.2 Adversarial Stress Testing Observations & Discrepancies

1. **Enum Hashability Failure**:
   - Command:
     ```powershell
     python -c "from ampy.core.models import PhaseSystem, LimitingConstraint; print(hash(PhaseSystem.SINGLE_PHASE))"
     ```
   - Verbatim Error:
     ```
     TypeError: unhashable type: 'PhaseSystem'
     ```
   - Command:
     ```powershell
     python -c "from ampy.core.models import LimitingConstraint; print(hash(LimitingConstraint.AMPACITY))"
     ```
   - Verbatim Error:
     ```
     TypeError: unhashable type: 'LimitingConstraint'
     ```
   - Command:
     ```powershell
     python -c "from ampy.core.models import PhaseSystem; print(PhaseSystem.SINGLE_PHASE in {1, '1P'})"
     ```
   - Verbatim Error:
     ```
     TypeError: unhashable type: 'PhaseSystem'
     ```

2. **String Shorthand Rejection in Pure Calculation Functions**:
   - Command:
     ```powershell
     python -c "from ampy.core.formulas import calculate_ib; print(calculate_ib(system='1P', voltage_v=230, power_w=2300))"
     ```
   - Verbatim Error:
     ```
     ValueError: Unsupported system type: 1P
     ```
   - Command:
     ```powershell
     python -c "from ampy.core.formulas import calculate_ib; print(calculate_ib(system='3P', voltage_v=400, power_w=2300))"
     ```
   - Verbatim Error:
     ```
     ValueError: Unsupported system type: 3P
     ```
   - Command:
     ```powershell
     python -c "from ampy.core.formulas import calculate_voltage_drop; print(calculate_voltage_drop(system='1P', length_m=10, section_mm2=4, ib_a=10))"
     ```
   - Verbatim Error:
     ```
     ValueError: Unsupported system type: 1P
     ```

3. **CircuitDefinition Mutability**:
   - Command:
     ```powershell
     python -c "from ampy.core.models import CircuitDefinition, ElectricalLoad, CableSpecs; c = CircuitDefinition(load=ElectricalLoad(voltage_v=230, power_kw=3), cable=CableSpecs(length_m=10)); c.du_max_percent = -10.0; print(c.du_max_percent)"
     ```
   - Verbatim Output:
     ```
     -10.0
     ```
   - Result: Invalid negative threshold `-10.0` was accepted post-instantiation without validation error.

4. **Dead Code in CircuitDefinition.validate_insulation_temperature**:
   - File `src/ampy/core/models.py`, lines 420-424:
     ```python
     if insulation == InsulationType.XLPE and temp >= 90.0:
         raise ValueError(...)
     ```
   - File `src/ampy/core/models.py`, lines 315-320:
     ```python
     ambient_temp_c: float = Field(default=30.0, ge=-20.0, le=80.0, ...)
     ```
   - Coverage report line 421 is missing because `InstallationConditions.ambient_temp_c` rejects any value `> 80.0` before `CircuitDefinition`'s validator is ever invoked.

5. **Unused Parameter in get_conductor_resistivity**:
   - File `src/ampy/core/formulas.py`, line 247:
     ```python
     def get_conductor_resistivity(material: ConductorMaterial | str, operating_temp_c: float | None = None, insulation: InsulationType | str | None = None) -> float:
     ```
   - `insulation` is accepted in the signature and forwarded by `calculate_voltage_drop`, but is never referenced or used inside `get_conductor_resistivity`.

6. **Missing Root README.md**:
   - File `PROJECT.md` line 122 lists `ampy/README.md`.
   - File `README.md` is currently missing from the repository root.

---

## 2. Logic Chain

1. **Integrity Assessment**:
   - I inspected `src/ampy/core/formulas.py` to ensure that results are computed using actual physical equations rather than hardcoded lookup returns.
   - Formulas for $I_b$ ($\frac{P}{\sqrt{3} U \cos\varphi}$ and $\frac{P}{U \cos\varphi}$), $\Delta U$ ($b \left[\frac{\rho_1 L}{S}\cos\varphi + \lambda L \sin\varphi\right] I_b$), adiabatic thermal withstand ($S_{\min} = \frac{I_k \sqrt{t}}{k}$), and temperature factor ($k_3 = \sqrt{\frac{\theta_{\max}-\theta}{\theta_{\max}-\theta_0}}$) are all genuine, mathematically sound, and reproduce normative UTE C 15-105 derivations within $<0.5\%$ tolerance.
   - No hardcoded test results, facade logic, or integrity shortcuts were detected.

2. **Enum Contract & Milestone 2 Impact (Observation 1.2.1)**:
   - In Python, defining `__eq__` on a class without explicitly defining `__hash__` automatically sets `__hash__ = None`.
   - `PhaseSystem` (`src/ampy/core/models.py:48-67`) and `LimitingConstraint` (`src/ampy/core/models.py:166-178`) implement custom `__eq__` methods to support loose equality against strings and ints, but omitted `__hash__`.
   - Consequently, `hash(PhaseSystem.SINGLE_PHASE)` and `hash(LimitingConstraint.AMPACITY)` raise `TypeError: unhashable type`.
   - In Milestone 2 (`tables.py`), reference current tables and derating factors are planned to index or group by PhaseSystem or LimitingConstraint. Furthermore, Python users cannot use `PhaseSystem` in sets (e.g. `val in {PhaseSystem.SINGLE_PHASE}`) or as dictionary keys.
   - The unit tests in `test_models.py:29` failed to detect this bug because they checked membership in a tuple: `assert PhaseSystem.SINGLE_PHASE in (1, "1P", "SINGLE_PHASE")`, which uses linear equality comparison and bypasses hashability.

3. **String Shorthand Rejection (Observation 1.2.2)**:
   - The docstrings and type annotations for `calculate_ib` and `calculate_voltage_drop` advertise support for `system: PhaseSystem | str | int`.
   - In `PhaseSystem._missing_`, the strings `"1p"`, `"1P"`, `"3p"`, and `"3P"` are explicitly recognized and coerced.
   - However, in `formulas.py:149` and `formulas.py:361`, the code performs `is_single = "SINGLE" in sys_str or sys_str == "1"` and `is_three = "THREE" in sys_str or sys_str == "3"`.
   - When `"1P"` or `"3P"` is passed, neither `"SINGLE"` nor `"1"` matches `"1P"`, causing `calculate_ib` and `calculate_voltage_drop` to throw `ValueError: Unsupported system type: 1P`.
   - Because `"1P"` and `"3P"` are the primary normative notations in French electrical engineering (and are the exact strings used in benchmark configurations in `conftest.py`), this inconsistency creates a sharp defect between domain models and pure formulas.

4. **Immutability Contract (Observation 1.2.3)**:
   - Worker handoff §1.1.5 and §2.2 claimed that domain models have `frozen=True` to prevent silent mutation.
   - However, `CircuitDefinition` (`src/ampy/core/models.py:376`) was configured with `model_config = ConfigDict(extra="forbid", populate_by_name=True)`, omitting `frozen=True`.
   - As observed, modifying attributes on `CircuitDefinition` after instantiation succeeds without validation, permitting invalid states such as negative voltage drop thresholds.

5. **Dead Code & Cleanup (Observations 1.2.4 & 1.2.5)**:
   - The branch checking `temp >= 90.0` in `CircuitDefinition.validate_insulation_temperature` cannot be triggered because `InstallationConditions.ambient_temp_c` is constrained to `le=80.0`.
   - `get_conductor_resistivity` declares `insulation` as a parameter but does not use it.

---

## 3. Caveats

- **Scope Boundary**: Milestone 1 is properly confined to core models, pure formulas, packaging, and unit tests. Normative lookup tables (`tables.py`) and `SizingEngine` (`engine.py`) are scheduled for Milestones 2 and 3 respectively. The skip on `tests/e2e/test_ute_benchmarks.py` is normal and expected at this stage.
- **Mypy Execution**: Mypy was not installed in the execution environment (`python -m mypy` exited with code 1: No module named mypy). However, Ruff static analysis passed 100% with `target-version = "py310"` and all models use explicit standard type hints with PEP 561 marker present.

---

## 4. Conclusion & Required Changes

The codebase demonstrates solid mathematical foundations and high test coverage (97%), with zero integrity violations. However, the unhashable Enums and the rejection of standard `"1P"`/`"3P"` strings in calculation formulas represent critical architectural defects that will break Milestone 2 tables and downstream integrations.

### Actionable Remediation Items for Worker:

1. **[CRITICAL] Restore Hashability to `PhaseSystem` and `LimitingConstraint`**:
   - In `src/ampy/core/models.py`:
     - Add `def __hash__(self) -> int: return hash(self.value)` (or `__hash__ = Enum.__hash__`) to `PhaseSystem`.
     - Add `def __hash__(self) -> int: return hash(self.value)` (or `__hash__ = Enum.__hash__`) to `LimitingConstraint`.
   - Add unit tests in `tests/unit/test_models.py` verifying that all Enums can be hashed and stored as dictionary keys and set elements: `hash(val)`, `{val}`, `{val: 1}`.

2. **[MAJOR] Support Standard `"1P"` and `"3P"` Shorthand in Pure Formulas**:
   - In `src/ampy/core/formulas.py` (`calculate_ib` and `calculate_voltage_drop`):
     - Normalize `system` using `PhaseSystem(system)` if not already an instance of `PhaseSystem`, or extend string checks to include `"1P"` / `"3P"`.
   - Add test cases in `tests/unit/test_formulas.py` verifying that `calculate_ib(system="1P", ...)` and `calculate_voltage_drop(system="3P", ...)` work seamlessly.

3. **[MAJOR] Enforce Immutability on `CircuitDefinition`**:
   - In `src/ampy/core/models.py:376`:
     - Set `model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)`.
   - Add unit test verifying that attribute mutation on `CircuitDefinition` raises an error.

4. **[MINOR] Add `extra="forbid"` to Output Domain Models**:
   - Add `extra="forbid"` to `IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, and `SizingResult`.

5. **[MINOR] Resolve Dead Code in `CircuitDefinition.validate_insulation_temperature`**:
   - Align `InstallationConditions.ambient_temp_c` (e.g. `le=90.0` or allow up to insulation limits) so that XLPE insulation validation is testable and reachable, or simplify the check.

6. **[MINOR] Clean up `insulation` Parameter in `get_conductor_resistivity`**:
   - Either utilize `insulation` (e.g. default operating temp based on insulation if provided), or document its rationale/deprecation.

---

## 5. Verification Method

Once the worker has implemented the requested changes, the reviewer will independently execute:

1. **Verify Enum Hashability and Set Operations**:
   ```powershell
   python -c "from ampy.core.models import PhaseSystem, LimitingConstraint; s = {PhaseSystem.SINGLE_PHASE, LimitingConstraint.AMPACITY}; d = {PhaseSystem.THREE_PHASE: '3P'}; print('Hash OK')"
   ```
   *Expected Result*: Prints `Hash OK` with exit code `0`.

2. **Verify String Shorthand in Pure Formulas**:
   ```powershell
   python -c "from ampy.core.formulas import calculate_ib, calculate_voltage_drop; print(calculate_ib(system='1P', voltage_v=230, power_w=2300)); print(calculate_voltage_drop(system='3P', length_m=10, section_mm2=4, ib_a=10).du_volts)"
   ```
   *Expected Result*: Prints `10.0` and calculated voltage drop with exit code `0`.

3. **Verify CircuitDefinition Immutability**:
   ```powershell
   python -c "from ampy.core.models import CircuitDefinition, ElectricalLoad, CableSpecs; c = CircuitDefinition(load=ElectricalLoad(voltage_v=230, power_kw=3), cable=CableSpecs(length_m=10)); c.du_max_percent = 4.0"
   ```
   *Expected Result*: Raises `ValidationError` or `TypeError` indicating frozen instance.

4. **Verify Full Unit Test Suite & Coverage**:
   ```powershell
   pytest tests/unit/ -v --cov=ampy.core --cov-report=term-missing
   ```
   *Expected Result*: All unit tests pass, statement coverage $\ge 97\%$, exit code `0`.

5. **Verify Ruff Linting**:
   ```powershell
   python -m ruff check src/ tests/unit/
   ```
   *Expected Result*: `All checks passed!`, exit code `0`.
