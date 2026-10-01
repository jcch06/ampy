"""
ampy.core.models
================
Strongly-typed Pydantic v2 schemas and standard enums for electrical cable sizing
in strict compliance with NF C 15-100 (Part 5-52) and UTE C 15-105.
"""

from __future__ import annotations

from enum import Enum

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

# ==============================================================================
# Standard Normative Enums
# ==============================================================================

class PhaseSystem(str, Enum):
    """
    Electrical phase arrangement.
    - SINGLE_PHASE: 1-phase AC (Phase + Neutral or Phase-Phase, standard 230V, b=2)
    - THREE_PHASE: 3-phase AC (3-Phase balanced, standard 400V, b=1)
    - DC: Direct Current 2-wire system (b=2)
    """
    SINGLE_PHASE = "single_phase"
    THREE_PHASE = "three_phase"
    DC = "dc"

    @classmethod
    def _missing_(cls, value: object) -> PhaseSystem | None:
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("1", "1p", "single", "single_phase", "single-phase"):
                return cls.SINGLE_PHASE
            if v in ("3", "3p", "three", "three_phase", "three-phase"):
                return cls.THREE_PHASE
            if v in ("dc", "direct", "direct_current", "0"):
                return cls.DC
        elif isinstance(value, int) and not isinstance(value, bool):
            if value == 1:
                return cls.SINGLE_PHASE
            if value == 3:
                return cls.THREE_PHASE
            if value == 0:
                return cls.DC
        return None

    def __eq__(self, other: object) -> bool:
        res = super().__eq__(other)
        if res is True:
            return True
        if isinstance(other, int) and not isinstance(other, bool):
            if self.value == "single_phase" and other == 1:
                return True
            if self.value == "three_phase" and other == 3:
                return True
            if self.value == "dc" and other == 0:
                return True
        if isinstance(other, str):
            v = other.strip().lower()
            if self.value == "single_phase" and v in ("1", "1p", "single", "single_phase", "single-phase"):
                return True
            if self.value == "three_phase" and v in ("3", "3p", "three", "three_phase", "three-phase"):
                return True
            if self.value == "dc" and v in ("dc", "direct", "direct_current", "0"):
                return True
        return False

    def __hash__(self) -> int:
        return hash(self.value)


# Convenient aliases
PhaseSystem.SINGLE = PhaseSystem.SINGLE_PHASE
PhaseSystem.THREE = PhaseSystem.THREE_PHASE


class ConductorMaterial(str, Enum):
    """
    Conductor core metal according to NF C 15-100 Part 5-52:
    - CU: Pure Copper (rho1 = 0.023 ohm.mm2/m)
    - AL: Pure Aluminium (rho1 = 0.037 ohm.mm2/m, standard min section >= 16 mm2)
    """
    CU = "Cu"
    AL = "Al"

    @classmethod
    def _missing_(cls, value: object) -> ConductorMaterial | None:
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("cu", "copper", "cuivre"):
                return cls.CU
            if v in ("al", "aluminum", "aluminium"):
                return cls.AL
        return None


class InsulationType(str, Enum):
    """
    Dielectric insulation material and maximum continuous operating temperature:
    - PVC: Polyvinyl Chloride (max continuous operating temp 70°C)
    - XLPE: Cross-linked Polyethylene / PR / EPR (max continuous operating temp 90°C)
    """
    PVC = "PVC"
    XLPE = "XLPE"

    @classmethod
    def _missing_(cls, value: object) -> InsulationType | None:
        if isinstance(value, str):
            v = value.strip().upper()
            if v in ("PVC",):
                return cls.PVC
            if v in ("XLPE", "PR", "EPR"):
                return cls.XLPE
        return None


class InstallationMethod(str, Enum):
    """
    Reference Installation Method Letter according to NF C 15-100 Table 52C:
    - B: Conduit or trunking on a wall or embedded in building structures
    - C: Single-core or multi-core cables on wall, wooden surface, or unperforated tray
    - E: Multi-core cable in free air or on perforated cable tray/ladder
    - F: Single-core cables in free air or on perforated cable tray touching
    """
    B = "B"
    C = "C"
    E = "E"
    F = "F"

    @classmethod
    def _missing_(cls, value: object) -> InstallationMethod | None:
        if isinstance(value, str):
            v = value.strip().upper()
            if v in ("B", "B1", "B2"):
                return cls.B
            if v in ("C",):
                return cls.C
            if v in ("E",):
                return cls.E
            if v in ("F",):
                return cls.F
        return None


