# Milestone 1 Unit Tests: Test Strategy & Test Case Design Blueprint

> **Component Scope**: Milestone 1 (M1) Foundation Layer  
> **Target Test Modules**:  
> - `tests/unit/test_models.py` (Validation, Invalidation, Enums, Hierarchy, Serialization)  
> - `tests/unit/test_formulas.py` (Pure Equations, $I_b$, $\Delta U$, Thermal Stress $S_{\min}$, Temperature $k_3$, Harmonics)  
> **Author**: `teamwork_preview_explorer_m1_3` (Test Strategist & Test Designer)  
> **Date**: 2026-09-30  
> **Normative References**: NF C 15-100 (Parties 4-43, 5-52), UTE C 15-105 §5.3, IEC 60364-5-52 Annex E

---

## 1. Executive Strategy & Testing Philosophy

Milestone 1 establishes the mathematical and domain-model foundation of `ampy`. All subsequent milestones (normative tables in M2, the iterative sizing solver in M3, and the Typer CLI in M4) depend entirely on the correctness and stability of `models.py` and `formulas.py`.

```
                        +---------------------------------------+
                        |       Milestone 1 Test Pyramid        |
                        +---------------------------------------+
                                           |
                +--------------------------+--------------------------+
                |                                                     |
                v                                                     v
   tests/unit/test_models.py                             tests/unit/test_formulas.py
   - All Enums (members, string/int values)              - Ib exact formulas (1P, 3P, DC; kW, kVA, A)
   - Valid instantiations across all load modes          - Power factor sin(phi) conversion
   - Invalid input rejection (negative, zero, NaN)       - Conductor resistivity (Cu, Al) & reactance
   - Mutual exclusivity (0 or >1 inputs rejected)        - Voltage drop dU & dU% (b=1 vs b=2, <=0.5% tol)
   - Frozen immutability & extra field prohibition       - Short-circuit adiabatic withstand (4 combos)
   - JSON / dict round-trip serialization & schemas     - Temperature factor k3 (air & ground, cutoff)
```

### 1.1 Core Principles
1. **Mathematical Invariance**: Electrical equations are pure, deterministic functions. They must be validated against theoretical hand calculations derived from NF C 15-100 and UTE C 15-105.
2. **Strict Normative Tolerances**:
   - Discrete categorical outputs (enums, boolean compliance flags, integer circuit counts) must match **100% exactly**.
   - Continuous physical variables ($\Delta U$ in Volts and %, $I_b$ in Amperes, $S_{\min}$ in mm², $k_3$ factor) must match within **$\le 0.5\%$ relative tolerance** (`math.isclose` or `pytest.approx(..., rel=0.005)`).
3. **Fail-Fast Boundary Invalidation**: Invalid electrical inputs (e.g. negative powers, $\cos\varphi > 1.0$, ambient temperatures exceeding insulation thermal limits, negative cable lengths) must be rejected immediately at the model layer via Pydantic `ValidationError` or domain-specific exceptions.
4. **Hermetic Test Isolation**: Tests in `tests/unit/` must never perform disk I/O (beyond schema parsing), network operations, or depend on table lookup states from M2.

---

## 2. Interface Contracts & Data Specifications

### 2.1 Model Contracts (`ampy.core.models`)
The test suite validates the following domain models specified in `models_plan.md`:

| Schema / Enum | Responsibility & Key Constraints |
| :--- | :--- |
| `PhaseSystem` | System topology: `SINGLE_PHASE` (1 / "1P"), `THREE_PHASE` (3 / "3P"), `DC` (0 / "DC"). |
| `ConductorMaterial` | Core material: `CU` ("Cu"), `AL` ("Al"). |
| `InsulationType` | Insulation jacket: `PVC` (max 70°C), `XLPE` (max 90°C). |
| `InstallationMethod` | Normative reference method letter: `B`, `C`, `E`, `F`. |
| `LimitingConstraint` | Governing dimensioning factor: `AMPACITY` ("Iz"), `VOLTAGE_DROP` ("dU"), `THERMAL_STRESS` ("thermal_stress"). |
| `ElectricalLoad` | Load input specifications with strict mutual exclusivity: exactly one of `power_kw`, `apparent_power_kva`, or `current_a` must be provided. $\cos\varphi \in (0.0, 1.0]$, $V > 0$, frequency $> 0$. |
| `CableSpecs` | Conductor specs: `length_m > 0`, `conductor`, `insulation`, `multicore: bool`. |
| `InstallationConditions` | Environmental factors: `method`, `ambient_temp_c \in [-20, 80]`, `grouping_circuits \ge 1`, `in_ground: bool`, `k_custom \in (0, 2.0]`. |
| `ProtectionDevice` | Upstream breaker/fuse parameters: optional `in_a > 0`, `ik_a > 0`, `disconnection_time_s \in (0, 10.0]`. |
| `CircuitDefinition` | Composite circuit configuration uniting load, cable, installation, protection, and `du_max_percent \in (0, 20.0]`. |
| `VoltageDropResult` | Computed voltage drop metrics: `du_volts`, `du_percent`, `du_max_percent`, `is_compliant`, `margin_percent`. |
| `ThermalStressResult` | Adiabatic withstand assessment: `ik_a`, `time_s`, `i2t`, `k_factor`, `s_min_mm2`, `is_compliant`. |
| `IntermediateFactors` | Audit trail of intermediate factors: $k_1, k_2, k_3, k_{\text{custom}}, k_{\text{total}}, \rho_1, \lambda, \sin\varphi$. |
| `SizingResult` | Final consolidated output schema. |

### 2.2 Formula Contracts (`ampy.core.formulas`)
The test suite validates the following functional signatures:

```python
# Operating Current
def calculate_ib(
    phases: PhaseSystem,
    voltage_v: float,
    power_kw: float | None = None,
    apparent_power_kva: float | None = None,
    current_a: float | None = None,
    cos_phi: float = 1.0,
) -> float: ...

# Power factor reactive conversion
def calculate_sin_phi(cos_phi: float) -> float: ...

# Physical conductor parameters
def get_conductor_resistivity(material: ConductorMaterial, insulation: InsulationType | None = None) -> float: ...
def get_linear_reactance(section_mm2: float, multicore: bool = True) -> float: ...

# Harmonic derating
def calculate_harmonic_derating(ib_a: float, ih3_ratio: float) -> tuple[float, str, float]: ...

# Voltage drop
def calculate_voltage_drop(
    ib_a: float,
    length_m: float,
    section_mm2: float,
    phases: PhaseSystem,
    cos_phi: float,
    material: ConductorMaterial,
    insulation: InsulationType = InsulationType.XLPE,
    voltage_v: float = 400.0,
    du_max_percent: float = 5.0,
    multicore: bool = True,
) -> VoltageDropResult: ...

# Thermal stress
def calculate_thermal_stress_min_section(
    ik_a: float,
    time_s: float,
    material: ConductorMaterial,
    insulation: InsulationType,
) -> float: ...

def calculate_thermal_stress(
    ik_a: float,
    time_s: float,
    material: ConductorMaterial,
    insulation: InsulationType,
    selected_section_mm2: float,
) -> ThermalStressResult: ...

# Temperature correction factor k3
def calculate_k3_temp_factor(
    insulation: InsulationType,
    ambient_temp_c: float,
    in_ground: bool = False,
) -> float: ...
```

---

## 3. Blueprint for `tests/unit/test_models.py`

This test suite covers validation, invalidation, edge cases, immutability, and serialization across all Pydantic models.

### 3.1 Test Taxonomy & Organization

