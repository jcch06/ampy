# Handoff Report: Remediation Specification for `src/ampy/core/models.py`

**Agent**: `teamwork_preview_explorer_m1_fix_1`  
**Role**: `explorer` (read-only investigation, architectural synthesis, remediation specification)  
**Working Directory**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_1`  
**Target Milestone**: Milestone 1 Remediation (`m1_fix_1`)  
**Parent Conversation ID**: `776386d9-70f0-46fd-896e-befc19ccbade`  
**Date**: 2026-09-30  
**Handoff Type**: Hard (Task Complete)  

---

## 1. Observation

### 1.1 Baseline Adversarial Stress Testing Execution
Running `python tests/adversarial_challenge_models.py` produced verbatim:

```
================================================================================
EMPIRICAL ADVERSARIAL CHALLENGE REPORT: ampy.core.models
================================================================================
TOTAL TESTS: 51
PASSED (ROBUST / BLOCKED): 33
FAILED (VULNERABILITIES DISCOVERED): 18
--------------------------------------------------------------------------------

CRITICAL VULNERABILITIES IDENTIFIED:
  1. [Numeric Extremes & Types] Boolean coercion (True passed as float)
     Details: Silently coerced bool True to float: voltage_v=1.0, power_kw=1.0
  2. [Numeric Extremes & Types] Positive Inf in voltage_v
     Details: Field(gt=0.0) allowed float('inf') without finiteness check!
  3. [Numeric Extremes & Types] Positive Inf in power_kw
  4. [Numeric Extremes & Types] Positive Inf in apparent_power_kva
  5. [Numeric Extremes & Types] Positive Inf in current_a
  6. [Numeric Extremes & Types] Positive Inf in frequency_hz
  7. [Numeric Extremes & Types] Positive Inf in length_m
  8. [Numeric Extremes & Types] Positive Inf in in_a
  9. [Numeric Extremes & Types] Positive Inf in ik_a
  10. [Numeric Extremes & Types] String 'inf' coercion
     Details: Parsed string 'inf' into float('inf'): voltage_v=inf
  11. [Model Immutability] CircuitDefinition direct mutation (frozen=True missing)
     Details: CircuitDefinition is NOT frozen! Mutated du_max_percent to invalid negative value: -999.0 without validation!
  12. [Model Immutability] CircuitDefinition type bypass via mutation
     Details: Bypassed type contract via mutation! circuit.name became int: 12345
  13. [Extra Fields Handling] IntermediateFactors extra field
     Details: IntermediateFactors omits extra='forbid'! Silently accepted/ignored undeclared extra fields.
  14. [Extra Fields Handling] VoltageDropResult extra field
     Details: VoltageDropResult omits extra='forbid'! Silently accepted/ignored undeclared extra fields.
  15. [JSON Serialization Fidelity] Inf JSON serialization data corruption
     Details: Data corruption during serialization: float('inf') serialized to 'null', failing roundtrip with ValidationError: Input should be a valid number
  16. [Enum Integrity & Type Safety] PhaseSystem hashability (CRITICAL DEFECT)
     Details: PhaseSystem is UNHASHABLE due to overriding __eq__ without __hash__! TypeError: unhashable type: 'PhaseSystem'. Breaks dict keys, sets, and caching!
  17. [Enum Integrity & Type Safety] LimitingConstraint hashability (CRITICAL DEFECT)
     Details: LimitingConstraint is UNHASHABLE due to overriding __eq__ without __hash__! TypeError: unhashable type: 'LimitingConstraint'. Breaks dict keys, sets, and caching!
  18. [Enum Integrity & Type Safety] PhaseSystem boolean trap (PhaseSystem.SINGLE_PHASE == True)
     Details: Overly broad __eq__ matches booleans: SINGLE_PHASE == True is True, DC == False is True!

