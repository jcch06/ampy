"""
End-to-End acceptance test suite for the 5 canonical UTE C 15-105 worked benchmark scenarios.

Normative References:
- NF C 15-100 (Parties 4-43, 5-52)
- UTE C 15-105 (Guide pratique de calcul - Sections de conducteurs et calibres de protection)
- TEST_INFRA.md and benchmarks specification

Canonical Scenarios:
- BENCH-01: Standard 3P Motor 18.5kW (Method E, XLPE, Cu, 45m) -> S=4.0mm², In=32A, dU=3.03%
- BENCH-02: 1P Commercial Lighting 3.68kW (Method B, PVC, Cu, 35m) -> S=4.0mm², In=16A, dU=2.80%
- BENCH-03: Long-Run Feeder Pumping 37kW (Method C, XLPE, Cu, 220m) -> S=25.0mm², In=63A, dU=4.95%
- BENCH-04: Multi-Cable Grouping N=6 touching (Method E, XLPE, Cu, 30m) -> S=10.0mm², In=40A, dU=0.97%
- BENCH-05: High Ambient Temp 50°C Plant (Method C, XLPE, Cu, 40m) -> S=16.0mm², In=63A, dU=1.12%
"""

from typing import Any

import pytest

# Require ampy package or gracefully skip until implemented
ampy = pytest.importorskip("ampy", reason="ampy package is not yet installed or importable")

try:
    # Attempt public facade import (PROJECT.md F17_PUBLIC_API)
    from ampy import (
        CableSpecs,
        CircuitDefinition,
        ConductorMaterial,
        ElectricalLoad,
        InstallationConditions,
        InstallationMethod,
        InsulationType,
        LimitingConstraint,
        PhaseSystem,
        SizingEngine,
        SizingResult,
    )
except ImportError:
    # Fallback to core modular imports during intermediate milestones
    try:
        from ampy.core.engine import SizingEngine
        from ampy.core.models import (
            CableSpecs,
            CircuitDefinition,
            ConductorMaterial,
            ElectricalLoad,
            InstallationConditions,
            InstallationMethod,
            InsulationType,
            LimitingConstraint,
            PhaseSystem,
            SizingResult,
        )
    except ImportError as exc:
        pytest.skip(
            f"ampy public API / core engine not yet available: {exc}",
            allow_module_level=True,
        )

from tests.conftest import (
    ToleranceConfig,
    assert_sizing_result_matches_benchmark,
    extract_result_fields,
)

# ---------------------------------------------------------------------------
# Canonical Circuit Builders
# ---------------------------------------------------------------------------


def build_bench01_circuit() -> CircuitDefinition:
    """BENCH-01: Standard 3P Motor 18.5kW (Method E, XLPE, Cu, 45m)."""
    return CircuitDefinition(
        name="BENCH-01: Industrial Motor 18.5kW",
        load=ElectricalLoad(
            active_power_kw=18.5,
            voltage_v=400.0,
            phases=PhaseSystem.THREE,
            cos_phi=0.85,
        ),
        cable=CableSpecs(
            conductor_material=ConductorMaterial.CU,
            insulation=InsulationType.XLPE,
            length_m=45.0,
        ),
        installation=InstallationConditions(
            method=InstallationMethod.E,
            ambient_temp_c=30.0,
            grouping_circuits=1,
        ),
        max_voltage_drop_pct=5.0,
    )


def build_bench02_circuit() -> CircuitDefinition:
    """BENCH-02: 1P Commercial Lighting 3.68kW (Method B, PVC, Cu, 35m)."""
    return CircuitDefinition(
        name="BENCH-02: Lighting Sub-Distribution 3.68kW",
        load=ElectricalLoad(
            active_power_kw=3.68,
            voltage_v=230.0,
            phases=PhaseSystem.SINGLE,
            cos_phi=1.00,
        ),
        cable=CableSpecs(
            conductor_material=ConductorMaterial.CU,
            insulation=InsulationType.PVC,
            length_m=35.0,
        ),
        installation=InstallationConditions(
            method=InstallationMethod.B,
            ambient_temp_c=30.0,
            grouping_circuits=1,
        ),
        max_voltage_drop_pct=3.0,
    )


