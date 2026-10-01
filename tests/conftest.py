"""
Pytest configuration, shared fixtures, and numerical tolerance comparison helpers.

Conforming strictly to:
- NF C 15-100 (Part 5-52)
- UTE C 15-105 (Guide pratique de calcul)
- TEST_INFRA.md and benchmarks specification
"""

import math
from dataclasses import dataclass
from typing import Any

import pytest


# Register standard pytest markers
def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line("markers", "tier1: Unit tests for pure formulas and tables")
    config.addinivalue_line("markers", "tier2: Boundary, corner cases, and stress tests")
    config.addinivalue_line("markers", "tier3: Combinatorial pairwise test matrix")
    config.addinivalue_line("markers", "tier4: Canonical UTE C 15-105 worked benchmark scenarios")
    config.addinivalue_line("markers", "e2e: End-to-end integration and benchmark tests")
    config.addinivalue_line("markers", "cli: Command-line interface tests")


@dataclass(frozen=True)
class ToleranceConfig:
    """
    Standard numerical tolerances for continuous electrical parameters.
    
    Discrete normative values (S, In, constraint) are checked with exact equality (tolerance = 0.0).
    Continuous physical parameters (Ib, Iz, dU, k_total) are checked with strict relative/absolute tolerances.
    """
    discrete_exact: bool = True
    ib_rel_tol: float = 0.005        # <= 0.5% relative tolerance on design current Ib
    k_total_rel_tol: float = 0.001   # <= 0.1% relative tolerance on total derating factor
    iz_abs_tol: float = 0.2          # <= 0.2 A absolute tolerance on permissible current Iz
    iz_rel_tol: float = 0.005        # <= 0.5% relative tolerance on Iz
    du_v_rel_tol: float = 0.005      # <= 0.5% relative tolerance on voltage drop in Volts
    du_pct_abs_tol: float = 0.05     # <= 0.05% absolute tolerance on relative voltage drop %


def assert_discrete_match(actual: Any, expected: Any, field_name: str = "") -> None:
    """Assert exact equality for discrete normative values."""
    assert actual == expected, (
        f"Discrete mismatch for '{field_name}': expected {expected!r}, got {actual!r}"
    )


def assert_continuous_match(
    actual: float,
    expected: float,
    rel_tol: float | None = None,
    abs_tol: float | None = None,
    field_name: str = "",
) -> None:
    """Assert floating point value is close to expected value within specified tolerance."""
    kwargs: dict[str, float] = {}
    if rel_tol is not None:
        kwargs["rel_tol"] = rel_tol
    if abs_tol is not None:
        kwargs["abs_tol"] = abs_tol

    assert math.isclose(actual, expected, **kwargs), (
        f"Continuous tolerance violation for '{field_name}': "
        f"expected {expected}, got {actual} (rel_tol={rel_tol}, abs_tol={abs_tol}, "
        f"diff={abs(actual - expected)})"
    )


def extract_result_fields(result: Any) -> dict[str, Any]:
    """
    Extract normalized sizing metrics from SizingResult supporting both direct attributes
    and nested sub-objects (e.g. result.voltage_drop.delta_u_v).
    """
    extracted: dict[str, Any] = {}

    # Selected Section S (mm²)
    extracted["section_mm2"] = getattr(
        result, "selected_section_mm2", getattr(result, "section_mm2", None)
    )

    # Protective device nominal rating In (A)
    extracted["protective_in"] = getattr(
        result,
        "protective_device_in",
        getattr(result, "in_a", getattr(result, "protective_in", None)),
    )

    # Design operating current Ib (A)
    extracted["ib"] = getattr(
        result, "design_current_ib", getattr(result, "ib_a", getattr(result, "ib", None))
    )

    # Permissible current Iz (A)
    extracted["iz"] = getattr(
        result, "permissible_current_iz", getattr(result, "iz_a", getattr(result, "iz", None))
    )

    # Total derating factor k_total
    k_tot = getattr(result, "total_derating_factor", getattr(result, "k_total", None))
    if k_tot is None and hasattr(result, "intermediate_factors"):
        k_tot = getattr(result.intermediate_factors, "k_total", None)
    extracted["k_total"] = k_tot

    # Voltage drop in Volts (V)
    du_v = getattr(result, "voltage_drop_v", getattr(result, "du_v", None))
    if du_v is None and hasattr(result, "voltage_drop"):
        vd = result.voltage_drop
        du_v = getattr(vd, "delta_u_v", getattr(vd, "voltage_drop_v", getattr(vd, "du_v", None)))
    extracted["du_v"] = du_v

    # Voltage drop in percent (%)
    du_pct = getattr(result, "voltage_drop_pct", getattr(result, "du_pct", None))
    if du_pct is None and hasattr(result, "voltage_drop"):
        vd = result.voltage_drop
        du_pct = getattr(
            vd, "delta_u_pct", getattr(vd, "voltage_drop_pct", getattr(vd, "du_pct", None))
        )
    extracted["du_pct"] = du_pct

    # Limiting constraint
    extracted["limiting_constraint"] = getattr(result, "limiting_constraint", None)

    # Compliance flag
    extracted["is_compliant"] = getattr(result, "is_compliant", True)

    return extracted


