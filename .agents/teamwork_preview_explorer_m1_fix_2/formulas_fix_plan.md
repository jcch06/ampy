# Technical Remediation Specification: `src/ampy/core/formulas.py`

**Document ID**: `AMPY-M1-FIX-FORMULAS-SPEC-001`  
**Target Milestone**: Milestone 1 Remediation (M1 Fix)  
**Author**: `teamwork_preview_explorer_m1_fix_2`  
**Target File**: `src/ampy/core/formulas.py`  
**Dependent Test Files**: `tests/unit/test_formulas.py`, `tests/boundary/test_boundaries.py`  
**Status**: SPECIFICATION_COMPLETE  

---

## 1. Executive Summary & Problem Analysis

Following the Milestone 1 Review (`teamwork_preview_reviewer_m1_2`) and Adversarial Challenge (`teamwork_preview_challenger_m1_1`), four distinct defects were identified in `src/ampy/core/formulas.py`:

| Ref | Category | Defect Description | Root Cause | Impact |
|---|---|---|---|---|
| **D1** | System String Coercion | `calculate_ib` and `calculate_voltage_drop` reject `"1P"` and `"3P"` with `ValueError: Unsupported system type: 1P`. | Custom string slicing checks `"SINGLE" in sys_str or sys_str == "1"` rather than leveraging `PhaseSystem._missing_` conversion. | Breaches interface contract; normative French notation `"1P"`/`"3P"` breaks in pure calculations. |
| **D2** | Material String Coercion | `calculate_thermal_stress_min_section` rejects `"copper"` / `"cuivre"` / `"al"` with `ValueError: Unknown material/insulation combination: ('Copper', 'PVC')`. | Direct `.capitalize()` turns `"copper"` into `"Copper"`, which fails lookup in `K_THERMAL_FACTORS` (keyed by `"Cu"`). | Inconsistent with `get_conductor_resistivity` and `ConductorMaterial` enum. |
| **D3** | Defensive Voltage Validation | `calculate_voltage_drop` crashes with `ZeroDivisionError` when `voltage_v=0.0` or computes negative percentages when `voltage_v < 0.0`. Custom `u_ref <= 0.0` is unvalidated. | Missing entry guard: `calculate_voltage_drop` does not validate `voltage_v > 0.0` and `u_ref > 0.0`, unlike `calculate_ib`. | Crash in standalone library usage; silent bypass of compliance check on negative voltages. |
| **D4** | Dead Code & Unused Params | `get_conductor_resistivity` accepts `insulation` parameter but never uses it. In `calculate_voltage_drop`, DC circuits compute AC reactance when `cos_phi < 1.0`. | Leftover signature artifact forwarded without implementation; DC branch missing AC reactance override. | Dead code, linter / review audit warnings, potential confusion on physical validity. |

---

## 2. Exact Remediation Specification for `src/ampy/core/formulas.py`

### 2.1 Coerce System Strings in `calculate_ib` (Defect D1)

#### Location
`src/ampy/core/formulas.py`, lines 146–178.

#### Current Code
```python
    # Normalize system identifier
    sys_str = system.value if hasattr(system, "value") else str(system).upper()
    sys_str = str(sys_str).upper()
    is_single = "SINGLE" in sys_str or sys_str == "1"
    is_three = "THREE" in sys_str or sys_str == "3"
    is_dc = "DC" in sys_str

    if is_dc:
        if power_w is not None:
            ib = power_w / voltage_v
        else:
            raise ValueError("DC circuits require active power (W/kW) or direct current (A).")
        return round(ib, 3)

    # Validate power factor for AC circuits
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError(f"cos_phi must be in the open-closed interval (0.0, 1.0], got {cos_phi}")

    if is_single:
        if power_w is not None:
            ib = power_w / (voltage_v * cos_phi)
        else:  # apparent_power_va is not None
            ib = apparent_power_va / voltage_v
    elif is_three:
        sqrt3 = math.sqrt(3.0)
        if power_w is not None:
            ib = power_w / (sqrt3 * voltage_v * cos_phi)
        else:  # apparent_power_va is not None
            ib = apparent_power_va / (sqrt3 * voltage_v)
    else:
        raise ValueError(f"Unsupported system type: {system}")
```

