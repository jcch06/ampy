"""
Unit tests for domain models and data schemas (ampy.core.models).
Conforms to NF C 15-100 and UTE C 15-105.
"""

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


class TestEnums:
    def test_phase_system_enum(self):
        assert PhaseSystem.SINGLE_PHASE in (1, "1P", "SINGLE_PHASE")
        assert PhaseSystem.THREE_PHASE in (3, "3P", "THREE_PHASE")
        assert hasattr(PhaseSystem, "DC")
        assert PhaseSystem.SINGLE == PhaseSystem.SINGLE_PHASE
        assert PhaseSystem.THREE == PhaseSystem.THREE_PHASE
        # Missing coercion
        assert PhaseSystem("1p") == PhaseSystem.SINGLE_PHASE
        assert PhaseSystem("3p") == PhaseSystem.THREE_PHASE
        assert PhaseSystem("dc") == PhaseSystem.DC

    def test_conductor_material_enum(self):
        assert ConductorMaterial.CU.value == "Cu"
        assert ConductorMaterial.AL.value == "Al"
        # Missing coercion
        assert ConductorMaterial("copper") == ConductorMaterial.CU
        assert ConductorMaterial("aluminum") == ConductorMaterial.AL

    def test_insulation_type_enum(self):
        assert InsulationType.PVC.value == "PVC"
        assert InsulationType.XLPE.value == "XLPE"
        # Missing coercion
        assert InsulationType("pvc") == InsulationType.PVC
        assert InsulationType("pr") == InsulationType.XLPE
        assert InsulationType("epr") == InsulationType.XLPE

    def test_installation_method_enum(self):
        values = {m.value for m in InstallationMethod}
        assert {"B", "C", "E", "F"}.issubset(values)
        # Missing coercion
        assert InstallationMethod("b1") == InstallationMethod.B
        assert InstallationMethod("b2") == InstallationMethod.B

    def test_limiting_constraint_enum(self):
        values = {c.value for c in LimitingConstraint}
        assert any(v in ("Iz", "ampacity") for v in values)
        assert any(v in ("dU", "voltage_drop") for v in values)
        assert "thermal_stress" in values
        assert LimitingConstraint.IZ == LimitingConstraint.AMPACITY
        assert LimitingConstraint.DU == LimitingConstraint.VOLTAGE_DROP
        # Missing coercion
        assert LimitingConstraint("iz") == LimitingConstraint.AMPACITY
        assert LimitingConstraint("du") == LimitingConstraint.VOLTAGE_DROP
        assert LimitingConstraint("i2t") == LimitingConstraint.THERMAL_STRESS