def assert_sizing_result_matches_benchmark(
    result: Any,
    benchmark_spec: dict[str, Any],
    tol: ToleranceConfig | None = None,
) -> None:
    """
    Authoritative benchmark verification helper.
    
    Validates:
    1. Discrete matches (S mm², In A, limiting constraint).
    2. Continuous physical values within tolerance (Ib, Iz, dU V, dU %, k_total).
    3. Normative coordination condition: Ib <= In <= Iz.
    4. Normative voltage drop condition: dU% <= max_dU%.
    """
    if tol is None:
        tol = ToleranceConfig()

    bench_id = benchmark_spec.get("id", "BENCH")
    fields = extract_result_fields(result)

    # 1. Exact Discrete Sizing Section
    expected_section = benchmark_spec["expected_section"]
    assert_discrete_match(
        fields["section_mm2"],
        expected_section,
        field_name=f"{bench_id}.selected_section_mm2",
    )

    # 2. Exact Protective Device Rating In
    expected_in = benchmark_spec["expected_in"]
    assert_discrete_match(
        fields["protective_in"],
        expected_in,
        field_name=f"{bench_id}.protective_device_in",
    )

    # 3. Limiting Constraint
    expected_constraint = benchmark_spec.get("expected_constraint")
    if expected_constraint is not None and fields["limiting_constraint"] is not None:
        actual_val = (
            fields["limiting_constraint"].value
            if hasattr(fields["limiting_constraint"], "value")
            else str(fields["limiting_constraint"])
        )
        expected_val = (
            expected_constraint.value
            if hasattr(expected_constraint, "value")
            else str(expected_constraint)
        )
        assert actual_val == expected_val, (
            f"Constraint mismatch for {bench_id}: expected {expected_val}, got {actual_val}"
        )

    # 4. Continuous Engineering Quantities
    # Design Current Ib
    if "expected_ib" in benchmark_spec and fields["ib"] is not None:
        assert_continuous_match(
            actual=float(fields["ib"]),
            expected=float(benchmark_spec["expected_ib"]),
            rel_tol=tol.ib_rel_tol,
            field_name=f"{bench_id}.design_current_ib",
        )

    # Derating Factor k_total
    if "expected_k_total" in benchmark_spec and fields["k_total"] is not None:
        assert_continuous_match(
            actual=float(fields["k_total"]),
            expected=float(benchmark_spec["expected_k_total"]),
            rel_tol=tol.k_total_rel_tol,
            field_name=f"{bench_id}.total_derating_factor",
        )

    # Permissible Current Iz
    if "expected_iz" in benchmark_spec and fields["iz"] is not None:
        assert_continuous_match(
            actual=float(fields["iz"]),
            expected=float(benchmark_spec["expected_iz"]),
            abs_tol=tol.iz_abs_tol,
            field_name=f"{bench_id}.permissible_current_iz",
        )

    # Voltage Drop in Volts
    if "expected_du_v" in benchmark_spec and fields["du_v"] is not None:
        assert_continuous_match(
            actual=float(fields["du_v"]),
            expected=float(benchmark_spec["expected_du_v"]),
            rel_tol=tol.du_v_rel_tol,
            field_name=f"{bench_id}.voltage_drop_v",
        )

    # Relative Voltage Drop in %
    if "expected_du_pct" in benchmark_spec and fields["du_pct"] is not None:
        assert_continuous_match(
            actual=float(fields["du_pct"]),
            expected=float(benchmark_spec["expected_du_pct"]),
            abs_tol=tol.du_pct_abs_tol,
            field_name=f"{bench_id}.voltage_drop_pct",
        )

    # 5. Fundamental Normative Inequalities
    # Ib <= In <= Iz
    if fields["ib"] is not None and fields["protective_in"] is not None:
        assert fields["ib"] <= fields["protective_in"] + 1e-4, (
            f"{bench_id}: Coordination violation Ib ({fields['ib']:.2f}A) > "
            f"In ({fields['protective_in']}A)"
        )
    if fields["protective_in"] is not None and fields["iz"] is not None:
        assert fields["protective_in"] <= fields["iz"] + 1e-4, (
            f"{bench_id}: Coordination violation In ({fields['protective_in']}A) > "
            f"Iz ({fields['iz']:.2f}A)"
        )

    # Voltage Drop Compliance dU% <= max_dU%
    max_du = benchmark_spec.get("circuit_raw", {}).get("max_voltage_drop_pct", 5.0)
    if fields["du_pct"] is not None:
        assert fields["du_pct"] <= max_du + 1e-4, (
            f"{bench_id}: Voltage drop limit exceeded: dU%={fields['du_pct']:.2f}% > "
            f"max_dU%={max_du}%"
        )

    # Compliance flag
    assert fields["is_compliant"] is True, f"{bench_id}: SizingResult marked non-compliant"


