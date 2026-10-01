# Adversarial Challenge Report: `src/ampy/core/models.py`

## 1. Observation

Adversarial stress-testing was conducted using the standalone test harness `tests/adversarial_challenge_models.py` (51 test vectors across 6 challenge categories). The harness uncovered **18 vulnerabilities/failures** (33 tests passed, 18 failed).

### Observation 1.1: Unhashable Normative Enums (`PhaseSystem` and `LimitingConstraint`)
In `src/ampy/core/models.py`:
- Lines 48–67: `PhaseSystem` defines `def __eq__(self, other: object) -> bool:` without defining `__hash__`.
- Lines 166–179: `LimitingConstraint` defines `def __eq__(self, other: object) -> bool:` without defining `__hash__`.

**Tool command & verbatim output:**
```bash
$ python -c "from ampy.core.models import PhaseSystem; print(hash(PhaseSystem.SINGLE_PHASE))"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
TypeError: unhashable type: 'PhaseSystem'

$ python -c "from ampy.core.models import PhaseSystem; d = {PhaseSystem.SINGLE_PHASE: 230}"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
TypeError: unhashable type: 'PhaseSystem'

$ python -c "import functools; from ampy.core.models import PhaseSystem; @functools.lru_cache; def f(s): return s.value; f(PhaseSystem.SINGLE_PHASE)"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
TypeError: unhashable type: 'PhaseSystem'
```

### Observation 1.2: Positive Infinity (`float('inf')` and `"inf"`) Bypasses Validation and Corrupts JSON
In `src/ampy/core/models.py`:
- `voltage_v`, `power_kw`, `apparent_power_kva`, `current_a`, `frequency_hz` in `ElectricalLoad` (lines 198–233).
- `length_m` in `CableSpecs` (line 271).
- `in_a`, `ik_a` in `ProtectionDevice` (lines 349–357).
All use `Field(..., gt=0.0)` without upper bounds and without `allow_inf_nan=False` in `model_config`.

**Tool command & verbatim output:**
```bash
$ python -c "from ampy.core.models import ElectricalLoad; load = ElectricalLoad(voltage_v=float('inf'), power_kw=10.0); print(load.voltage_v)"
inf

$ python -c "from ampy.core.models import ElectricalLoad; load = ElectricalLoad(voltage_v='inf', power_kw=10.0); print(load.voltage_v)"
inf
```

When serialized to JSON, `inf` becomes `null` (since standard JSON does not support `Infinity`), and deserialization crashes:
```bash
$ python -c "from ampy.core.models import ElectricalLoad; load = ElectricalLoad(voltage_v=float('inf'), power_kw=10.0); s = load.model_dump_json(); print('JSON:', s); ElectricalLoad.model_validate_json(s)"
JSON: {"voltage_v":null,"phases":"three_phase","cos_phi":0.85,"power_kw":10.0,"apparent_power_kva":null,"current_a":null,"frequency_hz":50.0,"harmonic_ih3_ratio":0.0}
Traceback (most recent call last):
  File "<string>", line 1, in <module>
pydantic_core._pydantic_core.ValidationError: 1 validation error for ElectricalLoad
voltage_v
  Input should be a valid number [type=float_type, input_value=None, input_type=NoneType]
```

Furthermore, passing `inf` to formulas causes downstream calculations to produce `NaN`:
```bash
$ python -c "from ampy.core.formulas import calculate_ib; from ampy.core.models import PhaseSystem; print(calculate_ib(PhaseSystem.SINGLE_PHASE, voltage_v=float('inf'), power_w=float('inf')))"
nan
```

### Observation 1.3: `CircuitDefinition` Lacks `frozen=True` Allowing In-Place Validation Bypass
In `src/ampy/core/models.py`:
- Lines 196, 269, 309, 347: `ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice` all configure `model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)`.
- Line 376: `CircuitDefinition` configures:
  ```python
  model_config = ConfigDict(extra="forbid", populate_by_name=True)
  ```
  `frozen=True` is omitted. Because Pydantic defaults to `validate_assignment=False`, attributes can be mutated to invalid and out-of-bounds values with zero validation.