```
tests/unit/test_models.py
├── TestEnums
│   ├── test_phase_system_members_and_values()
│   ├── test_conductor_material_members_and_values()
│   ├── test_insulation_type_members_and_values()
│   ├── test_installation_method_members_and_values()
│   └── test_limiting_constraint_members_and_values()
├── TestElectricalLoadValidation
│   ├── test_valid_load_with_active_power()
│   ├── test_valid_load_with_apparent_power()
│   ├── test_valid_load_with_direct_current()
│   ├── test_valid_load_defaults()
│   ├── test_invalid_load_missing_all_inputs()
│   ├── test_invalid_load_conflicting_multiple_inputs()
│   ├── test_invalid_load_negative_power()
│   ├── test_invalid_load_zero_power()
│   ├── test_invalid_load_negative_voltage()
│   ├── test_invalid_load_zero_voltage()
│   ├── test_invalid_load_cos_phi_greater_than_one()
│   ├── test_invalid_load_cos_phi_less_or_equal_zero()
│   ├── test_invalid_load_negative_frequency()
│   └── test_load_immutability_and_extra_fields()
├── TestCableSpecsValidation
│   ├── test_valid_cable_specs()
│   ├── test_invalid_cable_length_zero_or_negative()
│   ├── test_invalid_cable_material_unrecognized()
│   └── test_cable_specs_immutability()
├── TestInstallationConditionsValidation
│   ├── test_valid_installation_defaults()
│   ├── test_valid_installation_custom_values()
│   ├── test_invalid_grouping_circuits_zero_or_negative()
│   ├── test_invalid_ambient_temperature_below_minimum()
│   ├── test_invalid_ambient_temperature_above_maximum()
│   └── test_invalid_k_custom_zero_or_negative()
├── TestProtectionDeviceValidation
│   ├── test_valid_protection_defaults()
│   ├── test_valid_protection_explicit_values()
│   ├── test_invalid_in_rating_negative()
│   ├── test_invalid_ik_current_negative()
│   └── test_invalid_disconnection_time_negative_or_excessive()
├── TestCircuitDefinitionValidation
│   ├── test_valid_circuit_definition_composition()
│   ├── test_invalid_du_max_percent_negative_or_zero()
│   ├── test_invalid_du_max_percent_excessive()
│   └── test_circuit_nested_validation_propagation()
├── TestOutputModelsValidation
│   ├── test_voltage_drop_result_immutability_and_margin()
│   ├── test_thermal_stress_result_immutability()
│   └── test_intermediate_factors_immutability()
└── TestModelSerialization
    ├── test_electrical_load_to_dict_and_back()
    ├── test_circuit_definition_json_roundtrip()
    ├── test_sizing_result_json_roundtrip()
    └── test_model_json_schema_generation()
```

### 3.2 Concrete Test Case Specifications & Assertions

#### 1. `TestEnums`
- **`PhaseSystem`**:
  - Assert `PhaseSystem.SINGLE_PHASE` or `PhaseSystem.SINGLE` equals 1 (or `"1P"`, supporting both representations).
  - Assert `PhaseSystem.THREE_PHASE` or `PhaseSystem.THREE` equals 3 (or `"3P"`).
  - Assert `PhaseSystem.DC` exists (value `0` or `"DC"`).
- **`ConductorMaterial`**:
  - `ConductorMaterial.CU.value == "Cu"`
  - `ConductorMaterial.AL.value == "Al"`
- **`InsulationType`**:
  - `InsulationType.PVC.value == "PVC"`
  - `InsulationType.XLPE.value == "XLPE"`
- **`InstallationMethod`**:
  - Verify `'B', 'C', 'E', 'F'` in `[m.value for m in InstallationMethod]`.
- **`LimitingConstraint`**:
  - Verify members representing Ampacity (`"Iz"` or `"ampacity"`), Voltage Drop (`"dU"` or `"voltage_drop"`), Thermal Stress (`"thermal_stress"`).

#### 2. `TestElectricalLoadValidation`
- **Valid Parametrized Instantiations**:
  ```python
  @pytest.mark.parametrize("load_kwargs", [
      {"voltage_v": 230.0, "phases": PhaseSystem.SINGLE_PHASE, "power_kw": 3.68, "cos_phi": 1.0},
      {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "power_kw": 18.5, "cos_phi": 0.85},
      {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "apparent_power_kva": 25.0},
      {"voltage_v": 230.0, "phases": PhaseSystem.SINGLE_PHASE, "apparent_power_kva": 6.0},
      {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "current_a": 45.0},
      {"voltage_v": 240.0, "phases": PhaseSystem.DC, "power_kw": 12.0},
      {"voltage_v": 48.0, "phases": PhaseSystem.DC, "current_a": 50.0},
  ])
  def test_valid_load_instantiations(load_kwargs):
      load = ElectricalLoad(**load_kwargs)
      assert load.voltage_v == load_kwargs["voltage_v"]
  ```
- **Mutual Exclusivity Matrix**:
  | Condition | `power_kw` | `apparent_power_kva` | `current_a` | Expected Outcome |
  | :--- | :---: | :---: | :---: | :--- |
  | Missing all | `None` | `None` | `None` | `pytest.raises(ValidationError)` (message matches "at least one") |
  | Conflict: P and S | `10.0` | `10.0` | `None` | `pytest.raises(ValidationError)` (message matches "ONLY ONE") |
  | Conflict: P and I | `10.0` | `None` | `20.0` | `pytest.raises(ValidationError)` (message matches "ONLY ONE") |
  | Conflict: S and I | `None` | `10.0` | `20.0` | `pytest.raises(ValidationError)` (message matches "ONLY ONE") |
  | Conflict: All 3 | `10.0` | `10.0` | `20.0` | `pytest.raises(ValidationError)` (message matches "ONLY ONE") |
- **Range & Invalidation Boundaries**:
  - `voltage_v = -230.0` $\implies$ `ValidationError`
  - `voltage_v = 0.0` $\implies$ `ValidationError`
  - `power_kw = -5.0` $\implies$ `ValidationError`
  - `power_kw = 0.0` $\implies$ `ValidationError`
  - `apparent_power_kva = -10.0` $\implies$ `ValidationError`
  - `current_a = -1.0` $\implies$ `ValidationError`
  - `cos_phi = 1.0001` $\implies$ `ValidationError`
  - `cos_phi = 0.0` $\implies$ `ValidationError`
  - `cos_phi = -0.5` $\implies$ `ValidationError`
  - `frequency_hz = 0.0` or `-50.0` $\implies$ `ValidationError`
- **Immutability & Extra Fields**:
  - Assigning `load.voltage_v = 400.0` must raise `ValidationError` or `TypeError` (frozen model).
  - Passing `unknown_param=123` must raise `ValidationError` (`extra="forbid"`).

#### 3. `TestCableSpecsValidation`
- Valid: `CableSpecs(length_m=50.0, conductor=ConductorMaterial.CU, insulation=InsulationType.XLPE, multicore=True)`
- Boundary: `length_m = 0.001` $\implies$ Valid
- Invalid: `length_m = 0.0` $\implies$ `ValidationError` (must be `gt=0.0`)
- Invalid: `length_m = -25.0` $\implies$ `ValidationError`
- Invalid: `conductor="Iron"` $\implies$ `ValidationError`
- Frozen check: `cable.length_m = 100.0` $\implies$ Error

#### 4. `TestInstallationConditionsValidation`
- Default verification: `inst = InstallationConditions()`
  - `inst.method == InstallationMethod.C`
  - `inst.ambient_temp_c == 30.0`
  - `inst.grouping_circuits == 1`
  - `inst.in_ground is False`
  - `inst.k_custom == 1.0`
- Boundary checks:
  - `grouping_circuits = 1` $\implies$ Valid
  - `grouping_circuits = 0` $\implies$ `ValidationError` (`ge=1`)
  - `grouping_circuits = -5` $\implies$ `ValidationError`
  - `ambient_temp_c = -20.0` $\implies$ Valid
  - `ambient_temp_c = 80.0` $\implies$ Valid
  - `ambient_temp_c = 100.0` $\implies$ `ValidationError` (`le=80.0`)
  - `k_custom = 0.0` or `-0.1` $\implies$ `ValidationError` (`gt=0.0`)
  - `k_custom = 2.0` $\implies$ Valid
  - `k_custom = 2.1` $\implies$ `ValidationError` (`le=2.0`)

#### 5. `TestProtectionDeviceValidation`
- Default verification: `prot = ProtectionDevice()`
  - `prot.in_a is None`
  - `prot.ik_a is None`
  - `prot.disconnection_time_s is None`
