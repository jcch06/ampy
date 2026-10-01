"""
ampy.core.engine
================

Multi-constraint cable sizing engine per NF C 15-100 & UTE C 15-105.

The SizingEngine orchestrates the complete sizing workflow:
1. Calculate design current Ib
2. Apply harmonic derating (if applicable)
3. Determine correction factors (k1, k2, k3)
4. Select protection rating In
5. Iterate over standard sections to find the smallest one satisfying
   all constraints: ampacity (Ib <= In <= Iz), voltage drop (dU% <= max),
   and thermal stress (I²t <= k²S²).
"""

from __future__ import annotations

import math
from typing import Union

from ampy.core.formulas import (
    calculate_harmonic_derating,
    calculate_ib,
    calculate_k3_temp_factor,
    calculate_sin_phi,
    calculate_thermal_stress,
    calculate_voltage_drop,
    get_conductor_resistivity,
    get_linear_reactance,
)
from ampy.core.models import (
    CircuitDefinition,
    ConductorMaterial,
    InstallationMethod,
    InsulationType,
    IntermediateFactors,
    LimitingConstraint,
    PhaseSystem,
    SizingResult,
    ThermalStressResult,
    VoltageDropResult,
)
from ampy.core.tables import (
    STANDARD_SECTIONS,
    get_k1_factor,
    get_k2_factor,
    get_k3_factor,
    get_next_standard_in,
    get_reference_current_i0,
    get_sections_for_material,
)


