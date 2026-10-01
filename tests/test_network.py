"""
Tests for the network topology models and solver.

Validates:
- Transformer impedance calculations per UTE C 15-105 §4.2
- Network tree validation (connectivity, no loops)
- Impedance chain propagation through a multi-level network
- Short-circuit current calculations (Ik3max, Ik1min)
- Cumulative voltage drop
"""

import math

import pytest

from ampy.core.models import (
    CableSpecs,
    CircuitDefinition,
    ConductorMaterial,
    ElectricalLoad,
    InstallationConditions,
    InstallationMethod,
    InsulationType,
    PhaseSystem,
)
from ampy.network import (
    EarthingSystem,
    NetworkDefinition,
    NetworkLink,
    NodeResult,
    TransformerSource,
    UtilitySource,
)
from ampy.network.solver import NetworkSolver


# ==============================================================================
# Transformer Impedance Tests
# ==============================================================================


class TestTransformerSource:
    """Tests for transformer impedance calculations per UTE C 15-105."""

    def test_630kva_transformer_impedance(self):
        """Standard 630 kVA transformer, Ucc=4%, Pcu=6500W."""
        tr = TransformerSource(
            nominal_power_kva=630,
            voltage_v=400,
            ucc_percent=4.0,
            pcu_w=6500,
        )
        z = tr.transformer_impedance()

        # Ztr = 4% × 400² / (630×1000) = 0.01016 Ω
        expected_z = 0.04 * 400**2 / 630000
        assert math.isclose(abs(z), expected_z, rel_tol=0.01)

        # Rtr = 6500 × 400² / (630000)² = 0.00262 Ω
        expected_r = 6500 * 400**2 / 630000**2
        assert math.isclose(z.real, expected_r, rel_tol=0.01)

        # Xtr = sqrt(Ztr² - Rtr²)
        expected_x = math.sqrt(expected_z**2 - expected_r**2)
        assert math.isclose(z.imag, expected_x, rel_tol=0.01)

    def test_400kva_transformer_default_pcu(self):
        """400 kVA transformer with default Pcu estimation."""
        tr = TransformerSource(
            nominal_power_kva=400,
            voltage_v=400,
            ucc_percent=4.0,
        )
        z = tr.transformer_impedance()

        # Without Pcu, Rtr ≈ 0.31 × Ztr
        z_tr = 0.04 * 400**2 / 400000
        assert math.isclose(z.real, 0.31 * z_tr, rel_tol=0.01)
        assert abs(z) > 0

    def test_nominal_current(self):
        """Verify transformer nominal current calculation."""
        tr = TransformerSource(nominal_power_kva=630, voltage_v=400)
        # In = 630000 / (sqrt(3) × 400) = 909.3 A
        assert math.isclose(tr.nominal_current_a, 909.3, rel_tol=0.01)

    def test_upstream_network_impedance(self):
        """Verify upstream HV network impedance contribution."""
        tr = TransformerSource(
            nominal_power_kva=630,
            voltage_v=400,
            ucc_percent=4.0,
            upstream_ik3_ka=25.0,
        )
        z_up = tr.upstream_impedance()
        # Z_up = 400 / (sqrt(3) × 25000) = 0.00924 Ω
        expected_z = 400 / (math.sqrt(3) * 25000)
        assert math.isclose(abs(z_up), expected_z, rel_tol=0.02)
        assert z_up.real > 0
        assert z_up.imag > 0

    def test_stiff_source_zero_upstream(self):
        """Infinite source (no upstream Ik) should have zero upstream impedance."""
        tr = TransformerSource(
            nominal_power_kva=630,
            voltage_v=400,
            ucc_percent=4.0,
        )
        z_up = tr.upstream_impedance()
        assert z_up == complex(0, 0)


class TestUtilitySource:
    """Tests for utility supply source."""

    def test_utility_impedance(self):
        """Verify impedance from declared Ik3."""
        src = UtilitySource(voltage_v=400, ik3_ka=10.0)
        z = src.total_source_impedance()
        # Z = 400 / (sqrt(3) × 10000) = 0.02309 Ω
        expected_z = 400 / (math.sqrt(3) * 10000)
        assert math.isclose(abs(z), expected_z, rel_tol=0.02)


# ==============================================================================
# Network Topology Validation Tests
# ==============================================================================