#### Proposed Replacement
```python
    # Normalize system identifier via PhaseSystem
    try:
        phase_sys = system if isinstance(system, PhaseSystem) else PhaseSystem(system)
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Unsupported system type: {system}") from exc

    if phase_sys == PhaseSystem.DC:
        if power_w is not None:
            ib = power_w / voltage_v
        else:
            raise ValueError("DC circuits require active power (W/kW) or direct current (A).")
        return round(ib, 3)

    # Validate power factor for AC circuits
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError(f"cos_phi must be in the open-closed interval (0.0, 1.0], got {cos_phi}")

    if phase_sys == PhaseSystem.SINGLE_PHASE:
        if power_w is not None:
            ib = power_w / (voltage_v * cos_phi)
        else:  # apparent_power_va is not None
            ib = apparent_power_va / voltage_v
    elif phase_sys == PhaseSystem.THREE_PHASE:
        sqrt3 = math.sqrt(3.0)
        if power_w is not None:
            ib = power_w / (sqrt3 * voltage_v * cos_phi)
        else:  # apparent_power_va is not None
            ib = apparent_power_va / (sqrt3 * voltage_v)
    else:
        raise ValueError(f"Unsupported system type: {system}")
```

#### Technical Rationale
- `PhaseSystem(system)` invokes `PhaseSystem._missing_`, automatically handling:
  - `"1P"`, `"1p"`, `"1"`, `"single"`, `"single_phase"`, `"single-phase"`, `1`
  - `"3P"`, `"3p"`, `"3"`, `"three"`, `"three_phase"`, `"three-phase"`, `3`
  - `"DC"`, `"dc"`, `"direct"`, `"direct_current"`, `"0"`, `0`
- Catching `(ValueError, TypeError, KeyError)` and re-raising `ValueError(f"Unsupported system type: {system}")` ensures backward compatibility with existing test assertions (`pytest.raises(ValueError, match="Unsupported system type")`).

---

### 2.2 Clean Up `get_conductor_resistivity` (Defects D2 & D4)

#### Location
`src/ampy/core/formulas.py`, lines 244–275.

#### Current Code
```python
def get_conductor_resistivity(
    material: ConductorMaterial | str,
    operating_temp_c: float | None = None,
    insulation: InsulationType | str | None = None,
) -> float:
    """
    Returns conductor resistivity rho1 in Ω·mm²/m.
    Default returns normative conventional values (UTE C 15-105 §5.3):
      - Cu: 0.023 Ω·mm²/m
      - Al: 0.037 Ω·mm²/m
    If operating_temp_c is provided, computes exact temperature-adjusted resistivity.
    """
    mat_str = material.value if hasattr(material, "value") else str(material)
    mat_str = mat_str.strip().capitalize()

    if operating_temp_c is None:
        if mat_str in ("Cu", "Copper"):
            return RHO1_CU
        elif mat_str in ("Al", "Aluminium", "Aluminum"):
            return RHO1_AL
        raise ValueError(f"Unknown conductor material: {material}")

    # Temperature adjustment: rho(theta) = rho20 * [1 + alpha20 * (theta - 20)]
    if mat_str in ("Cu", "Copper"):
        rho20, alpha20 = 0.01851, 0.00393
    elif mat_str in ("Al", "Aluminium", "Aluminum"):
        rho20, alpha20 = 0.02941, 0.00403
    else:
        raise ValueError(f"Unknown conductor material: {material}")

    return round(rho20 * (1.0 + alpha20 * (operating_temp_c - 20.0)), 5)
```