class LimitingConstraint(str, Enum):
    """
    Governing constraint that dictated the final conductor cross-section:
    - AMPACITY: Continuous current thermal carrying capacity (Ib <= In <= Iz)
    - VOLTAGE_DROP: Permissible relative voltage drop limit (dU% <= dU_max%)
    - THERMAL_STRESS: Adiabatic short-circuit withstand limit (I2t <= k2S2)
    """
    AMPACITY = "ampacity"
    VOLTAGE_DROP = "voltage_drop"
    THERMAL_STRESS = "thermal_stress"

    @classmethod
    def _missing_(cls, value: object) -> LimitingConstraint | None:
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("iz", "ampacity", "thermal_ampacity"):
                return cls.AMPACITY
            if v in ("du", "voltage_drop", "voltage-drop", "drop"):
                return cls.VOLTAGE_DROP
            if v in ("thermal_stress", "thermal", "i2t", "short_circuit"):
                return cls.THERMAL_STRESS
        return None

    def __eq__(self, other: object) -> bool:
        res = super().__eq__(other)
        if res is True:
            return True
        if isinstance(other, str):
            v = other.strip().lower()
            if self.value == "ampacity" and v in ("iz", "ampacity", "thermal_ampacity"):
                return True
            if self.value == "voltage_drop" and v in ("du", "voltage_drop", "voltage-drop", "drop"):
                return True
            if self.value == "thermal_stress" and v in ("thermal_stress", "thermal", "i2t", "short_circuit"):
                return True
        return False

    def __hash__(self) -> int:
        return hash(self.value)


# Convenient aliases
LimitingConstraint.IZ = LimitingConstraint.AMPACITY
LimitingConstraint.DU = LimitingConstraint.VOLTAGE_DROP


# ==============================================================================
# Input Domain Schemas
# ==============================================================================

class ElectricalLoad(BaseModel):
    """
    Electrical load specifications.
    User must specify exactly one of: active power (kW), apparent power (kVA),
    or direct design current (A).
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def reject_boolean_numeric_inputs(cls, data: Any) -> Any:
        """Reject boolean values for numeric inputs to prevent Python's bool->int->float coercion."""
        if isinstance(data, dict):
            for field in (
                "voltage_v",
                "power_kw",
                "apparent_power_kva",
                "current_a",
                "frequency_hz",
                "cos_phi",
                "harmonic_ih3_ratio",
            ):
                if field in data and isinstance(data[field], bool):
                    raise ValueError(f"Field '{field}' cannot be a boolean value.")
        return data

    voltage_v: float = Field(
        ...,
        gt=0.0,
        description="Nominal system voltage in Volts (V) (e.g. 230V for 1P, 400V for 3P)"
    )
    phases: PhaseSystem = Field(
        default=PhaseSystem.THREE_PHASE,
        description="Electrical phase system topology (SINGLE_PHASE, THREE_PHASE, DC)"
    )
    cos_phi: float = Field(
        default=0.85,
        gt=0.0,
        le=1.0,
        description="Displacement operating power factor cos(phi) (0.0 < cos_phi <= 1.0)"
    )
    power_kw: float | None = Field(
        default=None,
        gt=0.0,
        validation_alias=AliasChoices("power_kw", "active_power_kw"),
        description="Active power demand in kilowatts (kW)"
    )
    apparent_power_kva: float | None = Field(
        default=None,
        gt=0.0,
        description="Apparent power demand in kilovolt-amperes (kVA)"
    )
    current_a: float | None = Field(
        default=None,
        gt=0.0,
        description="Direct design operating current in Amperes (A)"
    )
    frequency_hz: float = Field(
        default=50.0,
        gt=0.0,
        description="AC system frequency in Hertz (Hz) (default 50.0 Hz, strictly positive)"
    )
    harmonic_ih3_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of 3rd harmonic current to fundamental Ih3 / Ib (0.0 to 1.0)"
    )

    @property
    def active_power_kw(self) -> float | None:
        return self.power_kw

    @model_validator(mode="after")
    def validate_load_input(self) -> ElectricalLoad:
        """Enforces mutual exclusivity: exactly one load input parameter must be given."""
        provided = [
            self.power_kw is not None,
            self.apparent_power_kva is not None,
            self.current_a is not None,
        ]
        if not any(provided):
            raise ValueError(
                "Must provide at least one of: power_kw, apparent_power_kva, or current_a."
            )
        if sum(provided) > 1:
            raise ValueError(
                "Please provide ONLY ONE of: power_kw, apparent_power_kva, or current_a "
                "to avoid ambiguity."
            )
        return self