def build_bench03_circuit() -> CircuitDefinition:
    """BENCH-03: Long-Run Feeder Pumping 37kW (Method C, XLPE, Cu, 220m)."""
    return CircuitDefinition(
        name="BENCH-03: Pumping Station Feeder 37kW 220m",
        load=ElectricalLoad(
            active_power_kw=37.0,
            voltage_v=400.0,
            phases=PhaseSystem.THREE,
            cos_phi=0.85,
        ),
        cable=CableSpecs(
            conductor_material=ConductorMaterial.CU,
            insulation=InsulationType.XLPE,
            length_m=220.0,
        ),
        installation=InstallationConditions(
            method=InstallationMethod.C,
            ambient_temp_c=30.0,
            grouping_circuits=1,
        ),
        max_voltage_drop_pct=5.0,
    )


def build_bench04_circuit() -> CircuitDefinition:
    """BENCH-04: Multi-Cable Grouping N=6 touching (Method E, XLPE, Cu, 30m)."""
    return CircuitDefinition(
        name="BENCH-04: Grouping Gallery 22kW N=6",
        load=ElectricalLoad(
            active_power_kw=22.0,
            voltage_v=400.0,
            phases=PhaseSystem.THREE,
            cos_phi=0.85,
        ),
        cable=CableSpecs(
            conductor_material=ConductorMaterial.CU,
            insulation=InsulationType.XLPE,
            length_m=30.0,
        ),
        installation=InstallationConditions(
            method=InstallationMethod.E,
            ambient_temp_c=30.0,
            grouping_circuits=6,
        ),
        max_voltage_drop_pct=5.0,
    )


def build_bench05_circuit() -> CircuitDefinition:
    """BENCH-05: High Ambient Temp 50°C Plant (Method C, XLPE, Cu, 40m)."""
    return CircuitDefinition(
        name="BENCH-05: Thermal Boiler Pump 30kW 50C",
        load=ElectricalLoad(
            active_power_kw=30.0,
            voltage_v=400.0,
            phases=PhaseSystem.THREE,
            cos_phi=0.85,
        ),
        cable=CableSpecs(
            conductor_material=ConductorMaterial.CU,
            insulation=InsulationType.XLPE,
            length_m=40.0,
        ),
        installation=InstallationConditions(
            method=InstallationMethod.C,
            ambient_temp_c=50.0,
            grouping_circuits=1,
        ),
        max_voltage_drop_pct=5.0,
    )


CANONICAL_BENCHMARK_CASES: list[dict[str, Any]] = [
    {
        "id": "BENCH-01",
        "name": "Standard 3P Industrial Motor 18.5kW",
        "builder": build_bench01_circuit,
        "expected_section": 4.0,
        "expected_in": 32,
        "expected_ib": 31.41,
        "expected_k_total": 1.0000,
        "expected_iz": 42.00,
        "expected_du_v": 6.969,
        "expected_du_pct": 3.03,
        "expected_constraint": LimitingConstraint.IZ,
    },
    {
        "id": "BENCH-02",
        "name": "1P Commercial Lighting Circuit 3.68kW",
        "builder": build_bench02_circuit,
        "expected_section": 4.0,
        "expected_in": 16,
        "expected_ib": 16.00,
        "expected_k_total": 1.0000,
        "expected_iz": 32.00,
        "expected_du_v": 6.440,
        "expected_du_pct": 2.80,
        "expected_constraint": LimitingConstraint.DU,
    },
    {
        "id": "BENCH-03",
        "name": "Long-Run Feeder Pumping 37kW 220m",
        "builder": build_bench03_circuit,
        "expected_section": 25.0,
        "expected_in": 63,
        "expected_ib": 62.83,
        "expected_k_total": 1.0000,
        "expected_iz": 119.00,
        "expected_du_v": 11.392,
        "expected_du_pct": 4.95,
        "expected_constraint": LimitingConstraint.DU,
    },
    {
        "id": "BENCH-04",
        "name": "Multi-Cable Grouping N=6 touching 22kW",
        "builder": build_bench04_circuit,
        "expected_section": 10.0,
        "expected_in": 40,
        "expected_ib": 37.36,
        "expected_k_total": 0.7300,
        "expected_iz": 54.75,
        "expected_du_v": 2.238,
        "expected_du_pct": 0.97,
        "expected_constraint": LimitingConstraint.IZ,
    },
    {
        "id": "BENCH-05",
        "name": "High Ambient Temp 50°C Plant 30kW",
        "builder": build_bench05_circuit,
        "expected_section": 16.0,
        "expected_in": 63,
        "expected_ib": 50.94,
        "expected_k_total": 0.8200,
        "expected_iz": 78.72,
        "expected_du_v": 2.576,
        "expected_du_pct": 1.12,
        "expected_constraint": LimitingConstraint.IZ,
    },
]