#### Proposed Replacement
```python
def get_conductor_resistivity(
    material: ConductorMaterial | str,
    operating_temp_c: float | None = None,
) -> float:
    """
    Returns conductor resistivity rho1 in Ω·mm²/m per UTE C 15-105 §5.3.

    Default returns normative conventional values:
      - Cu: 0.023 Ω·mm²/m
      - Al: 0.037 Ω·mm²/m
    If operating_temp_c is provided, computes exact temperature-adjusted resistivity:
      rho(theta) = rho20 * [1 + alpha20 * (theta - 20)]
    """
    try:
        mat = material if isinstance(material, ConductorMaterial) else ConductorMaterial(material)
        mat_str = mat.value  # strictly "Cu" or "Al"
    except (ValueError, TypeError, KeyError):
        mat_str = str(material)

    if mat_str == "Cu":
        if operating_temp_c is None:
            return RHO1_CU
        rho20, alpha20 = 0.01851, 0.00393
        return round(rho20 * (1.0 + alpha20 * (operating_temp_c - 20.0)), 5)
    elif mat_str == "Al":
        if operating_temp_c is None:
            return RHO1_AL
        rho20, alpha20 = 0.02941, 0.00403
        return round(rho20 * (1.0 + alpha20 * (operating_temp_c - 20.0)), 5)
    else:
        raise ValueError(f"Unknown conductor material: {material}")
```

#### Technical Rationale
- Completely removes the dead/unused parameter `insulation`.
- Leverages `ConductorMaterial` coercion to uniformly recognize `"Cu"`, `"cu"`, `"copper"`, `"cuivre"`, `"Al"`, `"al"`, `"aluminium"`, `"aluminum"`.
- Eliminates duplicated branch checking (`if operating_temp_c is None` vs not None).
- Re-raises `ValueError(f"Unknown conductor material: {material}")` on unrecognized inputs like `"Gold"`, preserving 100% test compatibility.

---

### 2.3 Defensive Handling & System Coercion in `calculate_voltage_drop` (Defects D1, D3 & D4)

#### Location
`src/ampy/core/formulas.py`, lines 288–405.

#### Current Code
```python
def calculate_voltage_drop(
    system: PhaseSystem | str | int | None = None,
    length_m: float = 0.0,
    section_mm2: float = 0.0,
    ib_a: float = 0.0,
    cos_phi: float = 1.0,
    material: ConductorMaterial | str = ConductorMaterial.CU,
    voltage_v: float = 400.0,
    du_max_percent: float = 5.0,
    operating_temp_c: float | None = None,
    u_ref: float | None = None,
    phases: PhaseSystem | str | int | None = None,
    conductor: ConductorMaterial | str | None = None,
    insulation: InsulationType | str | None = None,
    multicore: bool = True,
    reactance_ohm_m: float | None = None,
) -> VoltageDropResult:
...
    if phases is not None:
        system = phases
    if conductor is not None:
        material = conductor
    if system is None:
        raise ValueError("Must provide system or phases.")

    if length_m < 0.0:
        raise ValueError(f"length_m must be non-negative, got {length_m}")
    if section_mm2 <= 0.0:
        raise ValueError(f"section_mm2 must be strictly positive, got {section_mm2}")
    if ib_a < 0.0:
        raise ValueError(f"ib_a must be non-negative, got {ib_a}")
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError(f"cos_phi must be in (0.0, 1.0], got {cos_phi}")

    sys_str = system.value if hasattr(system, "value") else str(system).upper()
    sys_str = str(sys_str).upper()
    is_single = "SINGLE" in sys_str or sys_str == "1"
    is_three = "THREE" in sys_str or sys_str == "3"
    is_dc = "DC" in sys_str

    if is_three:
        b = 1.0
        default_u_ref = 230.0 if math.isclose(voltage_v, 400.0, rel_tol=0.1) else (voltage_v / math.sqrt(3.0))
    elif is_single or is_dc:
        b = 2.0
        default_u_ref = voltage_v
    else:
        raise ValueError(f"Unsupported system type: {system}")

    ref_voltage = u_ref if u_ref is not None else default_u_ref

    if length_m == 0.0 or ib_a == 0.0:
        return VoltageDropResult(
            du_volts=0.0,
            du_percent=0.0,
            du_max_percent=round(du_max_percent, 2),
            is_compliant=True,
            margin_percent=round(du_max_percent, 2),
            b_factor=b,
        )

    sin_phi = calculate_sin_phi(cos_phi)
    rho = get_conductor_resistivity(material, operating_temp_c, insulation=insulation)
    lambda_val = reactance_ohm_m if reactance_ohm_m is not None else get_linear_reactance(section_mm2, multicore=multicore)

    resistance_term = (rho * length_m / section_mm2) * cos_phi
    reactance_term = (lambda_val * length_m) * sin_phi

    du_volts = b * (resistance_term + reactance_term) * ib_a
    du_percent = (du_volts / ref_voltage) * 100.0
    is_compliant = du_percent <= (du_max_percent + 1e-9)

    return VoltageDropResult(
        du_volts=round(du_volts, 3),
        du_percent=round(du_percent, 3),
        du_max_percent=round(du_max_percent, 2),
        is_compliant=is_compliant,
        margin_percent=round(du_max_percent - du_percent, 3),
        b_factor=b,
    )
```