FINAL VERDICT: CHALLENGE_FAILED
```

### 1.2 Inspection of Source Code in `src/ampy/core/models.py`
1. **Enum Hashability**:
   - Lines 48–67: `PhaseSystem` defines `def __eq__(self, other: object) -> bool:` without defining `__hash__`.
   - Lines 166–179: `LimitingConstraint` defines `def __eq__(self, other: object) -> bool:` without defining `__hash__`.
   - Lines 52–58: `if isinstance(other, int):` allows `bool` (`True == 1`, `False == 0`) to match `SINGLE_PHASE` and `DC`.
2. **Missing `allow_inf_nan=False`**:
   - `ElectricalLoad` (line 196), `CableSpecs` (line 269), `InstallationConditions` (line 309), `ProtectionDevice` (line 347), and `CircuitDefinition` (line 376) lack `allow_inf_nan=False`.
   - `Field(gt=0.0)` accepts `float('inf')` because IEEE-754 defines `inf > 0.0` as `True`.
3. **`CircuitDefinition` Immutability**:
   - Line 376: `model_config = ConfigDict(extra="forbid", populate_by_name=True)`. `frozen=True` is missing.
4. **Output Schema `extra="forbid"`**:
   - Lines 436, 454, 484, 498: `IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, and `SizingResult` specify `ConfigDict(frozen=True)` without `extra="forbid"`.
5. **Boolean Coercion**:
   - `ElectricalLoad(voltage_v=True, power_kw=True)` coerced `True` into `1.0` due to Python's `bool` subclassing `int`.
6. **Existing Unit Test Baseline**:
   - Running `pytest tests/unit/` currently passes 182/182 tests with 95% coverage on `models.py`. Line 220 of `tests/unit/test_models.py` asserts that `ambient_temp_c: 85.0` raises `ValidationError`, confirming that `InstallationConditions.ambient_temp_c` must strictly retain `le=80.0`.

---

## 2. Logic Chain

1. **Enum Hashability and Boolean Equality**:
   - Per Python Data Model §3.3.1, a class overriding `__eq__` without `__hash__` has `__hash__ = None`. Adding `def __hash__(self) -> int: return hash(self.value)` to both `PhaseSystem` and `LimitingConstraint` immediately restores hashability, enabling dictionary key lookup, `set` membership, and `@functools.lru_cache` decoration.
   - Because `isinstance(True, int)` is `True` in Python, replacing `if isinstance(other, int):` with `if isinstance(other, int) and not isinstance(other, bool):` in `PhaseSystem.__eq__` and `PhaseSystem._missing_` eliminates the boolean trap where `SINGLE_PHASE == True` or `DC == False` evaluated to `True`.

2. **Non-Finite Numeric Ingress**:
   - Standard JSON (RFC 8259) does not permit `Infinity` or `NaN`. Pydantic serializes `float('inf')` to `null`. On deserialization, `null` is rejected for float fields, causing roundtrip corruption.
   - Setting `allow_inf_nan=False` in `model_config` causes Pydantic to validate that all float inputs are finite numbers, rejecting `float('inf')`, `float('-inf')`, `'inf'`, and `'Infinity'` at instantiation with `ValidationError: Input should be a finite number`.
   - Applying `allow_inf_nan=False` across all 9 schemas resolves vulnerabilities #2 through #10, and prevents serialization corruption (#15).

3. **CircuitDefinition Immutability**:
   - In Pydantic v2, `validate_assignment=False` by default. Without `frozen=True`, attributes of instantiated `CircuitDefinition` objects can be mutated to invalid negative numbers or mismatched types without re-validation.
   - Adding `frozen=True` to `CircuitDefinition.model_config` forbids all post-instantiation attribute assignment, raising `ValidationError: Instance is frozen` and resolving vulnerabilities #11 and #12.