class TestNetworkTopology:
    """Tests for network tree validation."""

    def _make_simple_link(self, from_n: str, to_n: str, power_kw: float = 10.0) -> NetworkLink:
        return NetworkLink(
            from_node=from_n,
            to_node=to_n,
            circuit=CircuitDefinition(
                name=f"{from_n}->{to_n}",
                load=ElectricalLoad(power_kw=power_kw, voltage_v=400, phases="3", cos_phi=0.85),
                cable=CableSpecs(length_m=20, conductor="Cu", insulation="XLPE"),
                installation=InstallationConditions(method="C"),
            ),
            is_load=True,
        )

    def test_valid_simple_network(self):
        """Valid 2-level network: Source -> TGBT -> 2 loads."""
        net = NetworkDefinition(
            source=TransformerSource(name="Source", nominal_power_kva=400, voltage_v=400),
            links=[
                self._make_simple_link("Source", "TGBT", 50),
                NetworkLink(
                    from_node="TGBT", to_node="Load1",
                    circuit=CircuitDefinition(
                        name="L1", load=ElectricalLoad(power_kw=10, voltage_v=400, phases="3", cos_phi=0.85),
                        cable=CableSpecs(length_m=30, conductor="Cu", insulation="XLPE"),
                    ),
                    is_load=True,
                ),
                NetworkLink(
                    from_node="TGBT", to_node="Load2",
                    circuit=CircuitDefinition(
                        name="L2", load=ElectricalLoad(power_kw=15, voltage_v=400, phases="3", cos_phi=0.85),
                        cable=CableSpecs(length_m=40, conductor="Cu", insulation="XLPE"),
                    ),
                    is_load=True,
                ),
            ],
        )
        assert len(net.links) == 3

    def test_orphan_node_rejected(self):
        """Network with disconnected node should fail validation."""
        with pytest.raises(ValueError, match="not reachable"):
            NetworkDefinition(
                source=TransformerSource(name="Source", nominal_power_kva=400, voltage_v=400),
                links=[
                    self._make_simple_link("Source", "TGBT"),
                    self._make_simple_link("Orphan", "Load1"),  # Not connected to Source
                ],
            )

    def test_duplicate_to_node_rejected(self):
        """Two links feeding the same node should fail."""
        with pytest.raises(ValueError, match="Duplicate"):
            NetworkDefinition(
                source=TransformerSource(name="Source", nominal_power_kva=400, voltage_v=400),
                links=[
                    self._make_simple_link("Source", "Load1"),
                    self._make_simple_link("Source", "Load1"),  # Duplicate
                ],
            )

    def test_no_root_link_rejected(self):
        """Network with no link from source should fail."""
        with pytest.raises(ValueError, match="No link originates"):
            NetworkDefinition(
                source=TransformerSource(name="Source", nominal_power_kva=400, voltage_v=400),
                links=[
                    self._make_simple_link("TGBT", "Load1"),
                ],
            )


# ==============================================================================
# Network Solver Tests
# ==============================================================================


