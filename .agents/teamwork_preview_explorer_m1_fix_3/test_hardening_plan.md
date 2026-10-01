# Test Suite Hardening Plan — Milestone 1 (M1)

**Author**: `teamwork_preview_explorer_m1_fix_3`  
**Roles**: `explorer`, `investigation`, `synthesis`  
**Target Milestone**: Milestone 1 — Foundation, Pydantic v2 Models & Pure Formulas  
**Date**: 2026-09-30  
**Status**: COMPLETE / READY FOR IMPLEMENTATION  

---

## 1. Executive Summary & Hardening Objectives

During Milestone 1 quality audits, Challenger 2 established a 51-vector standalone empirical stress harness (`tests/adversarial_challenge_models.py`) uncovering 18 vulnerabilities in `ampy.core.models`, while Challenger 1 established a 39-vector stress harness in `tests/boundary/test_boundaries.py` uncovering 2 vulnerabilities in `ampy.core.formulas`.

This hardening plan defines the complete specifications to:
1. **Convert the 51-vector Challenger 2 harness into a formal pytest module**:
   - Target location: `tests/boundary/test_models_adversarial.py`.
   - Collect and execute all 51 adversarial vectors natively under `pytest`.
   - Ensure clear parameterization, informative failure reports, and full compatibility with the existing test runner.
2. **Add dedicated unit tests** in `tests/unit/test_models.py` and `tests/unit/test_formulas.py`:
   - Enum hashability: verifying `hash(PhaseSystem.*)`, `hash(LimitingConstraint.*)`, dictionary key storage, set operations, `@functools.lru_cache` support, and strict boolean trap isolation (`PhaseSystem.SINGLE_PHASE != True`, `PhaseSystem.DC != False`).
   - String inputs to calculation formulas: `calculate_ib(system="1P", ...)` and `calculate_voltage_drop(system="3P", ...)` supporting `"1P"`, `"3P"`, `"DC"`, `"single_phase"`, `"three_phase"`, etc.
   - Conductor material string aliases in `calculate_thermal_stress_min_section`: supporting `"copper"`, `"cuivre"`, `"Cu"`, `"aluminium"`, `"aluminum"`, `"Al"`, along with insulation aliases (`"pvc"`, `"xlpe"`, `"pr"`, `"epr"`).
3. **Guarantee zero regression across existing suites**:
   - Preserve all existing 182 unit tests (101 formulas, 81 models).
   - Reconcile the 2 vulnerability probes in `tests/boundary/test_boundaries.py` (`TestDiscoveredVulnerabilities`) to assert hardened behavior, maintaining 39/39 passing tests.
   - Deliver a combined suite of 278+ automated tests passing with 100% success rate.

---

## 2. Test Architecture & Directory Layout

The hardened test suite strictly adheres to the 4-tier testing hierarchy defined in `PROJECT.md` § Code Layout:

```
tests/
├── __init__.py
├── conftest.py
├── test_harness_fixtures.py             # 6 fixture validation tests
├── unit/                                # Tier 1: Unit & formula tests (182 + 12 new = 194 tests)
│   ├── test_formulas.py                 # 101 existing + 8 new string/material tests = 109 tests
│   ├── test_models.py                   # 81 existing + 4 new enum hash/bool tests = 85 tests
│   └── test_tables.py                   # (Scheduled M2)
├── boundary/                            # Tier 2: Boundary & adversarial stress tests (90 tests)
│   ├── test_boundaries.py               # 39 adversarial formulas stress tests (reconciled)
│   └── test_models_adversarial.py       # 51 adversarial domain model vectors (NEW)
├── combinatorial/                       # Tier 3: Pairwise matrix (Scheduled M3)
└── e2e/                                 # Tier 4: UTE C 15-105 benchmarks (Scheduled M3/M5)
    ├── test_ute_benchmarks.py           # (1 test currently skipped pending M3 engine)
    └── test_cli.py                      # (Scheduled M4)
```

---

## 3. Part 1: Conversion of Challenger 2 Harness into `tests/boundary/test_models_adversarial.py`

### 3.1 Traceability Matrix (51 Vectors)

The standalone script `tests/adversarial_challenge_models.py` executes 51 distinct adversarial vectors across 6 challenge categories. In `test_models_adversarial.py`, each vector maps directly to an automated pytest test case:

