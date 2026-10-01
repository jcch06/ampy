"""
ampy.network.solver
====================

Network solver: propagates impedances through a radial distribution tree,
calculates short-circuit currents (Ik3max, Ik2, Ik1min) at every node,
cumulative voltage drops, and sizes all circuits.

References:
- UTE C 15-105 §4 (méthode des impédances)
- NF C 15-100 §434 (protection against short-circuit)
- NF C 15-100 §411 (automatic disconnection of supply)
"""

from __future__ import annotations

import math
from collections import defaultdict

from ampy.core.engine import SizingEngine
from ampy.core.formulas import (
    get_conductor_resistivity,
    get_linear_reactance,
)
from ampy.core.models import (
    CircuitDefinition,
    PhaseSystem,
    SizingResult,
)
from ampy.network import (
    EarthingSystem,
    NetworkDefinition,
    NetworkLink,
    NetworkResult,
    NodeImpedance,
    NodeResult,
    ShortCircuitResult,
    TransformerSource,
    UtilitySource,
)


def _cable_impedance(circuit: CircuitDefinition, section_mm2: float) -> complex:
    """
    Calculate cable impedance R + jX in ohms for one conductor per UTE C 15-105 §5.3.

    R = rho1 × L / S  (ohms)
    X = lambda × L     (ohms)
    """
    rho = get_conductor_resistivity(circuit.cable.conductor)
    lam = get_linear_reactance(section_mm2)
    length = circuit.cable.length_m

    r = rho * length / section_mm2
    x = lam * length
    return complex(r, x)


def _pe_section(phase_section_mm2: float, pe_override: float | None = None) -> float:
    """
    Determine PE conductor section per NF C 15-100 §543 Table 54F.

    - S_phase <= 16 mm² → S_PE = S_phase
    - 16 < S_phase <= 35 mm² → S_PE = 16 mm²
    - S_phase > 35 mm² → S_PE = S_phase / 2
    """
    if pe_override is not None:
        return pe_override

    if phase_section_mm2 <= 16.0:
        return phase_section_mm2
    elif phase_section_mm2 <= 35.0:
        return 16.0
    else:
        return phase_section_mm2 / 2.0


def _pe_cable_impedance(
    circuit: CircuitDefinition,
    phase_section_mm2: float,
    pe_section_mm2: float,
) -> complex:
    """
    Calculate PE conductor impedance for fault loop (Ik1min calculation).
    Uses the same resistivity as phase conductor (same material assumed).
    """
    rho = get_conductor_resistivity(circuit.cable.conductor)
    lam = get_linear_reactance(pe_section_mm2)
    length = circuit.cable.length_m

    r = rho * length / pe_section_mm2
    x = lam * length
    return complex(r, x)


def _make_impedance(z: complex) -> NodeImpedance:
    """Create NodeImpedance from complex impedance."""
    return NodeImpedance(
        r_total_ohm=round(z.real, 6),
        x_total_ohm=round(z.imag, 6),
        z_total_ohm=round(abs(z), 6),
    )


def _short_circuit_at_node(
    z_phase: complex,
    z_loop: complex,
    voltage_v: float,
) -> ShortCircuitResult:
    """
    Calculate short-circuit currents at a node per UTE C 15-105.

    Parameters
    ----------
    z_phase : complex
        Total phase-to-neutral impedance (source to node).
    z_loop : complex
        Total fault loop impedance for Ik1min (phase + PE path).
    voltage_v : float
        Nominal line-to-line voltage (e.g. 400V).
    """
    u = voltage_v
    u0 = u / math.sqrt(3)  # Phase-to-neutral voltage

    # Ik3max: 3-phase bolted fault (UTE C 15-105 §4.3)
    z_3ph = abs(z_phase)
    ik3 = u / (math.sqrt(3) * z_3ph) if z_3ph > 1e-9 else 999999.0

    # Ik2: 2-phase fault (= Ik3 × sqrt(3)/2 = Ik3 × 0.866)
    ik2 = ik3 * math.sqrt(3) / 2.0

    # Ik1min: phase-to-PE/neutral minimum fault current (NF C 15-100 §411)
    # With 0.95 coefficient for voltage variation
    z_loop_abs = abs(z_loop)
    ik1min = (0.95 * u0) / z_loop_abs if z_loop_abs > 1e-9 else 999999.0

    # ip: peak current (IEC 60909), with kappa factor ≈ 1.8 for typical LV
    kappa = 1.8
    ip = kappa * math.sqrt(2) * ik3

    return ShortCircuitResult(
        ik3_max_a=round(ik3, 1),
        ik2_max_a=round(ik2, 1),
        ik1_min_a=round(ik1min, 1),
        ip_peak_ka=round(ip / 1000.0, 2),
    )


