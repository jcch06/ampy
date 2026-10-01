"""
Unit tests for pure mathematical calculation functions (ampy.core.formulas).
Conforms strictly to NF C 15-100 and UTE C 15-105 §5.3.
"""

import math

import pytest

from ampy.core.formulas import (
    calculate_harmonic_derating,
    calculate_ib,
    calculate_k3_temp_factor,
    calculate_sin_phi,
    calculate_thermal_stress,
    calculate_thermal_stress_min_section,
    calculate_voltage_drop,
    get_conductor_resistivity,
    get_linear_reactance,
)
from ampy.core.models import (
    ConductorMaterial,
    InsulationType,
    PhaseSystem,
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

    def test_ib_power_in_watts(self):
        ib = calculate_ib(
            system=PhaseSystem.SINGLE_PHASE,
            voltage_v=230.0,
            power_w=2300.0,
            cos_phi=1.0,
        )
        assert ib == 10.000

    def test_ib_apparent_power_in_va(self):
        ib = calculate_ib(
            system=PhaseSystem.THREE_PHASE,
            voltage_v=400.0,
            apparent_power_va=25000.0,
        )
        assert math.isclose(ib, 36.084, rel_tol=0.001)

    def test_ib_invalid_voltage(self):
        with pytest.raises(ValueError, match="voltage_v must be strictly positive"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=0.0, power_kw=5.0)

    def test_ib_invalid_cos_phi(self):
        with pytest.raises(ValueError, match="cos_phi must be in the open-closed interval"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_kw=5.0, cos_phi=1.2)

        with pytest.raises(ValueError, match="cos_phi must be in the open-closed interval"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_kw=5.0, cos_phi=0.0)

    def test_ib_missing_all_load_inputs(self):
        with pytest.raises(ValueError, match="Must provide exactly one of"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0)

    def test_ib_conflicting_multiple_inputs(self):
        with pytest.raises(ValueError, match="Provide either power_w or power_kw"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_w=1000.0, power_kw=1.0)

        with pytest.raises(ValueError, match="Must provide exactly one of"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_kw=5.0, current_a=20.0)

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

    def test_harmonic_derating_invalid_inputs(self):
        with pytest.raises(ValueError, match="ib_a must be strictly positive"):
            calculate_harmonic_derating(ib_a=-10.0, ih3_ratio=0.2)

        with pytest.raises(ValueError, match="ih3_ratio must be non-negative"):
            calculate_harmonic_derating(ib_a=50.0, ih3_ratio=-0.1)


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


class TestPhysicalConductorParameters:
    def test_get_conductor_resistivity_cu_and_al(self):
        assert get_conductor_resistivity(ConductorMaterial.CU) == 0.023
        assert math.isclose(get_conductor_resistivity(ConductorMaterial.AL), 0.037, rel_tol=0.03)

    def test_get_conductor_resistivity_temperature_adjusted(self):
        # At 20°C: Cu should be rho20 = 0.01851
        rho_20 = get_conductor_resistivity(ConductorMaterial.CU, operating_temp_c=20.0)
        assert math.isclose(rho_20, 0.01851, abs_tol=1e-5)

        # At higher temp: Cu resistivity increases
        rho_70 = get_conductor_resistivity(ConductorMaterial.CU, operating_temp_c=70.0)
        assert rho_70 > rho_20

    def test_get_conductor_resistivity_unknown_material(self):
        with pytest.raises(ValueError):
            get_conductor_resistivity("Gold")

    @pytest.mark.parametrize("section, expected_lambda", [
        (1.5, 0.00008),
        (2.5, 0.00008),
        (4.0, 0.00008),
        (6.0, 0.00008),
        (10.0, 0.00008),
        (16.0, 0.00008),
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
        assert res.b_factor == 2.0

    def test_three_phase_motor_bench01(self):
        # BENCH-01: 3P 400V, L=45m, S=4mm², Ib=31.415A, cos=0.85, Cu
        # UTE C 15-105 §5.3: lambda=0.00008 for all sections
        res = calculate_voltage_drop(
            ib_a=31.415,
            length_m=45.0,
            section_mm2=4.0,
            phases=PhaseSystem.THREE_PHASE,
            cos_phi=0.85,
            material=ConductorMaterial.CU,
            voltage_v=400.0,
            du_max_percent=5.0,
        )
        assert math.isclose(res.du_volts, 6.969, rel_tol=0.005)
        assert math.isclose(res.du_percent, 3.030, rel_tol=0.005)
        assert res.is_compliant is True
        assert res.b_factor == 1.0

    def test_three_phase_long_run_bench03(self):
        # BENCH-03: 3P 400V, L=220m, S=25mm², Ib=62.829A, cos=0.85, Cu, S>16 so lambda=0.00008
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

    def test_three_phase_grouping_bench04(self):
        # BENCH-04: 3P 400V, L=30m, S=10mm², Ib=37.358A, cos=0.85, Cu
        # UTE C 15-105 §5.3: lambda=0.00008 for all sections
        res = calculate_voltage_drop(
            ib_a=37.358,
            length_m=30.0,
            section_mm2=10.0,
            phases=PhaseSystem.THREE_PHASE,
            cos_phi=0.85,
            material=ConductorMaterial.CU,
            voltage_v=400.0,
            du_max_percent=5.0,
        )
        assert math.isclose(res.du_volts, 2.238, rel_tol=0.005)
        assert math.isclose(res.du_percent, 0.973, rel_tol=0.005)
        assert res.is_compliant is True

    def test_three_phase_high_temp_bench05(self):
        # BENCH-05: 3P 400V, L=40m, S=16mm², Ib=50.943A, cos=0.85, Cu
        # UTE C 15-105 §5.3: lambda=0.00008 for all sections
        res = calculate_voltage_drop(
            ib_a=50.943,
            length_m=40.0,
            section_mm2=16.0,
            phases=PhaseSystem.THREE_PHASE,
            cos_phi=0.85,
            material=ConductorMaterial.CU,
            voltage_v=400.0,
            du_max_percent=5.0,
        )
        assert math.isclose(res.du_volts, 2.576, rel_tol=0.005)
        assert math.isclose(res.du_percent, 1.120, rel_tol=0.005)
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
        assert res.is_compliant is True

    @pytest.mark.parametrize("invalid_arg", [
        {"length_m": -10.0},
        {"section_mm2": 0.0},
        {"section_mm2": -2.5},
        {"ib_a": -5.0},
        {"cos_phi": 0.0},
        {"cos_phi": 1.1},
    ])
    def test_voltage_drop_invalid_bounds(self, invalid_arg):
        base = {
            "ib_a": 20.0,
            "length_m": 50.0,
            "section_mm2": 10.0,
            "phases": PhaseSystem.THREE_PHASE,
            "cos_phi": 0.85,
            "material": ConductorMaterial.CU,
        }
        base.update(invalid_arg)
        with pytest.raises(ValueError):
            calculate_voltage_drop(**base)


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
        assert res_pass.k_factor == 143.0
        assert res_pass.s_min_mm2 == 22.11

        res_fail = calculate_thermal_stress(
            ik_a=10000.0, time_s=0.10, conductor=ConductorMaterial.CU,
            insulation=InsulationType.XLPE, selected_section_mm2=16.0,
        )
        assert res_fail.is_compliant is False

    @pytest.mark.parametrize("invalid_kwargs", [
        {"ik_a": 0.0, "time_s": 0.1, "mat": ConductorMaterial.CU, "ins": InsulationType.PVC},
        {"ik_a": -1000.0, "time_s": 0.1, "mat": ConductorMaterial.CU, "ins": InsulationType.PVC},
        {"ik_a": 5000.0, "time_s": 0.0, "mat": ConductorMaterial.CU, "ins": InsulationType.PVC},
        {"ik_a": 5000.0, "time_s": -0.1, "mat": ConductorMaterial.CU, "ins": InsulationType.PVC},
        {"ik_a": 5000.0, "time_s": 5.5, "mat": ConductorMaterial.CU, "ins": InsulationType.PVC},
        {"ik_a": 5000.0, "time_s": 0.1, "mat": "Steel", "ins": InsulationType.PVC},
    ])
    def test_thermal_stress_invalid_parameters(self, invalid_kwargs):
        with pytest.raises(ValueError):
            calculate_thermal_stress_min_section(
                ik_a=invalid_kwargs["ik_a"],
                time_s=invalid_kwargs["time_s"],
                material=invalid_kwargs["mat"],
                insulation=invalid_kwargs["ins"],
            )


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

    def test_k3_temp_in_ground(self):
        assert calculate_k3_temp_factor(InsulationType.PVC, 20.0, in_ground=True) == 1.0
        assert calculate_k3_temp_factor(InsulationType.XLPE, 20.0, in_ground=True) == 1.0

    @pytest.mark.parametrize("ins, temp_c", [
        (InsulationType.PVC, 70.0),
        (InsulationType.PVC, 75.0),
        (InsulationType.XLPE, 90.0),
        (InsulationType.XLPE, 95.0),
    ])
    def test_k3_over_temperature_rejection(self, ins, temp_c):
        with pytest.raises(ValueError, match="equals or exceeds maximum continuous"):
            calculate_k3_temp_factor(ins, temp_c)


class TestEdgeAndCornerCases:
    def test_calculate_ib_edge_cases(self):
        with pytest.raises(ValueError, match="Must provide system or phases"):
            calculate_ib(system=None, phases=None, voltage_v=230.0, power_w=1000.0)

        with pytest.raises(ValueError, match="Provide either apparent_power_va or apparent_power_kva"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, apparent_power_va=1000.0, apparent_power_kva=1.0)

        with pytest.raises(ValueError, match="current_a must be strictly positive"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, current_a=-5.0)

        with pytest.raises(ValueError, match="power_w must be strictly positive"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_w=-100.0)

        with pytest.raises(ValueError, match="apparent_power_va must be strictly positive"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, apparent_power_va=-100.0)

        with pytest.raises(ValueError, match="DC circuits require active power"):
            calculate_ib(system=PhaseSystem.DC, voltage_v=240.0, apparent_power_va=500.0)

        with pytest.raises(ValueError, match="Unsupported system type"):
            calculate_ib(system="SolarInverter4P", voltage_v=230.0, power_w=1000.0)

    def test_conductor_resistivity_edge_cases(self):
        rho_al_temp = get_conductor_resistivity(ConductorMaterial.AL, operating_temp_c=50.0)
        assert rho_al_temp > 0.02941

        with pytest.raises(ValueError, match="Unknown conductor material"):
            get_conductor_resistivity("Silver", operating_temp_c=25.0)

    def test_calculate_voltage_drop_edge_cases(self):
        res = calculate_voltage_drop(phases=PhaseSystem.THREE_PHASE, length_m=10.0, section_mm2=25.0, ib_a=10.0, conductor=ConductorMaterial.AL)
        assert res.is_compliant is True

        with pytest.raises(ValueError, match="Must provide system or phases"):
            calculate_voltage_drop(system=None, phases=None, length_m=10.0, section_mm2=4.0, ib_a=10.0)

        with pytest.raises(ValueError, match="Unsupported system type"):
            calculate_voltage_drop(system="ComplexSystem", length_m=10.0, section_mm2=4.0, ib_a=10.0)

    def test_thermal_stress_edge_cases(self):
        with pytest.raises(ValueError, match="Must provide material or conductor"):
            calculate_thermal_stress(ik_a=1000.0, time_s=0.1, material=None, conductor=None, insulation=InsulationType.PVC)

        with pytest.raises(ValueError, match="Must provide insulation"):
            calculate_thermal_stress(ik_a=1000.0, time_s=0.1, material=ConductorMaterial.CU, insulation=None)

        with pytest.raises(ValueError, match="Unknown material/insulation combination"):
            calculate_thermal_stress(ik_a=1000.0, time_s=0.1, material="Silver", insulation=InsulationType.PVC)

    def test_k3_temp_factor_edge_cases(self):
        with pytest.raises(ValueError, match="Must provide temp_c or ambient_temp_c"):
            calculate_k3_temp_factor(insulation=InsulationType.PVC, temp_c=None, ambient_temp_c=None)

        with pytest.raises(ValueError, match="Unknown insulation type"):
            calculate_k3_temp_factor(insulation="Rubber", temp_c=30.0)


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

    @pytest.mark.parametrize("bad_v", [0.0, -10.0, -230.0])
    def test_calculate_voltage_drop_invalid_voltage(self, bad_v: float):
        with pytest.raises(ValueError, match="voltage_v must be strictly positive"):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=10.0,
                section_mm2=4.0,
                ib_a=10.0,
                voltage_v=bad_v,
            )

    @pytest.mark.parametrize("bad_u_ref", [0.0, -10.0, -230.0])
    def test_calculate_voltage_drop_invalid_u_ref(self, bad_u_ref: float):
        with pytest.raises(ValueError, match="u_ref must be strictly positive"):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=10.0,
                section_mm2=4.0,
                ib_a=10.0,
                voltage_v=230.0,
                u_ref=bad_u_ref,
            )


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
        with pytest.raises(ValueError, match="(?i)unknown conductor material|unsupported material|unknown material/insulation combination"):
            calculate_thermal_stress_min_section(
                ik_a=5000.0,
                time_s=0.10,
                material="Titanium",
                insulation="PVC",
            )

    @pytest.mark.parametrize("mat_alias", ["copper", "cu", "cuivre"])
    def test_get_conductor_resistivity_aliases(self, mat_alias: str):
        assert get_conductor_resistivity(mat_alias) == 0.023
        assert get_conductor_resistivity(mat_alias, operating_temp_c=20.0) == 0.01851