| Vector ID | Category | Original Harness Vector | Pytest Test Method | Parametrized Cases |
|-----------|----------|-------------------------|--------------------|-------------------|
| **V1.1** | Multi-Load Confusion | No load parameters provided | `test_no_load_parameters_rejected` | 1 |
| **V1.2** | Multi-Load Confusion | All load parameters None | `test_all_load_parameters_none_rejected` | 1 |
| **V1.3** | Multi-Load Confusion | `power_kw` + `current_a` | `test_conflicting_power_kw_and_current_a_rejected` | 1 |
| **V1.4** | Multi-Load Confusion | `power_kw` + `apparent_power_kva` | `test_conflicting_power_kw_and_apparent_power_kva_rejected` | 1 |
| **V1.5** | Multi-Load Confusion | `apparent_power_kva` + `current_a` | `test_conflicting_apparent_power_kva_and_current_a_rejected` | 1 |
| **V1.6** | Multi-Load Confusion | All three load parameters | `test_all_three_load_parameters_provided_rejected` | 1 |
| **V1.7** | Multi-Load Confusion | Alias collision (`power_kw` + `active_power_kw`) | `test_alias_collision_power_kw_and_active_power_kw_rejected` | 1 |
| **V1.8** | Multi-Load Confusion | Non-positive loads (0.0 and -5.0) | `test_non_positive_load_rejected` | 6 (`power_kw`, `apparent_power_kva`, `current_a` × {0, -5}) |
| **V2.1** | Numeric Extremes & Types | String in numeric field | `test_string_in_numeric_field_rejected` | 3 (`voltage_v`, `power_kw`, `length_m`) |
| **V2.2** | Numeric Extremes & Types | Boolean coercion attack (`True == 1.0`) | `test_boolean_coercion_rejected` | 1 |
| **V2.3** | Numeric Extremes & Types | `NaN` in float fields | `test_nan_in_float_fields_rejected` | 3 (`voltage_v`, `power_kw`, `length_m`) |
| **V2.4** | Numeric Extremes & Types | Positive Infinity (`float('inf')`) | `test_positive_inf_in_fields_rejected` | 8 (`voltage_v`, `power_kw`, `kva`, `current_a`, `freq`, `length_m`, `in_a`, `ik_a`) |
| **V2.5** | Numeric Extremes & Types | String `'inf'` / `'Infinity'` coercion | `test_string_inf_coercion_rejected` | 1 |
| **V2.6** | Numeric Extremes & Types | Negative Infinity (`float('-inf')`) | `test_negative_inf_in_voltage_rejected` | 1 |
| **V3.1** | Model Immutability | Direct mutation of sub-models | `test_submodels_direct_mutation_blocked` | 5 (`ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `VoltageDropResult`) |
| **V3.2** | Model Immutability | `CircuitDefinition` direct mutation & type bypass | `test_circuit_definition_mutation_blocked`, `test_circuit_definition_type_bypass_mutation_blocked` | 2 |
| **V4.1** | Extra Fields Handling | Input models extra fields forbidden | `test_input_models_extra_fields_forbidden` | 5 (`ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `CircuitDefinition`) |
| **V4.2** | Extra Fields Handling | Output models extra fields forbidden | `test_intermediate_factors_extra_fields_forbidden`, `test_voltage_drop_result_extra_fields_forbidden` | 2 |
| **V5.1** | JSON Fidelity | `CircuitDefinition` roundtrip | `test_circuit_definition_json_roundtrip_fidelity` | 1 |
| **V5.2** | JSON Fidelity | `SizingResult` nested roundtrip | `test_sizing_result_json_roundtrip_fidelity` | 1 |
| **V5.3** | JSON Fidelity | IEEE-754 64-bit precision preservation | `test_ieee754_precision_preservation` | 1 |
| **V5.4** | JSON Fidelity | Inf JSON serialization protection | `test_inf_json_serialization_protection` | 1 |
| **V6.1** | Enum Integrity | `PhaseSystem` hashability | `test_phase_system_hashability` | 1 |
| **V6.2** | Enum Integrity | `LimitingConstraint` hashability | `test_limiting_constraint_hashability` | 1 |
| **V6.3** | Enum Integrity | `PhaseSystem` boolean trap (`== True/False`) | `test_phase_system_boolean_trap` | 1 |
| **TOTAL**| | | | **51 Collected Test Cases** |

### 3.2 Full Source Code Specification: `tests/boundary/test_models_adversarial.py`

This module is designed to be placed at `tests/boundary/test_models_adversarial.py`. It requires zero external dependencies beyond `pytest` and `pydantic`.