4. **Output Model Extra Fields**:
   - Adding `extra="forbid"` to `IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, and `SizingResult` ensures that unexpected or misspelled fields are rejected at model construction, resolving vulnerabilities #13 and #14.

5. **Boolean Coercion Defense**:
   - Because Pydantic converts `True` to `1.0` for non-strict float fields, adding a `mode="before"` model validator `reject_boolean_numeric_inputs` to `ElectricalLoad` that checks `isinstance(val, bool)` for numeric inputs raises a clear `ValueError` before coercion occurs, resolving vulnerability #1.

6. **Adversarial Harness Test 5.4 Alignment**:
   - In `tests/adversarial_challenge_models.py`, test vector 5.4 had `load_with_inf = ElectricalLoad(voltage_v=float("inf"), power_kw=10.0)` outside any `try` block. When `allow_inf_nan=False` correctly blocks infinity at instantiation, this unhandled exception would crash the script. Wrapping the instantiation in `try...except ValidationError` allows test 5.4 to register `CONFIRMED_ROBUST: Blocked float('inf') at model instantiation`.

7. **Empirical Proof of Specification**:
   - A dedicated verification script (`verify_proposed_models.py`) was compiled with the exact proposed code modifications and tested against the entire adversarial suite.
   - Result: **51/51 PASSED (0 failures)**, and **182/182 unit tests passed (0 failures)** with zero regressions.

---

## 3. Caveats

- **Test Harness Vector 5.4**: The worker/implementer must apply the patch to `tests/adversarial_challenge_models.py` lines 432–446 alongside `src/ampy/core/models.py`. Otherwise, line 433 of the challenge test script will crash on the newly added finiteness validation.
- **Ambient Temperature Upper Bound**: Reviewer 2 noted unreachable code in `CircuitDefinition.validate_insulation_temperature` (`temp >= 90.0` for XLPE) due to `ambient_temp_c` having `le=80.0`. However, existing test `test_invalid_installation_bounds` in `tests/unit/test_models.py:220` explicitly expects `ambient_temp_c: 85.0` to be rejected with `ValidationError`. Therefore, `le=80.0` must be maintained on `InstallationConditions.ambient_temp_c`.
- **Pure Formulas Shorthand**: Reviewer 2's note regarding `"1P"`/`"3P"` strings in `formulas.py` is an independent formula normalization enhancement documented in the plan, but not part of `models.py` schema validation.

---

## 4. Conclusion

The specification formulated in `.agents/teamwork_preview_explorer_m1_fix_1/models_fix_plan.md` is complete, exact, and empirically validated. It eliminates all 18 vulnerabilities while maintaining 100% backward compatibility with all existing unit tests and normative contracts.

### Action Items for Worker (`teamwork_preview_worker_m1_fix_1`):
1. Apply the exact diffs in `models_fix_plan.md` §2 to `src/ampy/core/models.py`.
2. Apply the test harness alignment in `models_fix_plan.md` §3 to `tests/adversarial_challenge_models.py`.
3. Execute the verification commands listed below to confirm 0 failures.

---

## 5. Verification Method

The worker and reviewer can independently verify the implementation using the following commands:

1. **Verify Adversarial Challenge Suite (All 51 tests pass)**:
   ```powershell
   python tests/adversarial_challenge_models.py
   ```
   *Expected Output*:
   ```
   TOTAL TESTS: 51
   PASSED (ROBUST / BLOCKED): 51
   FAILED (VULNERABILITIES DISCOVERED): 0
   FINAL VERDICT: APPROVE
   ```
   *Exit code*: `0`.

2. **Verify Enum Hashability and Set / Cache Operations**:
   ```powershell
   python -c "from ampy.core.models import PhaseSystem, LimitingConstraint; s = {PhaseSystem.SINGLE_PHASE, LimitingConstraint.AMPACITY}; d = {PhaseSystem.SINGLE_PHASE: 1, LimitingConstraint.VOLTAGE_DROP: 2}; print('Hash OK:', len(s), len(d))"
   ```
   *Expected Output*: `Hash OK: 2 2` (*Exit code*: `0`).

3. **Verify Boolean Equality Guard**:
   ```powershell
   python -c "from ampy.core.models import PhaseSystem; assert (PhaseSystem.SINGLE_PHASE == True) is False; assert (PhaseSystem.DC == False) is False; assert (PhaseSystem.SINGLE_PHASE == 1) is True; print('Bool Guard OK')"
   ```
   *Expected Output*: `Bool Guard OK` (*Exit code*: `0`).

4. **Verify CircuitDefinition Immutability**:
   ```powershell
   python -c "from ampy.core.models import CircuitDefinition, ElectricalLoad, CableSpecs; c = CircuitDefinition(load=ElectricalLoad(voltage_v=230, power_kw=3), cable=CableSpecs(length_m=10)); c.du_max_percent = 4.0"
   ```
   *Expected Output*: Raises `pydantic_core._pydantic_core.ValidationError: Instance is frozen` (*Exit code*: `1`).

5. **Verify Full Unit Test Suite & Coverage**:
   ```powershell
   pytest tests/unit/ -v --cov=ampy.core.models --cov-report=term-missing
   ```
   *Expected Output*: `182 passed in ...`, coverage $\ge 95\%$ (*Exit code*: `0`).

6. **Verify Ruff Linter**:
   ```powershell
   python -m ruff check src/ tests/
   ```
   *Expected Output*: `All checks passed!` (*Exit code*: `0`).