class TestElectricalLoadValidation:
    @pytest.mark.parametrize("load_data", [
        {"voltage_v": 230.0, "phases": PhaseSystem.SINGLE_PHASE, "power_kw": 3.68, "cos_phi": 1.0},
        {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "power_kw": 18.5, "cos_phi": 0.85},
        {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "apparent_power_kva": 25.0},
        {"voltage_v": 230.0, "phases": PhaseSystem.SINGLE_PHASE, "apparent_power_kva": 6.0},
        {"voltage_v": 400.0, "phases": PhaseSystem.THREE_PHASE, "current_a": 45.0},
        {"voltage_v": 240.0, "phases": PhaseSystem.DC, "power_kw": 12.0},
        {"voltage_v": 48.0, "phases": PhaseSystem.DC, "current_a": 50.0},
    ])
    def test_valid_load_instantiations(self, load_data):
        load = ElectricalLoad(**load_data)
        assert load.voltage_v == load_data["voltage_v"]
        assert load.phases == load_data["phases"]

    def test_valid_load_with_active_power_kw_alias(self):
        load = ElectricalLoad(voltage_v=400.0, active_power_kw=15.0, cos_phi=0.85)
        assert load.power_kw == 15.0
        assert load.active_power_kw == 15.0

    def test_valid_load_defaults(self):
        load = ElectricalLoad(voltage_v=400.0, power_kw=10.0)
        assert load.cos_phi == 0.85
        assert load.frequency_hz == 50.0
        assert load.harmonic_ih3_ratio == 0.0

    def test_invalid_load_missing_all_inputs(self):
        with pytest.raises(ValidationError, match="(?i)at least one|power_kw|current_a"):
            ElectricalLoad(voltage_v=230.0)

    @pytest.mark.parametrize("conflicting_data", [
        {"voltage_v": 400.0, "power_kw": 10.0, "apparent_power_kva": 12.0},
        {"voltage_v": 400.0, "power_kw": 10.0, "current_a": 20.0},
        {"voltage_v": 400.0, "apparent_power_kva": 12.0, "current_a": 20.0},
        {"voltage_v": 400.0, "power_kw": 10.0, "apparent_power_kva": 12.0, "current_a": 20.0},
    ])
    def test_invalid_load_conflicting_multiple_inputs(self, conflicting_data):
        with pytest.raises(ValidationError, match="(?i)only one|ambiguity|mutually exclusive"):
            ElectricalLoad(**conflicting_data)

    @pytest.mark.parametrize("invalid_kwarg", [
        {"power_kw": -5.0},
        {"power_kw": 0.0},
        {"apparent_power_kva": -10.0},
        {"apparent_power_kva": 0.0},
        {"current_a": -2.0},
        {"current_a": 0.0},
        {"voltage_v": -230.0},
        {"voltage_v": 0.0},
        {"cos_phi": 1.05},
        {"cos_phi": 0.0},
        {"cos_phi": -0.5},
        {"frequency_hz": -50.0},
        {"frequency_hz": 0.0},
        {"harmonic_ih3_ratio": -0.1},
        {"harmonic_ih3_ratio": 1.2},
    ])
    def test_invalid_load_numeric_bounds(self, invalid_kwarg):
        base = {"voltage_v": 230.0, "power_kw": 5.0}
        base.update(invalid_kwarg)
        with pytest.raises(ValidationError):
            ElectricalLoad(**base)

    def test_load_immutability_and_extra_fields(self):
        load = ElectricalLoad(voltage_v=230.0, power_kw=3.68)
        with pytest.raises((ValidationError, TypeError)):
            load.voltage_v = 400.0

        with pytest.raises(ValidationError, match="extra_forbidden"):
            ElectricalLoad(voltage_v=230.0, power_kw=3.68, unknown_param=999)


class TestCableSpecsValidation:
    def test_valid_cable_specs(self):
        cable = CableSpecs(
            length_m=45.0,
            conductor=ConductorMaterial.CU,
            insulation=InsulationType.XLPE,
            multicore=True,
        )
        assert cable.length_m == 45.0
        assert cable.conductor == ConductorMaterial.CU
        assert cable.insulation == InsulationType.XLPE
        assert cable.multicore is True

    def test_valid_cable_specs_aliases(self):
        cable = CableSpecs(
            length_m=30.0,
            conductor_material=ConductorMaterial.AL,
            insulation_type=InsulationType.PVC,
        )
        assert cable.conductor == ConductorMaterial.AL
        assert cable.conductor_material == ConductorMaterial.AL
        assert cable.insulation == InsulationType.PVC
        assert cable.insulation_type == InsulationType.PVC

    @pytest.mark.parametrize("invalid_length", [0.0, -10.0, -0.001])
    def test_invalid_cable_length_zero_or_negative(self, invalid_length):
        with pytest.raises(ValidationError):
            CableSpecs(length_m=invalid_length)

    def test_invalid_cable_material_unrecognized(self):
        with pytest.raises(ValidationError):
            CableSpecs(length_m=50.0, conductor="Iron")

    def test_cable_specs_immutability_and_extra_fields(self):
        cable = CableSpecs(length_m=20.0)
        with pytest.raises((ValidationError, TypeError)):
            cable.length_m = 50.0

        with pytest.raises(ValidationError, match="extra_forbidden"):
            CableSpecs(length_m=20.0, extra_prop=123)