class TestNetworkSolver:
    """Integration tests for the network solver."""

    def _build_industrial_network(self) -> NetworkDefinition:
        """
        Build a realistic 3-level industrial network:
        Source (630kVA) -> TGBT -> [Motor 18.5kW, TD1] -> [Lighting 3.68kW]
        """
        return NetworkDefinition(
            name="Installation Industrielle",
            source=TransformerSource(
                name="Transfo",
                nominal_power_kva=630,
                voltage_v=400,
                ucc_percent=4.0,
                pcu_w=6500,
                earthing=EarthingSystem.TN_S,
            ),
            links=[
                # Transfo -> TGBT (main feeder)
                NetworkLink(
                    from_node="Transfo",
                    to_node="TGBT",
                    circuit=CircuitDefinition(
                        name="Liaison Transfo-TGBT",
                        load=ElectricalLoad(current_a=250, voltage_v=400, phases="3", cos_phi=0.85),
                        cable=CableSpecs(length_m=5, conductor="Cu", insulation="XLPE"),
                        installation=InstallationConditions(method="F"),
                    ),
                    is_load=False,
                ),
                # TGBT -> Motor 18.5kW (BENCH-01 equivalent)
                NetworkLink(
                    from_node="TGBT",
                    to_node="Moteur M1",
                    circuit=CircuitDefinition(
                        name="Départ Moteur M1",
                        load=ElectricalLoad(power_kw=18.5, voltage_v=400, phases="3", cos_phi=0.85),
                        cable=CableSpecs(length_m=45, conductor="Cu", insulation="XLPE"),
                        installation=InstallationConditions(method="E"),
                    ),
                    is_load=True,
                ),
                # TGBT -> TD1 (sub-panel feeder)
                NetworkLink(
                    from_node="TGBT",
                    to_node="TD1",
                    circuit=CircuitDefinition(
                        name="Départ TD1",
                        load=ElectricalLoad(power_kw=30, voltage_v=400, phases="3", cos_phi=0.85),
                        cable=CableSpecs(length_m=50, conductor="Cu", insulation="XLPE"),
                        installation=InstallationConditions(method="C"),
                    ),
                    is_load=False,
                ),
                # TD1 -> Lighting (1P)
                NetworkLink(
                    from_node="TD1",
                    to_node="Eclairage Bureau",
                    circuit=CircuitDefinition(
                        name="Départ Éclairage",
                        load=ElectricalLoad(power_kw=3.68, voltage_v=230, phases="1", cos_phi=1.0),
                        cable=CableSpecs(length_m=35, conductor="Cu", insulation="PVC"),
                        installation=InstallationConditions(method="B"),
                        du_max_percent=3.0,
                    ),
                    is_load=True,
                ),
            ],
        )

    def test_solve_network_produces_results(self):
        """Solver returns results for all nodes."""
        network = self._build_industrial_network()
        solver = NetworkSolver()
        result = solver.solve(network)

        assert result.network_name == "Installation Industrielle"
        assert result.source_ik3_a > 0
        assert len(result.node_results) == 4  # TGBT, M1, TD1, Eclairage
        assert "TGBT" in result.node_results
        assert "Moteur M1" in result.node_results
        assert "TD1" in result.node_results
        assert "Eclairage Bureau" in result.node_results

    def test_ik3_decreases_downstream(self):
        """Ik3max must decrease as we go further from the source."""
        network = self._build_industrial_network()
        result = NetworkSolver().solve(network)

        ik3_tgbt = result.node_results["TGBT"].short_circuit.ik3_max_a
        ik3_td1 = result.node_results["TD1"].short_circuit.ik3_max_a
        ik3_ecl = result.node_results["Eclairage Bureau"].short_circuit.ik3_max_a

        assert result.source_ik3_a > ik3_tgbt
        assert ik3_tgbt > ik3_td1
        assert ik3_td1 > ik3_ecl

    def test_impedance_increases_downstream(self):
        """Total impedance must increase as we go further from the source."""
        network = self._build_industrial_network()
        result = NetworkSolver().solve(network)

        z_tgbt = result.node_results["TGBT"].impedance.z_total_ohm
        z_td1 = result.node_results["TD1"].impedance.z_total_ohm
        z_ecl = result.node_results["Eclairage Bureau"].impedance.z_total_ohm

        assert z_tgbt < z_td1
        assert z_td1 < z_ecl

    def test_cumulative_du_increases_downstream(self):
        """Cumulative voltage drop must increase downstream."""
        network = self._build_industrial_network()
        result = NetworkSolver().solve(network)

        du_tgbt = result.node_results["TGBT"].cumulative_du_percent
        du_ecl = result.node_results["Eclairage Bureau"].cumulative_du_percent

        assert du_ecl > du_tgbt

    def test_all_circuits_sized(self):
        """All nodes should have sizing results when auto_size=True."""
        network = self._build_industrial_network()
        result = NetworkSolver().solve(network, auto_size=True)

        for name, node in result.node_results.items():
            assert node.sizing is not None, f"No sizing for node '{name}'"

    def test_motor_sizing_matches_bench01(self):
        """Motor circuit sizing should match BENCH-01 expectations."""
        network = self._build_industrial_network()
        result = NetworkSolver().solve(network)

        motor = result.node_results["Moteur M1"]
        assert motor.sizing is not None
        assert motor.sizing.selected_section_mm2 == 4.0
        assert motor.sizing.in_a == 32.0
        assert math.isclose(motor.sizing.ib_a, 31.415, rel_tol=0.005)

    def test_source_ik3_realistic(self):
        """Source Ik3 for 630kVA/4% should be around 22-23 kA."""
        network = self._build_industrial_network()
        result = NetworkSolver().solve(network)

        # Ik3 = U / (sqrt(3) × Ztr) where Ztr = 4% × 400² / 630000 ≈ 0.01016 Ω
        # Ik3 ≈ 400 / (1.732 × 0.01016) ≈ 22.7 kA
        assert 15000 < result.source_ik3_a < 30000

    def test_ik1min_positive(self):
        """Ik1min must be positive at all nodes."""
        network = self._build_industrial_network()
        result = NetworkSolver().solve(network)

        for name, node in result.node_results.items():
            assert node.short_circuit.ik1_min_a > 0, f"Ik1min <= 0 at '{name}'"


class TestSimpleNetwork:
    """Simple 2-node network tests."""

    def test_single_circuit_network(self):
        """Source -> single load."""
        network = NetworkDefinition(
            name="Simple",
            source=TransformerSource(
                name="Source",
                nominal_power_kva=400,
                voltage_v=400,
                ucc_percent=4.0,
            ),
            links=[
                NetworkLink(
                    from_node="Source",
                    to_node="Load",
                    circuit=CircuitDefinition(
                        name="Départ unique",
                        load=ElectricalLoad(power_kw=20, voltage_v=400, phases="3", cos_phi=0.85),
                        cable=CableSpecs(length_m=30, conductor="Cu", insulation="XLPE"),
                        installation=InstallationConditions(method="C"),
                    ),
                    is_load=True,
                ),
            ],
        )
        result = NetworkSolver().solve(network)

        assert len(result.node_results) == 1
        load = result.node_results["Load"]
        assert load.short_circuit.ik3_max_a > 0
        assert load.short_circuit.ik1_min_a > 0
        assert load.sizing is not None
        assert load.sizing.is_compliant