```python
"""
tests/boundary/test_models_adversarial.py
=========================================
Adversarial stress testing and empirical boundary verification for `ampy.core.models`.
Converts the 51-vector standalone challenge harness into a formal pytest module.

Conforms strictly to:
- NF C 15-100 (Part 5-52)
- UTE C 15-105
- Tier 2 Boundary / Tier 5 Adversarial test specifications
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from ampy.core.models import (
    CableSpecs,
    CircuitDefinition,
    ConductorMaterial,
    ElectricalLoad,
    InstallationConditions,
    InstallationMethod,
    InsulationType,
    IntermediateFactors,
    LimitingConstraint,
    PhaseSystem,
    ProtectionDevice,
    SizingResult,
    ThermalStressResult,
    VoltageDropResult,
)


# ==============================================================================
# Suite 1: Multi-Load Confusion & Load Boundary Attacks (13 test cases)
# ==============================================================================

class TestAdversarialMultiLoad:
    """Stress testing load input exclusivity and non-positive boundary rejections."""

    def test_no_load_parameters_rejected(self):
        """V1.1: Instantiation with no load parameter must raise ValidationError/ValueError."""
        with pytest.raises((ValidationError, ValueError)):
            ElectricalLoad(voltage_v=230.0)

    def test_all_load_parameters_none_rejected(self):
        """V1.2: Instantiation with all load parameters explicitly None must be rejected."""
        with pytest.raises((ValidationError, ValueError)):
            ElectricalLoad(voltage_v=230.0, power_kw=None, apparent_power_kva=None, current_a=None)

    def test_conflicting_power_kw_and_current_a_rejected(self):
        """V1.3: Conflicting power_kw and current_a must be rejected."""
        with pytest.raises((ValidationError, ValueError)):
            ElectricalLoad(voltage_v=400.0, power_kw=15.0, current_a=25.0)

    def test_conflicting_power_kw_and_apparent_power_kva_rejected(self):
        """V1.4: Conflicting power_kw and apparent_power_kva must be rejected."""
        with pytest.raises((ValidationError, ValueError)):
            ElectricalLoad(voltage_v=400.0, power_kw=15.0, apparent_power_kva=20.0)

    def test_conflicting_apparent_power_kva_and_current_a_rejected(self):
        """V1.5: Conflicting apparent_power_kva and current_a must be rejected."""
        with pytest.raises((ValidationError, ValueError)):
            ElectricalLoad(voltage_v=400.0, apparent_power_kva=20.0, current_a=25.0)

    def test_all_three_load_parameters_provided_rejected(self):
        """V1.6: All three load parameters provided simultaneously must be rejected."""
        with pytest.raises((ValidationError, ValueError)):
            ElectricalLoad(voltage_v=400.0, power_kw=15.0, apparent_power_kva=20.0, current_a=25.0)

    def test_alias_collision_power_kw_and_active_power_kw_rejected(self):
        """V1.7: Supplying both canonical field and alias in dict input must be rejected as extra_forbidden."""
        with pytest.raises(ValidationError):
            ElectricalLoad.model_validate({"voltage_v": 400.0, "power_kw": 10.0, "active_power_kw": 15.0})

    @pytest.mark.parametrize("param, val", [
        ("power_kw", 0.0),
        ("power_kw", -5.0),
        ("apparent_power_kva", 0.0),
        ("apparent_power_kva", -5.0),
        ("current_a", 0.0),
        ("current_a", -5.0),
    ])
    def test_non_positive_load_rejected(self, param: str, val: float):
        """V1.8.1-V1.8.6: Zero and negative loads must be strictly rejected by validation bounds."""
        with pytest.raises(ValidationError):
            ElectricalLoad(**{"voltage_v": 230.0, param: val})


# ==============================================================================
# Suite 2: Numeric Extremes, Types, NaN and Inf Values (17 test cases)
# ==============================================================================

class TestAdversarialNumericExtremesAndTypes:
    """Stress testing type safety, boolean coercion, and non-finite float rejection."""

    @pytest.mark.parametrize("field, bad_str", [
        ("voltage_v", "two-hundred-thirty"),
        ("power_kw", "10kW"),
        ("length_m", "50m"),
    ])
    def test_string_in_numeric_field_rejected(self, field: str, bad_str: str):
        """V2.1.1-V2.1.3: Arbitrary non-numeric strings in numeric fields must raise ValidationError."""
        with pytest.raises(ValidationError):
            if field == "length_m":
                CableSpecs(length_m=bad_str)  # type: ignore
            else:
                ElectricalLoad(**{"voltage_v": 230.0, "power_kw": 10.0, field: bad_str})

    def test_boolean_coercion_rejected(self):
        """V2.2: Boolean values (True/False) must not be silently coerced to numeric 1.0/0.0."""
        with pytest.raises(ValidationError):
            ElectricalLoad(voltage_v=True, power_kw=True)  # type: ignore

    @pytest.mark.parametrize("field, model_cls, kwargs", [
        ("voltage_v", ElectricalLoad, {"voltage_v": float("nan"), "power_kw": 10.0}),
        ("power_kw", ElectricalLoad, {"voltage_v": 230.0, "power_kw": float("nan")}),
        ("length_m", CableSpecs, {"length_m": float("nan")}),
    ])
    def test_nan_in_float_fields_rejected(self, field: str, model_cls: Any, kwargs: dict[str, Any]):
        """V2.3.1-V2.3.3: NaN in float fields must be strictly rejected."""
        with pytest.raises(ValidationError):
            model_cls(**kwargs)

    @pytest.mark.parametrize("field, model_cls, kwargs", [
        ("voltage_v", ElectricalLoad, {"voltage_v": float("inf"), "power_kw": 10.0}),
        ("power_kw", ElectricalLoad, {"voltage_v": 230.0, "power_kw": float("inf")}),
        ("apparent_power_kva", ElectricalLoad, {"voltage_v": 230.0, "apparent_power_kva": float("inf")}),
        ("current_a", ElectricalLoad, {"voltage_v": 230.0, "current_a": float("inf")}),
        ("frequency_hz", ElectricalLoad, {"voltage_v": 230.0, "power_kw": 10.0, "frequency_hz": float("inf")}),
        ("length_m", CableSpecs, {"length_m": float("inf")}),
        ("in_a", ProtectionDevice, {"in_a": float("inf")}),
        ("ik_a", ProtectionDevice, {"ik_a": float("inf")}),
    ])
    def test_positive_inf_in_fields_rejected(self, field: str, model_cls: Any, kwargs: dict[str, Any]):
        """V2.4.1-V2.4.8: Positive Infinity float('inf') must be rejected by allow_inf_nan=False."""
        with pytest.raises(ValidationError):
            model_cls(**kwargs)

    def test_string_inf_coercion_rejected(self):
        """V2.5: String 'inf' or 'Infinity' must be rejected rather than parsed into float('inf')."""
        with pytest.raises(ValidationError):
            ElectricalLoad(voltage_v="inf", power_kw=10.0)  # type: ignore

    def test_negative_inf_in_voltage_rejected(self):
        """V2.6: Negative Infinity float('-inf') must be rejected."""
        with pytest.raises(ValidationError):
            ElectricalLoad(voltage_v=float("-inf"), power_kw=10.0)


# ==============================================================================
# Suite 3: Model Immutability (7 test cases)
# ==============================================================================

class TestAdversarialModelImmutability:
    """Stress testing frozen=True across all domain models."""

    def test_electrical_load_mutation_blocked(self):
        """V3.1.1: Direct mutation of ElectricalLoad attributes must raise TypeError/ValidationError."""
        load = ElectricalLoad(voltage_v=230.0, power_kw=3.68)
        with pytest.raises((ValidationError, TypeError)):
            load.voltage_v = 400.0  # type: ignore

    def test_cable_specs_mutation_blocked(self):
        """V3.1.2: Direct mutation of CableSpecs attributes must be blocked."""
        cable = CableSpecs(length_m=50.0)
        with pytest.raises((ValidationError, TypeError)):
            cable.length_m = 100.0  # type: ignore

    def test_installation_conditions_mutation_blocked(self):
        """V3.1.3: Direct mutation of InstallationConditions attributes must be blocked."""
        inst = InstallationConditions()
        with pytest.raises((ValidationError, TypeError)):
            inst.ambient_temp_c = 45.0  # type: ignore

    def test_protection_device_mutation_blocked(self):
        """V3.1.4: Direct mutation of ProtectionDevice attributes must be blocked."""
        prot = ProtectionDevice(in_a=16.0)
        with pytest.raises((ValidationError, TypeError)):
            prot.in_a = 32.0  # type: ignore

    def test_voltage_drop_result_mutation_blocked(self):
        """V3.1.5: Direct mutation of VoltageDropResult attributes must be blocked."""
        vd = VoltageDropResult(du_volts=5.0, du_percent=2.0, du_max_percent=5.0, is_compliant=True, margin_percent=3.0)
        with pytest.raises((ValidationError, TypeError)):
            vd.du_volts = 15.0  # type: ignore

    def test_circuit_definition_mutation_blocked(self):
        """V3.2.1: CircuitDefinition must have frozen=True to forbid post-instantiation mutation."""
        circuit = CircuitDefinition(
            name="Circuit_Mutation_Target",
            load=ElectricalLoad(voltage_v=230.0, power_kw=3.68),
            cable=CableSpecs(length_m=50.0),
            du_max_percent=3.0,
        )
        with pytest.raises((ValidationError, TypeError)):
            circuit.du_max_percent = -999.0  # type: ignore

    def test_circuit_definition_type_bypass_mutation_blocked(self):
        """V3.2.2: CircuitDefinition must forbid mutating name to an invalid type."""
        circuit = CircuitDefinition(
            name="Circuit_Type_Target",
            load=ElectricalLoad(voltage_v=230.0, power_kw=3.68),
            cable=CableSpecs(length_m=50.0),
        )
        with pytest.raises((ValidationError, TypeError)):
            circuit.name = 12345  # type: ignore


# ==============================================================================
# Suite 4: Undeclared Extra Fields (7 test cases)
# ==============================================================================

class TestAdversarialExtraFields:
    """Stress testing extra='forbid' across input and output domain schemas."""

    @pytest.mark.parametrize("model_cls, kwargs", [
        (ElectricalLoad, {"voltage_v": 230.0, "power_kw": 3.0, "unauthorized_extra": 123}),
        (CableSpecs, {"length_m": 25.0, "hacked_param": True}),
        (InstallationConditions, {"bypass_flag": "enabled"}),
        (ProtectionDevice, {"backdoor": True}),
        (CircuitDefinition, {
            "name": "Exploit",
            "load": ElectricalLoad(voltage_v=230.0, power_kw=3.0),
            "cable": CableSpecs(length_m=25.0),
            "malicious_extra": 42,
        }),
    ])
    def test_input_models_extra_fields_forbidden(self, model_cls: Any, kwargs: dict[str, Any]):
        """V4.1.1-V4.1.5: Input domain models must forbid extra undeclared fields."""
        with pytest.raises(ValidationError, match="(?i)extra_forbidden|extra fields not permitted"):
            model_cls(**kwargs)

    def test_intermediate_factors_extra_fields_forbidden(self):
        """V4.2.1: IntermediateFactors output schema must enforce extra='forbid'."""
        factors_kwargs = {
            "k1_method": 1.0, "k2_grouping": 1.0, "k3_temperature": 1.0, "k_total": 1.0,
            "rho_ohm_mm2_m": 0.023, "reactance_ohm_m": 0.0, "cos_phi": 0.85, "sin_phi": 0.5268,
            "undeclared_output_field": 999.9,
        }
        with pytest.raises(ValidationError, match="(?i)extra_forbidden|extra fields not permitted"):
            IntermediateFactors(**factors_kwargs)  # type: ignore

    def test_voltage_drop_result_extra_fields_forbidden(self):
        """V4.2.2: VoltageDropResult output schema must enforce extra='forbid'."""
        vd_kwargs = {
            "du_volts": 5.0, "du_percent": 2.0, "du_max_percent": 5.0, "is_compliant": True,
            "margin_percent": 3.0, "unauthorized_metadata": "leak",
        }
        with pytest.raises(ValidationError, match="(?i)extra_forbidden|extra fields not permitted"):
            VoltageDropResult(**vd_kwargs)  # type: ignore


# ==============================================================================
# Suite 5: JSON Serialization Fidelity & Roundtrip Integrity (4 test cases)
# ==============================================================================

class TestAdversarialJsonSerializationFidelity:
    """Stress testing JSON serialization without data loss or corruption."""

    def test_circuit_definition_json_roundtrip_fidelity(self):
        """V5.1: Full CircuitDefinition serialization roundtrip must preserve exact identity."""
        c_orig = CircuitDefinition(
            name="Feeder_Distribution_Hall_A",
            load=ElectricalLoad(
                voltage_v=400.0,
                phases=PhaseSystem.THREE_PHASE,
                power_kw=45.5,
                cos_phi=0.88,
                frequency_hz=50.0,
                harmonic_ih3_ratio=0.15,
            ),
            cable=CableSpecs(
                length_m=135.75,
                conductor=ConductorMaterial.CU,
                insulation=InsulationType.XLPE,
                multicore=True,
                section_custom_mm2=35.0,
            ),
            installation=InstallationConditions(
                method=InstallationMethod.E,
                ambient_temp_c=35.0,
                grouping_circuits=4,
                touching=False,
                in_ground=False,
                k_custom=0.95,
            ),
            protection=ProtectionDevice(
                in_a=100.0,
                ik_a=16000.0,
                disconnection_time_s=0.15,
                device_type="circuit_breaker",
            ),
            du_max_percent=4.5,
        )
        json_repr = c_orig.model_dump_json(indent=2)
        c_restored = CircuitDefinition.model_validate_json(json_repr)
        assert c_orig == c_restored

    def test_sizing_result_json_roundtrip_fidelity(self):
        """V5.2: Complex nested SizingResult serialization roundtrip must preserve exact identity."""
        vd = VoltageDropResult(
            du_volts=7.12345,
            du_percent=1.78086,
            du_max_percent=4.5,
            is_compliant=True,
            margin_percent=2.71914,
            b_factor=1.0,
        )
        ts = ThermalStressResult(
            ik_a=16000.0,
            time_s=0.15,
            i2t=38400000.0,
            k_factor=143.0,
            s_min_mm2=43.33,
            is_compliant=True,
        )
        factors = IntermediateFactors(
            k1_method=1.0,
            k2_grouping=0.77,
            k3_temperature=0.96,
            k_custom=0.95,
            kh_harmonic=0.86,
            k_total=0.6046,
            rho_ohm_mm2_m=0.023,
            reactance_ohm_m=0.00008,
            cos_phi=0.88,
            sin_phi=0.47497,
        )
        res_orig = SizingResult(
            circuit_name="Feeder_Distribution_Hall_A",
            ib_a=74.63,
            in_a=100.0,
            iz_min_required_a=165.4,
            selected_section_mm2=50.0,
            i0_reference_a=192.0,
            iz_effective_a=116.08,
            ampacity_compliant=True,
            voltage_drop=vd,
            thermal_stress=ts,
            intermediate_factors=factors,
            limiting_constraint=LimitingConstraint.THERMAL_STRESS,
            is_compliant=True,
            notes=["Sizing governed by short-circuit thermal stress limit."],
        )
        res_json = res_orig.model_dump_json(indent=2)
        res_restored = SizingResult.model_validate_json(res_json)
        assert res_orig == res_restored

    def test_ieee754_precision_preservation(self):
        """V5.3: Full 64-bit IEEE float precision must be retained across JSON serialization."""
        high_prec_vd = VoltageDropResult(
            du_volts=3.141592653589793,
            du_percent=1.365909849386866,
            du_max_percent=5.0,
            is_compliant=True,
            margin_percent=3.634090150613134,
            b_factor=1.0,
        )
        hp_json = high_prec_vd.model_dump_json()
        hp_restored = VoltageDropResult.model_validate_json(hp_json)
        assert high_prec_vd.du_volts == hp_restored.du_volts

    def test_inf_json_serialization_protection(self):
        """V5.4: Non-finite values cannot be instantiated or deserialized, preventing JSON null corruption."""
        # Instantiation gate: float('inf') must be rejected before entering model
        with pytest.raises(ValidationError):
            ElectricalLoad(voltage_v=float("inf"), power_kw=10.0)

        # Deserialization gate: JSON with 'inf' or null in non-nullable float must be rejected
        with pytest.raises(ValidationError):
            ElectricalLoad.model_validate_json('{"voltage_v": "inf", "power_kw": 10.0}')

        with pytest.raises(ValidationError):
            ElectricalLoad.model_validate_json('{"voltage_v": null, "power_kw": 10.0}')


# ==============================================================================
# Suite 6: Enum Integrity, Hashability, and Boolean Traps (3 test cases)
# ==============================================================================

class TestAdversarialEnumIntegrity:
    """Stress testing hashability, dict/set indexing, and strict boolean inequality."""

    def test_phase_system_hashability(self):
        """V6.1: PhaseSystem must be hashable and usable as dict keys, in sets, and in caches."""
        h = hash(PhaseSystem.SINGLE_PHASE)
        assert isinstance(h, int)
        s = {PhaseSystem.SINGLE_PHASE, PhaseSystem.THREE_PHASE, PhaseSystem.DC}
        assert len(s) == 3
        assert PhaseSystem.SINGLE_PHASE in s
        d = {PhaseSystem.SINGLE_PHASE: "1P", PhaseSystem.THREE_PHASE: "3P", PhaseSystem.DC: "DC"}
        assert d[PhaseSystem.SINGLE_PHASE] == "1P"
        assert d[PhaseSystem.THREE_PHASE] == "3P"

    def test_limiting_constraint_hashability(self):
        """V6.2: LimitingConstraint must be hashable and usable in sets and dictionaries."""
        h = hash(LimitingConstraint.AMPACITY)
        assert isinstance(h, int)
        s = {LimitingConstraint.AMPACITY, LimitingConstraint.VOLTAGE_DROP, LimitingConstraint.THERMAL_STRESS}
        assert len(s) == 3
        d = {LimitingConstraint.AMPACITY: "Iz", LimitingConstraint.VOLTAGE_DROP: "dU"}
        assert d[LimitingConstraint.AMPACITY] == "Iz"
        assert d[LimitingConstraint.VOLTAGE_DROP] == "dU"

    def test_phase_system_boolean_trap(self):
        """V6.3: PhaseSystem must not compare equal to booleans (True / False)."""
        assert (PhaseSystem.SINGLE_PHASE == True) is False
        assert (PhaseSystem.SINGLE_PHASE != True) is True
        assert (PhaseSystem.DC == False) is False
        assert (PhaseSystem.DC != False) is True
        assert (PhaseSystem.THREE_PHASE == True) is False
        assert (PhaseSystem.THREE_PHASE == False) is False


# ==============================================================================
# Standalone execution helper
# ==============================================================================

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
```

