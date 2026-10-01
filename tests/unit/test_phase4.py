"""
Tests for Phase 4: Catalog and Selectivity
"""

import pytest

from ampy.core.catalog import select_breaker, BreakerReference, CATALOG
from ampy.core.models import CurveType
from ampy.core.selectivity import check_selectivity, SelectivityStatus


def test_catalog_selection_modular():
    # Requires 16A, Ik3 = 5kA -> Should pick 10kA Modular
    b = select_breaker(in_required=16.0, ik3_max_ka=5.0, preferred_curve=CurveType.C)
    assert b is not None
    assert b.in_a == 16.0
    assert b.icu_ka == 10.0
    assert b.family == "Modular 10kA"
    assert b.curve == CurveType.C


def test_catalog_selection_mccb_due_to_ik3():
    # Requires 16A, Ik3 = 20kA -> Should pick 36kA MCCB (since modular is 10kA max)
    b = select_breaker(in_required=16.0, ik3_max_ka=20.0, preferred_curve=CurveType.C)
    assert b is not None
    assert b.in_a == 16.0
    assert b.icu_ka == 36.0
    assert b.family == "MCCB 36kA"


def test_catalog_selection_heavy_mccb():
    # Requires 400A -> Should pick Heavy MCCB 70kA
    b = select_breaker(in_required=400.0, ik3_max_ka=30.0, preferred_curve=CurveType.C)
    assert b is not None
    assert b.in_a == 400.0
    assert b.icu_ka == 70.0
    assert b.family == "Heavy MCCB 70kA"


def test_selectivity_total():
    # Upstream: 160A Curve C -> Im = 1600A = 1.6kA
    # Downstream: Ik3_max = 1.0kA -> Total selectivity
    upstream = BreakerReference(family="MCCB", reference="Up", in_a=160.0, icu_ka=36.0, curve=CurveType.C)
    downstream = BreakerReference(family="Mod", reference="Dn", in_a=32.0, icu_ka=10.0, curve=CurveType.C)
    
    res = check_selectivity(upstream, downstream, ik3_downstream_ka=1.0)
    assert res.status == SelectivityStatus.TOTAL


def test_selectivity_partial():
    # Upstream: 100A Curve C -> Im = 1000A = 1.0kA
    # Downstream: Ik3_max = 2.5kA -> Partial selectivity
    upstream = BreakerReference(family="MCCB", reference="Up", in_a=100.0, icu_ka=36.0, curve=CurveType.C)
    downstream = BreakerReference(family="Mod", reference="Dn", in_a=16.0, icu_ka=10.0, curve=CurveType.C)
    
    res = check_selectivity(upstream, downstream, ik3_downstream_ka=2.5)
    assert res.status == SelectivityStatus.PARTIAL
    assert res.limit_ka == 1.0


def test_selectivity_none_ratio():
    # Upstream: 32A
    # Downstream: 25A
    # Ratio = 32/25 = 1.28 < 1.6 -> No selectivity
    upstream = BreakerReference(family="Mod", reference="Up", in_a=32.0, icu_ka=10.0, curve=CurveType.C)
    downstream = BreakerReference(family="Mod", reference="Dn", in_a=25.0, icu_ka=10.0, curve=CurveType.C)
    
    res = check_selectivity(upstream, downstream, ik3_downstream_ka=0.5)
    assert res.status == SelectivityStatus.NONE