- Invalid bounds:
  - `in_a = 0.0` or `-10.0` $\implies$ `ValidationError`
  - `ik_a = 0.0` or `-5000.0` $\implies$ `ValidationError`
  - `disconnection_time_s = 0.0` or `-0.1` $\implies$ `ValidationError`
  - `disconnection_time_s = 15.0` $\implies$ `ValidationError` (`le=10.0`)

#### 6. `TestCircuitDefinitionValidation`
- Full composite creation:
  ```python
  circuit = CircuitDefinition(
      name="Feeder_1",
      load=ElectricalLoad(voltage_v=400.0, power_kw=37.0, cos_phi=0.85, phases=PhaseSystem.THREE_PHASE),
      cable=CableSpecs(length_m=220.0, conductor=ConductorMaterial.CU, insulation=InsulationType.XLPE),
      installation=InstallationConditions(method=InstallationMethod.C, ambient_temp_c=30.0),
      protection=ProtectionDevice(in_a=63.0),
      du_max_percent=5.0,
  )
  assert circuit.name == "Feeder_1"
  assert circuit.du_max_percent == 5.0
  ```
- Invalidation: `du_max_percent = 0.0` or `-1.0` or `25.0` $\implies$ `ValidationError`.

#### 7. `TestModelSerialization`
- **Dict Roundtrip**:
  ```python
  raw_dict = circuit.model_dump()
  assert isinstance(raw_dict, dict)
  restored = CircuitDefinition.model_validate(raw_dict)
  assert restored == circuit
  ```
- **JSON String Roundtrip**:
  ```python
  json_str = circuit.model_dump_json(indent=2)
  assert "Feeder_1" in json_str
  assert "37.0" in json_str
  restored = CircuitDefinition.model_validate_json(json_str)
  assert restored == circuit
  ```
- **JSON Schema Export**:
  ```python
  schema = CircuitDefinition.model_json_schema()
  assert "properties" in schema
  assert "load" in schema["properties"]
  assert "cable" in schema["properties"]
  ```

---

## 4. Blueprint for `tests/unit/test_formulas.py`

This test suite covers pure mathematical functions, precision tolerance adherence, and error handling in isolation.

### 4.1 Test Taxonomy & Organization

```
tests/unit/test_formulas.py
├── TestCalculateIb
│   ├── test_ib_single_phase_active_power()
│   ├── test_ib_single_phase_apparent_power()
│   ├── test_ib_single_phase_direct_current()
│   ├── test_ib_three_phase_active_power()
│   ├── test_ib_three_phase_apparent_power()
│   ├── test_ib_three_phase_direct_current()
│   ├── test_ib_dc_active_power()
│   ├── test_ib_dc_direct_current()
│   ├── test_ib_harmonic_neutral_sizing()
│   └── test_ib_invalid_inputs_raise_errors()
├── TestCalculateSinPhi
│   ├── test_sin_phi_exact_values()
│   └── test_sin_phi_out_of_bounds_raises_error()
├── TestPhysicalConductorParameters
│   ├── test_get_conductor_resistivity_cu_and_al()
│   └── test_get_linear_reactance_threshold()
├── TestCalculateVoltageDrop
│   ├── test_voltage_drop_single_phase_resistive_bench02()
│   ├── test_voltage_drop_single_phase_inductive()
│   ├── test_voltage_drop_three_phase_motor_bench01()
│   ├── test_voltage_drop_three_phase_long_run_bench03()
│   ├── test_voltage_drop_three_phase_grouping_bench04()
│   ├── test_voltage_drop_three_phase_high_temp_bench05()
│   ├── test_voltage_drop_zero_length()
│   ├── test_voltage_drop_b_factor_distinction()
│   └── test_voltage_drop_tolerance_within_half_percent()
├── TestCalculateThermalStress
│   ├── test_thermal_stress_cu_pvc()
│   ├── test_thermal_stress_cu_xlpe()
│   ├── test_thermal_stress_al_pvc()
│   ├── test_thermal_stress_al_xlpe()
│   ├── test_thermal_stress_result_compliance_flag()
│   └── test_thermal_stress_invalid_time_or_current()
└── TestCalculateK3TempFactor
    ├── test_k3_temp_in_air_pvc_grid()
    ├── test_k3_temp_in_air_xlpe_grid()
    ├── test_k3_temp_in_ground()
    ├── test_k3_reference_temp_30c_in_air_is_unity()
    └── test_k3_temperature_at_or_above_limit_raises_error()
```

### 4.2 Detailed Test Case Calculations & Reference Tables

#### 1. Operating Current ($I_b$) Test Vectors

| # | System | Input Type | Numerical Parameters | Theoretical Formula | Expected Exact Value ($I_b$) | Tolerance |
|---|:------:|:----------:|:---------------------|:--------------------|:----------------------------:|:---------:|
| 1 | 1P | Active ($P$) | $P = 2.30\text{ kW}, V = 230\text{ V}, \cos\varphi = 1.0$ | $\frac{2300}{230 \times 1.0}$ | **$10.000\text{ A}$** | exact |
| 2 | 1P | Active ($P$) | $P = 3.68\text{ kW}, V = 230\text{ V}, \cos\varphi = 1.0$ (BENCH-02) | $\frac{3680}{230 \times 1.0}$ | **$16.000\text{ A}$** | exact |
| 3 | 1P | Active ($P$) | $P = 7.36\text{ kW}, V = 230\text{ V}, \cos\varphi = 0.8$ | $\frac{7360}{230 \times 0.8} = \frac{7360}{184}$ | **$40.000\text{ A}$** | exact |
| 4 | 1P | Apparent ($S$) | $S = 6.00\text{ kVA}, V = 230\text{ V}$ | $\frac{6000}{230}$ | **$26.087\text{ A}$** | $\le 0.1\%$ |
| 5 | 1P | Apparent ($S$) | $S = 9.20\text{ kVA}, V = 230\text{ V}$ | $\frac{9200}{230}$ | **$40.000\text{ A}$** | exact |
| 6 | 1P | Direct ($I$) | $I = 32.00\text{ A}$ | $I$ | **$32.000\text{ A}$** | exact |
| 7 | 3P | Active ($P$) | $P = 18.50\text{ kW}, U = 400\text{ V}, \cos\varphi = 0.85$ (BENCH-01) | $\frac{18500}{\sqrt{3} \times 400 \times 0.85}$ | **$31.415\text{ A}$** | $\le 0.1\%$ |
| 8 | 3P | Active ($P$) | $P = 37.00\text{ kW}, U = 400\text{ V}, \cos\varphi = 0.85$ (BENCH-03) | $\frac{37000}{\sqrt{3} \times 400 \times 0.85}$ | **$62.829\text{ A}$** | $\le 0.1\%$ |
| 9 | 3P | Active ($P$) | $P = 22.00\text{ kW}, U = 400\text{ V}, \cos\varphi = 0.85$ (BENCH-04) | $\frac{22000}{\sqrt{3} \times 400 \times 0.85}$ | **$37.358\text{ A}$** | $\le 0.1\%$ |
| 10 | 3P | Active ($P$) | $P = 30.00\text{ kW}, U = 400\text{ V}, \cos\varphi = 0.85$ (BENCH-05) | $\frac{30000}{\sqrt{3} \times 400 \times 0.85}$ | **$50.943\text{ A}$** | $\le 0.1\%$ |
| 11 | 3P | Active ($P$) | $P = 15.00\text{ kW}, U = 400\text{ V}, \cos\varphi = 0.80$ | $\frac{15000}{\sqrt{3} \times 400 \times 0.80}$ | **$27.063\text{ A}$** | $\le 0.1\%$ |
| 12 | 3P | Active ($P$) | $P = 55.00\text{ kW}, U = 400\text{ V}, \cos\varphi = 0.90$ | $\frac{55000}{\sqrt{3} \times 400 \times 0.90}$ | **$88.208\text{ A}$** | $\le 0.1\%$ |
| 13 | 3P | Apparent ($S$) | $S = 25.00\text{ kVA}, U = 400\text{ V}$ | $\frac{25000}{\sqrt{3} \times 400}$ | **$36.084\text{ A}$** | $\le 0.1\%$ |
| 14 | 3P | Apparent ($S$) | $S = 100.00\text{ kVA}, U = 400\text{ V}$ | $\frac{100000}{\sqrt{3} \times 400}$ | **$144.338\text{ A}$** | $\le 0.1\%$ |
| 15 | 3P | Direct ($I$) | $I = 63.00\text{ A}$ | $I$ | **$63.000\text{ A}$** | exact |
| 16 | DC | Active ($P$) | $P = 12.00\text{ kW}, U = 240\text{ V}$ | $\frac{12000}{240}$ | **$50.000\text{ A}$** | exact |
| 17 | DC | Active ($P$) | $P = 3.00\text{ kW}, U = 48\text{ V}$ | $\frac{3000}{48}$ | **$62.500\text{ A}$** | exact |
| 18 | DC | Direct ($I$) | $I = 25.00\text{ A}$ | $I$ | **$25.000\text{ A}$** | exact |