# ---------------------------------------------------------------------------
# Individual Canonical Benchmark Acceptance Tests (Tier 4 / E2E)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.tier4
def test_bench_01_standard_3p_motor(tolerance_config: ToleranceConfig) -> None:
    """
    BENCH-01: Standard 3P Motor 18.5kW (Method E, XLPE, Cu, 45m).
    
    Verifies:
    - Ib = 18500 / (sqrt(3) * 400 * 0.85) = 31.41 A
    - In = 32 A (standard rating >= Ib)
    - Correction factors k1=1.0, k2=1.0, k3=1.0 => k_total=1.0000
    - Thermally required section S = 4.0 mm² (I0=42 A >= 32 A)
    - Calculated dU = 6.97 V (3.03% <= 5.0% max)
    - Limiting constraint: LimitingConstraint.IZ
    """
    circuit = build_bench01_circuit()
    engine = SizingEngine()
    result: SizingResult = engine.size_circuit(circuit)

    spec = CANONICAL_BENCHMARK_CASES[0]
    assert_sizing_result_matches_benchmark(result, spec, tol=tolerance_config)


@pytest.mark.e2e
@pytest.mark.tier4
def test_bench_02_single_phase_lighting(tolerance_config: ToleranceConfig) -> None:
    """
    BENCH-02: 1P Commercial Lighting 3.68kW (Method B, PVC, Cu, 35m).
    
    Verifies:
    - Ib = 3680 / (230 * 1.0) = 16.00 A
    - In = 16 A
    - Thermally S=1.5 mm² is sufficient (I0=17.5 A >= 16 A), but yields dU=7.47% > 3.0% limit.
    - S=2.5 mm² yields dU=4.48% > 3.0% limit.
    - S=4.0 mm² satisfies dU=2.80% <= 3.0% limit.
    - Voltage drop strictly governs section up-sizing: LimitingConstraint.DU.
    """
    circuit = build_bench02_circuit()
    engine = SizingEngine()
    result: SizingResult = engine.size_circuit(circuit)

    spec = CANONICAL_BENCHMARK_CASES[1]
    assert_sizing_result_matches_benchmark(result, spec, tol=tolerance_config)


@pytest.mark.e2e
@pytest.mark.tier4
def test_bench_03_long_run_feeder_pumping(tolerance_config: ToleranceConfig) -> None:
    """
    BENCH-03: Long-Run Feeder Pumping 37kW 220m (Method C, XLPE, Cu, 220m).
    
    Verifies:
    - Ib = 37000 / (sqrt(3) * 400 * 0.85) = 62.83 A
    - In = 63 A
    - Thermally S=10.0 mm² is sufficient (I0=71 A >= 63 A), but dU=12.00% > 5.0%.
    - S=16.0 mm² yields dU=7.60% > 5.0%.
    - S=25.0 mm² satisfies dU=4.95% <= 5.0% (tight 0.05% margin).
    - Voltage drop strictly governs section selection: LimitingConstraint.DU.
    """
    circuit = build_bench03_circuit()
    engine = SizingEngine()
    result: SizingResult = engine.size_circuit(circuit)

    spec = CANONICAL_BENCHMARK_CASES[2]
    assert_sizing_result_matches_benchmark(result, spec, tol=tolerance_config)