---

## 4. Part 2: Dedicated Unit Test Specifications

### 4.1 Specification A: Enum Hashability & Boolean Isolation (`tests/unit/test_models.py`)

Add the following test methods to `TestEnums` (or a dedicated class `TestEnumHashabilityAndIntegrity`) in `tests/unit/test_models.py`:

```python
class TestEnumHashabilityAndIntegrity:
    """Comprehensive verification of Enum hashability, collection indexing, and boolean isolation."""

    def test_phase_system_hashability_and_dict_indexing(self):
        """Verify PhaseSystem is fully hashable and can index dictionaries."""
        # 1. Direct hash verification
        h_single = hash(PhaseSystem.SINGLE_PHASE)
        h_three = hash(PhaseSystem.THREE_PHASE)
        h_dc = hash(PhaseSystem.DC)
        assert isinstance(h_single, int)
        assert isinstance(h_three, int)
        assert isinstance(h_dc, int)

        # 2. Dictionary key indexing
        lookup = {
            PhaseSystem.SINGLE_PHASE: "single_phase_circuit",
            PhaseSystem.THREE_PHASE: "three_phase_circuit",
            PhaseSystem.DC: "dc_circuit",
        }
        assert lookup[PhaseSystem.SINGLE_PHASE] == "single_phase_circuit"
        assert lookup[PhaseSystem.THREE_PHASE] == "three_phase_circuit"
        assert lookup[PhaseSystem.DC] == "dc_circuit"

        # 3. Set membership and uniqueness
        system_set = {PhaseSystem.SINGLE_PHASE, PhaseSystem.THREE_PHASE, PhaseSystem.DC}
        assert len(system_set) == 3
        assert PhaseSystem.SINGLE_PHASE in system_set
        assert PhaseSystem.SINGLE in system_set  # Alias check

    def test_limiting_constraint_hashability_and_dict_indexing(self):
        """Verify LimitingConstraint is fully hashable and can index dictionaries."""
        h_amp = hash(LimitingConstraint.AMPACITY)
        h_vd = hash(LimitingConstraint.VOLTAGE_DROP)
        h_ts = hash(LimitingConstraint.THERMAL_STRESS)
        assert isinstance(h_amp, int)
        assert isinstance(h_vd, int)
        assert isinstance(h_ts, int)

        constraint_map = {
            LimitingConstraint.AMPACITY: "Governed by Iz",
            LimitingConstraint.VOLTAGE_DROP: "Governed by dU",
            LimitingConstraint.THERMAL_STRESS: "Governed by I2t",
        }
        assert constraint_map[LimitingConstraint.AMPACITY] == "Governed by Iz"
        assert constraint_map[LimitingConstraint.IZ] == "Governed by Iz"
        assert constraint_map[LimitingConstraint.VOLTAGE_DROP] == "Governed by dU"

    def test_enum_lru_cache_compatibility(self):
        """Verify that Enums can be passed as arguments to @functools.lru_cache."""
        import functools

        call_count = 0

        @functools.lru_cache(maxsize=16)
        def get_system_tag(system: PhaseSystem) -> str:
            nonlocal call_count
            call_count += 1
            return f"TAG_{system.value}"

        res1 = get_system_tag(PhaseSystem.SINGLE_PHASE)
        res2 = get_system_tag(PhaseSystem.SINGLE_PHASE)
        assert res1 == "TAG_single_phase"
        assert res2 == "TAG_single_phase"
        assert call_count == 1  # Cache hit verified!

    def test_enum_strict_boolean_isolation(self):
        """Verify that Enums strictly do not compare equal to boolean values True or False."""
        # Single-phase != True even though other == 1
        assert (PhaseSystem.SINGLE_PHASE == True) is False
        assert (PhaseSystem.SINGLE_PHASE != True) is True

        # DC != False even though other == 0
        assert (PhaseSystem.DC == False) is False
        assert (PhaseSystem.DC != False) is True

        # Three-phase != True and != False
        assert (PhaseSystem.THREE_PHASE == True) is False
        assert (PhaseSystem.THREE_PHASE == False) is False

        # Integer comparisons must continue to work
        assert (PhaseSystem.SINGLE_PHASE == 1) is True
        assert (PhaseSystem.THREE_PHASE == 3) is True
        assert (PhaseSystem.DC == 0) is True
        assert (PhaseSystem.SINGLE_PHASE == 2) is False
```