class CableSpecs(BaseModel):
    """
    Cable physical attributes and circuit route configuration.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, populate_by_name=True)

    length_m: float = Field(
        ...,
        gt=0.0,
        description="One-way circuit route length in meters (m)"
    )
    conductor: ConductorMaterial = Field(
        default=ConductorMaterial.CU,
        validation_alias=AliasChoices("conductor", "conductor_material"),
        description="Conductor metal core: Cu (Copper) or Al (Aluminium)"
    )
    insulation: InsulationType = Field(
        default=InsulationType.XLPE,
        validation_alias=AliasChoices("insulation", "insulation_type"),
        description="Insulation material: PVC (max 70°C) or XLPE (max 90°C)"
    )
    multicore: bool = Field(
        default=True,
        description="True for multi-conductor cable, False for single-core cables"
    )
    section_custom_mm2: float | None = Field(
        default=None,
        gt=0.0,
        description="Optional pre-selected cross-section in mm² (enforces section evaluation)"
    )

    @property
    def conductor_material(self) -> ConductorMaterial:
        return self.conductor

    @property
    def insulation_type(self) -> InsulationType:
        return self.insulation


class InstallationConditions(BaseModel):
    """
    Installation environment and normative derating parameters (NF C 15-100 Table 52C/E/H).
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, populate_by_name=True)

    method: InstallationMethod = Field(
        default=InstallationMethod.C,
        description="Normative reference installation method letter (B, C, E, F)"
    )
    ambient_temp_c: float = Field(
        default=30.0,
        ge=-20.0,
        le=80.0,
        description="Ambient temperature in °C (reference: 30°C in air, 20°C in ground)"
    )
    grouping_circuits: int = Field(
        default=1,
        ge=1,
        le=40,
        description="Number of circuits or multi-core cables grouped together (factor k2)"
    )
    touching: bool = Field(
        default=True,
        description="True if grouped cables are touching (jointifs), False if spaced (d >= D)"
    )
    in_ground: bool = Field(
        default=False,
        description="True if cable is installed underground or buried in soil"
    )
    k_custom: float = Field(
        default=1.0,
        gt=0.0,
        le=2.0,
        description="User-defined additional derating multiplier (e.g. solar radiation, safety margin)"
    )


class EarthingSystem(str, Enum):
    """
    Earthing system per NF C 15-100 Part 4-41.
    - TT: Neutral earthed, exposed conductive parts earthed separately
    - TN_S: Neutral earthed, separate PE conductor
    - TN_C: Neutral earthed, combined PEN conductor
    - IT: Neutral isolated or impedance-earthed
    """
    TT = "TT"
    TN_S = "TN-S"
    TN_C = "TN-C"
    IT = "IT"

    @classmethod
    def _missing_(cls, value: object) -> EarthingSystem | None:
        if isinstance(value, str):
            v = value.strip().upper().replace("_", "-")
            for member in cls:
                if v == member.value:
                    return member
        return None

class CurveType(str, Enum):
    """
    Magnetic tripping curve for circuit breakers.
    - B: Im = 3 to 5 In (standard calculation uses 5 In)
    - C: Im = 5 to 10 In (standard calculation uses 10 In)
    - D: Im = 10 to 14 In (standard calculation uses 14 In)
    """
    B = "B"
    C = "C"
    D = "D"


