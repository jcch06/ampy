"""
Tests for Phase 3: Neutral, PE and Indirect Contact Protection.
"""

import pytest

from ampy.core.models import ConductorMaterial, CurveType, EarthingSystem
from ampy.core.protection import (
    check_indirect_contact,
    get_magnetic_tripping_current,
    get_neutral_section,
    get_pe_section,
)

def test_neutral_section_cu():
    assert get_neutral_section(10.0, ConductorMaterial.CU) == 10.0
    assert get_neutral_section(16.0, ConductorMaterial.CU) == 16.0
    assert get_neutral_section(25.0, ConductorMaterial.CU) == 16.0
    assert get_neutral_section(35.0, ConductorMaterial.CU) == 16.0
    assert get_neutral_section(50.0, ConductorMaterial.CU) == 25.0
    assert get_neutral_section(95.0, ConductorMaterial.CU) == 50.0
    assert get_neutral_section(150.0, ConductorMaterial.CU) == 70.0

def test_neutral_section_al():
    assert get_neutral_section(16.0, ConductorMaterial.AL) == 16.0
    assert get_neutral_section(25.0, ConductorMaterial.AL) == 25.0
    assert get_neutral_section(35.0, ConductorMaterial.AL) == 16.0

def test_neutral_section_no_neutral():
    assert get_neutral_section(25.0, ConductorMaterial.CU, has_neutral=False) is None

def test_pe_section():
    assert get_pe_section(10.0) == 10.0
    assert get_pe_section(16.0) == 16.0
    assert get_pe_section(25.0) == 16.0
    assert get_pe_section(35.0) == 16.0
    assert get_pe_section(50.0) == 25.0
    assert get_pe_section(95.0) == 47.5  # Returns exact half. Actual practice often uses 50mm2, but /2 is compliant
    assert get_pe_section(150.0) == 75.0

def test_magnetic_tripping():
    assert get_magnetic_tripping_current(16.0, CurveType.B) == 16.0 * 5.0
    assert get_magnetic_tripping_current(16.0, CurveType.C) == 16.0 * 10.0
    assert get_magnetic_tripping_current(16.0, CurveType.D) == 16.0 * 14.0

def test_indirect_contact_tn():
    # ik1_min_a >= Im
    ok, notes = check_indirect_contact(EarthingSystem.TN_S, 200.0, 16.0, CurveType.C)
    assert ok is True
    assert "Conforme" in notes[0]

    # ik1_min_a < Im
    ok, notes = check_indirect_contact(EarthingSystem.TN_S, 100.0, 16.0, CurveType.C)
    assert ok is False
    assert "NON CONFORME" in notes[0]

    # With curve B, 100A > 16 * 5 = 80A -> compliant
    ok, notes = check_indirect_contact(EarthingSystem.TN_S, 100.0, 16.0, CurveType.B)
    assert ok is True

def test_indirect_contact_tt():
    # RCD required
    ok, notes = check_indirect_contact(EarthingSystem.TT, 50.0, 16.0, CurveType.C, rcd_sensitivity_a=0.03)
    assert ok is True
    assert "Conforme avec DDR" in notes[0]

    # No RCD provided
    ok, notes = check_indirect_contact(EarthingSystem.TT, 50.0, 16.0, CurveType.C, rcd_sensitivity_a=None)
    assert ok is False
    assert "DDR requis" in notes[0]

def test_indirect_contact_it():
    ok, notes = check_indirect_contact(EarthingSystem.IT, 50.0, 16.0, CurveType.C)
    assert ok is True
    assert "alarme" in notes[0]