class NetworkSolver:
    """
    Radial distribution network solver.

    Traverses the network tree from source to loads, accumulating impedances
    and calculating short-circuit currents at every node. Optionally sizes
    all circuits using SizingEngine.

    Usage::

        solver = NetworkSolver()
        result = solver.solve(network, auto_size=True)
    """

    def __init__(self) -> None:
        self._engine = SizingEngine()

    def solve(
        self,
        network: NetworkDefinition,
        auto_size: bool = True,
    ) -> NetworkResult:
        """
        Solve the complete network: impedances, short-circuits, voltage drops, sizing.

        Parameters
        ----------
        network : NetworkDefinition
            Network topology and circuit specifications.
        auto_size : bool, default True
            If True, automatically size all circuits using SizingEngine.

        Returns
        -------
        NetworkResult
            Complete network analysis results.
        """
        source = network.source
        voltage = source.voltage_v
        notes: list[str] = []

        # Build adjacency: parent -> [children links]
        children: dict[str, list[NetworkLink]] = defaultdict(list)
        for link in network.links:
            children[link.from_node].append(link)

        # Source impedance
        z_source = source.total_source_impedance()
        source_impedance = _make_impedance(z_source)
        source_ik3 = voltage / (math.sqrt(3) * abs(z_source)) if abs(z_source) > 1e-9 else 999999.0

        notes.append(
            f"Source: Zsource = {z_source.real*1000:.2f} + j{z_source.imag*1000:.2f} mΩ, "
            f"Ik3 = {source_ik3:.0f} A ({source_ik3/1000:.1f} kA)"
        )

        # Get earthing system
        earthing = source.earthing

        # BFS/DFS traversal from source
        node_results: dict[str, NodeResult] = {}
        # Track cumulative impedances: node_name -> (z_phase, z_loop, cumul_du%)
        node_state: dict[str, tuple[complex, complex, float]] = {
            source.name: (z_source, z_source, 0.0)
        }

        # Process nodes in topological order (BFS)
        queue = [source.name]
        all_compliant = True

        while queue:
            current = queue.pop(0)
            z_phase_current, z_loop_current, du_cumul_current = node_state[current]

            for link in children.get(current, []):
                child = link.to_node
                circuit = link.circuit

                # Size the circuit if auto_size
                sizing_result: SizingResult | None = None
                if auto_size:
                    # Inject Ik at this node's busbar for thermal stress check
                    sizing_result = self._engine.size_circuit(circuit)
                    if not sizing_result.is_compliant:
                        all_compliant = False

                # Get the selected section (from sizing or from circuit spec)
                if sizing_result is not None:
                    section = sizing_result.selected_section_mm2
                elif circuit.cable.section_custom_mm2 is not None:
                    section = circuit.cable.section_custom_mm2
                else:
                    # Fallback: size anyway to get a section
                    fallback = self._engine.size_circuit(circuit)
                    section = fallback.selected_section_mm2

                # Calculate cable impedance for phase conductor
                z_cable_phase = _cable_impedance(circuit, section)

                # Calculate PE conductor impedance for fault loop
                pe_section = _pe_section(section, link.pe_section_mm2)
                z_cable_pe = _pe_cable_impedance(circuit, section, pe_section)

                # Cumulative impedances at child node
                z_phase_child = z_phase_current + z_cable_phase
                z_loop_child = z_loop_current + z_cable_phase + z_cable_pe

                # Voltage drop contribution of this link
                du_link = sizing_result.voltage_drop.du_percent if sizing_result else 0.0
                du_cumul_child = du_cumul_current + du_link

                # Short-circuit at child node
                sc = _short_circuit_at_node(z_phase_child, z_loop_child, voltage)

                # Phase 3: Indirect contact protection
                from ampy.core.protection import check_indirect_contact
                in_a = sizing_result.in_a if sizing_result else (circuit.protection.in_a or 16.0)
                is_prot_ok, prot_notes = check_indirect_contact(
                    earthing=earthing,
                    ik1_min_a=sc.ik1_min_a,
                    in_a=in_a,
                    curve=circuit.protection.curve,
                    rcd_sensitivity_a=circuit.protection.rcd_sensitivity_a
                )

                if sizing_result:
                    sizing_result.notes.extend(prot_notes)
                    # For now, we only log it, but we could set all_compliant = False
                    if not is_prot_ok:
                        all_compliant = False

                # Phase 4: Catalog & Selectivity
                from ampy.core.catalog import select_breaker, BreakerReference
                from ampy.core.selectivity import check_selectivity, SelectivityResult
                
                # Breaking capacity required at the START of the circuit (parent node)
                if current == source.name:
                    ik3_for_breaker = source_ik3
                else:
                    ik3_for_breaker = node_results[current].short_circuit.ik3_max_a
                
                ik3_ka = ik3_for_breaker / 1000.0
                
                breaker = select_breaker(in_required=in_a, ik3_max_ka=ik3_ka, preferred_curve=circuit.protection.curve)
                
                # Use object.__setattr__ to bypass frozen Pydantic model for breaker info
                if sizing_result and breaker:
                    object.__setattr__(sizing_result, 'breaker_ref', breaker.reference)
                    object.__setattr__(sizing_result, 'breaker_icu_ka', breaker.icu_ka)

                # Selectivity
                selectivity_res = None
                upstream_node_result = node_results.get(current)
                if upstream_node_result and upstream_node_result.sizing and upstream_node_result.sizing.breaker_ref:
                    # Find the upstream breaker reference object (we can recreate it or fetch it, but let's do a simple lookup)
                    # For simplicity, we just search the catalog again by reference
                    from ampy.core.catalog import CATALOG
                    upstream_breaker = next((b for b in CATALOG if b.reference == upstream_node_result.sizing.breaker_ref), None)
                    if upstream_breaker and breaker:
                        selectivity_res = check_selectivity(
                            upstream=upstream_breaker,
                            downstream=breaker,
                            ik3_downstream_ka=sc.ik3_max_a / 1000.0
                        )

                # Store result
                node_results[child] = NodeResult(
                    node_name=child,
                    impedance=_make_impedance(z_phase_child),
                    short_circuit=sc,
                    cumulative_du_percent=round(du_cumul_child, 2),
                    sizing=sizing_result,
                    selectivity=selectivity_res,
                )

                # Store state for downstream propagation
                node_state[child] = (z_phase_child, z_loop_child, du_cumul_child)

                # Enqueue for further traversal (if it's a bus, not a terminal load)
                if not link.is_load:
                    queue.append(child)

                # Notes for significant Ik values
                notes.append(
                    f"{child}: Ik3max={sc.ik3_max_a:.0f}A, "
                    f"Ik1min={sc.ik1_min_a:.0f}A, "
                    f"ΔU cumul={du_cumul_child:.2f}%"
                )

        return NetworkResult(
            network_name=network.name,
            source_impedance=source_impedance,
            source_ik3_a=round(source_ik3, 1),
            node_results=node_results,
            is_compliant=all_compliant,
            notes=notes,
        )