#### Proposed Replacement
```python
def calculate_voltage_drop(
    system: PhaseSystem | str | int | None = None,
    length_m: float = 0.0,
    section_mm2: float = 0.0,
    ib_a: float = 0.0,
    cos_phi: float = 1.0,
    material: ConductorMaterial | str = ConductorMaterial.CU,
    voltage_v: float = 400.0,
    du_max_percent: float = 5.0,
    operating_temp_c: float | None = None,
    u_ref: float | None = None,
    phases: PhaseSystem | str | int | None = None,
    conductor: ConductorMaterial | str | None = None,
    insulation: InsulationType | str | None = None,
    multicore: bool = True,
    reactance_ohm_m: float | None = None,
) -> VoltageDropResult:
    """
    Calculates exact voltage drop dU in Volts and % per UTE C 15-105 §5.3.

    Formula:
      dU = b * [ rho1 * (L / S) * cos_phi + lambda * L * sin_phi ] * Ib
    """
    if phases is not None:
        system = phases
    if conductor is not None:
        material = conductor
    if system is None:
        raise ValueError("Must provide system or phases.")

    # Input boundary validations
    if length_m < 0.0:
        raise ValueError(f"length_m must be non-negative, got {length_m}")
    if section_mm2 <= 0.0:
        raise ValueError(f"section_mm2 must be strictly positive, got {section_mm2}")
    if ib_a < 0.0:
        raise ValueError(f"ib_a must be non-negative, got {ib_a}")
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError(f"cos_phi must be in (0.0, 1.0], got {cos_phi}")
    if voltage_v <= 0.0:
        raise ValueError(f"voltage_v must be strictly positive, got {voltage_v}")
    if u_ref is not None and u_ref <= 0.0:
        raise ValueError(f"u_ref must be strictly positive, got {u_ref}")
    if du_max_percent <= 0.0:
        raise ValueError(f"du_max_percent must be strictly positive, got {du_max_percent}")

    # Coerce system through PhaseSystem
    try:
        phase_sys = system if isinstance(system, PhaseSystem) else PhaseSystem(system)
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Unsupported system type: {system}") from exc

    if phase_sys == PhaseSystem.THREE_PHASE:
        b = 1.0
        default_u_ref = 230.0 if math.isclose(voltage_v, 400.0, rel_tol=0.1) else (voltage_v / math.sqrt(3.0))
    elif phase_sys in (PhaseSystem.SINGLE_PHASE, PhaseSystem.DC):
        b = 2.0
        default_u_ref = voltage_v
    else:
        raise ValueError(f"Unsupported system type: {system}")

    ref_voltage = u_ref if u_ref is not None else default_u_ref

    if length_m == 0.0 or ib_a == 0.0:
        return VoltageDropResult(
            du_volts=0.0,
            du_percent=0.0,
            du_max_percent=round(du_max_percent, 2),
            is_compliant=True,
            margin_percent=round(du_max_percent, 2),
            b_factor=b,
        )

    rho = get_conductor_resistivity(material, operating_temp_c)

    if phase_sys == PhaseSystem.DC:
        # DC circuits have zero frequency: reactance is identically zero, cos_phi = 1.0
        resistance_term = (rho * length_m / section_mm2)
        reactance_term = 0.0
    else:
        sin_phi = calculate_sin_phi(cos_phi)
        lambda_val = (
            reactance_ohm_m
            if reactance_ohm_m is not None
            else get_linear_reactance(section_mm2, multicore=multicore)
        )
        resistance_term = (rho * length_m / section_mm2) * cos_phi
        reactance_term = (lambda_val * length_m) * sin_phi

    du_volts = b * (resistance_term + reactance_term) * ib_a
    du_percent = (du_volts / ref_voltage) * 100.0
    is_compliant = du_percent <= (du_max_percent + 1e-9)

    return VoltageDropResult(
        du_volts=round(du_volts, 3),
        du_percent=round(du_percent, 3),
        du_max_percent=round(du_max_percent, 2),
        is_compliant=is_compliant,
        margin_percent=round(du_max_percent - du_percent, 3),
        b_factor=b,
    )
```

