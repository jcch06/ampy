"""
ampy.core.selectivity
=====================

Selectivity analysis between upstream and downstream protective devices.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

from ampy.core.catalog import BreakerReference
from ampy.core.protection import get_magnetic_tripping_current


class SelectivityStatus(str, Enum):
    TOTAL = "TOTAL"
    PARTIAL = "PARTIAL"
    NONE = "NONE"


class SelectivityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: SelectivityStatus
    limit_ka: float | None = Field(
        default=None, 
        description="Limit of selectivity Is in kA. If Ik < Is, selectivity is total."
    )
    notes: list[str] = Field(default_factory=list)


def check_selectivity(
    upstream: BreakerReference,
    downstream: BreakerReference,
    ik3_downstream_ka: float
) -> SelectivityResult:
    """
    Check amperometric selectivity between two breakers.
    
    Theoretical amperometric selectivity:
    - We look at the magnetic threshold of the upstream breaker (Im_amont).
    - If the maximum short-circuit at the downstream breaker (ik3_downstream_ka) is 
      LESS than Im_amont, then selectivity is TOTAL (the upstream breaker won't see 
      the fault as a short-circuit, so only the downstream breaker trips).
    - If ik3_downstream_ka >= Im_amont, selectivity is PARTIAL up to Im_amont.
    
    Also apply a basic empiric rule: In_upstream >= 1.6 * In_downstream for any selectivity.
    """
    notes = []
    
    # Check current ratio rule (empiric)
    if upstream.in_a < 1.6 * downstream.in_a:
        notes.append(f"Aucune sélectivité : In_amont ({upstream.in_a}A) < 1.6 * In_aval ({downstream.in_a}A)")
        return SelectivityResult(status=SelectivityStatus.NONE, limit_ka=0.0, notes=notes)

    # Magnetic threshold of upstream breaker
    # Curve is required for accurate Im, fallback to curve C equivalent (10x) if none
    curve = upstream.curve
    if curve is None:
        from ampy.core.models import CurveType
        curve = CurveType.C
        
    im_amont_a = get_magnetic_tripping_current(upstream.in_a, curve)
    im_amont_ka = im_amont_a / 1000.0

    if ik3_downstream_ka < im_amont_ka:
        notes.append(f"Sélectivité TOTALE : Ik3_aval ({ik3_downstream_ka:.2f}kA) < Im_amont ({im_amont_ka:.2f}kA)")
        return SelectivityResult(status=SelectivityStatus.TOTAL, limit_ka=None, notes=notes)
    else:
        notes.append(f"Sélectivité PARTIELLE : Limite Is = {im_amont_ka:.2f}kA (Ik3_aval={ik3_downstream_ka:.2f}kA)")
        return SelectivityResult(status=SelectivityStatus.PARTIAL, limit_ka=im_amont_ka, notes=notes)
