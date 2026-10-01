"""
Verification tests for test harness integrity, fixtures, and numerical tolerance comparison helpers.

Validates that conftest.py helpers strictly enforce:
- Discrete exact matches
- Continuous tolerance constraints (Ib, Iz, dU, k_total)
- Mathematical consistency of canonical UTE C 15-105 worked benchmarks
"""

from dataclasses import dataclass
from typing import Any

import pytest

from tests.conftest import (
    ToleranceConfig,
    assert_continuous_match,
    assert_discrete_match,
    assert_sizing_result_matches_benchmark,
)


@dataclass
class MockVoltageDrop:
    delta_u_v: float
    delta_u_pct: float


@dataclass
class MockSizingResult:
    selected_section_mm2: float
    protective_device_in: float
    design_current_ib: float
    permissible_current_iz: float
    total_derating_factor: float
    voltage_drop: MockVoltageDrop
    limiting_constraint: str
    is_compliant: bool = True


def test_tolerance_config_defaults(tolerance_config: ToleranceConfig) -> None:
    """Verify standard tolerances match the precision requirements in TEST_INFRA.md."""
    assert tolerance_config.discrete_exact is True
    assert tolerance_config.ib_rel_tol <= 0.005
    assert tolerance_config.k_total_rel_tol <= 0.001
    assert tolerance_config.iz_abs_tol <= 0.2
    assert tolerance_config.du_v_rel_tol <= 0.005
    assert tolerance_config.du_pct_abs_tol <= 0.05


def test_discrete_match_helper() -> None:
    """Verify assert_discrete_match behavior."""
    assert_discrete_match(4.0, 4.0, "section")
    assert_discrete_match(32, 32, "in")
    assert_discrete_match("IZ", "IZ", "constraint")

    with pytest.raises(AssertionError, match="Discrete mismatch for 'section'"):
        assert_discrete_match(2.5, 4.0, "section")


def test_continuous_match_helper() -> None:
    """Verify assert_continuous_match behavior."""
    # Within 0.5% relative tolerance
    assert_continuous_match(31.414, 31.41, rel_tol=0.005, field_name="ib")
    # Outside 0.5% tolerance
    with pytest.raises(AssertionError, match="Continuous tolerance violation for 'ib'"):
        assert_continuous_match(33.0, 31.41, rel_tol=0.005, field_name="ib")

    # Within 0.05 absolute tolerance
    assert_continuous_match(3.03, 3.05, abs_tol=0.05, field_name="du_pct")
    # Outside 0.05 absolute tolerance
    with pytest.raises(AssertionError, match="Continuous tolerance violation for 'du_pct'"):
        assert_continuous_match(3.20, 3.03, abs_tol=0.05, field_name="du_pct")


def test_canonical_benchmarks_specs_internal_consistency(
    ute_benchmarks_specs: dict[str, dict[str, Any]],
) -> None:
    """Verify all 5 canonical benchmark specs satisfy fundamental normative inequalities."""
    expected_ids = ["BENCH-01", "BENCH-02", "BENCH-03", "BENCH-04", "BENCH-05"]
    assert list(ute_benchmarks_specs.keys()) == expected_ids

    for bench_id, spec in ute_benchmarks_specs.items():
        ib = spec["expected_ib"]
        in_rating = spec["expected_in"]
        iz = spec["expected_iz"]
        k1 = spec["expected_k1"]
        k2 = spec["expected_k2"]
        k3 = spec["expected_k3"]
        k_total = spec["expected_k_total"]
        du_pct = spec["expected_du_pct"]
        max_du = spec["circuit_raw"]["max_voltage_drop_pct"]

        # Normative coordination rule: Ib <= In <= Iz
        assert ib <= in_rating, f"{bench_id}: Ib ({ib}) > In ({in_rating})"
        assert in_rating <= iz, f"{bench_id}: In ({in_rating}) > Iz ({iz})"

        # Derating product rule: k_total = k1 * k2 * k3
        assert pytest.approx(k1 * k2 * k3, rel=1e-3) == k_total

        # Voltage drop limit rule: dU% <= max_dU%
        assert du_pct <= max_du, f"{bench_id}: dU% ({du_pct}) > max ({max_du})"


def test_harness_benchmark_verification_with_mock_results(
    ute_benchmarks_specs: dict[str, dict[str, Any]],
    tolerance_config: ToleranceConfig,
) -> None:
    """Verify assert_sizing_result_matches_benchmark passes when engine produces exact targets."""
    for spec in ute_benchmarks_specs.values():
        vd = MockVoltageDrop(
            delta_u_v=spec["expected_du_v"],
            delta_u_pct=spec["expected_du_pct"],
        )
        res = MockSizingResult(
            selected_section_mm2=spec["expected_section"],
            protective_device_in=spec["expected_in"],
            design_current_ib=spec["expected_ib"],
            permissible_current_iz=spec["expected_iz"],
            total_derating_factor=spec["expected_k_total"],
            voltage_drop=vd,
            limiting_constraint=spec["expected_constraint"],
        )
        assert_sizing_result_matches_benchmark(res, spec, tol=tolerance_config)


def test_harness_detects_coordination_and_section_violations(
    bench01_spec: dict[str, Any],
    tolerance_config: ToleranceConfig,
) -> None:
    """Verify test harness detects coordination and section errors."""
    valid_res = MockSizingResult(
        selected_section_mm2=bench01_spec["expected_section"],
        protective_device_in=bench01_spec["expected_in"],
        design_current_ib=bench01_spec["expected_ib"],
        permissible_current_iz=bench01_spec["expected_iz"],
        total_derating_factor=bench01_spec["expected_k_total"],
        voltage_drop=MockVoltageDrop(
            bench01_spec["expected_du_v"],
            bench01_spec["expected_du_pct"],
        ),
        limiting_constraint=bench01_spec["expected_constraint"],
    )

    # 1. Section undersized
    invalid_res = MockSizingResult(
        selected_section_mm2=2.5,
        protective_device_in=valid_res.protective_device_in,
        design_current_ib=valid_res.design_current_ib,
        permissible_current_iz=valid_res.permissible_current_iz,
        total_derating_factor=valid_res.total_derating_factor,
        voltage_drop=valid_res.voltage_drop,
        limiting_constraint=valid_res.limiting_constraint,
    )
    with pytest.raises(AssertionError, match="Discrete mismatch for 'BENCH-01.selected_section_mm2'"):
        assert_sizing_result_matches_benchmark(invalid_res, bench01_spec, tol=tolerance_config)

    # 2. Coordination violation (In > Iz)
    invalid_res2 = MockSizingResult(
        selected_section_mm2=valid_res.selected_section_mm2,
        protective_device_in=valid_res.protective_device_in,
        design_current_ib=valid_res.design_current_ib,
        permissible_current_iz=30.0,  # Below In=32
        total_derating_factor=valid_res.total_derating_factor,
        voltage_drop=valid_res.voltage_drop,
        limiting_constraint=valid_res.limiting_constraint,
    )
    with pytest.raises(AssertionError):
        assert_sizing_result_matches_benchmark(invalid_res2, bench01_spec, tol=tolerance_config)