#### Technical Rationale
- `voltage_v <= 0.0` and `u_ref <= 0.0` are explicitly validated at function entry, raising `ValueError` and preventing any potential `ZeroDivisionError` or negative percentage calculations.
- `du_max_percent <= 0.0` is validated to prevent inverted compliance logic.
- Coerces `system` through `PhaseSystem`, allowing `"1P"`, `"3P"`, `"DC"`, etc.
- If `phase_sys == PhaseSystem.DC`, AC reactance is zeroed and $\cos\varphi$ is treated as $1.0$.
- Call to `get_conductor_resistivity(material, operating_temp_c)` removes dead `insulation` forwarding.
- `insulation: InsulationType | str | None = None` is retained in the signature as optional for backward compatibility with keyword callers.

---

### 2.4 Material & Insulation Coercion in `calculate_thermal_stress_min_section` and `calculate_thermal_stress` (Defect D2)

#### Location
`src/ampy/core/formulas.py`, lines 411–500.

#### Current Code (`calculate_thermal_stress_min_section`)
```python
    mat_str = material.value if hasattr(material, "value") else str(material)
    mat_str = mat_str.strip().capitalize()
    ins_str = insulation.value if hasattr(insulation, "value") else str(insulation)
    ins_str = ins_str.strip().upper()

    key = (mat_str, ins_str)
    if key not in K_THERMAL_FACTORS:
        raise ValueError(f"Unknown material/insulation combination: {key}")
```

#### Current Code (`calculate_thermal_stress`)
```python
    mat_str = material.value if hasattr(material, "value") else str(material)
    mat_str = mat_str.strip().capitalize()
    ins_str = insulation.value if hasattr(insulation, "value") else str(insulation)
    ins_str = ins_str.strip().upper()

    k = K_THERMAL_FACTORS.get((mat_str, ins_str))
    if k is None:
        raise ValueError(f"Unknown material/insulation combination: {(mat_str, ins_str)}")
```

#### Proposed Replacement for Both Functions
In `calculate_thermal_stress_min_section`:
```python
    # Coerce material and insulation through standard Enums
    try:
        mat = material if isinstance(material, ConductorMaterial) else ConductorMaterial(material)
        mat_str = mat.value  # strictly "Cu" or "Al"
    except (ValueError, TypeError, KeyError):
        mat_str = str(material)

    try:
        ins = insulation if isinstance(insulation, InsulationType) else InsulationType(insulation)
        ins_str = ins.value  # strictly "PVC" or "XLPE"
    except (ValueError, TypeError, KeyError):
        ins_str = str(insulation)

    key = (mat_str, ins_str)
    if key not in K_THERMAL_FACTORS:
        raise ValueError(f"Unknown material/insulation combination: {key}")

    k = K_THERMAL_FACTORS[key]
    s_min = (ik_a * math.sqrt(time_s)) / k
    return round(s_min, 2)
```

In `calculate_thermal_stress`:
```python
    # Coerce material and insulation through standard Enums
    try:
        mat = material if isinstance(material, ConductorMaterial) else ConductorMaterial(material)
        mat_str = mat.value
    except (ValueError, TypeError, KeyError):
        mat_str = str(material)

    try:
        ins = insulation if isinstance(insulation, InsulationType) else InsulationType(insulation)
        ins_str = ins.value
    except (ValueError, TypeError, KeyError):
        ins_str = str(insulation)

    key = (mat_str, ins_str)
    k = K_THERMAL_FACTORS.get(key)
    if k is None:
        raise ValueError(f"Unknown material/insulation combination: {key}")

    s_min = calculate_thermal_stress_min_section(ik_a, time_s, mat, ins)
    i2t = (ik_a ** 2) * time_s
    is_compliant = selected_section_mm2 >= s_min

    return ThermalStressResult(
        ik_a=float(ik_a),
        time_s=float(time_s),
        i2t=round(i2t, 2),
        k_factor=k,
        s_min_mm2=s_min,
        is_compliant=is_compliant,
    )
```

