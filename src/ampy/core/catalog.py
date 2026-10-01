"""
ampy.core.catalog
=================

Mock catalog of protective devices (circuit breakers).
Provides selection of standard protective devices based on rating (In) and breaking capacity (Icu).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ampy.core.models import CurveType


class BreakerReference(BaseModel):
    """A specific circuit breaker model from the catalog."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    family: str = Field(description="Family or product range name (e.g. 'Acti9', 'Compact NSX')")
    reference: str = Field(description="Commercial reference or display name")
    in_a: float = Field(description="Nominal rating In (A)")
    icu_ka: float = Field(description="Ultimate short-circuit breaking capacity Icu (kA)")
    curve: CurveType | None = Field(default=None, description="Tripping curve for modular breakers")


# Pre-populated mock catalog
# This represents a typical manufacturer offering (e.g. Schneider Electric):
# - Modular breakers up to 63A (10kA)
# - MCCB (Molded Case Circuit Breakers) from 16A to 250A (36kA)
# - Heavy MCCB from 250A to 630A (70kA)

_MODULAR_RATINGS = [2, 6, 10, 16, 20, 25, 32, 40, 50, 63]
_MCCB_RATINGS = [16, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250]
_HEAVY_MCCB_RATINGS = [250, 320, 400, 500, 630, 800, 1000]

CATALOG: list[BreakerReference] = []

# 1. Populate modular range (e.g. iC60N) -> 10kA
for rating in _MODULAR_RATINGS:
    for c in [CurveType.B, CurveType.C, CurveType.D]:
        CATALOG.append(BreakerReference(
            family="Modular 10kA",
            reference=f"MCB-{rating}A-Courbe{c.value}-10kA",
            in_a=rating,
            icu_ka=10.0,
            curve=c
        ))

# 2. Populate MCCB range (e.g. NSX100F/160F/250F) -> 36kA
for rating in _MCCB_RATINGS:
    CATALOG.append(BreakerReference(
        family="MCCB 36kA",
        reference=f"MCCB-TM{rating}D-36kA",
        in_a=rating,
        icu_ka=36.0,
        curve=CurveType.C  # Typical TM-D magnetic is around 10x In, similar to Curve C
    ))

# 3. Populate Heavy MCCB range (e.g. NSX400H/630H) -> 70kA
for rating in _HEAVY_MCCB_RATINGS:
    CATALOG.append(BreakerReference(
        family="Heavy MCCB 70kA",
        reference=f"MCCB-Micrologic{rating}-70kA",
        in_a=rating,
        icu_ka=70.0,
        curve=CurveType.D  # Heavy industrial breakers often have adjustable Im, let's treat as D for calculation
    ))


def select_breaker(in_required: float, ik3_max_ka: float, preferred_curve: CurveType = CurveType.C) -> BreakerReference | None:
    """
    Find the most economical breaker from the catalog that satisfies:
    - In >= in_required
    - Icu >= ik3_max_ka
    - Curve match (if applicable to the family)
    
    If no exact curve match is found for MCCB, it falls back to the available MCCB.
    """
    candidates = []
    for b in CATALOG:
        if b.in_a >= in_required and b.icu_ka >= ik3_max_ka:
            candidates.append(b)
            
    if not candidates:
        return None
        
    # Sort by (Icu, In) to pick the most economical one (lowest Icu that fits, then lowest In)
    candidates.sort(key=lambda x: (x.icu_ka, x.in_a))
    
    # Try to find one with the preferred curve
    for b in candidates:
        if b.curve == preferred_curve:
            return b
            
    # Fallback to the first candidate (usually MCCB don't have B/C/D explicitly in our mock, or we accept the default)
    return candidates[0]