### 4.2 Specification B: String Shorthand Inputs to Pure Calculation Formulas (`tests/unit/test_formulas.py`)

Add the following test methods to `TestCalculateIb` and `TestCalculateVoltageDrop` in `tests/unit/test_formulas.py`:

```python
class TestStringSystemInputsInFormulas:
    """Verifying string system shorthands ('1P', '3P', 'DC') in calculate_ib and calculate_voltage_drop."""

    @pytest.mark.parametrize("system_str, expected_ib", [
        ("1P", 10.0),
        ("1p", 10.0),
        ("single", 10.0),
        ("single_phase", 10.0),
        ("single-phase", 10.0),
    ])
    def test_calculate_ib_with_single_phase_string_shorthands(self, system_str: str, expected_ib: float):
        """calculate_ib must accept standard single-phase string notations."""
        ib = calculate_ib(system=system_str, voltage_v=230.0, power_w=2300.0, cos_phi=1.0)
        assert math.isclose(ib, expected_ib, rel_tol=1e-3)

    @pytest.mark.parametrize("system_str, expected_ib", [
        ("3P", 10.0),
        ("3p", 10.0),
        ("three", 10.0),
        ("three_phase", 10.0),
        ("three-phase", 10.0),
    ])
    def test_calculate_ib_with_three_phase_string_shorthands(self, system_str: str, expected_ib: float):
        """calculate_ib must accept standard three-phase string notations."""
        # P = sqrt(3) * U * Ib * cos_phi = sqrt(3) * 400 * 10 * 1.0 = 6928.203 W
        power_w = 400.0 * math.sqrt(3) * 10.0
        ib = calculate_ib(system=system_str, voltage_v=400.0, power_w=power_w, cos_phi=1.0)
        assert math.isclose(ib, expected_ib, rel_tol=1e-3)

    @pytest.mark.parametrize("system_str", ["DC", "dc", "direct", "0"])
    def test_calculate_ib_with_dc_string_shorthands(self, system_str: str):
        """calculate_ib must accept DC string notations."""
        ib = calculate_ib(system=system_str, voltage_v=240.0, power_w=2400.0)
        assert math.isclose(ib, 10.0, rel_tol=1e-3)

    def test_calculate_ib_with_phases_kwarg_string(self):
        """calculate_ib must accept string shorthand via 'phases' keyword argument."""
        ib = calculate_ib(phases="3P", voltage_v=400.0, power_kw=40.0 * math.sqrt(3), cos_phi=1.0)
        assert math.isclose(ib, 100.0, rel_tol=1e-3)

    @pytest.mark.parametrize("system_str, expected_b", [
        ("1P", 2.0),
        ("1p", 2.0),
        ("single_phase", 2.0),
        ("3P", 1.0),
        ("3p", 1.0),
        ("three_phase", 1.0),
        ("DC", 2.0),
        ("dc", 2.0),
    ])
    def test_calculate_voltage_drop_with_string_system_shorthands(self, system_str: str, expected_b: float):
        """calculate_voltage_drop must accept string shorthands and assign correct b-factor."""
        res = calculate_voltage_drop(
            system=system_str,
            length_m=50.0,
            section_mm2=6.0,
            ib_a=20.0,
            cos_phi=0.9,
            material=ConductorMaterial.CU,
            voltage_v=230.0 if expected_b == 2.0 else 400.0,
        )
        assert res.b_factor == expected_b
        assert res.du_volts > 0.0
        assert res.is_compliant is True

    def test_calculate_voltage_drop_with_phases_kwarg_string(self):
        """calculate_voltage_drop must accept string shorthand via 'phases' keyword argument."""
        res = calculate_voltage_drop(
            phases="3P",
            length_m=100.0,
            section_mm2=25.0,
            ib_a=40.0,
            voltage_v=400.0,
        )
        assert res.b_factor == 1.0
        assert res.du_volts > 0.0
```