- **Harmonic Neutral Derating (Table E.52.1)**:
  - Vector 1: $I_b = 100\text{ A}, i_{h3} = 0.10 \implies k_h = 1.00, \text{basis} = \text{"phase"}, I_{\text{eff}} = 100.0\text{ A}$
  - Vector 2: $I_b = 100\text{ A}, i_{h3} = 0.15 \implies k_h = 1.00, \text{basis} = \text{"phase"}, I_{\text{eff}} = 100.0\text{ A}$
  - Vector 3: $I_b = 100\text{ A}, i_{h3} = 0.25 \implies k_h = 0.86, \text{basis} = \text{"phase"}, I_{\text{eff}} = 100 / 0.86 = 116.28\text{ A}$
  - Vector 4: $I_b = 100\text{ A}, i_{h3} = 0.33 \implies k_h = 0.86, \text{basis} = \text{"phase"}, I_{\text{eff}} = 100 / 0.86 = 116.28\text{ A}$
  - Vector 5: $I_b = 100\text{ A}, i_{h3} = 0.40 \implies k_h = 0.86, \text{basis} = \text{"neutral"}, I_N = 3 \times 0.4 \times 100 = 120\text{ A}, I_{\text{eff}} = 120 / 0.86 = 139.53\text{ A}$
  - Vector 6: $I_b = 100\text{ A}, i_{h3} = 0.50 \implies k_h = 1.00, \text{basis} = \text{"neutral"}, I_N = 3 \times 0.5 \times 100 = 150\text{ A}, I_{\text{eff}} = 150.0\text{ A}$

#### 2. Power Factor Reactive Conversion ($\sin\varphi$) Test Vectors
$$\sin\varphi = \sqrt{1 - \cos^2\varphi}$$
- $\cos\varphi = 1.0 \implies \sin\varphi = 0.0$ (exact)
- $\cos\varphi = 0.85 \implies \sin\varphi = \sqrt{1 - 0.7225} = \sqrt{0.2775} \approx 0.5267827$
- $\cos\varphi = 0.80 \implies \sin\varphi = \sqrt{1 - 0.64} = \sqrt{0.36} = 0.60000$ (exact 3-4-5 triangle)
- $\cos\varphi = 0.60 \implies \sin\varphi = \sqrt{1 - 0.36} = \sqrt{0.64} = 0.80000$ (exact)
- $\cos\varphi = 0.00 \implies \sin\varphi = 1.00000$ (pure reactive)
- Error assertions:
  - $\cos\varphi = -0.1 \implies \text{ValueError}$
  - $\cos\varphi = 1.05 \implies \text{ValueError}$

#### 3. Conductor Resistivity & Linear Reactance
- **Resistivity ($\rho_1$)**:
  - `get_conductor_resistivity(ConductorMaterial.CU) == 0.023`
  - `get_conductor_resistivity(ConductorMaterial.AL) in (0.036, 0.037)` (assert matches standard constant $\le 0.5\%$)
- **Linear Reactance ($\lambda$)**:
  - `get_linear_reactance(1.5) == 0.0`
  - `get_linear_reactance(2.5) == 0.0`
  - `get_linear_reactance(4.0) == 0.0`
  - `get_linear_reactance(6.0) == 0.0`
  - `get_linear_reactance(10.0) == 0.0`
  - `get_linear_reactance(16.0) == 0.0`
  - `get_linear_reactance(25.0) == 0.00008` (or $8 \times 10^{-5}$)
  - `get_linear_reactance(70.0) == 0.00008`
  - `get_linear_reactance(300.0) == 0.00008`

#### 4. Voltage Drop ($\Delta U$ and $\Delta U\%$) Test Vectors

Formula:
$$\Delta U = b \times \left( \rho_1 \times \frac{L}{S} \times \cos\varphi + \lambda \times L \times \sin\varphi \right) \times I_b$$
$$\Delta U\% = 100 \times \frac{\Delta U}{U_{\text{ref}}}$$
where $b=2, U_{\text{ref}}=230\text{ V}$ for single-phase; $b=1, U_{\text{ref}}=230\text{ V}$ (phase-to-neutral reference) or $b=\sqrt{3}, U_{\text{ref}}=400\text{ V}$ for three-phase.

| Case ID | System | $b$ | $L$ (m) | $S$ (mm²) | $I_b$ (A) | $\cos\varphi$ | Mat | $\rho_1$ | $\lambda$ | Expected $\Delta U$ (V) | Expected $\Delta U\%$ | Tolerance |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1P-Resistive (BENCH-02)** | 1P | 2 | 35.0 | 4.0 | 16.000 | 1.00 | Cu | 0.023 | 0.0 | **$6.440\text{ V}$** | **$2.800\%$** | $\le 0.5\%$ |
| **1P-Rejected-1.5** | 1P | 2 | 35.0 | 1.5 | 16.000 | 1.00 | Cu | 0.023 | 0.0 | **$17.173\text{ V}$** | **$7.467\%$** | $\le 0.5\%$ |
| **1P-Rejected-2.5** | 1P | 2 | 35.0 | 2.5 | 16.000 | 1.00 | Cu | 0.023 | 0.0 | **$10.304\text{ V}$** | **$4.480\%$** | $\le 0.5\%$ |
| **1P-Inductive-Large** | 1P | 2 | 100.0 | 25.0 | 50.000 | 0.80 | Cu | 0.023 | 0.00008 | **$7.840\text{ V}$** | **$3.409\%$** | $\le 0.5\%$ |
| **3P-Motor (BENCH-01, $\lambda=0$)** | 3P | 1 | 45.0 | 4.0 | 31.415 | 0.85 | Cu | 0.023 | 0.0 | **$6.909\text{ V}$** | **$3.004\%$** | $\le 0.5\%$ |
| **3P-Motor (BENCH-01, full $\lambda$)** | 3P | 1 | 45.0 | 4.0 | 31.415 | 0.85 | Cu | 0.023 | 0.00008 | **$6.969\text{ V}$** | **$3.030\%$** | $\le 0.5\%$ |
| **3P-Feeder (BENCH-03)** | 3P | 1 | 220.0 | 25.0 | 62.829 | 0.85 | Cu | 0.023 | 0.00008 | **$11.392\text{ V}$** | **$4.953\%$** | $\le 0.5\%$ |
| **3P-Feeder-10mm²** | 3P | 1 | 220.0 | 10.0 | 62.829 | 0.85 | Cu | 0.023 | 0.0 | **$27.025\text{ V}$** | **$11.750\%$** | $\le 0.5\%$ |
| **3P-Grouping (BENCH-04)** | 3P | 1 | 30.0 | 10.0 | 37.358 | 0.85 | Cu | 0.023 | 0.0 | **$2.238\text{ V}$** | **$0.973\%$** | $\le 0.5\%$ |
| **3P-HighTemp (BENCH-05)** | 3P | 1 | 40.0 | 16.0 | 50.943 | 0.85 | Cu | 0.023 | 0.0 | **$2.576\text{ V}$** | **$1.120\%$** | $\le 0.5\%$ |
| **Zero-Length** | 3P | 1 | 0.0 | 10.0 | 50.000 | 0.85 | Cu | 0.023 | 0.0 | **$0.000\text{ V}$** | **$0.000\%$** | exact 0.0 |