class TestInstallationConditionsValidation:
    def test_valid_installation_defaults(self):
        inst = InstallationConditions()
        assert inst.method == InstallationMethod.C
        assert inst.ambient_temp_c == 30.0
        assert inst.grouping_circuits == 1
        assert inst.touching is True
        assert inst.in_ground is False
        assert inst.k_custom == 1.0

    def test_valid_installation_custom_values(self):
        inst = InstallationConditions(
            method=InstallationMethod.E,
            ambient_temp_c=45.0,
            grouping_circuits=4,
            touching=False,
            in_ground=True,
            k_custom=0.9,
        )
        assert inst.method == InstallationMethod.E
        assert inst.ambient_temp_c == 45.0
        assert inst.grouping_circuits == 4
        assert inst.touching is False
        assert inst.in_ground is True
        assert inst.k_custom == 0.9

    @pytest.mark.parametrize("invalid_kwargs", [
        {"grouping_circuits": 0},
        {"grouping_circuits": -1},
        {"grouping_circuits": 41},
        {"ambient_temp_c": 85.0},
        {"ambient_temp_c": -35.0},
        {"k_custom": 0.0},
        {"k_custom": -0.5},
        {"k_custom": 2.5},
    ])
    def test_invalid_installation_bounds(self, invalid_kwargs):
        with pytest.raises(ValidationError):
            InstallationConditions(**invalid_kwargs)

    def test_installation_immutability_and_extra_fields(self):
        inst = InstallationConditions()
        with pytest.raises((ValidationError, TypeError)):
            inst.ambient_temp_c = 40.0

        with pytest.raises(ValidationError, match="extra_forbidden"):
            InstallationConditions(invalid_arg=True)


class TestProtectionDeviceValidation:
    def test_valid_protection_defaults(self):
        prot = ProtectionDevice()
        assert prot.in_a is None
        assert prot.ik_a is None
        assert prot.disconnection_time_s is None
        assert prot.device_type == "circuit_breaker"

    def test_valid_protection_explicit_values(self):
        prot = ProtectionDevice(
            in_a=32.0,
            ik_a=10000.0,
            disconnection_time_s=0.1,
            device_type="fuse_gG",
        )
        assert prot.in_a == 32.0
        assert prot.ik_a == 10000.0
        assert prot.disconnection_time_s == 0.1
        assert prot.device_type == "fuse_gG"

    @pytest.mark.parametrize("invalid_kwargs", [
        {"in_a": 0.0},
        {"in_a": -32.0},
        {"ik_a": 0.0},
        {"ik_a": -5000.0},
        {"disconnection_time_s": 0.0},
        {"disconnection_time_s": -0.1},
        {"disconnection_time_s": 5.5},
        {"disconnection_time_s": 15.0},
    ])
    def test_invalid_protection_bounds(self, invalid_kwargs):
        with pytest.raises(ValidationError):
            ProtectionDevice(**invalid_kwargs)

    def test_protection_immutability_and_extra_fields(self):
        prot = ProtectionDevice(in_a=16.0)
        with pytest.raises((ValidationError, TypeError)):
            prot.in_a = 32.0

        with pytest.raises(ValidationError, match="extra_forbidden"):
            ProtectionDevice(bogus=123)


class TestCircuitDefinitionValidation:
    def test_valid_circuit_definition_composition(self):
        circuit = CircuitDefinition(
            name="Feeder_1",
            load=ElectricalLoad(voltage_v=400.0, power_kw=37.0, cos_phi=0.85, phases=PhaseSystem.THREE_PHASE),
            cable=CableSpecs(length_m=220.0, conductor=ConductorMaterial.CU, insulation=InsulationType.XLPE),
            installation=InstallationConditions(method=InstallationMethod.C, ambient_temp_c=30.0),
            protection=ProtectionDevice(in_a=63.0),
            du_max_percent=5.0,
        )
        assert circuit.name == "Feeder_1"
        assert circuit.load.power_kw == 37.0
        assert circuit.cable.length_m == 220.0
        assert circuit.du_max_percent == 5.0
        assert circuit.max_voltage_drop_pct == 5.0

    def test_valid_circuit_definition_alias(self):
        circuit = CircuitDefinition(
            load=ElectricalLoad(voltage_v=230.0, power_kw=3.68),
            cable=CableSpecs(length_m=35.0),
            max_voltage_drop_pct=3.0,
        )
        assert circuit.du_max_percent == 3.0
        assert circuit.max_voltage_drop_pct == 3.0

    @pytest.mark.parametrize("invalid_du", [0.0, -1.0, 25.0])
    def test_invalid_du_max_percent_negative_zero_or_excessive(self, invalid_du):
        with pytest.raises(ValidationError):
            CircuitDefinition(
                load=ElectricalLoad(voltage_v=230.0, power_kw=3.0),
                cable=CableSpecs(length_m=10.0),
                du_max_percent=invalid_du,
            )

    def test_ambient_temperature_exceeding_pvc_insulation_rating(self):
        with pytest.raises(ValidationError, match="(?i)reaches or exceeds maximum operating temperature of PVC"):
            CircuitDefinition(
                load=ElectricalLoad(voltage_v=230.0, power_kw=3.0),
                cable=CableSpecs(length_m=10.0, insulation=InsulationType.PVC),
                installation=InstallationConditions(ambient_temp_c=70.0),
            )

    def test_ambient_temperature_exceeding_xlpe_insulation_rating(self):
        with pytest.raises(ValidationError, match="(?i)reaches or exceeds maximum operating temperature of XLPE|less than or equal to 80"):
            CircuitDefinition(
                load=ElectricalLoad(voltage_v=400.0, power_kw=10.0),
                cable=CableSpecs(length_m=10.0, insulation=InsulationType.XLPE),
                installation=InstallationConditions(ambient_temp_c=90.0),
            )

    def test_circuit_nested_validation_propagation(self):
        with pytest.raises(ValidationError):
            CircuitDefinition(
                load=ElectricalLoad(voltage_v=400.0, power_kw=-10.0),
                cable=CableSpecs(length_m=10.0),
            )


