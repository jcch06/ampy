"""
ampy.network.models
====================

Data models for electrical distribution network topology.

Represents a radial (tree) network: Source → TGBT → Sub-panels → Loads.
Each node accumulates upstream impedances for short-circuit and voltage drop calculations
per UTE C 15-105 (méthode des impédances).
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ampy.core.models import (
    CableSpecs,
    CircuitDefinition,
    ConductorMaterial,
    EarthingSystem,
    ElectricalLoad,
    InstallationConditions,
    InstallationMethod,
    InsulationType,
    LimitingConstraint,
    PhaseSystem,
    SizingResult,
    VoltageDropResult,
)


# ==============================================================================
# Source Models
# ==============================================================================

class TransformerSource(BaseModel):
    """
    HV/LV transformer or utility supply defining upstream fault level.

    Per UTE C 15-105 §4.2:
    - Ztr = (Ucc% / 100) × U² / Sn
    - Rtr = Pcu × U² / Sn²
    - Xtr = sqrt(Ztr² - Rtr²)
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    name: str = Field(default="Source", description="Source identifier")
    nominal_power_kva: float = Field(
        ..., gt=0, description="Transformer apparent power in kVA (e.g. 630)"
    )
    voltage_v: float = Field(
        default=400.0, gt=0, description="Secondary nominal voltage in V"
    )
    ucc_percent: float = Field(
        default=4.0, gt=0, le=15,
        description="Short-circuit impedance voltage Ucc% (typically 4-6%)"
    )
    pcu_w: float | None = Field(
        default=None, gt=0,
        description="Copper losses at full load in Watts (Pcu). If None, estimated from Sn."
    )
    upstream_ik3_ka: float | None = Field(
        default=None, gt=0,
        description="Upstream HV network 3-phase Ik in kA (default: infinite = stiff source)"
    )
    earthing: EarthingSystem = Field(
        default=EarthingSystem.TN_S,
        description="Earthing system (TT, TN-S, TN-C, IT)"
    )

    @property
    def nominal_power_va(self) -> float:
        return self.nominal_power_kva * 1000.0

    @property
    def nominal_current_a(self) -> float:
        """Transformer nominal secondary current In."""
        return self.nominal_power_va / (math.sqrt(3) * self.voltage_v)

    def transformer_impedance(self) -> complex:
        """
        Calculate transformer impedance Ztr = Rtr + jXtr in ohms per UTE C 15-105 §4.2.
        """
        u = self.voltage_v
        sn = self.nominal_power_va
        ucc = self.ucc_percent / 100.0

        # Total impedance magnitude
        z_tr = ucc * (u ** 2) / sn

        # Resistance: from copper losses or estimated
        if self.pcu_w is not None:
            r_tr = self.pcu_w * (u ** 2) / (sn ** 2)
        else:
            # Typical estimation: Rtr ≈ 0.31 × Ztr for oil transformers
            # (UTE C 15-105 §4.2 simplified)
            r_tr = 0.31 * z_tr

        # Reactance
        x_tr_sq = z_tr ** 2 - r_tr ** 2
        x_tr = math.sqrt(max(0.0, x_tr_sq))

        return complex(r_tr, x_tr)

    def upstream_impedance(self) -> complex:
        """
        Calculate upstream HV network impedance reflected to LV side.
        If upstream_ik3_ka is None, assumes infinite network (Z_upstream = 0).
        """
        if self.upstream_ik3_ka is None:
            return complex(0, 0)

        ik3 = self.upstream_ik3_ka * 1000.0  # Convert to A
        u = self.voltage_v
        z_up = u / (math.sqrt(3) * ik3)
        # Typically X/R ≈ 10 for HV networks
        r_up = z_up / math.sqrt(1 + 10**2)
        x_up = 10 * r_up
        return complex(r_up, x_up)

    def total_source_impedance(self) -> complex:
        """Total source impedance = upstream network + transformer."""
        return self.upstream_impedance() + self.transformer_impedance()


class UtilitySource(BaseModel):
    """
    Direct utility supply defined by fault level Icc at delivery point.
    Used when no private transformer is present.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    name: str = Field(default="Réseau Public", description="Source identifier")
    voltage_v: float = Field(default=400.0, gt=0, description="Nominal voltage in V")
    ik3_ka: float = Field(
        ..., gt=0,
        description="3-phase short-circuit current at delivery point in kA"
    )
    earthing: EarthingSystem = Field(
        default=EarthingSystem.TT,
        description="Earthing system (TT, TN-S, TN-C, IT)"
    )

    def total_source_impedance(self) -> complex:
        """Calculate source impedance from declared Ik3."""
        ik3 = self.ik3_ka * 1000.0
        u = self.voltage_v
        z = u / (math.sqrt(3) * ik3)
        # Typical X/R ratio for utility supply
        r = z / math.sqrt(1 + 5**2)
        x = 5 * r
        return complex(r, x)


class GeneratorSource(BaseModel):
    """
    Backup generator (Groupe Électrogène) source.
    Short-circuit current is limited by the subtransient reactance X''d.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    name: str = Field(default="Groupe Électrogène", description="Source identifier")
    nominal_power_kva: float = Field(..., gt=0, description="Generator rated apparent power in kVA")
    voltage_v: float = Field(default=400.0, gt=0, description="Nominal Phase-to-Phase voltage in V")
    xd_subtransient_percent: float = Field(
        default=15.0, gt=0.0,
        description="Subtransient reactance X''d in % (typically 10% to 20%)"
    )
    x_to_r_ratio: float = Field(
        default=0.1, gt=0.0,
        description="R/X ratio for generator impedance (typically ~0.1)"
    )
    earthing: EarthingSystem = Field(
        default=EarthingSystem.TN_S,
        description="Earthing system (TT, TN-S, TN-C, IT)"
    )

    def total_source_impedance(self) -> complex:
        """Calculate source impedance from X''d."""
        u = self.voltage_v
        s_va = self.nominal_power_kva * 1000.0
        # Zbase = U^2 / S
        z_base = (u ** 2) / s_va
        
        # Zgen = Zbase * (X''d / 100)
        z_gen = z_base * (self.xd_subtransient_percent / 100.0)
        
        # We assume Zgen ~ Xgen, and Rgen = Xgen * x_to_r_ratio
        # Strictly speaking, Z^2 = R^2 + X^2 = (0.1X)^2 + X^2 = 1.01 X^2
        x_gen = z_gen / math.sqrt(1 + self.x_to_r_ratio ** 2)
        r_gen = self.x_to_r_ratio * x_gen
        
        return complex(r_gen, x_gen)