- **Verification of $b=1$ vs $b=2$ Topology Ratio**:
  Executing the identical electrical line under single-phase ($b=2$) must produce **exactly twice** the voltage drop of the three-phase line ($b=1$):
  $$\frac{\Delta U(b=2)}{\Delta U(b=1)} = 2.00000$$

#### 5. Short-Circuit Thermal Stress ($S_{\min}$) Test Vectors

Formula:
$$S_{\min} = \frac{\sqrt{I_k^2 \cdot t}}{k}$$

Adiabatic Constant $k$:
- **Cu / PVC**: $k = 115$
- **Cu / XLPE**: $k = 143$
- **Al / PVC**: $k = 76$
- **Al / XLPE**: $k = 94$

| Test Vector ID | $I_k$ (A) | $t$ (s) | Conductor | Insulation | $k$ | $\sqrt{I_k^2 t}$ ($A\cdot s^{1/2}$) | Expected $S_{\min}$ (mm²) | Selected $S$ | `is_compliant` |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `TS-01` | 10,000 | 0.10 | Cu | PVC | 115 | 3,162.278 | **27.50** | 35.0 | True |
| `TS-02` | 10,000 | 0.10 | Cu | XLPE | 143 | 3,162.278 | **22.11** | 25.0 | True |
| `TS-03` | 10,000 | 0.10 | Al | PVC | 76 | 3,162.278 | **41.61** | 50.0 | True |
| `TS-04` | 10,000 | 0.10 | Al | XLPE | 94 | 3,162.278 | **33.64** | 35.0 | True |
| `TS-05` | 5,000 | 0.20 | Cu | PVC | 115 | 2,236.068 | **19.44** | 16.0 | False |
| `TS-06` | 5,000 | 0.20 | Cu | XLPE | 143 | 2,236.068 | **15.64** | 16.0 | True |
| `TS-07` | 5,000 | 0.20 | Al | PVC | 76 | 2,236.068 | **29.42** | 25.0 | False |
| `TS-08` | 5,000 | 0.20 | Al | XLPE | 94 | 2,236.068 | **23.79** | 25.0 | True |
| `TS-09` | 1,500 | 0.05 | Cu | PVC | 115 | 335.410 | **2.92** | 2.5 | False |
| `TS-10` | 1,500 | 0.05 | Cu | XLPE | 143 | 335.410 | **2.35** | 2.5 | True |

- **Edge Condition Invalidation**:
  - $t \le 0.0 \implies \text{ValueError}$
  - $I_k \le 0.0 \implies \text{ValueError}$
  - $t > 5.0\text{ s} \implies \text{ValueError}$ or warning (non-adiabatic condition).

#### 6. Temperature Correction Factor ($k_3$) Test Vectors

Normative Formula:
$$k_3 = \sqrt{\frac{\theta_{\max} - \theta_{\text{ambient}}}{\theta_{\max} - \theta_0}}$$

- **In Air ($\theta_0 = 30^\circ\text{C}$)**:
  - PVC ($\theta_{\max} = 70^\circ\text{C}$): denominator $\sqrt{70 - 30} = \sqrt{40} \approx 6.324555$
  - XLPE ($\theta_{\max} = 90^\circ\text{C}$): denominator $\sqrt{90 - 30} = \sqrt{60} \approx 7.745967$

| Ambient Temp ($\theta$) | Insulation | Exact Analytical $\sqrt{\frac{\theta_{\max}-\theta}{\theta_{\max}-30}}$ | Table 52K Value | Assert Tolerance |
|:---:|:---:|:---:|:---:|:---:|
| **10 °C** | PVC | $\sqrt{60/40} = 1.22474$ | 1.22 | $\le 0.5\%$ |
| **15 °C** | PVC | $\sqrt{55/40} = 1.17260$ | 1.17 | $\le 0.5\%$ |
| **20 °C** | PVC | $\sqrt{50/40} = 1.11803$ | 1.12 | $\le 0.5\%$ |
| **25 °C** | PVC | $\sqrt{45/40} = 1.06066$ | 1.06 | $\le 0.5\%$ |
| **30 °C** | PVC | $\sqrt{40/40} = \mathbf{1.00000}$ | 1.00 | exact 1.00 |
| **35 °C** | PVC | $\sqrt{35/40} = 0.93541$ | 0.94 | $\le 0.5\%$ |
| **40 °C** | PVC | $\sqrt{30/40} = 0.86603$ | 0.87 | $\le 0.5\%$ |
| **45 °C** | PVC | $\sqrt{25/40} = 0.79057$ | 0.79 | $\le 0.5\%$ |
| **50 °C** | PVC | $\sqrt{20/40} = 0.70711$ | 0.71 | $\le 0.5\%$ |
| **55 °C** | PVC | $\sqrt{15/40} = 0.61237$ | 0.61 | $\le 0.5\%$ |
| **60 °C** | PVC | $\sqrt{10/40} = 0.50000$ | 0.50 | exact 0.50 |
| **10 °C** | XLPE | $\sqrt{80/60} = 1.15470$ | 1.15 | $\le 0.5\%$ |
| **20 °C** | XLPE | $\sqrt{70/60} = 1.08012$ | 1.08 | $\le 0.5\%$ |
| **30 °C** | XLPE | $\sqrt{60/60} = \mathbf{1.00000}$ | 1.00 | exact 1.00 |
| **40 °C** | XLPE | $\sqrt{50/60} = 0.91287$ | 0.91 | $\le 0.5\%$ |
| **50 °C** | XLPE | $\sqrt{40/60} = 0.81650$ | 0.82 | $\le 0.5\%$ |
| **60 °C** | XLPE | $\sqrt{30/60} = 0.70711$ | 0.71 | $\le 0.5\%$ |
| **70 °C** | XLPE | $\sqrt{20/60} = 0.57735$ | 0.58 | $\le 0.5\%$ |
| **80 °C** | XLPE | $\sqrt{10/60} = 0.40825$ | 0.41 | $\le 0.5\%$ |

- **In Ground ($\theta_0 = 20^\circ\text{C}$)**:
  - $\theta = 20^\circ\text{C} \implies k_3 = 1.00000$ (exact unity)
  - $\theta = 10^\circ\text{C}$, PVC $\implies \sqrt{60/50} \approx 1.095$
  - $\theta = 30^\circ\text{C}$, XLPE $\implies \sqrt{60/70} \approx 0.926$
- **Singularity & Over-Temperature Invalidation**:
  - `calculate_k3_temp_factor(InsulationType.PVC, 70.0)` $\implies \text{ValueError}$
  - `calculate_k3_temp_factor(InsulationType.PVC, 75.0)` $\implies \text{ValueError}$
  - `calculate_k3_temp_factor(InsulationType.XLPE, 90.0)` $\implies \text{ValueError}$
  - `calculate_k3_temp_factor(InsulationType.XLPE, 95.0)` $\implies \text{ValueError}$

---

## 5. Executable Test Code Blueprint: `tests/unit/test_models.py`

Below is the concrete implementation blueprint for `tests/unit/test_models.py` ready for the test writer or implementer:

