"""
tests/adversarial_challenge_models.py
======================================
Standalone adversarial challenge test suite for `ampy.core.models`.
Designed to aggressively stress-test validation boundaries, edge cases,
type safety, immutability, extra-field forbidding, and JSON serialization fidelity.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from typing import Any

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


@dataclass
class TestResult:
    category: str
    name: str
    passed: bool
    status: str  # "BLOCKED_AS_EXPECTED", "VULNERABILITY_FOUND", "UNEXPECTED_ERROR", "CONFIRMED_ROBUST"
    detail: str


class AdversarialModelChallenger:
    def __init__(self) -> None:
        self.results: list[TestResult] = []

    def record(self, category: str, name: str, passed: bool, status: str, detail: str) -> None:
        self.results.append(TestResult(category, name, passed, status, detail))

    # =========================================================================
    # Suite 1: Multi-Load Confusion & Load Boundary Attacks
    # =========================================================================
    def challenge_multi_load_confusion(self) -> None:
        cat = "Multi-Load Confusion"

        # 1.1 No load parameters provided
        try:
            ElectricalLoad(voltage_v=230.0)
            self.record(cat, "No load parameters", False, "VULNERABILITY_FOUND", "Instantiated without any load parameter!")
        except (ValidationError, ValueError) as e:
            self.record(cat, "No load parameters", True, "BLOCKED_AS_EXPECTED", f"Correctly blocked: {type(e).__name__}")

        # 1.2 All load parameters explicitly None
        try:
            ElectricalLoad(voltage_v=230.0, power_kw=None, apparent_power_kva=None, current_a=None)
            self.record(cat, "All load parameters None", False, "VULNERABILITY_FOUND", "Instantiated with all load parameters as None!")
        except (ValidationError, ValueError) as e:
            self.record(cat, "All load parameters None", True, "BLOCKED_AS_EXPECTED", f"Correctly blocked: {type(e).__name__}")

        # 1.3 Two load parameters: power_kw AND current_a
        try:
            ElectricalLoad(voltage_v=400.0, power_kw=15.0, current_a=25.0)
            self.record(cat, "Conflicting power_kw + current_a", False, "VULNERABILITY_FOUND", "Allowed both power_kw and current_a simultaneously!")
        except (ValidationError, ValueError) as e:
            self.record(cat, "Conflicting power_kw + current_a", True, "BLOCKED_AS_EXPECTED", f"Correctly blocked: {type(e).__name__}")

        # 1.4 Two load parameters: power_kw AND apparent_power_kva
        try:
            ElectricalLoad(voltage_v=400.0, power_kw=15.0, apparent_power_kva=20.0)
            self.record(cat, "Conflicting power_kw + apparent_power_kva", False, "VULNERABILITY_FOUND", "Allowed both power_kw and apparent_power_kva!")
        except (ValidationError, ValueError) as e:
            self.record(cat, "Conflicting power_kw + apparent_power_kva", True, "BLOCKED_AS_EXPECTED", f"Correctly blocked: {type(e).__name__}")

        # 1.5 Two load parameters: apparent_power_kva AND current_a
        try:
            ElectricalLoad(voltage_v=400.0, apparent_power_kva=20.0, current_a=25.0)
            self.record(cat, "Conflicting apparent_power_kva + current_a", False, "VULNERABILITY_FOUND", "Allowed both apparent_power_kva and current_a!")
        except (ValidationError, ValueError) as e:
            self.record(cat, "Conflicting apparent_power_kva + current_a", True, "BLOCKED_AS_EXPECTED", f"Correctly blocked: {type(e).__name__}")

        # 1.6 All three load parameters provided
        try:
            ElectricalLoad(voltage_v=400.0, power_kw=15.0, apparent_power_kva=20.0, current_a=25.0)
            self.record(cat, "All 3 load parameters provided", False, "VULNERABILITY_FOUND", "Allowed all three load parameters simultaneously!")
        except (ValidationError, ValueError) as e:
            self.record(cat, "All 3 load parameters provided", True, "BLOCKED_AS_EXPECTED", f"Correctly blocked: {type(e).__name__}")

        # 1.7 Alias injection: power_kw AND active_power_kw in dict
        try:
            ElectricalLoad.model_validate({"voltage_v": 400.0, "power_kw": 10.0, "active_power_kw": 15.0})
            self.record(cat, "Alias collision power_kw + active_power_kw", False, "VULNERABILITY_FOUND", "Accepted colliding field and alias!")
        except ValidationError as e:
            self.record(cat, "Alias collision power_kw + active_power_kw", True, "BLOCKED_AS_EXPECTED", "Rejected as extra_forbidden")

        # 1.8 Zero and negative loads
        for param, val in [("power_kw", 0.0), ("power_kw", -5.0), ("apparent_power_kva", 0.0), ("apparent_power_kva", -5.0), ("current_a", 0.0), ("current_a", -5.0)]:
            try:
                ElectricalLoad(**{"voltage_v": 230.0, param: val})
                self.record(cat, f"Non-positive load {param}={val}", False, "VULNERABILITY_FOUND", f"Accepted {param}={val}!")
            except ValidationError:
                self.record(cat, f"Non-positive load {param}={val}", True, "BLOCKED_AS_EXPECTED", f"Blocked non-positive {param}")

    # =========================================================================
    # Suite 2: Invalid Types, Strings in Numeric Fields, NaN and Inf Values
    # =========================================================================
    def challenge_numeric_extremes_and_types(self) -> None:
        cat = "Numeric Extremes & Types"

        # 2.1 String in numeric field
        for field, bad_str in [("voltage_v", "two-hundred-thirty"), ("power_kw", "10kW"), ("length_m", "50m")]:
            try:
                if field == "length_m":
                    CableSpecs(length_m=bad_str)  # type: ignore
                else:
                    ElectricalLoad(**{"voltage_v": 230.0, "power_kw": 10.0, field: bad_str})
                self.record(cat, f"String in numeric field {field}='{bad_str}'", False, "VULNERABILITY_FOUND", "Accepted arbitrary string!")
            except ValidationError:
                self.record(cat, f"String in numeric field {field}='{bad_str}'", True, "BLOCKED_AS_EXPECTED", "Correctly rejected non-numeric string")

        # 2.2 Boolean coercion attack (True == 1.0)
        try:
            load_bool = ElectricalLoad(voltage_v=True, power_kw=True)  # type: ignore
            self.record(cat, "Boolean coercion (True passed as float)", False, "VULNERABILITY_FOUND", f"Silently coerced bool True to float: voltage_v={load_bool.voltage_v}, power_kw={load_bool.power_kw}")
        except ValidationError:
            self.record(cat, "Boolean coercion (True passed as float)", True, "BLOCKED_AS_EXPECTED", "Blocked boolean value")

        # 2.3 NaN in float fields
        for field, model_cls, kwargs in [
            ("voltage_v", ElectricalLoad, {"voltage_v": float("nan"), "power_kw": 10.0}),
            ("power_kw", ElectricalLoad, {"voltage_v": 230.0, "power_kw": float("nan")}),
            ("length_m", CableSpecs, {"length_m": float("nan")}),
        ]:
            try:
                obj = model_cls(**kwargs)
                self.record(cat, f"NaN in {field}", False, "VULNERABILITY_FOUND", f"Accepted NaN in {field}!")
            except ValidationError:
                self.record(cat, f"NaN in {field}", True, "BLOCKED_AS_EXPECTED", f"Correctly blocked NaN in {field}")

        # 2.4 Positive Infinity (float('inf')) in float fields with gt=0.0
        inf_targets = [
            ("voltage_v", ElectricalLoad, {"voltage_v": float("inf"), "power_kw": 10.0}),
            ("power_kw", ElectricalLoad, {"voltage_v": 230.0, "power_kw": float("inf")}),
            ("apparent_power_kva", ElectricalLoad, {"voltage_v": 230.0, "apparent_power_kva": float("inf")}),
            ("current_a", ElectricalLoad, {"voltage_v": 230.0, "current_a": float("inf")}),
            ("frequency_hz", ElectricalLoad, {"voltage_v": 230.0, "power_kw": 10.0, "frequency_hz": float("inf")}),
            ("length_m", CableSpecs, {"length_m": float("inf")}),
            ("in_a", ProtectionDevice, {"in_a": float("inf")}),
            ("ik_a", ProtectionDevice, {"ik_a": float("inf")}),
        ]
        for field, model_cls, kwargs in inf_targets:
            try:
                obj = model_cls(**kwargs)
                self.record(cat, f"Positive Inf in {field}", False, "VULNERABILITY_FOUND", f"Field(gt=0.0) allowed float('inf') without finiteness check! Object: {obj}")
            except ValidationError:
                self.record(cat, f"Positive Inf in {field}", True, "BLOCKED_AS_EXPECTED", f"Blocked Inf in {field}")

        # 2.5 String 'inf' / 'Infinity' parsed into float('inf')
        try:
            load_str_inf = ElectricalLoad(voltage_v="inf", power_kw=10.0)  # type: ignore
            self.record(cat, "String 'inf' coercion", False, "VULNERABILITY_FOUND", f"Parsed string 'inf' into float('inf'): voltage_v={load_str_inf.voltage_v}")
        except ValidationError:
            self.record(cat, "String 'inf' coercion", True, "BLOCKED_AS_EXPECTED", "Blocked string 'inf'")

        # 2.6 Negative Infinity (float('-inf'))
        try:
            ElectricalLoad(voltage_v=float("-inf"), power_kw=10.0)
            self.record(cat, "Negative Inf in voltage_v", False, "VULNERABILITY_FOUND", "Allowed -inf in voltage_v!")
        except ValidationError:
            self.record(cat, "Negative Inf in voltage_v", True, "BLOCKED_AS_EXPECTED", "Blocked -inf due to gt=0.0")

    # =========================================================================
    # Suite 3: In-Place Mutation of Models (frozen=True vs frozen=False)
    # =========================================================================
    def challenge_model_immutability(self) -> None:
        cat = "Model Immutability"

        # 3.1 Sub-models immutability
        load = ElectricalLoad(voltage_v=230.0, power_kw=3.68)
        try:
            load.voltage_v = 400.0  # type: ignore
            self.record(cat, "ElectricalLoad direct mutation", False, "VULNERABILITY_FOUND", "ElectricalLoad is mutable!")
        except (ValidationError, TypeError):
            self.record(cat, "ElectricalLoad direct mutation", True, "BLOCKED_AS_EXPECTED", "Frozen: direct assignment blocked")

        cable = CableSpecs(length_m=50.0)
        try:
            cable.length_m = 100.0  # type: ignore
            self.record(cat, "CableSpecs direct mutation", False, "VULNERABILITY_FOUND", "CableSpecs is mutable!")
        except (ValidationError, TypeError):
            self.record(cat, "CableSpecs direct mutation", True, "BLOCKED_AS_EXPECTED", "Frozen: direct assignment blocked")

        inst = InstallationConditions()
        try:
            inst.ambient_temp_c = 45.0  # type: ignore
            self.record(cat, "InstallationConditions direct mutation", False, "VULNERABILITY_FOUND", "InstallationConditions is mutable!")
        except (ValidationError, TypeError):
            self.record(cat, "InstallationConditions direct mutation", True, "BLOCKED_AS_EXPECTED", "Frozen: direct assignment blocked")

        prot = ProtectionDevice(in_a=16.0)
        try:
            prot.in_a = 32.0  # type: ignore
            self.record(cat, "ProtectionDevice direct mutation", False, "VULNERABILITY_FOUND", "ProtectionDevice is mutable!")
        except (ValidationError, TypeError):
            self.record(cat, "ProtectionDevice direct mutation", True, "BLOCKED_AS_EXPECTED", "Frozen: direct assignment blocked")

        vd = VoltageDropResult(du_volts=5.0, du_percent=2.0, du_max_percent=5.0, is_compliant=True, margin_percent=3.0)
        try:
            vd.du_volts = 15.0  # type: ignore
            self.record(cat, "VoltageDropResult direct mutation", False, "VULNERABILITY_FOUND", "VoltageDropResult is mutable!")
        except (ValidationError, TypeError):
            self.record(cat, "VoltageDropResult direct mutation", True, "BLOCKED_AS_EXPECTED", "Frozen: direct assignment blocked")

        # 3.2 CircuitDefinition immutability challenge: is frozen=True set on CircuitDefinition?
        circuit = CircuitDefinition(
            name="Circuit_Mutation_Target",
            load=load,
            cable=cable,
            du_max_percent=3.0,
        )
        try:
            circuit.du_max_percent = -999.0  # Mutating to an invalid negative value!
            self.record(
                cat,
                "CircuitDefinition direct mutation (frozen=True missing)",
                False,
                "VULNERABILITY_FOUND",
                f"CircuitDefinition is NOT frozen! Mutated du_max_percent to invalid negative value: {circuit.du_max_percent} without validation!",
            )
        except (ValidationError, TypeError):
            self.record(cat, "CircuitDefinition direct mutation (frozen=True missing)", True, "BLOCKED_AS_EXPECTED", "CircuitDefinition blocked mutation")

        try:
            circuit.name = 12345  # type: ignore
            self.record(
                cat,
                "CircuitDefinition type bypass via mutation",
                False,
                "VULNERABILITY_FOUND",
                f"Bypassed type contract via mutation! circuit.name became int: {circuit.name}",
            )
        except (ValidationError, TypeError):
            self.record(cat, "CircuitDefinition type bypass via mutation", True, "BLOCKED_AS_EXPECTED", "Blocked type bypass")

    # =========================================================================
    # Suite 4: Undeclared Extra Fields (extra='forbid')
    # =========================================================================
    def challenge_extra_fields(self) -> None:
        cat = "Extra Fields Handling"

        # 4.1 Input models with extra fields
        for model_cls, kwargs, name in [
            (ElectricalLoad, {"voltage_v": 230.0, "power_kw": 3.0, "unauthorized_extra": 123}, "ElectricalLoad extra field"),
            (CableSpecs, {"length_m": 25.0, "hacked_param": True}, "CableSpecs extra field"),
            (InstallationConditions, {"bypass_flag": "enabled"}, "InstallationConditions extra field"),
            (ProtectionDevice, {"backdoor": True}, "ProtectionDevice extra field"),
            (CircuitDefinition, {
                "name": "Exploit",
                "load": ElectricalLoad(voltage_v=230.0, power_kw=3.0),
                "cable": CableSpecs(length_m=25.0),
                "malicious_extra": 42
            }, "CircuitDefinition extra field"),
        ]:
            try:
                model_cls(**kwargs)  # type: ignore
                self.record(cat, name, False, "VULNERABILITY_FOUND", f"{model_cls.__name__} accepted undeclared extra field!")
            except ValidationError:
                self.record(cat, name, True, "BLOCKED_AS_EXPECTED", f"Correctly blocked: extra_forbidden")

        # 4.2 Output models extra fields: do they enforce extra='forbid'?
        factors_kwargs = {
            "k1_method": 1.0, "k2_grouping": 1.0, "k3_temperature": 1.0, "k_total": 1.0,
            "rho_ohm_mm2_m": 0.023, "reactance_ohm_m": 0.0, "cos_phi": 0.85, "sin_phi": 0.5268,
            "undeclared_output_field": 999.9,
        }
        try:
            factors = IntermediateFactors(**factors_kwargs)  # type: ignore
            self.record(
                cat,
                "IntermediateFactors extra field",
                False,
                "VULNERABILITY_FOUND",
                f"IntermediateFactors omits extra='forbid'! Silently accepted/ignored undeclared extra fields.",
            )
        except ValidationError:
            self.record(cat, "IntermediateFactors extra field", True, "BLOCKED_AS_EXPECTED", "IntermediateFactors blocked extra field")

        vd_kwargs = {
            "du_volts": 5.0, "du_percent": 2.0, "du_max_percent": 5.0, "is_compliant": True,
            "margin_percent": 3.0, "unauthorized_metadata": "leak",
        }
        try:
            vd = VoltageDropResult(**vd_kwargs)  # type: ignore
            self.record(
                cat,
                "VoltageDropResult extra field",
                False,
                "VULNERABILITY_FOUND",
                f"VoltageDropResult omits extra='forbid'! Silently accepted/ignored undeclared extra fields.",
            )
        except ValidationError:
            self.record(cat, "VoltageDropResult extra field", True, "BLOCKED_AS_EXPECTED", "VoltageDropResult blocked extra field")

    # =========================================================================
    # Suite 5: JSON Serialization Fidelity & Roundtrip Information Loss
    # =========================================================================
    def challenge_json_serialization_fidelity(self) -> None:
        cat = "JSON Serialization Fidelity"

        # 5.1 Comprehensive CircuitDefinition roundtrip
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
        if c_orig == c_restored:
            self.record(cat, "CircuitDefinition JSON roundtrip", True, "CONFIRMED_ROBUST", "Complete fidelity: original == restored")
        else:
            self.record(cat, "CircuitDefinition JSON roundtrip", False, "VULNERABILITY_FOUND", "Information lost or corrupted during JSON roundtrip!")

        # 5.2 SizingResult roundtrip with full nested results
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
        if res_orig == res_restored:
            self.record(cat, "SizingResult JSON roundtrip", True, "CONFIRMED_ROBUST", "Complete fidelity: original == restored")
        else:
            self.record(cat, "SizingResult JSON roundtrip", False, "VULNERABILITY_FOUND", "Information lost or corrupted in SizingResult JSON roundtrip!")

        # 5.3 Float precision integrity (high-precision floating point preservation)
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
        if high_prec_vd.du_volts == hp_restored.du_volts:
            self.record(cat, "IEEE-754 precision preservation", True, "CONFIRMED_ROBUST", "Full 64-bit float precision preserved")
        else:
            self.record(cat, "IEEE-754 precision preservation", False, "VULNERABILITY_FOUND", f"Precision lost: {high_prec_vd.du_volts} != {hp_restored.du_volts}")

        # 5.4 JSON Serialization with Inf -> null data corruption attack
        try:
            load_with_inf = ElectricalLoad(voltage_v=float("inf"), power_kw=10.0)
            inf_json = load_with_inf.model_dump_json()
            try:
                ElectricalLoad.model_validate_json(inf_json)
                self.record(cat, "Inf JSON roundtrip", False, "VULNERABILITY_FOUND", "Restored object with Inf (unexpected)")
            except ValidationError as e:
                self.record(
                    cat,
                    "Inf JSON serialization data corruption",
                    False,
                    "VULNERABILITY_FOUND",
                    f"Data corruption during serialization: float('inf') serialized to 'null', failing roundtrip with ValidationError: {e.errors()[0]['msg']}",
                )
        except ValidationError:
            self.record(
                cat,
                "Inf JSON serialization data corruption",
                True,
                "CONFIRMED_ROBUST",
                "Blocked float('inf') at model instantiation",
            )

    # =========================================================================
    # Suite 6: Enum Integrity (Hashability, Symmetry, and Boolean Traps)
    # =========================================================================
    def challenge_enum_integrity(self) -> None:
        cat = "Enum Integrity & Type Safety"

        # 6.1 PhaseSystem hashability
        try:
            h = hash(PhaseSystem.SINGLE_PHASE)
            s = {PhaseSystem.SINGLE_PHASE, PhaseSystem.THREE_PHASE}
            d = {PhaseSystem.SINGLE_PHASE: 1, PhaseSystem.THREE_PHASE: 3}
            self.record(cat, "PhaseSystem hashability", True, "CONFIRMED_ROBUST", f"Hashable: hash={h}")
        except TypeError as e:
            self.record(
                cat,
                "PhaseSystem hashability (CRITICAL DEFECT)",
                False,
                "VULNERABILITY_FOUND",
                f"PhaseSystem is UNHASHABLE due to overriding __eq__ without __hash__! TypeError: {e}. Breaks dict keys, sets, and caching!",
            )

        # 6.2 LimitingConstraint hashability
        try:
            h = hash(LimitingConstraint.AMPACITY)
            s = {LimitingConstraint.AMPACITY, LimitingConstraint.VOLTAGE_DROP}
            d = {LimitingConstraint.AMPACITY: "Iz", LimitingConstraint.VOLTAGE_DROP: "dU"}
            self.record(cat, "LimitingConstraint hashability", True, "CONFIRMED_ROBUST", f"Hashable: hash={h}")
        except TypeError as e:
            self.record(
                cat,
                "LimitingConstraint hashability (CRITICAL DEFECT)",
                False,
                "VULNERABILITY_FOUND",
                f"LimitingConstraint is UNHASHABLE due to overriding __eq__ without __hash__! TypeError: {e}. Breaks dict keys, sets, and caching!",
            )

        # 6.3 Boolean trap: PhaseSystem == True / False
        eq_single_true = (PhaseSystem.SINGLE_PHASE == True)
        eq_dc_false = (PhaseSystem.DC == False)
        if eq_single_true or eq_dc_false:
            self.record(
                cat,
                "PhaseSystem boolean trap (PhaseSystem.SINGLE_PHASE == True)",
                False,
                "VULNERABILITY_FOUND",
                f"Overly broad __eq__ matches booleans: SINGLE_PHASE == True is {eq_single_true}, DC == False is {eq_dc_false}!",
            )
        else:
            self.record(cat, "PhaseSystem boolean trap", True, "CONFIRMED_ROBUST", "PhaseSystem does not equal booleans")

    # =========================================================================
    # Runner and Reporter
    # =========================================================================
    def run_all(self) -> None:
        self.challenge_multi_load_confusion()
        self.challenge_numeric_extremes_and_types()
        self.challenge_model_immutability()
        self.challenge_extra_fields()
        self.challenge_json_serialization_fidelity()
        self.challenge_enum_integrity()

    def print_report(self) -> int:
        print("\n" + "=" * 80)
        print("EMPIRICAL ADVERSARIAL CHALLENGE REPORT: ampy.core.models")
        print("=" * 80)

        vulnerabilities = [r for r in self.results if not r.passed]
        passed_tests = [r for r in self.results if r.passed]

        current_cat = ""
        for r in self.results:
            if r.category != current_cat:
                current_cat = r.category
                print(f"\n--- Category: {current_cat} ---")
            status_symbol = "[FAIL/VULN]" if not r.passed else "[PASS]"
            print(f"  {status_symbol} {r.name:<45} | {r.status:<22} | {r.detail}")

        print("\n" + "-" * 80)
        print(f"TOTAL TESTS: {len(self.results)}")
        print(f"PASSED (ROBUST / BLOCKED): {len(passed_tests)}")
        print(f"FAILED (VULNERABILITIES DISCOVERED): {len(vulnerabilities)}")
        print("-" * 80)

        if vulnerabilities:
            print("\nCRITICAL VULNERABILITIES IDENTIFIED:")
            for i, v in enumerate(vulnerabilities, 1):
                print(f"  {i}. [{v.category}] {v.name}")
                print(f"     Details: {v.detail}")
            print("\nFINAL VERDICT: CHALLENGE_FAILED")
            return 1
        else:
            print("\nFINAL VERDICT: APPROVE")
            return 0


if __name__ == "__main__":
    challenger = AdversarialModelChallenger()
    challenger.run_all()
    exit_code = challenger.print_report()
    sys.exit(exit_code)