**Tool command & verbatim output:**
```bash
$ python -c "from ampy.core.models import CircuitDefinition, ElectricalLoad, CableSpecs; c = CircuitDefinition(load=ElectricalLoad(voltage_v=230.0, power_kw=3.0), cable=CableSpecs(length_m=10.0)); c.du_max_percent = -999.0; c.name = 12345; c.cable = None; print(c.du_max_percent, c.name, c.cable)"
-999.0 12345 None
```

### Observation 1.4: Output Models Omit `extra="forbid"`
In `src/ampy/core/models.py`:
- Lines 436, 454, 484, 498: `IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, and `SizingResult` specify `model_config = ConfigDict(frozen=True)` without `extra="forbid"`.
- Extra fields are silently accepted and ignored rather than raising `ValidationError`.

### Observation 1.5: Enum Boolean Trap (`PhaseSystem.SINGLE_PHASE == True`)
In `src/ampy/core/models.py`, lines 52–58:
```python
        if isinstance(other, int):
            if self.value == "single_phase" and other == 1:
                return True
            if self.value == "three_phase" and other == 3:
                return True
            if self.value == "dc" and other == 0:
                return True
```
Because `bool` inherits from `int` in Python (`isinstance(True, int) == True`), `PhaseSystem.SINGLE_PHASE == True` evaluates to `True`, and `PhaseSystem.DC == False` evaluates to `True`.

**Tool command & verbatim output:**
```bash
$ python -c "from ampy.core.models import PhaseSystem; print('1P == True:', PhaseSystem.SINGLE_PHASE == True); print('DC == False:', PhaseSystem.DC == False)"
1P == True: True
DC == False: True
```

### Observation 1.6: Robust / Passing Behaviors Verified
- **Multi-load confusion**: `ElectricalLoad` strictly blocks multiple inputs (`power_kw` + `current_a`, `power_kw` + `apparent_power_kva`, `current_a` + `apparent_power_kva`, all three, or None). All raise `ValueError` / `ValidationError`.
- **Extra field rejection on input models**: `ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `CircuitDefinition` all strictly reject undeclared extra fields at instantiation.
- **NaN rejection on input models**: `NaN` fails `gt=0.0` and is rejected with `ValidationError: Input should be greater than 0`.
- **JSON Serialization Fidelity for Finite Inputs**: Roundtrip serialization of valid `CircuitDefinition` and `SizingResult` instances succeeds with `original == restored`, retaining all enums and 64-bit IEEE float precision.

---

## 2. Logic Chain

1. **Enum Hashability Collapse**:
   - Python Data Model (§3.3.1) specifies: *If a class overrides `__eq__()` without defining `__hash__()`, its hash method is implicitly set to `None`.*
   - Observation 1.1 demonstrates that `PhaseSystem` and `LimitingConstraint` have `__hash__ = None`.
   - Normative sizing engines (such as Milestone M2 tables and M3 engine) use enums as keys in reference dispatch tables (`dict[PhaseSystem, ...]`), sets, and `@functools.lru_cache`.
   - Any attempt to use `PhaseSystem` or `LimitingConstraint` as dictionary keys or in caching raises `TypeError: unhashable type: 'PhaseSystem'`. This is a critical runtime defect that will break downstream integration.

2. **Infinity Ingress & Serialization Roundtrip Failure**:
   - In IEEE-754 floating point arithmetic, `float('inf') > 0.0` is mathematically `True`.
   - Observation 1.2 shows that `Field(..., gt=0.0)` accepts `float('inf')`, `"inf"`, and `"Infinity"` because `allow_inf_nan=False` is not declared on model configurations.
   - When models containing `float('inf')` are serialized via `model_dump_json()`, standard JSON (RFC 8259) does not permit `Infinity`. Pydantic serializes `inf` as `null`.
   - Upon deserializing via `model_validate_json()`, Pydantic rejects `null` for non-nullable `float` fields.
   - Therefore, the requirement of *zero information loss during JSON serialization and deserialization* is violated when infinite values enter the system.

3. **Schema Invariant Violation via Mutation**:
   - In Observation 1.3, `CircuitDefinition` omits `frozen=True`.
   - Because `validate_assignment=False` by default in Pydantic v2, modifying an attribute of an instantiated `CircuitDefinition` bypasses all field validators, bounds checks, and type annotations.
   - An adversary or calling code can set `du_max_percent = -999.0` or `cable = None` post-instantiation, breaking the engine's precondition contracts.