```python
"""
Unit tests for domain models and data schemas (ampy.core.models).
Conforms to NF C 15-100 and UTE C 15-105.
"""

import pytest
from pydantic import ValidationError

from ampy.core.models import (
    ConductorMaterial,
    InsulationType,
    InstallationMethod,
    PhaseSystem,
    LimitingConstraint,
    ElectricalLoad,
    CableSpecs,
    InstallationConditions,
    ProtectionDevice,
    CircuitDefinition,
    VoltageDropResult,
    ThermalStressResult,
    IntermediateFactors,
    SizingResult,
)


class TestEnums:
    def test_phase_system_enum(self):
        assert PhaseSystem.SINGLE_PHASE in (1, "1P", "SINGLE_PHASE")
        assert PhaseSystem.THREE_PHASE in (3, "3P", "THREE_PHASE")
        assert hasattr(PhaseSystem, "DC")

    def test_conductor_material_enum(self):
        assert ConductorMaterial.CU.value == "Cu"
        assert ConductorMaterial.AL.value == "Al"

    def test_insulation_type_enum(self):
        assert InsulationType.PVC.value == "PVC"
        assert InsulationType.XLPE.value == "XLPE"

    def test_installation_method_enum(self):
        values = {m.value for m in InstallationMethod}
        assert {"B", "C", "E", "F"}.issubset(values)

    def test_limiting_constraint_enum(self):
        values = {c.value for c in LimitingConstraint}
        assert any(v in ("Iz", "ampacity") for v in values)
        assert any(v in ("dU", "voltage_drop") for v in values)
        assert "thermal_stress" in values


class TestElectricalLoad:
    @pytest.mark.parametrize("load_data", [
        {"voltage_v": 230.0, "phases": PhaseSystem.SINGLE_PHASE, "power_kw": 3.68, "cos_phi": 1.0},
        {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "power_kw": 18.5, "cos_phi": 0.85},
        {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "apparent_power_kva": 25.0},
        {"voltage_v": 230.0, "phases": PhaseSystem.SINGLE_PHASE, "apparent_power_kva": 6.0},
        {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "current_a": 45.0},
        {"voltage_v": 240.0, "phases": PhaseSystem.DC, "power_kw": 12.0},
    ])
    def test_valid_load_instantiations(self, load_data):
        load = ElectricalLoad(**load_data)
        assert load.voltage_v == load_data["voltage_v"]
        assert load.phases == load_data["phases"]

    def test_load_defaults(self):
        load = ElectricalLoad(voltage_v=400.0, power_kw=10.0)
        assert load.cos_phi == 0.85 or load.cos_phi == 1.0
        assert load.frequency_hz == 50.0

    def test_invalid_load_missing_all_inputs(self):
        with pytest.raises(ValidationError, match="(?i)at least one|power_kw|current_a"):
            ElectricalLoad(voltage_v=230.0)

    @pytest.mark.parametrize("conflicting_data", [
        {"voltage_v": 400.0, "power_kw": 10.0, "apparent_power_kva": 12.0},
        {"voltage_v": 400.0, "power_kw": 10.0, "current_a": 20.0},
        {"voltage_v": 400.0, "apparent_power_kva": 12.0, "current_a": 20.0},
        {"voltage_v": 400.0, "power_kw": 10.0, "apparent_power_kva": 12.0, "current_a": 20.0},
    ])
    def test_invalid_load_conflicting_inputs(self, conflicting_data):
        with pytest.raises(ValidationError, match="(?i)only one|ambiguity|mutually exclusive"):
            ElectricalLoad(**conflicting_data)

    @pytest.mark.parametrize("invalid_kwarg", [
        {"power_kw": -5.0},
        {"power_kw": 0.0},
        {"apparent_power_kva": -10.0},
        {"current_a": -2.0},
        {"voltage_v": -230.0},
        {"voltage_v": 0.0},
        {"cos_phi": 1.05},
        {"cos_phi": 0.0},
        {"cos_phi": -0.5},
        {"frequency_hz": -50.0},
    ])
    def test_invalid_load_numeric_bounds(self, invalid_kwarg):
        base = {"voltage_v": 230.0, "power_kw": 5.0}
        base.update(invalid_kwarg)
        with pytest.raises(ValidationError):
            ElectricalLoad(**base)

    def test_load_immutability(self):
        load = ElectricalLoad(voltage_v=230.0, power_kw=3.68)
        with pytest.raises((ValidationError, TypeError)):
            load.voltage_v = 400.0


class TestCableSpecs:
    def test_valid_cable_specs(self):
        cable = CableSpecs(
            length_m=45.0,
            conductor=ConductorMaterial.CU,
            insulation=InsulationType.XLPE,
            multicore=True,
        )
        assert cable.length_m == 45.0
        assert cable.conductor == ConductorMaterial.CU

    @pytest.mark.parametrize("invalid_length", [0.0, -10.0, -0.001])
    def test_invalid_cable_length(self, invalid_length):
        with pytest.raises(ValidationError):
            CableSpecs(length_m=invalid_length)


class TestInstallationConditions:
    def test_installation_defaults(self):
        inst = InstallationConditions()
        assert inst.method == InstallationMethod.C
        assert inst.ambient_temp_c == 30.0
        assert inst.grouping_circuits == 1
        assert inst.in_ground is False
        assert inst.k_custom == 1.0

    @pytest.mark.parametrize("invalid_kwargs", [
        {"grouping_circuits": 0},
        {"grouping_circuits": -1},
        {"ambient_temp_c": 85.0},
        {"ambient_temp_c": -35.0},
        {"k_custom": 0.0},
        {"k_custom": -0.5},
        {"k_custom": 2.5},
    ])
    def test_invalid_installation_bounds(self, invalid_kwargs):
        with pytest.raises(ValidationError):
            InstallationConditions(**invalid_kwargs)


class TestProtectionDevice:
    def test_protection_defaults(self):
        prot = ProtectionDevice()
        assert prot.in_a is None
        assert prot.ik_a is None
        assert prot.disconnection_time_s is None

    def test_valid_protection_explicit(self):
        prot = ProtectionDevice(in_a=32.0, ik_a=10000.0, disconnection_time_s=0.1)
        assert prot.in_a == 32.0
        assert prot.ik_a == 10000.0

    @pytest.mark.parametrize("invalid_kwargs", [
        {"in_a": 0.0},
        {"in_a": -32.0},
        {"ik_a": -5000.0},
        {"disconnection_time_s": 0.0},
        {"disconnection_time_s": -0.1},
        {"disconnection_time_s": 15.0},
    ])
    def test_invalid_protection_bounds(self, invalid_kwargs):
        with pytest.raises(ValidationError):
            ProtectionDevice(**invalid_kwargs)


class TestCircuitDefinition:
    def test_valid_circuit_definition(self):
        circuit = CircuitDefinition(
            name="Motor_1",
            load=ElectricalLoad(voltage_v=400.0, power_kw=18.5, cos_phi=0.85, phases=PhaseSystem.THREE_PHASE),
            cable=CableSpecs(length_m=45.0, conductor=ConductorMaterial.CU, insulation=InsulationType.XLPE),
            installation=InstallationConditions(method=InstallationMethod.E),
            protection=ProtectionDevice(in_a=32.0),
            du_max_percent=5.0,
        )
        assert circuit.name == "Motor_1"
        assert circuit.load.power_kw == 18.5
        assert circuit.du_max_percent == 5.0

    @pytest.mark.parametrize("invalid_du", [0.0, -1.0, 25.0])
    def test_invalid_du_max_percent(self, invalid_du):
        with pytest.raises(ValidationError):
            CircuitDefinition(
                load=ElectricalLoad(voltage_v=230.0, power_kw=3.0),
                cable=CableSpecs(length_m=10.0),
                du_max_percent=invalid_du,
            )


class TestSerialization:
    def test_circuit_definition_json_roundtrip(self):
        circuit = CircuitDefinition(
            name="Lighting_Floor_1",
            load=ElectricalLoad(voltage_v=230.0, power_kw=3.68, cos_phi=1.0, phases=PhaseSystem.SINGLE_PHASE),
            cable=CableSpecs(length_m=35.0, conductor=ConductorMaterial.CU, insulation=InsulationType.PVC),
            installation=InstallationConditions(method=InstallationMethod.B),
            protection=ProtectionDevice(in_a=16.0),
            du_max_percent=3.0,
        )
        json_data = circuit.model_dump_json()
        restored = CircuitDefinition.model_validate_json(json_data)
        assert restored == circuit
        assert restored.load.power_kw == 3.68
        assert restored.cable.conductor == ConductorMaterial.CU

    def test_schema_generation(self):
        schema = CircuitDefinition.model_json_schema()
        assert schema["type"] == "object"
        assert "load" in schema["properties"]
        assert "cable" in schema["properties"]
```