class SizingEngine:
    """
    Multi-constraint cable sizing engine per NF C 15-100 & UTE C 15-105.

    Usage::

        engine = SizingEngine()
        result = engine.size_circuit(circuit_definition)
    """

    def size_circuit(self, circuit: CircuitDefinition) -> SizingResult:
        """
        Size a complete circuit and return comprehensive results.

        Parameters
        ----------
        circuit : CircuitDefinition
            Complete circuit specification (load, cable, installation, protection).

        Returns
        -------
        SizingResult
            Comprehensive sizing results with all intermediate audit data.

        Raises
        ------
        ValueError
            If no standard section can satisfy all constraints simultaneously.
        """
        notes: list[str] = []

        # ------------------------------------------------------------------
        # Step 1: Calculate design current Ib
        # ------------------------------------------------------------------
        ib_a = calculate_ib(
            system=circuit.load.phases,
            voltage_v=circuit.load.voltage_v,
            power_kw=circuit.load.power_kw,
            apparent_power_kva=circuit.load.apparent_power_kva,
            current_a=circuit.load.current_a,
            cos_phi=circuit.load.cos_phi,
        )

        # ------------------------------------------------------------------
        # Step 2: Harmonic derating (3rd harmonic in three-phase systems)
        # ------------------------------------------------------------------
        kh = 1.0
        if (
            circuit.load.harmonic_ih3_ratio > 0
            and circuit.load.phases == PhaseSystem.THREE_PHASE
        ):
            h_result = calculate_harmonic_derating(ib_a, circuit.load.harmonic_ih3_ratio)
            kh = h_result.kh
            ib_effective = h_result.ib_effective_a
            notes.append(
                f"Harmonique H3: ih3={circuit.load.harmonic_ih3_ratio:.0%}, "
                f"kh={kh}, base de dimensionnement={h_result.sizing_basis}, "
                f"Ib effectif={ib_effective:.2f} A"
            )
            # Use effective current for sizing but keep original Ib for reporting
        else:
            ib_effective = ib_a

        # ------------------------------------------------------------------
        # Step 3: Correction factors
        # ------------------------------------------------------------------
        k1 = get_k1_factor(circuit.installation.method)
        k2 = get_k2_factor(
            circuit.installation.grouping_circuits,
            circuit.installation.touching,
        )
        k3 = get_k3_factor(
            circuit.cable.insulation,
            circuit.installation.ambient_temp_c,
            circuit.installation.in_ground,
        )
        k_custom = circuit.installation.k_custom
        k_total = round(k1 * k2 * k3 * kh * k_custom, 4)

        if k2 < 1.0:
            notes.append(
                f"Facteur de groupement k2={k2:.2f} "
                f"({circuit.installation.grouping_circuits} circuits jointifs)"
            )
        if k3 != 1.0:
            notes.append(
                f"Facteur de température k3={k3:.2f} "
                f"(ambiante {circuit.installation.ambient_temp_c}°C, "
                f"isolant {circuit.cable.insulation.value})"
            )

        # ------------------------------------------------------------------
        # Step 4: Select protection rating In
        # ------------------------------------------------------------------
        if circuit.protection.in_a is not None:
            in_a = circuit.protection.in_a
            if ib_a > in_a + 1e-9:
                raise ValueError(
                    f"User-specified In={in_a} A is less than Ib={ib_a:.2f} A. "
                    f"Protection coordination Ib <= In is violated."
                )
        else:
            in_a = get_next_standard_in(ib_a)

        # ------------------------------------------------------------------
        # Step 5: Required base reference current
        # ------------------------------------------------------------------
        # I'z = In / k_total: minimum I0 from the table such that Iz = I0 * k_total >= In
        if k_total <= 0:
            raise ValueError(f"Total correction factor k_total={k_total} is non-positive.")
        iz_min_required = in_a / k_total

        # ------------------------------------------------------------------
        # Step 6: Iterate over standard sections
        # ------------------------------------------------------------------
        loaded_conductors = (
            3 if circuit.load.phases == PhaseSystem.THREE_PHASE else 2
        )
        valid_sections = get_sections_for_material(circuit.cable.conductor)

        cos_phi = circuit.load.cos_phi
        sin_phi = calculate_sin_phi(cos_phi)
        rho = get_conductor_resistivity(circuit.cable.conductor)

        # Track the section that first satisfies ampacity
        ampacity_section: float | None = None
        selected_section: float | None = None
        selected_i0: float = 0.0
        selected_iz: float = 0.0
        selected_du: VoltageDropResult | None = None
        selected_thermal: ThermalStressResult | None = None

        for section in valid_sections:
            # Look up I0 for this section
            try:
                i0 = get_reference_current_i0(
                    material=circuit.cable.conductor,
                    insulation=circuit.cable.insulation,
                    loaded_conductors=loaded_conductors,
                    method=circuit.installation.method,
                    section_mm2=section,
                )
            except ValueError:
                continue

            iz = i0 * k_total

            # Check ampacity: I0 >= I'z (equivalent to Iz >= In)
            if i0 < iz_min_required - 1e-9:
                continue

            if ampacity_section is None:
                ampacity_section = section

            # Calculate voltage drop for this section
            reactance = get_linear_reactance(section)
            du_result = calculate_voltage_drop(
                system=circuit.load.phases,
                length_m=circuit.cable.length_m,
                section_mm2=section,
                ib_a=ib_a,
                cos_phi=cos_phi,
                material=circuit.cable.conductor,
                voltage_v=circuit.load.voltage_v,
                du_max_percent=circuit.du_max_percent,
                reactance_ohm_m=reactance,
            )

            if not du_result.is_compliant:
                continue

            # Check thermal stress if fault data is provided
            thermal_result: ThermalStressResult | None = None
            if (
                circuit.protection.ik_a is not None
                and circuit.protection.disconnection_time_s is not None
            ):
                thermal_result = calculate_thermal_stress(
                    ik_a=circuit.protection.ik_a,
                    time_s=circuit.protection.disconnection_time_s,
                    material=circuit.cable.conductor,
                    insulation=circuit.cable.insulation,
                    selected_section_mm2=section,
                )
                if not thermal_result.is_compliant:
                    continue

            # All constraints satisfied — select this section
            selected_section = section
            selected_i0 = i0
            selected_iz = round(iz, 2)
            selected_du = du_result
            selected_thermal = thermal_result
            break

        if selected_section is None or selected_du is None:
            raise ValueError(
                f"No standard section satisfies all constraints for circuit "
                f"'{circuit.name}'. Ib={ib_a:.2f} A, In={in_a} A, "
                f"k_total={k_total}, max dU={circuit.du_max_percent}%."
            )

        # ------------------------------------------------------------------
        # Step 7: Determine limiting constraint
        # ------------------------------------------------------------------
        if (
            selected_thermal is not None
            and ampacity_section is not None
            and selected_section > ampacity_section
            and selected_thermal.s_min_mm2 > ampacity_section
        ):
            limiting = LimitingConstraint.THERMAL_STRESS
        elif ampacity_section is not None and selected_section > ampacity_section:
            limiting = LimitingConstraint.VOLTAGE_DROP
        else:
            limiting = LimitingConstraint.AMPACITY

        # Compliance check
        ampacity_compliant = (ib_a <= in_a + 1e-9) and (in_a <= selected_iz + 1e-9)
        overall_compliant = (
            ampacity_compliant
            and selected_du.is_compliant
            and (selected_thermal is None or selected_thermal.is_compliant)
        )

        # ------------------------------------------------------------------
        # Step 8: Build and return SizingResult
        # ------------------------------------------------------------------
        intermediate = IntermediateFactors(
            k1_method=k1,
            k2_grouping=k2,
            k3_temperature=k3,
            k_custom=k_custom,
            kh_harmonic=kh,
            k_total=k_total,
            rho_ohm_mm2_m=rho,
            reactance_ohm_m=get_linear_reactance(selected_section),
            cos_phi=cos_phi,
            sin_phi=round(sin_phi, 4),
        )

        from ampy.core.protection import get_neutral_section, get_pe_section
        neutral_section = get_neutral_section(
            phase_section_mm2=selected_section,
            conductor=circuit.cable.conductor,
            has_neutral=(circuit.load.phases in [PhaseSystem.SINGLE_PHASE, PhaseSystem.THREE_PHASE])
        )
        pe_section = get_pe_section(selected_section)

        if neutral_section and neutral_section < selected_section:
            notes.append(f"Section du neutre réduite : {neutral_section} mm²")
        if pe_section < selected_section:
            notes.append(f"Section du PE réduite : {pe_section} mm²")

        return SizingResult(
            circuit_name=circuit.name,
            ib_a=ib_a,
            in_a=in_a,
            iz_min_required_a=round(iz_min_required, 2),
            selected_section_mm2=selected_section,
            i0_reference_a=selected_i0,
            iz_effective_a=selected_iz,
            ampacity_compliant=ampacity_compliant,
            voltage_drop=selected_du,
            thermal_stress=selected_thermal,
            neutral_section_mm2=neutral_section,
            pe_section_mm2=pe_section,
            breaker_ref=None,
            breaker_icu_ka=None,
            intermediate_factors=intermediate,
            limiting_constraint=limiting,
            is_compliant=overall_compliant,
            notes=notes,
        )