4. **Boolean Trap in Equality**:
   - In Observation 1.5, `PhaseSystem.__eq__` uses `isinstance(other, int)` without excluding `bool`.
   - Python's `bool` is a subclass of `int`. `True == 1` and `False == 0`.
   - Consequently, `PhaseSystem.SINGLE_PHASE == True` evaluates to `True`, which can silently alter conditional logic in caller modules.

---

## 3. Caveats

- **No caveats on empirical findings**: All reported vulnerabilities have been reproduced and verified by directly executing Python commands and the dedicated test script.
- **Scope note**: The existing unit tests in `tests/unit/test_models.py` achieved 100% pass rate because they tested enum equality using `==` and membership in tuples, without testing hashability in `dict` keys or `set` collections.
- **Multi-load exclusivity is robust**: The validator `validate_load_input` in `ElectricalLoad` operates as designed for finite numeric loads.

---

## 4. Conclusion

### Final Verdict: `CHALLENGE_FAILED`

`src/ampy/core/models.py` cannot be approved for Milestone M1 due to:
1. **Critical architectural blocker**: `PhaseSystem` and `LimitingConstraint` are unhashable (`TypeError: unhashable type`), preventing their use in dictionary lookups, caching, and sets throughout M2 (Normative Tables) and M3 (Sizing Engine).
2. **Critical data validation & roundtrip corruption**: Non-finite numbers (`inf`, `"inf"`, `"Infinity"`) bypass `gt=0.0` validation, leading to calculation `NaN`s and serialization failure (`null` roundtrip error).
3. **High risk mutability bypass**: `CircuitDefinition` lacks `frozen=True`, allowing in-place bypass of all schema validation constraints.
4. **Minor schema inconsistency**: Output models omit `extra='forbid'`, and `PhaseSystem.__eq__` traps boolean values `True` and `False`.

### Actionable Mitigations for the Developer:
1. In `PhaseSystem` and `LimitingConstraint`:
   - Either remove `__eq__` entirely (since inheriting from `str, Enum` already provides exact string and enum equality), OR:
   - Add explicit `def __hash__(self) -> int: return hash(self.value)` to both enums, and update `isinstance(other, int)` to `if isinstance(other, int) and not isinstance(other, bool):`.
2. In all model `model_config`s:
   - Add `allow_inf_nan=False` to `ConfigDict` across all models (e.g. `ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, populate_by_name=True)`).
3. In `CircuitDefinition`:
   - Add `frozen=True` to `model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)`.
4. In `IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, `SizingResult`:
   - Add `extra="forbid"` and `allow_inf_nan=False` to `model_config`.

---

## 5. Verification Method

To independently verify these findings, run the following commands in the workspace root:

1. **Run full adversarial challenge suite:**
   ```powershell
   python tests/adversarial_challenge_models.py
   ```
   *Expected outcome*: Exits with code 1, displaying 18 identified vulnerabilities.

2. **Verify Enum Unhashability:**
   ```powershell
   python -c "from ampy.core.models import PhaseSystem, LimitingConstraint; print(hash(PhaseSystem.SINGLE_PHASE)); print(hash(LimitingConstraint.AMPACITY))"
   ```
   *Expected outcome*: Raises `TypeError: unhashable type: 'PhaseSystem'`.

3. **Verify Inf JSON Roundtrip Corruption:**
   ```powershell
   python -c "from ampy.core.models import ElectricalLoad; ElectricalLoad.model_validate_json(ElectricalLoad(voltage_v=float('inf'), power_kw=10.0).model_dump_json())"
   ```
   *Expected outcome*: Raises `pydantic_core._pydantic_core.ValidationError: 1 validation error for ElectricalLoad voltage_v Input should be a valid number`.

4. **Verify `CircuitDefinition` Mutation:**
   ```powershell
   python -c "from ampy.core.models import CircuitDefinition, ElectricalLoad, CableSpecs; c = CircuitDefinition(load=ElectricalLoad(voltage_v=230.0, power_kw=3.0), cable=CableSpecs(length_m=10.0)); c.du_max_percent = -999.0; print('Mutated:', c.du_max_percent)"
   ```
   *Expected outcome*: Prints `Mutated: -999.0` without any error.

5. **Invalidation condition:**
   When the proposed fixes are applied to `src/ampy/core/models.py`, running `python tests/adversarial_challenge_models.py` must exit with code 0 and output `FINAL VERDICT: APPROVE` (51/51 passed).