# ==============================================================================
# Network Link (Cable between two nodes)
# ==============================================================================

class NetworkLink(BaseModel):
    """
    A cable link connecting two nodes in the distribution network.
    Wraps a CircuitDefinition with topology information.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    from_node: str = Field(..., description="Name of the upstream bus/panel")
    to_node: str = Field(..., description="Name of the downstream bus/panel or load")
    circuit: CircuitDefinition = Field(..., description="Circuit specification for this link")
    pe_section_mm2: float | None = Field(
        default=None, gt=0,
        description="PE conductor section in mm² (if None, auto-calculated per NF C 15-100 §543)"
    )
    is_load: bool = Field(
        default=False,
        description="True if to_node is a terminal load (not a distribution panel)"
    )


# ==============================================================================
# Network Definition
# ==============================================================================

class NetworkDefinition(BaseModel):
    """
    Complete radial distribution network definition.
    The network must form a tree (no loops) rooted at the source.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    name: str = Field(default="Installation", description="Network name")
    source: TransformerSource | UtilitySource | GeneratorSource = Field(
        ..., description="Upstream power source"
    )
    links: list[NetworkLink] = Field(
        ..., min_length=1, description="Cable links forming the distribution tree"
    )

    @model_validator(mode="after")
    def validate_tree_topology(self) -> NetworkDefinition:
        """Validates that links form a connected tree (no orphans, no loops)."""
        # Collect all node names
        source_name = self.source.name
        from_nodes = {link.from_node for link in self.links}
        to_nodes = {link.to_node for link in self.links}

        # Check root connectivity
        root_links = [l for l in self.links if l.from_node == source_name]
        if not root_links:
            raise ValueError(
                f"No link originates from source '{source_name}'. "
                f"At least one link must have from_node='{source_name}'."
            )

        # Check for duplicate to_nodes (tree = each node has exactly one parent)
        if len(to_nodes) != len(self.links):
            raise ValueError("Duplicate to_node detected. Each node must have exactly one parent.")

        # Check all from_nodes are reachable from source
        reachable = {source_name}
        changed = True
        while changed:
            changed = False
            for link in self.links:
                if link.from_node in reachable and link.to_node not in reachable:
                    reachable.add(link.to_node)
                    changed = True

        all_nodes = from_nodes | to_nodes
        unreachable = all_nodes - reachable
        if unreachable:
            raise ValueError(
                f"Nodes {unreachable} are not reachable from source '{source_name}'. "
                f"Network must form a connected tree."
            )

        return self


# ==============================================================================
# Network Results
# ==============================================================================

class NodeImpedance(BaseModel):
    """Impedance data at a network node."""
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    r_total_ohm: float = Field(description="Total upstream resistance R (ohms)")
    x_total_ohm: float = Field(description="Total upstream reactance X (ohms)")
    z_total_ohm: float = Field(description="Total upstream impedance |Z| (ohms)")


class ShortCircuitResult(BaseModel):
    """Short-circuit currents at a network node per UTE C 15-105."""
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    ik3_max_a: float = Field(description="Maximum 3-phase short-circuit current Ik3max (A)")
    ik2_max_a: float = Field(description="Maximum 2-phase short-circuit current Ik2 (A)")
    ik1_min_a: float = Field(
        description="Minimum phase-neutral/PE fault current Ik1min (A) for TN verification"
    )
    ip_peak_ka: float = Field(description="Peak short-circuit current ip (kA)")


class NodeResult(BaseModel):
    """Complete results at a network node."""
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    node_name: str = Field(description="Node identifier")
    impedance: NodeImpedance = Field(description="Cumulative upstream impedance")
    short_circuit: ShortCircuitResult = Field(description="Short-circuit currents at this node")
    cumulative_du_percent: float = Field(description="Total voltage drop from source to this node (%)")
    sizing: SizingResult | None = Field(
        default=None, description="Cable sizing result for the link feeding this node"
    )
    selectivity: Any = Field(
        default=None, description="SelectivityResult against the upstream breaker"
    )



class NetworkResult(BaseModel):
    """Complete network analysis results."""
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    network_name: str = Field(description="Network identifier")
    source_impedance: NodeImpedance = Field(description="Source impedance (transformer + upstream)")
    source_ik3_a: float = Field(description="Ik3 at source secondary busbar (A)")
    node_results: dict[str, NodeResult] = Field(description="Results indexed by node name")
    is_compliant: bool = Field(description="True if all circuits are compliant")
    notes: list[str] = Field(default_factory=list, description="Network-level notes")