---

## 6. Executable Test Code Blueprint: `tests/unit/test_formulas.py`

Below is the concrete implementation blueprint for `tests/unit/test_formulas.py`:

```python
"""
Unit tests for pure mathematical calculation functions (ampy.core.formulas).
Conforms strictly to NF C 15-100 and UTE C 15-105 §5.3.
"""

import math
import pytest

from ampy.core.models import (
    PhaseSystem,
    ConductorMaterial,
    InsulationType,
    VoltageDropResult,
    ThermalStressResult,
)
from ampy.core.formulas import (
    calculate_ib,
    calculate_sin_phi,
    get_conductor_resistivity,
    get_linear_reactance,
    calculate_voltage_drop,
    calculate_thermal_stress,
    calculate_thermal_stress_min_section,
    calculate_k3_temp_factor,
    calculate_harmonic_derating,
)


class TestCalculateIb:
    @pytest.mark.parametrize(
        "phases, voltage_v, power_kw, apparent_power_kva, current_a, cos_phi, expected_ib",
        [
            # Single-phase active power (kW)
            (PhaseSystem.SINGLE_PHASE, 230.0, 2.30, None, None, 1.00, 10.000),
            (PhaseSystem.SINGLE_PHASE, 230.0, 3.68, None, None, 1.00, 16.000),
            (PhaseSystem.SINGLE_PHASE, 230.0, 7.36, None, None, 0.80, 40.000),
            # Single-phase apparent power (kVA)
            (PhaseSystem.SINGLE_PHASE, 230.0, None, 6.00, None, 1.00, 26.087),
            (PhaseSystem.SINGLE_PHASE, 230.0, None, 9.20, None, 1.00, 40.000),
            # Single-phase direct current (A)
            (PhaseSystem.SINGLE_PHASE, 230.0, None, None, 32.00, 1.00, 32.000),
            # Three-phase active power (kW)
            (PhaseSystem.THREE_PHASE, 400.0, 18.50, None, None, 0.85, 31.415),
            (PhaseSystem.THREE_PHASE, 400.0, 37.00, None, None, 0.85, 62.829),
            (PhaseSystem.THREE_PHASE, 400.0, 22.00, None, None, 0.85, 37.358),
            (PhaseSystem.THREE_PHASE, 400.0, 30.00, None, None, 0.85, 50.943),
            (PhaseSystem.THREE_PHASE, 400.0, 15.00, None, None, 0.80, 27.063),
            (PhaseSystem.THREE_PHASE, 400.0, 55.00, None, None, 0.90, 88.208),
            # Three-phase apparent power (kVA)
            (PhaseSystem.THREE_PHASE, 400.0, None, 25.00, None, 1.00, 36.084),
            (PhaseSystem.THREE_PHASE, 400.0, None, 100.00, None, 1.00, 144.338),
            # Three-phase direct current (A)
            (PhaseSystem.THREE_PHASE, 400.0, None, None, 63.00, 1.00, 63.000),
            # DC active power (kW)
            (PhaseSystem.DC, 240.0, 12.00, None, None, 1.00, 50.000),
            (PhaseSystem.DC, 48.0, 3.00, None, None, 1.00, 62.500),
            # DC direct current (A)
            (PhaseSystem.DC, 24.0, None, None, 25.00, 1.00, 25.000),
        ],
    )
    def test_ib_calculations(self, phases, voltage_v, power_kw, apparent_power_kva, current_a, cos_phi, expected_ib):
        ib = calculate_ib(
            phases=phases,
            voltage_v=voltage_v,
            power_kw=power_kw,
            apparent_power_kva=apparent_power_kva,
            current_a=current_a,
            cos_phi=cos_phi,
        )
        assert math.isclose(ib, expected_ib, rel_tol=0.005)

    def test_harmonic_derating_table_e521(self):
        # ih3 <= 15% -> kh = 1.0, basis = phase
        kh, basis, i_eff = calculate_harmonic_derating(ib_a=100.0, ih3_ratio=0.10)
        assert kh == 1.00
        assert basis == "phase"
        assert math.isclose(i_eff, 100.0, rel_tol=1e-3)

        # 15% < ih3 <= 33% -> kh = 0.86, basis = phase
        kh, basis, i_eff = calculate_harmonic_derating(ib_a=100.0, ih3_ratio=0.25)
        assert kh == 0.86
        assert basis == "phase"
        assert math.isclose(i_eff, 100.0 / 0.86, rel_tol=1e-3)

        # 33% < ih3 <= 45% -> kh = 0.86, basis = neutral
        kh, basis, i_eff = calculate_harmonic_derating(ib_a=100.0, ih3_ratio=0.40)
        assert kh == 0.86
        assert basis == "neutral"
        assert math.isclose(i_eff, (3.0 * 0.40 * 100.0) / 0.86, rel_tol=1e-3)

        # ih3 > 45% -> kh = 1.0, basis = neutral
        kh, basis, i_eff = calculate_harmonic_derating(ib_a=100.0, ih3_ratio=0.50)
        assert kh == 1.00
        assert basis == "neutral"
        assert math.isclose(i_eff, 3.0 * 0.50 * 100.0, rel_tol=1e-3)


class TestCalculateSinPhi:
    @pytest.mark.parametrize("cos_phi, expected_sin", [
        (1.00, 0.00000),
        (0.85, 0.52678),
        (0.80, 0.60000),
        (0.60, 0.80000),
        (0.00, 1.00000),
    ])
    def test_sin_phi_conversions(self, cos_phi, expected_sin):
        actual = calculate_sin_phi(cos_phi)
        assert math.isclose(actual, expected_sin, abs_tol=1e-4)

    @pytest.mark.parametrize("invalid_cos", [-0.1, 1.05, 2.0])
    def test_sin_phi_domain_error(self, invalid_cos):
        with pytest.raises(ValueError):
            calculate_sin_phi(invalid_cos)


class TestConductorProperties:
    def test_resistivity(self):
        assert get_conductor_resistivity(ConductorMaterial.CU) == 0.023
        assert math.isclose(get_conductor_resistivity(ConductorMaterial.AL), 0.037, rel_tol=0.03)

    @pytest.mark.parametrize("section, expected_lambda", [
        (1.5, 0.0),
        (2.5, 0.0),
        (4.0, 0.0),
        (6.0, 0.0),
        (10.0, 0.0),
        (16.0, 0.0),
        (25.0, 0.00008),
        (70.0, 0.00008),
        (150.0, 0.00008),
    ])
    def test_linear_reactance(self, section, expected_lambda):
        assert get_linear_reactance(section) == expected_lambda


class TestCalculateVoltageDrop:
    def test_single_phase_resistive_bench02(self):
        # BENCH-02: 1P 230V, L=35m, S=4mm², Ib=16A, cos=1.0, Cu
        res = calculate_voltage_drop(
            ib_a=16.0,
            length_m=35.0,
            section_mm2=4.0,
            phases=PhaseSystem.SINGLE_PHASE,
            cos_phi=1.0,
            material=ConductorMaterial.CU,
            voltage_v=230.0,
            du_max_percent=3.0,
        )
        assert math.isclose(res.du_volts, 6.440, rel_tol=0.005)
        assert math.isclose(res.du_percent, 2.800, rel_tol=0.005)
        assert res.is_compliant is True

    def test_three_phase_long_run_bench03(self):
        # BENCH-03: 3P 400V, L=220m, S=25mm², Ib=62.83A, cos=0.85, Cu
        res = calculate_voltage_drop(
            ib_a=62.829,
            length_m=220.0,
            section_mm2=25.0,
            phases=PhaseSystem.THREE_PHASE,
            cos_phi=0.85,
            material=ConductorMaterial.CU,
            voltage_v=400.0,
            du_max_percent=5.0,
        )
        assert math.isclose(res.du_volts, 11.392, rel_tol=0.005)
        assert math.isclose(res.du_percent, 4.953, rel_tol=0.005)
        assert res.is_compliant is True

    def test_b_factor_ratio(self):
        # Identical parameters, single-phase (b=2) must double three-phase (b=1) dU_volts
        res_3p = calculate_voltage_drop(
            ib_a=20.0, length_m=50.0, section_mm2=10.0, phases=PhaseSystem.THREE_PHASE,
            cos_phi=0.85, material=ConductorMaterial.CU, voltage_v=400.0,
        )
        res_1p = calculate_voltage_drop(
            ib_a=20.0, length_m=50.0, section_mm2=10.0, phases=PhaseSystem.SINGLE_PHASE,
            cos_phi=0.85, material=ConductorMaterial.CU, voltage_v=230.0,
        )
        assert math.isclose(res_1p.du_volts / res_3p.du_volts, 2.000, rel_tol=1e-4)

    def test_zero_length_voltage_drop(self):
        res = calculate_voltage_drop(
            ib_a=50.0, length_m=0.0, section_mm2=10.0, phases=PhaseSystem.THREE_PHASE,
            cos_phi=0.85, material=ConductorMaterial.CU,
        )
        assert res.du_volts == 0.0
        assert res.du_percent == 0.0


class TestCalculateThermalStress:
    @pytest.mark.parametrize("ik_a, time_s, mat, ins, expected_s_min", [
        (10000.0, 0.10, ConductorMaterial.CU, InsulationType.PVC, 27.50),
        (10000.0, 0.10, ConductorMaterial.CU, InsulationType.XLPE, 22.11),
        (10000.0, 0.10, ConductorMaterial.AL, InsulationType.PVC, 41.61),
        (10000.0, 0.10, ConductorMaterial.AL, InsulationType.XLPE, 33.64),
        (5000.0, 0.20, ConductorMaterial.CU, InsulationType.PVC, 19.44),
        (5000.0, 0.20, ConductorMaterial.CU, InsulationType.XLPE, 15.64),
        (5000.0, 0.20, ConductorMaterial.AL, InsulationType.PVC, 29.42),
        (5000.0, 0.20, ConductorMaterial.AL, InsulationType.XLPE, 23.79),
        (1500.0, 0.05, ConductorMaterial.CU, InsulationType.PVC, 2.92),
        (1500.0, 0.05, ConductorMaterial.CU, InsulationType.XLPE, 2.35),
    ])
    def test_thermal_stress_min_section(self, ik_a, time_s, mat, ins, expected_s_min):
        s_min = calculate_thermal_stress_min_section(ik_a, time_s, mat, ins)
        assert math.isclose(s_min, expected_s_min, rel_tol=0.005)

    def test_thermal_stress_compliance_flag(self):
        res_pass = calculate_thermal_stress(
            ik_a=10000.0, time_s=0.10, conductor=ConductorMaterial.CU,
            insulation=InsulationType.XLPE, selected_section_mm2=25.0,
        )
        assert res_pass.is_compliant is True

        res_fail = calculate_thermal_stress(
            ik_a=10000.0, time_s=0.10, conductor=ConductorMaterial.CU,
            insulation=InsulationType.XLPE, selected_section_mm2=16.0,
        )
        assert res_fail.is_compliant is False


class TestCalculateK3TempFactor:
    @pytest.mark.parametrize("temp_c, ins, expected_k3", [
        (10.0, InsulationType.PVC, 1.22),
        (20.0, InsulationType.PVC, 1.12),
        (30.0, InsulationType.PVC, 1.00),
        (40.0, InsulationType.PVC, 0.87),
        (50.0, InsulationType.PVC, 0.71),
        (60.0, InsulationType.PVC, 0.50),
        (10.0, InsulationType.XLPE, 1.15),
        (20.0, InsulationType.XLPE, 1.08),
        (30.0, InsulationType.XLPE, 1.00),
        (40.0, InsulationType.XLPE, 0.91),
        (50.0, InsulationType.XLPE, 0.82),
        (60.0, InsulationType.XLPE, 0.71),
        (70.0, InsulationType.XLPE, 0.58),
        (80.0, InsulationType.XLPE, 0.41),
    ])
    def test_k3_temp_in_air_grid(self, temp_c, ins, expected_k3):
        k3 = calculate_k3_temp_factor(insulation=ins, ambient_temp_c=temp_c, in_ground=False)
        assert math.isclose(k3, expected_k3, rel_tol=0.015)

    def test_k3_reference_temp_in_air_is_unity(self):
        assert calculate_k3_temp_factor(InsulationType.PVC, 30.0) == 1.0
        assert calculate_k3_temp_factor(InsulationType.XLPE, 30.0) == 1.0

    @pytest.mark.parametrize("ins, temp_c", [
        (InsulationType.PVC, 70.0),
        (InsulationType.PVC, 75.0),
        (InsulationType.XLPE, 90.0),
        (InsulationType.XLPE, 95.0),
    ])
    def test_k3_over_temperature_rejection(self, ins, temp_c):
        with pytest.raises(ValueError):
            calculate_k3_temp_factor(ins, temp_c)
```