# Canonical UTE C 15-105 worked benchmark raw specifications
UTE_BENCHMARKS_SPECS: dict[str, dict[str, Any]] = {
    "BENCH-01": {
        "id": "BENCH-01",
        "description": "Standard 3P Motor 18.5kW (Method E, XLPE, Cu, 45m)",
        "circuit_raw": {
            "name": "Industrial Motor 18.5kW",
            "active_power_kw": 18.5,
            "voltage_v": 400.0,
            "phases": "3P",
            "cos_phi": 0.85,
            "length_m": 45.0,
            "installation_method": "E",
            "conductor_material": "Cu",
            "insulation_type": "XLPE",
            "ambient_temp_c": 30.0,
            "grouping_circuits": 1,
            "max_voltage_drop_pct": 5.0,
        },
        "expected_ib": 31.41,
        "expected_in": 32,
        "expected_k1": 1.00,
        "expected_k2": 1.00,
        "expected_k3": 1.00,
        "expected_k_total": 1.0000,
        "expected_iz_prime": 32.00,
        "expected_section": 4.0,
        "expected_i0": 42.0,
        "expected_iz": 42.00,
        "expected_du_v": 6.969,
        "expected_du_pct": 3.03,
        "expected_constraint": "IZ",
    },
    "BENCH-02": {
        "id": "BENCH-02",
        "description": "1P Commercial Lighting 3.68kW (Method B, PVC, Cu, 35m)",
        "circuit_raw": {
            "name": "Lighting Sub-Distribution 3.68kW",
            "active_power_kw": 3.68,
            "voltage_v": 230.0,
            "phases": "1P",
            "cos_phi": 1.00,
            "length_m": 35.0,
            "installation_method": "B",
            "conductor_material": "Cu",
            "insulation_type": "PVC",
            "ambient_temp_c": 30.0,
            "grouping_circuits": 1,
            "max_voltage_drop_pct": 3.0,
        },
        "expected_ib": 16.00,
        "expected_in": 16,
        "expected_k1": 1.00,
        "expected_k2": 1.00,
        "expected_k3": 1.00,
        "expected_k_total": 1.0000,
        "expected_iz_prime": 16.00,
        "expected_section": 4.0,
        "expected_i0": 32.0,
        "expected_iz": 32.00,
        "expected_du_v": 6.440,
        "expected_du_pct": 2.80,
        "expected_constraint": "DU",
    },
    "BENCH-03": {
        "id": "BENCH-03",
        "description": "Long-Run Feeder Pumping 37kW (Method C, XLPE, Cu, 220m)",
        "circuit_raw": {
            "name": "Pumping Station Feeder 37kW 220m",
            "active_power_kw": 37.0,
            "voltage_v": 400.0,
            "phases": "3P",
            "cos_phi": 0.85,
            "length_m": 220.0,
            "installation_method": "C",
            "conductor_material": "Cu",
            "insulation_type": "XLPE",
            "ambient_temp_c": 30.0,
            "grouping_circuits": 1,
            "max_voltage_drop_pct": 5.0,
        },
        "expected_ib": 62.83,
        "expected_in": 63,
        "expected_k1": 1.00,
        "expected_k2": 1.00,
        "expected_k3": 1.00,
        "expected_k_total": 1.0000,
        "expected_iz_prime": 63.00,
        "expected_section": 25.0,
        "expected_i0": 119.0,
        "expected_iz": 119.00,
        "expected_du_v": 11.392,
        "expected_du_pct": 4.95,
        "expected_constraint": "DU",
    },
    "BENCH-04": {
        "id": "BENCH-04",
        "description": "Multi-Cable Grouping N=6 touching (Method E, XLPE, Cu, 30m)",
        "circuit_raw": {
            "name": "Grouping Gallery 22kW N=6",
            "active_power_kw": 22.0,
            "voltage_v": 400.0,
            "phases": "3P",
            "cos_phi": 0.85,
            "length_m": 30.0,
            "installation_method": "E",
            "conductor_material": "Cu",
            "insulation_type": "XLPE",
            "ambient_temp_c": 30.0,
            "grouping_circuits": 6,
            "max_voltage_drop_pct": 5.0,
        },
        "expected_ib": 37.36,
        "expected_in": 40,
        "expected_k1": 1.00,
        "expected_k2": 0.73,
        "expected_k3": 1.00,
        "expected_k_total": 0.7300,
        "expected_iz_prime": 54.79,
        "expected_section": 10.0,
        "expected_i0": 75.0,
        "expected_iz": 54.75,
        "expected_du_v": 2.238,
        "expected_du_pct": 0.97,
        "expected_constraint": "IZ",
    },
    "BENCH-05": {
        "id": "BENCH-05",
        "description": "High Ambient Temp 50°C Plant (Method C, XLPE, Cu, 40m)",
        "circuit_raw": {
            "name": "Thermal Boiler Pump 30kW 50C",
            "active_power_kw": 30.0,
            "voltage_v": 400.0,
            "phases": "3P",
            "cos_phi": 0.85,
            "length_m": 40.0,
            "installation_method": "C",
            "conductor_material": "Cu",
            "insulation_type": "XLPE",
            "ambient_temp_c": 50.0,
            "grouping_circuits": 1,
            "max_voltage_drop_pct": 5.0,
        },
        "expected_ib": 50.94,
        "expected_in": 63,
        "expected_k1": 1.00,
        "expected_k2": 1.00,
        "expected_k3": 0.82,
        "expected_k_total": 0.8200,
        "expected_iz_prime": 76.83,
        "expected_section": 16.0,
        "expected_i0": 96.0,
        "expected_iz": 78.72,
        "expected_du_v": 2.576,
        "expected_du_pct": 1.12,
        "expected_constraint": "IZ",
    },
}


@pytest.fixture
def tolerance_config() -> ToleranceConfig:
    """Fixture providing standard engineering tolerances."""
    return ToleranceConfig()


@pytest.fixture
def ute_benchmarks_specs() -> dict[str, dict[str, Any]]:
    """Fixture returning raw benchmark specifications for all 5 canonical scenarios."""
    return UTE_BENCHMARKS_SPECS


@pytest.fixture
def bench01_spec() -> dict[str, Any]:
    return UTE_BENCHMARKS_SPECS["BENCH-01"]


@pytest.fixture
def bench02_spec() -> dict[str, Any]:
    return UTE_BENCHMARKS_SPECS["BENCH-02"]


@pytest.fixture
def bench03_spec() -> dict[str, Any]:
    return UTE_BENCHMARKS_SPECS["BENCH-03"]


@pytest.fixture
def bench04_spec() -> dict[str, Any]:
    return UTE_BENCHMARKS_SPECS["BENCH-04"]


@pytest.fixture
def bench05_spec() -> dict[str, Any]:
    return UTE_BENCHMARKS_SPECS["BENCH-05"]