#### Technical Rationale
- Standardizes both `calculate_thermal_stress_min_section` and `calculate_thermal_stress` to accept string aliases:
  - Material: `"copper"`, `"cu"`, `"cuivre"`, `"Cu"`, `"aluminium"`, `"aluminum"`, `"al"`, `"Al"`.
  - Insulation: `"pvc"`, `"PVC"`, `"xlpe"`, `"XLPE"`, `"pr"`, `"PR"`, `"epr"`, `"EPR"`.
- If an unsupported material or insulation is passed (e.g. `"Steel"` or `"Silver"`), it raises `ValueError: Unknown material/insulation combination: ('Steel', 'PVC')`, matching existing unit test assertions.

---

## 3. Test Suite Remediation Specification

### 3.1 New Unit Tests in `tests/unit/test_formulas.py`

The following test methods must be added to `tests/unit/test_formulas.py`:

```python
class TestStringCoercionAndDefensiveGuards:
    """Verifies string shorthand normalization and defensive guards for pure calculation functions."""

    @pytest.mark.parametrize("sys_val", ["1P", "1p", "1", 1, "single", "single_phase", "single-phase"])
    def test_calculate_ib_single_phase_aliases(self, sys_val):
        ib = calculate_ib(system=sys_val, voltage_v=230.0, power_kw=2.3)
        assert math.isclose(ib, 10.0, rel_tol=1e-3)

    @pytest.mark.parametrize("sys_val", ["3P", "3p", "3", 3, "three", "three_phase", "three-phase"])
    def test_calculate_ib_three_phase_aliases(self, sys_val):
        ib = calculate_ib(system=sys_val, voltage_v=400.0, power_kw=4000.0 * math.sqrt(3) / 1000.0)
        assert math.isclose(ib, 10.0, rel_tol=1e-3)

    @pytest.mark.parametrize("sys_val", ["DC", "dc", "direct", 0])
    def test_calculate_ib_dc_aliases(self, sys_val):
        ib = calculate_ib(system=sys_val, voltage_v=24.0, power_w=240.0)
        assert math.isclose(ib, 10.0, rel_tol=1e-3)

    @pytest.mark.parametrize("sys_val", ["1P", "3P", "DC"])
    def test_calculate_voltage_drop_system_string_coercion(self, sys_val):
        res = calculate_voltage_drop(
            system=sys_val,
            length_m=50.0,
            section_mm2=10.0,
            ib_a=20.0,
            cos_phi=0.85,
            material="copper",
        )
        assert res.du_volts > 0.0
        assert res.du_percent > 0.0

    @pytest.mark.parametrize("bad_v", [0.0, -10.0, -230.0])
    def test_calculate_voltage_drop_invalid_voltage(self, bad_v):
        with pytest.raises(ValueError, match="voltage_v must be strictly positive"):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=10.0,
                section_mm2=4.0,
                ib_a=10.0,
                voltage_v=bad_v,
            )

    @pytest.mark.parametrize("bad_u_ref", [0.0, -10.0, -230.0])
    def test_calculate_voltage_drop_invalid_u_ref(self, bad_u_ref):
        with pytest.raises(ValueError, match="u_ref must be strictly positive"):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=10.0,
                section_mm2=4.0,
                ib_a=10.0,
                voltage_v=230.0,
                u_ref=bad_u_ref,
            )

    @pytest.mark.parametrize("mat_alias", ["copper", "cu", "cuivre", "Cu"])
    def test_thermal_stress_copper_aliases(self, mat_alias):
        s_min = calculate_thermal_stress_min_section(
            ik_a=5000.0,
            time_s=0.20,
            material=mat_alias,
            insulation="PVC",
        )
        assert math.isclose(s_min, 19.44, rel_tol=0.005)

    @pytest.mark.parametrize("mat_alias", ["aluminium", "aluminum", "al", "Al"])
    def test_thermal_stress_aluminium_aliases(self, mat_alias):
        s_min = calculate_thermal_stress_min_section(
            ik_a=5000.0,
            time_s=0.20,
            material=mat_alias,
            insulation="XLPE",
        )
        assert math.isclose(s_min, 23.79, rel_tol=0.005)

    @pytest.mark.parametrize("ins_alias", ["pvc", "PVC", "xlpe", "XLPE", "PR", "pr"])
    def test_thermal_stress_insulation_aliases(self, ins_alias):
        s_min = calculate_thermal_stress_min_section(
            ik_a=5000.0,
            time_s=0.20,
            material="Cu",
            insulation=ins_alias,
        )
        assert s_min > 0.0

    @pytest.mark.parametrize("mat_alias", ["copper", "cu", "cuivre"])
    def test_get_conductor_resistivity_aliases(self, mat_alias):
        assert get_conductor_resistivity(mat_alias) == 0.023
        assert get_conductor_resistivity(mat_alias, operating_temp_c=20.0) == 0.01851
```