class ProtectionDevice(BaseModel):
    """
    Upstream protective device settings and fault characteristics.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, populate_by_name=True)

    in_a: float | None = Field(
        default=None,
        gt=0.0,
        description="Nominal protection rating In (A). If None, ampy selects standard In >= Ib."
    )
    ik_a: float | None = Field(
        default=None,
        gt=0.0,
        description="Prospective short-circuit current at cable head in Amperes (A)"
    )
    disconnection_time_s: float | None = Field(
        default=None,
        gt=0.0,
        le=5.0,
        description="Disconnection / tripping time in seconds (s). Must be <= 5.0s for adiabatic regime."
    )
    device_type: str = Field(
        default="circuit_breaker",
        description="Protective device type: 'circuit_breaker' (NF EN 60898/60947-2) or 'fuse_gG' (NF EN 60269)"
    )
    curve: CurveType = Field(
        default=CurveType.C,
        description="Magnetic tripping curve (B, C, D) for circuit breakers."
    )
    rcd_sensitivity_a: float | None = Field(
        default=None,
        gt=0.0,
        description="Residual Current Device (RCD/DDR) sensitivity in Amperes (e.g., 0.03 for 30mA)."
    )



class CircuitDefinition(BaseModel):
    """
    Complete circuit definition combining load, cable, installation, and protection settings.
    Serves as input to SizingEngine and serialization root for YAML/JSON configurations.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, populate_by_name=True)

    name: str = Field(
        default="Circuit_1",
        description="Unique identifier or descriptive name for the circuit"
    )
    load: ElectricalLoad = Field(
        ...,
        description="Electrical load demand and voltage specifications"
    )
    cable: CableSpecs = Field(
        ...,
        description="Cable physical attributes and route length"
    )
    installation: InstallationConditions = Field(
        default_factory=InstallationConditions,
        description="Installation environmental and grouping conditions"
    )
    protection: ProtectionDevice = Field(
        default_factory=ProtectionDevice,
        description="Upstream protective device ratings and fault data"
    )
    du_max_percent: float = Field(
        default=5.0,
        gt=0.0,
        le=20.0,
        validation_alias=AliasChoices("du_max_percent", "max_voltage_drop_pct"),
        description="Maximum allowable relative voltage drop in percentage (%)"
    )

    @property
    def max_voltage_drop_pct(self) -> float:
        return self.du_max_percent

    @model_validator(mode="after")
    def validate_insulation_temperature(self) -> CircuitDefinition:
        """Validates that ambient temperature does not reach or exceed insulation maximum limits."""
        temp = self.installation.ambient_temp_c
        insulation = self.cable.insulation
        if insulation == InsulationType.PVC and temp >= 70.0:
            raise ValueError(
                f"Ambient temperature ({temp}°C) reaches or exceeds maximum operating "
                f"temperature of PVC insulation (70°C). Use XLPE or reduce ambient temperature."
            )
        if insulation == InsulationType.XLPE and temp >= 90.0:
            raise ValueError(
                f"Ambient temperature ({temp}°C) reaches or exceeds maximum operating "
                f"temperature of XLPE insulation (90°C)."
            )
        return self


# ==============================================================================
# Output & Audit Domain Schemas
# ==============================================================================

class IntermediateFactors(BaseModel):
    """
    Detailed audit trail of all intermediate derating coefficients and physical parameters.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    k1_method: float = Field(description="Installation method factor k1 (UTE C 15-105 Table BD)")
    k2_grouping: float = Field(description="Multi-circuit grouping factor k2 (NF C 15-100 Table 52N)")
    k3_temperature: float = Field(description="Ambient temperature factor k3 (NF C 15-100 Table 52K)")
    k_custom: float = Field(default=1.0, description="Custom user-defined derating multiplier")
    kh_harmonic: float = Field(default=1.0, description="Harmonic derating factor kh (IEC 60364-5-52 Table E.52.1)")
    k_total: float = Field(description="Total cumulative derating factor product prod(ki)")
    rho_ohm_mm2_m: float = Field(description="Conductor operating resistivity rho1 in ohm.mm2/m")
    reactance_ohm_m: float = Field(description="Linear conductor reactance lambda in ohm/m")
    cos_phi: float = Field(description="Operating displacement power factor cos(phi)")
    sin_phi: float = Field(description="Operating reactive factor sin(phi) = sqrt(1 - cos2(phi))")


class VoltageDropResult(BaseModel):
    """
    Detailed voltage drop calculation results and normative compliance status.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    du_volts: float = Field(description="Absolute line voltage drop in Volts (V)")
    du_percent: float = Field(description="Relative voltage drop in percentage (%)")
    du_max_percent: float = Field(description="Maximum permissible relative voltage drop threshold (%)")
    is_compliant: bool = Field(description="True if du_percent <= du_max_percent")
    margin_percent: float = Field(description="Remaining margin: du_max_percent - du_percent (%)")
    b_factor: float = Field(default=1.0, description="Circuit topology factor: 1.0 for three-phase, 2.0 for single-phase/DC")

    @property
    def delta_u_v(self) -> float:
        return self.du_volts

    @property
    def delta_u_pct(self) -> float:
        return self.du_percent

    @property
    def voltage_drop_v(self) -> float:
        return self.du_volts

    @property
    def voltage_drop_pct(self) -> float:
        return self.du_percent