---

## 7. Requirement Traceability Matrix

| Test Suite / Category | Requirement ID | Feature Code | Verification Method | Asserted Standard |
| :--- | :---: | :---: | :--- | :--- |
| `TestEnums` | R2 | F06 | Exact string/int equality | NF C 15-100 §522 |
| `TestElectricalLoadValidation` | R1, R2 | F01, F02, F06 | Model validation & exception traps | NF C 15-100 §311 |
| `TestCableSpecsValidation` | R1, R2 | F06 | Boundary value validation | NF C 15-100 §524 |
| `TestInstallationConditionsValidation` | R1, R2 | F06, F08, F11, F12 | Boundary value validation | NF C 15-100 §523 |
| `TestProtectionDeviceValidation` | R1, R2 | F06, F13 | Boundary value validation | NF C 15-100 §433 |
| `TestCircuitDefinition` | R1, R2 | F06, F14 | Composite schema validation | UTE C 15-105 §5.1 |
| `TestModelSerialization` | R2 | F06, F21 | JSON roundtrip & Schema export | Pydantic v2 Contract |
| `TestCalculateIb` | R1, R3 | F01, F02, F03 | Parameterized math checks ($\le 0.1\%$) | NF C 15-100 §311 / UTE §4.2 |
| `TestCalculateSinPhi` | R1 | F04 | Exact trigonometric assertions | Pure Math Invariance |
| `TestConductorProperties` | R1 | F04 | Property mapping ($S \le 16 \implies \lambda=0$) | UTE C 15-105 §5.3 |
| `TestCalculateVoltageDrop` | R1, R3 | F04 | Relative tolerance $\le 0.5\%$ | UTE C 15-105 §5.3 / NF C 15-100 §525 |
| `TestCalculateThermalStress` | R1, R3 | F05 | Exact $S_{\min} = \sqrt{I_k^2 t}/k$ ($\le 0.5\%$) | NF C 15-100 §434.5.2 |
| `TestCalculateK3TempFactor` | R1, R3 | F12 | Normative square root formula ($\le 0.01$) | NF C 15-100 Table 52K |

---

## 8. Pytest Test Runner & Execution Protocol

### 8.1 Command-Line Invocations
To run Milestone 1 unit tests independently:

```powershell
# Run all unit tests with concise summary
pytest tests/unit/ -v

# Run models unit tests specifically
pytest tests/unit/test_models.py -v

# Run formulas unit tests specifically
pytest tests/unit/test_formulas.py -v

# Run with full coverage reporting targeting M1 modules
pytest tests/unit/ --cov=ampy.core.models --cov=ampy.core.formulas --cov-report=term-missing
```

### 8.2 Pass/Fail Criteria
- **Pass**: 100% of test cases pass with exit code 0.
- **Coverage**: $\ge 95\%$ statement coverage across `ampy.core.models` and `ampy.core.formulas`.
- **Zero Warnings**: No unhandled deprecation or floating-point division-by-zero warnings.
