"""
Tests for Phase 5: Generator sources and Exports
"""

import pytest

from ampy.network import GeneratorSource
from ampy.network.solver import NetworkSolver


def test_generator_impedance():
    # 630kVA Generator, 400V, X''d = 15%
    gen = GeneratorSource(
        name="Gen 1",
        nominal_power_kva=630,
        voltage_v=400,
        xd_subtransient_percent=15.0,
        x_to_r_ratio=0.1
    )
    
    # Zbase = 400^2 / 630000 = 160000 / 630000 = 0.25396 ohms = 253.96 mOhms
    # Zgen = 253.96 * 0.15 = 38.09 mOhms
    
    z = gen.total_source_impedance()
    z_mag = abs(z)
    
    assert 0.038 < z_mag < 0.039  # ≈ 38 mOhms


def test_exports_generation():
    from ampy.cli.exports import generate_mermaid_from_def, generate_html_report
    from ampy.network import NetworkDefinition, NetworkLink, TransformerSource
    from ampy.core.models import CircuitDefinition, ElectricalLoad, CableSpecs, InstallationConditions

    # Build a tiny network
    source = TransformerSource(name="T1", nominal_power_kva=100)
    
    link1 = NetworkLink(
        from_node="T1",
        to_node="P1",
        circuit=CircuitDefinition(
            name="L1",
            load=ElectricalLoad(current_a=10, voltage_v=400, phases="3", cos_phi=0.8),
            cable=CableSpecs(length_m=10),
            installation=InstallationConditions(method="C")
        )
    )
    
    net = NetworkDefinition(name="TestNet", source=source, links=[link1])
    solver = NetworkSolver()
    result = solver.solve(net)
    
    # Test Mermaid
    mermaid_str = generate_mermaid_from_def(result, net)
    assert "graph TD" in mermaid_str or "flowchart TD" in mermaid_str
    assert "T1" in mermaid_str
    assert "P1" in mermaid_str
    assert "-->" in mermaid_str
    
    # Test HTML
    html_str = generate_html_report(result, net)
    assert "<!DOCTYPE html>" in html_str
    assert "TestNet" in html_str
    assert "<table>" in html_str
    assert "P1" in html_str