class TestOutputModelsValidation:
    def test_voltage_drop_result_immutability_and_margin(self):
        vd = VoltageDropResult(
            du_volts=6.44,
            du_percent=2.80,
            du_max_percent=3.00,
            is_compliant=True,
            margin_percent=0.20,
            b_factor=2.0,
        )
        assert vd.du_volts == 6.44
        assert vd.delta_u_v == 6.44
        assert vd.voltage_drop_v == 6.44
        assert vd.du_percent == 2.80
        assert vd.delta_u_pct == 2.80
        assert vd.voltage_drop_pct == 2.80
        assert vd.is_compliant is True
        assert vd.margin_percent == 0.20
        with pytest.raises((ValidationError, TypeError)):
            vd.du_volts = 10.0

    def test_thermal_stress_result_immutability(self):
        ts = ThermalStressResult(
            ik_a=10000.0,
            time_s=0.1,
            i2t=10000000.0,
            k_factor=143.0,
            s_min_mm2=22.11,
            is_compliant=True,
        )
        assert ts.ik_a == 10000.0
        assert ts.s_min_mm2 == 22.11
        with pytest.raises((ValidationError, TypeError)):
            ts.ik_a = 5000.0

    def test_intermediate_factors_immutability(self):
        factors = IntermediateFactors(
            k1_method=1.0,
            k2_grouping=0.73,
            k3_temperature=0.82,
            k_custom=1.0,
            kh_harmonic=1.0,
            k_total=0.5986,
            rho_ohm_mm2_m=0.023,
            reactance_ohm_m=0.00008,
            cos_phi=0.85,
            sin_phi=0.5268,
        )
        assert factors.k_total == 0.5986
        with pytest.raises((ValidationError, TypeError)):
            factors.k_total = 1.0