@pytest.mark.e2e
@pytest.mark.tier4
def test_bench_04_multi_cable_grouping(tolerance_config: ToleranceConfig) -> None:
    """
    BENCH-04: Multi-Cable Grouping N=6 touching (Method E, XLPE, Cu, 30m).
    
    Verifies:
    - Ib = 22000 / (sqrt(3) * 400 * 0.85) = 37.36 A
    - In = 40 A
    - Grouping factor k2 = 0.73 (Table 52E, 6 circuits touching single layer on perforated tray)
    - Required base current I'z = 40 / 0.73 = 54.79 A
    - S=6.0 mm² fails: I0=54 A < 54.79 A, Iz=39.42 A < 40 A
    - S=10.0 mm² valid: I0=75 A >= 54.79 A, Iz=54.75 A >= 40 A
    - Limiting constraint: LimitingConstraint.IZ
    """
    circuit = build_bench04_circuit()
    engine = SizingEngine()
    result: SizingResult = engine.size_circuit(circuit)

    spec = CANONICAL_BENCHMARK_CASES[3]
    assert_sizing_result_matches_benchmark(result, spec, tol=tolerance_config)


@pytest.mark.e2e
@pytest.mark.tier4
def test_bench_05_high_ambient_temp(tolerance_config: ToleranceConfig) -> None:
    """
    BENCH-05: High Ambient Temp 50°C Plant (Method C, XLPE, Cu, 40m).
    
    Verifies:
    - Ib = 30000 / (sqrt(3) * 400 * 0.85) = 50.94 A
    - In = 63 A (50A breaker insufficient since 50.94 > 50)
    - Ambient temp factor k3 = 0.82 (Table 52D for XLPE at 50°C)
    - Required base current I'z = 63 / 0.82 = 76.83 A
    - S=10.0 mm² fails: I0=71 A < 76.83 A, Iz=58.22 A < 63 A
    - S=16.0 mm² valid: I0=96 A >= 76.83 A, Iz=78.72 A >= 63 A
    - Limiting constraint: LimitingConstraint.IZ
    """
    circuit = build_bench05_circuit()
    engine = SizingEngine()
    result: SizingResult = engine.size_circuit(circuit)

    spec = CANONICAL_BENCHMARK_CASES[4]
    assert_sizing_result_matches_benchmark(result, spec, tol=tolerance_config)


# ---------------------------------------------------------------------------
# Parameterized Test Across All 5 Benchmarks
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.tier4
@pytest.mark.parametrize(
    "case",
    CANONICAL_BENCHMARK_CASES,
    ids=[c["id"] for c in CANONICAL_BENCHMARK_CASES],
)
def test_all_canonical_ute_benchmarks_parameterized(
    case: dict[str, Any],
    tolerance_config: ToleranceConfig,
) -> None:
    """Unified parameterized execution of all 5 UTE C 15-105 worked benchmark scenarios."""
    circuit = case["builder"]()
    engine = SizingEngine()
    result: SizingResult = engine.size_circuit(circuit)

    assert_sizing_result_matches_benchmark(result, case, tol=tolerance_config)


# ---------------------------------------------------------------------------
# Specialized Constraint & Coordination Verifications
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_protection_coordination_inequality_across_benchmarks() -> None:
    """
    Verify fundamental normative coordination inequality across all 5 benchmarks:
    Ib <= In <= Iz
    """
    engine = SizingEngine()
    for case in CANONICAL_BENCHMARK_CASES:
        circuit = case["builder"]()
        result: SizingResult = engine.size_circuit(circuit)
        fields = extract_result_fields(result)

        ib = fields["ib"]
        in_rating = fields["protective_in"]
        iz = fields["iz"]

        assert ib is not None and in_rating is not None and iz is not None
        assert ib <= in_rating + 1e-4, f"{case['id']}: Ib ({ib}A) > In ({in_rating}A)"
        assert in_rating <= iz + 1e-4, f"{case['id']}: In ({in_rating}A) > Iz ({iz}A)"


@pytest.mark.e2e
def test_voltage_drop_compliance_across_benchmarks() -> None:
    """
    Verify that calculated voltage drop satisfies the maximum permissible threshold:
    dU% <= dU_max% for each circuit.
    """
    engine = SizingEngine()
    for case in CANONICAL_BENCHMARK_CASES:
        circuit = case["builder"]()
        result: SizingResult = engine.size_circuit(circuit)
        fields = extract_result_fields(result)

        du_pct = fields["du_pct"]
        max_du = circuit.max_voltage_drop_pct

        assert du_pct is not None
        assert du_pct <= max_du + 1e-4, (
            f"{case['id']}: dU% ({du_pct:.2f}%) exceeds max permissible {max_du}%"
        )
