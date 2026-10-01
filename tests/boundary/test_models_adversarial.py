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