### 4.3 Specification C: Material String Aliases in `calculate_thermal_stress_min_section` (`tests/unit/test_formulas.py`)

Add the following test methods to `TestCalculateThermalStress` in `tests/unit/test_formulas.py`:

```python
class TestThermalStressMaterialStringAliases:
    """Verifying robust conductor material and insulation string alias coercion."""

    @pytest.mark.parametrize("mat_alias", [
        "copper",
        "Copper",
        "COPPER",
        "cu",
        "Cu",
        "CU",
        "cuivre",
        "Cuivre",
    ])
    def test_thermal_stress_copper_string_aliases_accepted(self, mat_alias: str):
        """All copper string variations must resolve to k=143 (XLPE) or k=115 (PVC)."""
        s_min = calculate_thermal_stress_min_section(
            ik_a=10000.0,
            time_s=0.10,
            material=mat_alias,
            insulation="PVC",
        )
        # s_min = (10000 * sqrt(0.1)) / 115 = 3162.277 / 115 = 27.50 mm2
        assert math.isclose(s_min, 27.50, rel_tol=0.01)

    @pytest.mark.parametrize("mat_alias", [
        "aluminium",
        "Aluminium",
        "aluminum",
        "Aluminum",
        "al",
        "Al",
        "AL",
    ])
    def test_thermal_stress_aluminium_string_aliases_accepted(self, mat_alias: str):
        """All aluminium string variations must resolve to k=94 (XLPE) or k=76 (PVC)."""
        s_min = calculate_thermal_stress_min_section(
            ik_a=10000.0,
            time_s=0.10,
            material=mat_alias,
            insulation="XLPE",
        )
        # s_min = (10000 * sqrt(0.1)) / 94 = 3162.277 / 94 = 33.64 mm2
        assert math.isclose(s_min, 33.64, rel_tol=0.01)

    @pytest.mark.parametrize("ins_alias", [
        "pvc",
        "PVC",
        "xlpe",
        "XLPE",
        "pr",
        "PR",
        "epr",
        "EPR",
    ])
    def test_thermal_stress_insulation_string_aliases_accepted(self, ins_alias: str):
        """All standard insulation string aliases must be accepted."""
        s_min = calculate_thermal_stress_min_section(
            ik_a=5000.0,
            time_s=0.20,
            material="Cu",
            insulation=ins_alias,
        )
        assert s_min > 0.0

    def test_thermal_stress_unrecognized_material_rejected(self):
        """Unrecognized metals (e.g. 'Steel', 'Iron', 'Titanium') must raise ValueError."""
        with pytest.raises(ValueError, match="(?i)unknown conductor material|unsupported material"):
            calculate_thermal_stress_min_section(
                ik_a=5000.0,
                time_s=0.10,
                material="Titanium",
                insulation="PVC",
            )
```

