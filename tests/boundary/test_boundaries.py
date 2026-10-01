"""
Adversarial stress testing and empirical boundary verification for ampy.core.formulas.

Conforms strictly to:
- NF C 15-100 (Parties 4-43, 5-52)
- UTE C 15-105 (§5.3)
- Tier 2 / Tier 5 adversarial stress harness specifications
"""

from __future__ import annotations

import math
import random
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


# ==============================================================================
# 1. Boundary and Adversarial cos_phi
# ==============================================================================

class TestBoundaryCosPhi:
    """Stress tests on displacement power factor cos(phi) across boundary and extreme values."""

    def test_cos_phi_boundary_one_purely_resistive(self):
        """cos_phi = 1.0: sin_phi must be 0.0, reactance contributes 0 in voltage drop."""
        assert calculate_sin_phi(1.0) == 0.0

        # Single-phase
        ib_1p = calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_w=2300.0, cos_phi=1.0)
        assert ib_1p == 10.0

        # Three-phase
        ib_3p = calculate_ib(system=PhaseSystem.THREE_PHASE, voltage_v=400.0, power_w=4000.0 * math.sqrt(3), cos_phi=1.0)
        assert math.isclose(ib_3p, 10.0, rel_tol=1e-3)

        # Voltage drop with cos_phi=1.0: pure resistive component
        res = calculate_voltage_drop(
            system=PhaseSystem.THREE_PHASE,
            length_m=100.0,
            section_mm2=25.0,  # lambda = 0.00008, but sin_phi = 0
            ib_a=20.0,
            cos_phi=1.0,
            material=ConductorMaterial.CU,
            voltage_v=400.0,
        )
        # dU = 1.0 * (0.023 * 100 / 25 * 1.0 + 0) * 20 = 0.092 * 20 = 1.84 V
        assert math.isclose(res.du_volts, 1.84, abs_tol=1e-3)

    def test_cos_phi_boundary_near_zero_inductive(self):
        """cos_phi = 0.01: extremely inductive load, Ib increases by 100x compared to cos=1.0."""
        sin_phi = calculate_sin_phi(0.01)
        assert math.isclose(sin_phi, math.sqrt(1.0 - 0.0001), rel_tol=1e-5)

        ib_unity = calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_w=230.0, cos_phi=1.0)
        ib_low = calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_w=230.0, cos_phi=0.01)
        assert math.isclose(ib_low, ib_unity * 100.0, rel_tol=1e-3)

    def test_cos_phi_zero_boundary(self):
        """cos_phi = 0.0: mathematically sin(acos(0))=1.0, but AC circuits must reject cos=0."""
        assert calculate_sin_phi(0.0) == 1.0

        with pytest.raises(ValueError, match="cos_phi must be in the open-closed interval"):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_w=2300.0, cos_phi=0.0)

        with pytest.raises(ValueError, match="cos_phi must be in"):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=50.0,
                section_mm2=4.0,
                ib_a=10.0,
                cos_phi=0.0,
            )

    @pytest.mark.parametrize("invalid_cos", [-0.01, -0.5, -1.0, 1.0001, 1.05, 2.0, -10.0])
    def test_cos_phi_out_of_bounds_rejected(self, invalid_cos):
        """Power factor outside (0.0, 1.0] must be rejected with ValueError."""
        with pytest.raises(ValueError):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_w=2300.0, cos_phi=invalid_cos)

        with pytest.raises(ValueError):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=50.0,
                section_mm2=4.0,
                ib_a=10.0,
                cos_phi=invalid_cos,
            )

        with pytest.raises(ValueError):
            calculate_sin_phi(invalid_cos)

    def test_cos_phi_nan_and_inf_rejected(self):
        """cos_phi = NaN or Inf must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, power_w=1000.0, cos_phi=float("nan"))

        with pytest.raises(ValueError):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=50.0,
                section_mm2=4.0,
                ib_a=10.0,
                cos_phi=float("nan"),
            )


# ==============================================================================
# 2. Extreme Currents (100 kA down to 0.001 A)
# ==============================================================================

class TestExtremeCurrents:
    """Stress testing on extreme currents: 100 kA (short circuit/huge plant) down to 1 mA."""

    def test_very_high_current_100ka(self):
        """100 kA (100,000 A) direct current handling."""
        ib = calculate_ib(system=PhaseSystem.THREE_PHASE, voltage_v=400.0, current_a=100_000.0)
        assert ib == 100_000.0

        # Short-circuit withstand at 100 kA, t=0.2s, Cu XLPE (k=143)
        # S_min = 100000 * sqrt(0.2) / 143 = 44721.36 / 143 = 312.74 mm²
        s_min = calculate_thermal_stress_min_section(
            ik_a=100_000.0,
            time_s=0.2,
            material=ConductorMaterial.CU,
            insulation=InsulationType.XLPE,
        )
        assert math.isclose(s_min, 312.74, rel_tol=1e-3)

        # Voltage drop at 100 kA across 10m of 300 mm²
        res = calculate_voltage_drop(
            system=PhaseSystem.THREE_PHASE,
            length_m=10.0,
            section_mm2=300.0,
            ib_a=100_000.0,
            cos_phi=0.85,
            material=ConductorMaterial.CU,
            voltage_v=400.0,
        )
        assert res.du_volts > 0.0
        assert math.isfinite(res.du_volts)
        assert math.isfinite(res.du_percent)

    def test_minimal_current_1ma(self):
        """0.001 A (1 mA) design operating current."""
        ib = calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, current_a=0.001)
        assert ib == 0.001

        res = calculate_voltage_drop(
            system=PhaseSystem.SINGLE_PHASE,
            length_m=50.0,
            section_mm2=1.5,
            ib_a=0.001,
            cos_phi=1.0,
            material=ConductorMaterial.CU,
            voltage_v=230.0,
        )
        # dU = 2 * (0.023 * 50 / 1.5) * 0.001 = 2 * 0.7667 * 0.001 = 0.00153 V -> round 0.002
        assert math.isclose(res.du_volts, 0.002, abs_tol=1e-3)
        assert res.is_compliant is True

    def test_zero_and_negative_currents_rejected(self):
        """Current <= 0.0 must be rejected."""
        with pytest.raises(ValueError):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, current_a=0.0)

        with pytest.raises(ValueError):
            calculate_ib(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, current_a=-1.0)

        with pytest.raises(ValueError):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=50.0,
                section_mm2=2.5,
                ib_a=-0.5,
            )

        with pytest.raises(ValueError):
            calculate_thermal_stress_min_section(
                ik_a=0.0,
                time_s=0.1,
                material=ConductorMaterial.CU,
                insulation=InsulationType.PVC,
            )


# ==============================================================================
# 3. Extreme Cable Route Lengths (0 m and 5000 m)
# ==============================================================================

class TestExtremeCableLengths:
    """Stress tests on cable route length: 0 m and 5000 m (5 km)."""

    def test_zero_cable_length(self):
        """0 m length: voltage drop must be exactly 0.0 V, 0.0% and compliant."""
        res = calculate_voltage_drop(
            system=PhaseSystem.THREE_PHASE,
            length_m=0.0,
            section_mm2=10.0,
            ib_a=50.0,
            cos_phi=0.85,
            material=ConductorMaterial.CU,
            voltage_v=400.0,
            du_max_percent=5.0,
        )
        assert res.du_volts == 0.0
        assert res.du_percent == 0.0
        assert res.is_compliant is True
        assert res.margin_percent == 5.0

    def test_very_long_cable_5000m(self):
        """5000 m (5 km) cable run: high dU, finite float output, compliance failure."""
        res = calculate_voltage_drop(
            system=PhaseSystem.THREE_PHASE,
            length_m=5000.0,
            section_mm2=25.0,
            ib_a=30.0,
            cos_phi=0.85,
            material=ConductorMaterial.CU,
            voltage_v=400.0,
            du_max_percent=5.0,
        )
        assert res.du_volts > 100.0
        assert res.du_percent > 40.0
        assert res.is_compliant is False
        assert res.margin_percent < 0.0
        assert math.isfinite(res.du_volts)

    def test_negative_cable_length_rejected(self):
        """Negative cable length must raise ValueError."""
        with pytest.raises(ValueError, match="length_m must be non-negative"):
            calculate_voltage_drop(
                system=PhaseSystem.SINGLE_PHASE,
                length_m=-0.01,
                section_mm2=2.5,
                ib_a=10.0,
            )


# ==============================================================================
# 4. Extreme Ambient Temperatures (-40°C, 65°C, 70°C for PVC, 90°C for XLPE)
# ==============================================================================

class TestExtremeAmbientTemperatures:
    """Stress tests on temperature derating k3 and conductor operating resistivity."""

    def test_sub_zero_temperature_minus_40c(self):
        """-40°C arctic conditions: k3 factor > 1.0 (enhanced cooling)."""
        # PVC in air: sqrt((70 - (-40)) / (70 - 30)) = sqrt(110 / 40) = sqrt(2.75) = 1.658 -> 1.66
        k3_pvc = calculate_k3_temp_factor(InsulationType.PVC, temp_c=-40.0, in_ground=False)
        assert math.isclose(k3_pvc, 1.66, abs_tol=0.01)

        # XLPE in air: sqrt((90 - (-40)) / (90 - 30)) = sqrt(130 / 60) = sqrt(2.167) = 1.472 -> 1.47
        k3_xlpe = calculate_k3_temp_factor(InsulationType.XLPE, temp_c=-40.0, in_ground=False)
        assert math.isclose(k3_xlpe, 1.47, abs_tol=0.01)

        # Resistivity at -40°C: Cu should decrease
        rho_cold = get_conductor_resistivity(ConductorMaterial.CU, operating_temp_c=-40.0)
        rho_20 = get_conductor_resistivity(ConductorMaterial.CU, operating_temp_c=20.0)
        assert rho_cold < rho_20
        # rho(-40) = 0.01851 * (1 + 0.00393 * (-60)) = 0.01851 * 0.7642 = 0.01415
        assert math.isclose(rho_cold, 0.01415, abs_tol=1e-5)

    def test_high_temperature_65c(self):
        """65°C desert/boiler plant: strong derating."""
        # PVC in air: sqrt((70 - 65) / (70 - 30)) = sqrt(5 / 40) = 0.353 -> 0.35
        k3_pvc = calculate_k3_temp_factor(InsulationType.PVC, temp_c=65.0, in_ground=False)
        assert math.isclose(k3_pvc, 0.35, abs_tol=0.01)

        # XLPE in air: sqrt((90 - 65) / (90 - 30)) = sqrt(25 / 60) = 0.645 -> 0.65
        k3_xlpe = calculate_k3_temp_factor(InsulationType.XLPE, temp_c=65.0, in_ground=False)
        assert math.isclose(k3_xlpe, 0.65, abs_tol=0.01)

    def test_pvc_limit_at_70c_rejected(self):
        """PVC ambient temp >= 70°C must raise ValueError (equals or exceeds max continuous temp)."""
        with pytest.raises(ValueError, match="equals or exceeds maximum continuous"):
            calculate_k3_temp_factor(InsulationType.PVC, temp_c=70.0)

        with pytest.raises(ValueError, match="equals or exceeds maximum continuous"):
            calculate_k3_temp_factor(InsulationType.PVC, temp_c=75.0)

        # XLPE at 70°C is still valid (max is 90°C)
        k3_xlpe = calculate_k3_temp_factor(InsulationType.XLPE, temp_c=70.0)
        # sqrt((90 - 70) / (90 - 30)) = sqrt(20/60) = 0.577 -> 0.58
        assert math.isclose(k3_xlpe, 0.58, abs_tol=0.01)

    def test_xlpe_limit_at_90c_rejected(self):
        """XLPE ambient temp >= 90°C must raise ValueError."""
        with pytest.raises(ValueError, match="equals or exceeds maximum continuous"):
            calculate_k3_temp_factor(InsulationType.XLPE, temp_c=90.0)

        with pytest.raises(ValueError, match="equals or exceeds maximum continuous"):
            calculate_k3_temp_factor(InsulationType.XLPE, temp_c=95.0)


# ==============================================================================
# 5. Invalid Cross-Sections and Disconnection Times (> 5s)
# ==============================================================================

class TestCrossSectionsAndDisconnectionTimes:
    """Stress tests on invalid cross-sections (<=0) and adiabatic time boundary (> 5s)."""

    @pytest.mark.parametrize("invalid_s", [0.0, -1.0, -16.0, -0.0001])
    def test_zero_or_negative_cross_section_rejected(self, invalid_s):
        """Cross section <= 0.0 must raise ValueError in calculate_voltage_drop."""
        with pytest.raises(ValueError, match="section_mm2 must be strictly positive"):
            calculate_voltage_drop(
                system=PhaseSystem.THREE_PHASE,
                length_m=50.0,
                section_mm2=invalid_s,
                ib_a=20.0,
            )

    def test_disconnection_time_boundary_5s(self):
        """Disconnection time up to exactly 5.0s is allowed; > 5.0s must raise ValueError."""
        # Boundary 5.0s: allowed
        s_min = calculate_thermal_stress_min_section(
            ik_a=5000.0,
            time_s=5.0,
            material=ConductorMaterial.CU,
            insulation=InsulationType.XLPE,
        )
        assert s_min > 0.0
        assert math.isfinite(s_min)

        # > 5.0s: non-adiabatic, must raise ValueError
        with pytest.raises(ValueError, match="exceeds maximum 5.0s limit for adiabatic assumption"):
            calculate_thermal_stress_min_section(
                ik_a=5000.0,
                time_s=5.001,
                material=ConductorMaterial.CU,
                insulation=InsulationType.XLPE,
            )

        with pytest.raises(ValueError, match="exceeds maximum 5.0s limit for adiabatic assumption"):
            calculate_thermal_stress_min_section(
                ik_a=5000.0,
                time_s=10.0,
                material=ConductorMaterial.CU,
                insulation=InsulationType.XLPE,
            )

    @pytest.mark.parametrize("invalid_t", [0.0, -0.001, -1.0])
    def test_non_positive_disconnection_time_rejected(self, invalid_t):
        """Disconnection time <= 0.0 must raise ValueError."""
        with pytest.raises(ValueError, match="time_s must be strictly positive"):
            calculate_thermal_stress_min_section(
                ik_a=5000.0,
                time_s=invalid_t,
                material=ConductorMaterial.CU,
                insulation=InsulationType.XLPE,
            )


# ==============================================================================
# 6. Physical Laws and Floating Point Invariants
# ==============================================================================

class TestPhysicalLawsAndFloatingPointInvariants:
    """Rigorous verification of physical laws, monotonicity, and mathematical invariants."""

    def test_voltage_drop_monotonicity_with_length(self):
        """dU must be strictly increasing with cable length L."""
        lengths = [1.0, 10.0, 50.0, 100.0, 500.0]
        du_vals = [
            calculate_voltage_drop(
                system=PhaseSystem.THREE_PHASE,
                length_m=l,
                section_mm2=16.0,
                ib_a=25.0,
                cos_phi=0.85,
            ).du_volts
            for l in lengths
        ]
        for i in range(len(du_vals) - 1):
            assert du_vals[i] < du_vals[i + 1], f"Monotonicity violation: dU({lengths[i]}) >= dU({lengths[i+1]})"

    def test_voltage_drop_monotonicity_with_current(self):
        """dU must be strictly increasing with operating current Ib."""
        currents = [1.0, 10.0, 25.0, 63.0, 125.0]
        du_vals = [
            calculate_voltage_drop(
                system=PhaseSystem.THREE_PHASE,
                length_m=50.0,
                section_mm2=16.0,
                ib_a=ib,
                cos_phi=0.85,
            ).du_volts
            for ib in currents
        ]
        for i in range(len(du_vals) - 1):
            assert du_vals[i] < du_vals[i + 1]

    def test_voltage_drop_monotonicity_with_section(self):
        """dU must be strictly decreasing with conductor cross-section S."""
        sections = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 50.0, 120.0, 240.0]
        du_vals = [
            calculate_voltage_drop(
                system=PhaseSystem.THREE_PHASE,
                length_m=100.0,
                section_mm2=s,
                ib_a=20.0,
                cos_phi=0.85,
            ).du_volts
            for s in sections
        ]
        for i in range(len(du_vals) - 1):
            assert du_vals[i] > du_vals[i + 1], f"Monotonicity violation: dU(S={sections[i]}) <= dU(S={sections[i+1]})"

    def test_single_phase_to_three_phase_exact_voltage_drop_ratio(self):
        """Single phase (b=2) dU_volts must be EXACTLY 2.0x three-phase (b=1) dU_volts."""
        args = dict(length_m=75.0, section_mm2=10.0, ib_a=32.0, cos_phi=0.85, material=ConductorMaterial.CU)
        res_3p = calculate_voltage_drop(system=PhaseSystem.THREE_PHASE, voltage_v=400.0, **args)
        res_1p = calculate_voltage_drop(system=PhaseSystem.SINGLE_PHASE, voltage_v=230.0, **args)
        assert math.isclose(res_1p.du_volts, 2.0 * res_3p.du_volts, rel_tol=1e-4)

    def test_scaling_linearity_with_rounding_tolerance(self):
        """Length scaling linearity: dU(2L) ~= 2 * dU(L) within 3-decimal rounding quantization (+-1mV)."""
        args = dict(system=PhaseSystem.THREE_PHASE, section_mm2=25.0, ib_a=40.0, cos_phi=0.85)
        res_1 = calculate_voltage_drop(length_m=50.0, **args)
        res_2 = calculate_voltage_drop(length_m=100.0, **args)
        # res_1.du_volts is rounded to 3 decimal places (1.648), res_2 is 3.297. Diff <= 0.002 V.
        assert abs(res_2.du_volts - 2.0 * res_1.du_volts) <= 0.002

    def test_thermal_stress_scaling_laws(self):
        """S_min scales linearly with Ik and with sqrt(t)."""
        s1 = calculate_thermal_stress_min_section(10_000.0, 0.1, ConductorMaterial.CU, InsulationType.PVC)
        s2 = calculate_thermal_stress_min_section(20_000.0, 0.1, ConductorMaterial.CU, InsulationType.PVC)
        assert math.isclose(s2, 2.0 * s1, rel_tol=0.01)

        s3 = calculate_thermal_stress_min_section(10_000.0, 0.4, ConductorMaterial.CU, InsulationType.PVC)
        # sqrt(0.4) / sqrt(0.1) = 2.0
        assert math.isclose(s3, 2.0 * s1, rel_tol=0.01)

    def test_trigonometric_invariants(self):
        """cos²(phi) + sin²(phi) == 1.0 across random distribution."""
        for _ in range(50):
            cos_val = random.uniform(0.01, 1.0)
            sin_val = calculate_sin_phi(cos_val)
            sum_sq = (cos_val ** 2) + (sin_val ** 2)
            assert math.isclose(sum_sq, 1.0, abs_tol=1e-12)

    def test_material_resistivity_cu_vs_al_physical_law(self):
        """Aluminium resistivity must be strictly greater than Copper at all valid temperatures."""
        for temp in [-40.0, 0.0, 20.0, 50.0, 70.0, 90.0]:
            rho_cu = get_conductor_resistivity(ConductorMaterial.CU, operating_temp_c=temp)
            rho_al = get_conductor_resistivity(ConductorMaterial.AL, operating_temp_c=temp)
            assert rho_al > rho_cu, f"Physical law violation at {temp}°C: rho_Al ({rho_al}) <= rho_Cu ({rho_cu})"


# ==============================================================================
# 7. Discovered Edge Vulnerabilities & Robustness Challenges
# ==============================================================================

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


# ==============================================================================
# Standalone Script Entry Point
# ==============================================================================

def run_standalone_adversarial_suite():
    """Execute all tests programmatically and print detailed audit report."""
    print("=" * 75)
    print("EMPIRICAL ADVERSARIAL STRESS SUITE: ampy.core.formulas")
    print("=" * 75)

    test_classes = [
        ("1. Boundary & Adversarial cos_phi", TestBoundaryCosPhi),
        ("2. Extreme Currents (100kA to 1mA)", TestExtremeCurrents),
        ("3. Extreme Cable Route Lengths (0m, 5000m)", TestExtremeCableLengths),
        ("4. Extreme Ambient Temperatures (-40°C, 65°C, 70°C, 90°C)", TestExtremeAmbientTemperatures),
        ("5. Cross-Sections and Disconnection Times", TestCrossSectionsAndDisconnectionTimes),
        ("6. Physical Laws and Floating Point Invariants", TestPhysicalLawsAndFloatingPointInvariants),
        ("7. Discovered Edge Vulnerabilities", TestDiscoveredVulnerabilities),
    ]

    total_passed = 0
    total_failed = 0
    failures = []

    for category, cls in test_classes:
        print(f"\n--- {category} ---")
        instance = cls()
        for method_name in sorted(dir(instance)):
            if not method_name.startswith("test_"):
                continue
            method = getattr(instance, method_name)

            # If method is decorated with pytest.mark.parametrize, handle its cases directly
            if hasattr(method, "pytestmark"):
                param_marks = [m for m in method.pytestmark if m.name == "parametrize"]
                if param_marks:
                    argnames = param_marks[0].args[0]
                    argvalues = param_marks[0].args[1]
                    for val in argvalues:
                        test_label = f"{cls.__name__}.{method_name}[{val}]"
                        try:
                            method(val)
                            print(f"  [PASS] {test_label}")
                            total_passed += 1
                        except Exception as exc:
                            print(f"  [FAIL] {test_label}: {exc}")
                            total_failed += 1
                            failures.append((test_label, exc))
                    continue

            test_label = f"{cls.__name__}.{method_name}"
            try:
                method()
                print(f"  [PASS] {test_label}")
                total_passed += 1
            except Exception as exc:
                print(f"  [FAIL] {test_label}: {exc}")
                total_failed += 1
                failures.append((test_label, exc))

    print("\n" + "=" * 75)
    print(f"FINAL STRESS HARNESS RESULTS: {total_passed} PASSED, {total_failed} FAILED")
    print("=" * 75)
    return total_failed == 0


if __name__ == "__main__":
    import sys
    success = run_standalone_adversarial_suite()
    sys.exit(0 if success else 1)