### 3.2 Update `tests/boundary/test_boundaries.py`

In `tests/boundary/test_boundaries.py`, class `TestDiscoveredVulnerabilities`:

#### Test 1: Update `test_voltage_v_zero_raises_unhandled_zero_division`
- **Before**:
  ```python
  def test_voltage_v_zero_raises_unhandled_zero_division(self):
      with pytest.raises(ZeroDivisionError):
          calculate_voltage_drop(
              system=PhaseSystem.SINGLE_PHASE,
              length_m=10.0,
              section_mm2=4.0,
              ib_a=10.0,
              voltage_v=0.0,
          )
  ```
- **After**:
  ```python
  def test_voltage_v_zero_raises_unhandled_zero_division(self):
      with pytest.raises(ValueError, match="voltage_v must be strictly positive"):
          calculate_voltage_drop(
              system=PhaseSystem.SINGLE_PHASE,
              length_m=10.0,
              section_mm2=4.0,
              ib_a=10.0,
              voltage_v=0.0,
          )
  ```

#### Test 2: Update `test_thermal_stress_string_material_copper_rejected`
- **Before**:
  ```python
  def test_thermal_stress_string_material_copper_rejected(self):
      with pytest.raises(ValueError, match="Unknown material/insulation combination"):
          calculate_thermal_stress_min_section(
              ik_a=5000.0,
              time_s=0.1,
              material="copper",
              insulation="PVC",
          )
  ```
- **After**:
  ```python
  def test_thermal_stress_string_material_copper_rejected(self):
      # Remediated: string alias 'copper' is now seamlessly accepted
      s_min = calculate_thermal_stress_min_section(
          ik_a=5000.0,
          time_s=0.1,
          material="copper",
          insulation="PVC",
      )
      assert math.isclose(s_min, 13.75, rel_tol=0.01)
  ```

---

## 4. Verification & Validation Protocol

The implementing agent can verify complete compliance using:

1. **Unit & Edge Case Suite**:
   ```powershell
   pytest tests/unit/test_formulas.py -v
   ```
   *Expected*: All tests pass, 100% pass rate.

2. **Adversarial Stress Harness**:
   ```powershell
   python tests/boundary/test_boundaries.py
   pytest tests/boundary/test_boundaries.py -v
   ```
   *Expected*: All 39 tests pass with `[PASS]`, exit code `0`.

3. **Full Repository Regression**:
   ```powershell
   pytest
   ```
   *Expected*: 100% test pass rate across all test suites.

4. **Code Quality and Ruff Formatting**:
   ```powershell
   python -m ruff check src/ tests/unit/
   ```
   *Expected*: `All checks passed!`, exit code `0`.

5. **Direct Verification One-Liners**:
   ```powershell
   python -c "from ampy.core.formulas import calculate_ib, calculate_voltage_drop, calculate_thermal_stress_min_section; assert calculate_ib('1P', 230, power_w=2300) == 10.0; assert calculate_voltage_drop('3P', 10, 4, 10).is_compliant; assert calculate_thermal_stress_min_section(5000, 0.1, 'copper', 'PVC') > 0; print('REMEDIATION VERIFIED OK')"
   ```
   *Expected*: Prints `REMEDIATION VERIFIED OK` with exit code `0`.