class ThermalStressResult(BaseModel):
    """
    Short-circuit thermal stress withstand assessment (I2t <= k2S2 per NF C 15-100 §434.5.2).
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    ik_a: float = Field(description="Prospective short-circuit current in Amperes (A)")
    time_s: float = Field(description="Disconnection duration in seconds (s)")
    i2t: float = Field(description="Joule integral thermal energy let-through I2t in A2.s")
    k_factor: float = Field(description="Adiabatic material constant k in A.s^(1/2)/mm2")
    s_min_mm2: float = Field(description="Minimum required cross-section for thermal withstand in mm2")
    is_compliant: bool = Field(description="True if selected section >= s_min_mm2")


class SizingResult(BaseModel):
    """
    Comprehensive cable sizing calculation output conforming to NF C 15-100 & UTE C 15-105.
    """
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    circuit_name: str = Field(description="Identifier of the sized circuit")
    ib_a: float = Field(description="Calculated design operating current Ib (A)")
    in_a: float = Field(description="Selected or validated nominal protection rating In (A)")
    iz_min_required_a: float = Field(description="Minimum required base current I'z = In / k_total (A)")
    selected_section_mm2: float = Field(description="Selected standard conductor cross-section (mm2)")
    i0_reference_a: float = Field(description="Normative reference admissible current I0 from standard table (A)")
    iz_effective_a: float = Field(description="Effective permissible current in actual conditions Iz = I0 * k_total (A)")
    ampacity_compliant: bool = Field(description="True if continuous current coordination Ib <= In <= Iz is satisfied")
    voltage_drop: VoltageDropResult = Field(description="Calculated voltage drop metrics and compliance")
    thermal_stress: ThermalStressResult | None = Field(
        default=None,
        description="Thermal stress withstand result if short-circuit parameters were provided"
    )
    neutral_section_mm2: float | None = Field(
        default=None,
        description="Calculated cross-section for the neutral conductor (mm2)"
    )
    pe_section_mm2: float | None = Field(
        default=None,
        description="Calculated cross-section for the protective earth conductor (mm2)"
    )
    breaker_ref: str | None = Field(
        default=None,
        description="Catalog reference of the selected protective device"
    )
    breaker_icu_ka: float | None = Field(
        default=None,
        description="Ultimate breaking capacity Icu in kA of the selected device"
    )
    intermediate_factors: IntermediateFactors = Field(description="Audit trail of all derating factors and constants")
    limiting_constraint: LimitingConstraint = Field(
        description="The governing condition that determined final cross-section: AMPACITY, VOLTAGE_DROP, or THERMAL_STRESS"
    )
    is_compliant: bool = Field(
        description="Overall compliance: True if ampacity, voltage drop, and thermal stress are all satisfied"
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Normative annotations, design margins, and engineering remarks"
    )

    @property
    def section_mm2(self) -> float:
        return self.selected_section_mm2

    @property
    def protective_device_in(self) -> float:
        return self.in_a

    @property
    def protective_in(self) -> float:
        return self.in_a

    @property
    def design_current_ib(self) -> float:
        return self.ib_a

    @property
    def ib(self) -> float:
        return self.ib_a

    @property
    def permissible_current_iz(self) -> float:
        return self.iz_effective_a

    @property
    def iz(self) -> float:
        return self.iz_effective_a

    @property
    def total_derating_factor(self) -> float:
        return self.intermediate_factors.k_total

    @property
    def k_total(self) -> float:
        return self.intermediate_factors.k_total

    @property
    def voltage_drop_v(self) -> float:
        return self.voltage_drop.du_volts

    @property
    def du_v(self) -> float:
        return self.voltage_drop.du_volts

    @property
    def voltage_drop_pct(self) -> float:
        return self.voltage_drop.du_percent

    @property
    def du_pct(self) -> float:
        return self.voltage_drop.du_percent