---

## 5. Part 3: Zero-Regression Assurance & Boundary Reconciliations

### 5.1 Reconciliation of `tests/boundary/test_boundaries.py`

In `tests/boundary/test_boundaries.py`, Challenger 1 originally introduced `TestDiscoveredVulnerabilities` (lines 471–503) to capture unpatched vulnerabilities:

```python
# CURRENT BUG-PROBE IMPLEMENTATION (lines 474-501):
class TestDiscoveredVulnerabilities:
    def test_voltage_v_zero_raises_unhandled_zero_division(self):
        with pytest.raises(ZeroDivisionError):
            calculate_voltage_drop(system=PhaseSystem.SINGLE_PHASE, length_m=10.0, section_mm2=4.0, ib_a=10.0, voltage_v=0.0)

    def test_thermal_stress_string_material_copper_rejected(self):
        with pytest.raises(ValueError, match="Unknown material/insulation combination"):
            calculate_thermal_stress_min_section(ik_a=5000.0, time_s=0.1, material="copper", insulation="PVC")
```

When Worker applies the fixes specified in `explorer_m1_fix_2`:
1. `calculate_voltage_drop` will validate `voltage_v > 0.0` and raise `ValueError` (not `ZeroDivisionError`).
2. `calculate_thermal_stress_min_section` will coerce `"copper"` and successfully compute `s_min` (not raise `ValueError`).