class TestModelSerialization:
    def test_electrical_load_to_dict_and_back(self):
        load = ElectricalLoad(voltage_v=400.0, power_kw=18.5, cos_phi=0.85)
        raw_dict = load.model_dump()
        assert isinstance(raw_dict, dict)
        restored = ElectricalLoad.model_validate(raw_dict)
        assert restored == load

    def test_circuit_definition_json_roundtrip(self):
        circuit = CircuitDefinition(
            name="Lighting_Floor_1",
            load=ElectricalLoad(voltage_v=230.0, power_kw=3.68, cos_phi=1.0, phases=PhaseSystem.SINGLE_PHASE),
            cable=CableSpecs(length_m=35.0, conductor=ConductorMaterial.CU, insulation=InsulationType.PVC),
            installation=InstallationConditions(method=InstallationMethod.B),
            protection=ProtectionDevice(in_a=16.0),
            du_max_percent=3.0,
        )
        json_str = circuit.model_dump_json(indent=2)
        assert "Lighting_Floor_1" in json_str
        assert "3.68" in json_str
        restored = CircuitDefinition.model_validate_json(json_str)
        assert restored == circuit

    def test_sizing_result_json_roundtrip(self):
        vd = VoltageDropResult(
            du_volts=6.969,
            du_percent=3.03,
            du_max_percent=5.00,
            is_compliant=True,
            margin_percent=1.97,
        )
        factors = IntermediateFactors(
            k1_method=1.0,
            k2_grouping=1.0,
            k3_temperature=1.0,
            k_total=1.0,
            rho_ohm_mm2_m=0.023,
            reactance_ohm_m=0.0,
            cos_phi=0.85,
            sin_phi=0.5268,
        )
        result = SizingResult(
            circuit_name="Motor_1",
            ib_a=31.415,
            in_a=32.0,
            iz_min_required_a=32.0,
            selected_section_mm2=4.0,
            i0_reference_a=42.0,
            iz_effective_a=42.0,
            ampacity_compliant=True,
            voltage_drop=vd,
            intermediate_factors=factors,
            limiting_constraint=LimitingConstraint.AMPACITY,
            is_compliant=True,
        )
        json_str = result.model_dump_json()
        restored = SizingResult.model_validate_json(json_str)
        assert restored == result
        assert restored.section_mm2 == 4.0
        assert restored.protective_device_in == 32.0
        assert restored.design_current_ib == 31.415
        assert restored.permissible_current_iz == 42.0
        assert restored.total_derating_factor == 1.0
        assert restored.voltage_drop_v == 6.969

    def test_model_json_schema_generation(self):
        schema = CircuitDefinition.model_json_schema()
        assert schema["type"] == "object"
        assert "load" in schema["properties"]
        assert "cable" in schema["properties"]
        assert "installation" in schema["properties"]


class TestModelPropertiesAndEdgeCases:
    def test_enum_edge_cases(self):
        # Missing fallbacks
        assert PhaseSystem._missing_("unrecognized") is None
        assert PhaseSystem._missing_(99) is None
        assert ConductorMaterial._missing_("titanium") is None
        assert InsulationType._missing_("paper") is None
        assert InstallationMethod._missing_("Z") is None
        assert LimitingConstraint._missing_("unknown_constraint") is None

        # Equality non-matching checks
        assert (PhaseSystem.SINGLE_PHASE == "unknown") is False
        assert (PhaseSystem.SINGLE_PHASE == 99) is False
        assert (PhaseSystem.DC == 0) is True
        assert (PhaseSystem.DC == "dc") is True
        assert (PhaseSystem.THREE_PHASE == 3) is True
        assert (LimitingConstraint.AMPACITY == "unknown") is False
        assert (LimitingConstraint.AMPACITY == 123) is False

    def test_all_sizing_result_compatibility_properties(self):
        vd = VoltageDropResult(
            du_volts=5.5,
            du_percent=2.5,
            du_max_percent=5.0,
            is_compliant=True,
            margin_percent=2.5,
        )
        factors = IntermediateFactors(
            k1_method=1.0,
            k2_grouping=1.0,
            k3_temperature=1.0,
            k_total=1.0,
            rho_ohm_mm2_m=0.023,
            reactance_ohm_m=0.0,
            cos_phi=0.85,
            sin_phi=0.5268,
        )
        result = SizingResult(
            circuit_name="Feeder_X",
            ib_a=50.0,
            in_a=63.0,
            iz_min_required_a=63.0,
            selected_section_mm2=16.0,
            i0_reference_a=80.0,
            iz_effective_a=80.0,
            ampacity_compliant=True,
            voltage_drop=vd,
            intermediate_factors=factors,
            limiting_constraint=LimitingConstraint.AMPACITY,
            is_compliant=True,
        )
        assert result.protective_in == 63.0
        assert result.ib == 50.0
        assert result.iz == 80.0
        assert result.k_total == 1.0
        assert result.du_v == 5.5
        assert result.voltage_drop_pct == 2.5
        assert result.du_pct == 2.5

        circuit = CircuitDefinition(
            load=ElectricalLoad(voltage_v=230.0, power_kw=3.0),
            cable=CableSpecs(length_m=10.0),
            du_max_percent=3.5,
        )
        assert circuit.max_voltage_drop_pct == 3.5


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