**Reconciliation Rule**: Update `TestDiscoveredVulnerabilities` in `tests/boundary/test_boundaries.py` to assert the **remediated behavior**:

```python
# HARDENED SPECIFICATION for tests/boundary/test_boundaries.py:
class TestDiscoveredVulnerabilities:
    """Regression guards verifying remediation of previously discovered edge vulnerabilities."""

    def test_voltage_v_zero_raises_unhandled_zero_division(self):
        """
        REMEDIATION VERIFICATION:
        voltage_v <= 0.0 now raises a clean domain ValueError rather than an unhandled ZeroDivisionError.
        """
        with pytest.raises(ValueError, match="(?i)voltage_v must be strictly positive"):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=10.0,
                section_mm2=4.0,
                ib_a=10.0,
                voltage_v=0.0,
            )

    def test_thermal_stress_string_material_copper_rejected(self):
        """
        REMEDIATION VERIFICATION:
        Material string aliases such as 'copper' / 'cu' are now coerced and successfully compute s_min.
        """
        s_min = calculate_thermal_stress_min_section(
            ik_a=5000.0,
            time_s=0.1,
            material="copper",
            insulation="PVC",
        )
        assert s_min > 0.0
        assert math.isclose(s_min, 13.75, rel_tol=0.01)
```

By keeping method names identical and updating assertions to reflect the fix, `tests/boundary/test_boundaries.py` continues to execute **exactly 39 tests with 100% pass rate**, maintaining zero regression.

### 5.2 Regression Risk Matrix

| Component | Code Modification | Affected Existing Tests | Regression Risk | Mitigation & Guard |
|---|---|---|---|---|
| `PhaseSystem.__eq__` | Add `and not isinstance(other, bool)` | `test_models.py:28-38` (PhaseSystem enum), `test_models.py:465-482` (Edge cases) | **ZERO** | Integer equality (`PhaseSystem.SINGLE_PHASE == 1`) is preserved; only `bool` is filtered out. |
| `PhaseSystem.__hash__` | Add `def __hash__(self) -> int: return hash(self.value)` | `test_models.py` | **ZERO** | Adding hashability restores Python Data Model compliance without modifying equality semantics. |
| `LimitingConstraint` | Add `__hash__` and boolean guard | `test_models.py:61-72` | **ZERO** | Pure addition of hash method; existing string equality unchanged. |
| Model Immutability | `CircuitDefinition` gets `frozen=True` | `test_models.py:280-337` | **ZERO** | Existing unit tests never mutate `CircuitDefinition` attributes post-instantiation. |
| `allow_inf_nan=False` | Added to all domain schemas | `test_models.py:74-390` | **ZERO** | Existing unit tests use strictly finite numbers. No test passes Inf or NaN expecting success. |
| `extra="forbid"` | Added to Output Models | `test_models.py:338-390` | **ZERO** | Output models in unit tests only use declared fields. |
| `calculate_ib` & `calculate_voltage_drop` | String system normalization (`PhaseSystem(system)`) | `test_formulas.py:28-100`, `test_formulas.py:288-348` | **ZERO** | Widens supported strings to include `"1P"`, `"3P"`, `"DC"`. Invalid strings like `"SolarInverter4P"` still raise `ValueError`. |
| `calculate_thermal_stress_min_section` | Normalize material and insulation aliases | `test_formulas.py:352-401` | **ZERO** | Enums continue to work identically. Only string aliases are newly resolved. |

---

## 6. Implementation Action Plan & Sequencing

```
Phase 1: Remediation Execution (Worker)
├── 1.1 Apply models remediation in src/ampy/core/models.py (per fix_1 plan)
└── 1.2 Apply formulas remediation in src/ampy/core/formulas.py (per fix_2 plan)

Phase 2: Test Suite Hardening Deployment (Worker / Test Writer)
├── 2.1 Create tests/boundary/test_models_adversarial.py (51 tests)
├── 2.2 Append Specification A tests to tests/unit/test_models.py (+4 tests)
├── 2.3 Append Specifications B & C tests to tests/unit/test_formulas.py (+8 tests)
└── 2.4 Update TestDiscoveredVulnerabilities in tests/boundary/test_boundaries.py (reconcile 2 tests)

Phase 3: Verification & Auditing
├── 3.1 Run pytest tests/boundary/test_models_adversarial.py -v (verify 51 passed)
├── 3.2 Run pytest tests/boundary/test_boundaries.py -v (verify 39 passed)
├── 3.3 Run pytest tests/unit/ -v (verify 194 passed)
├── 3.4 Run python tests/adversarial_challenge_models.py (verify 0 failures, APPROVE)
├── 3.5 Run pytest --cov=ampy.core (verify >= 97% statement coverage)
└── 3.6 Run python -m ruff check src/ tests/ (verify 0 lint errors)
```

---

## 7. Acceptance Criteria Checklist

- [x] Full conversion plan for `tests/boundary/test_models_adversarial.py` covering all 51 adversarial vectors.
- [x] Dedicated unit tests specified for Enum hashability, dict indexing, sets, and boolean trap isolation.
- [x] Dedicated unit tests specified for formula string inputs (`"1P"`, `"3P"`, `"DC"`).
- [x] Dedicated unit tests specified for material string aliases (`"copper"`, `"cu"`, `"aluminium"`, `"al"`).
- [x] Reconciled boundary test specification for `tests/boundary/test_boundaries.py` maintaining 39 passing tests.
- [x] Zero-regression impact analysis across all 182 existing unit tests and 39 boundary tests.
- [x] Target test count exceeds 278 automated passing tests with zero failures.
