"""
ampy.core.formulas
==================

Pure mathematical electrical calculation functions conforming strictly to:
- NF C 15-100 (Parties 4-43, 5-52)
- UTE C 15-105 (§5.3 Guide pratique de calcul)
- IEC 60364-5-52 (Annex E)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ampy.core.models import (
    ConductorMaterial,
    InsulationType,
    PhaseSystem,
    ThermalStressResult,
    VoltageDropResult,
)

# ==============================================================================
# 1. Physical & Normative Constants
# ==============================================================================

# Resistivity at normal operating temperature (UTE C 15-105 §5.3) in Ω·mm²/m
RHO1_CU: float = 0.023   # Copper (1.25 * 0.01851 Ω·mm²/m)
RHO1_AL: float = 0.037   # Aluminium (1.25 * 0.02941 Ω·mm²/m)

# Linear electrical reactance (UTE C 15-105 §5.3) in Ω/m
# UTE C 15-105 uses a constant value of 0.08 mΩ/m for all sections in
# the simplified voltage drop calculation method.
REACTANCE_DEFAULT: float = 0.00008  # 0.08 mΩ/m for all sections

# Short-circuit adiabatic thermal withstand constants k (A·s^(1/2)/mm²)
K_THERMAL_FACTORS: dict[tuple[str, str], float] = {
    ("Cu", "PVC"): 115.0,
    ("Cu", "XLPE"): 143.0,
    ("Al", "PVC"): 76.0,
    ("Al", "XLPE"): 94.0,
}

# Maximum continuous operating temperature by insulation type (°C)
MAX_OPERATING_TEMP_C: dict[str, float] = {
    "PVC": 70.0,
    "XLPE": 90.0,
}


@dataclass(frozen=True)
class HarmonicResult:
    """Detailed third harmonic derating evaluation."""
    kh: float
    in_neutral_a: float
    ib_effective_a: float
    sizing_basis: str  # 'phase' or 'neutral'

    def __iter__(self):
        """Allows direct unpacking: kh, basis, i_eff = calculate_harmonic_derating(...)."""
        return iter((self.kh, self.sizing_basis, self.ib_effective_a))


# ==============================================================================
# 2. Operating Current Calculations (Ib)
# ==============================================================================

def calculate_ib(
    system: PhaseSystem | str | int | None = None,
    voltage_v: float = 400.0,
    power_w: float | None = None,
    apparent_power_va: float | None = None,
    current_a: float | None = None,
    cos_phi: float = 1.0,
    power_kw: float | None = None,
    apparent_power_kva: float | None = None,
    phases: PhaseSystem | str | int | None = None,
) -> float:
    """
    Calculates design operating current Ib in Amperes (A) per NF C 15-100 §311.

    Parameters
    ----------
    system : PhaseSystem | str | int, optional
        Phase arrangement: SINGLE_PHASE (1), THREE_PHASE (3), or DC ('dc').
    voltage_v : float, default 400.0
        Nominal system voltage (V), e.g. 230.0 for 1P, 400.0 for 3P.
    power_w : float, optional
        Active power in Watts (W).
    apparent_power_va : float, optional
        Apparent power in Volt-Amperes (VA).
    current_a : float, optional
        Direct design current in Amperes (A).
    cos_phi : float, default 1.0
        Displacement power factor (0.0 < cos_phi <= 1.0).
    power_kw : float, optional
        Active power in Kilowatts (kW), converted automatically to Watts.
    apparent_power_kva : float, optional
        Apparent power in kVA, converted automatically to VA.
    phases : PhaseSystem | str | int, optional
        Alias for system parameter.

    Returns
    -------
    float
        Design current Ib in Amperes rounded to 3 decimal places.
    """
    if phases is not None:
        system = phases
    if system is None:
        raise ValueError("Must provide system or phases.")

    if voltage_v <= 0.0:
        raise ValueError(f"voltage_v must be strictly positive, got {voltage_v}")

    # Harmonize kW / kVA inputs
    if power_kw is not None:
        if power_w is not None:
            raise ValueError("Provide either power_w or power_kw, not both.")
        power_w = power_kw * 1000.0

    if apparent_power_kva is not None:
        if apparent_power_va is not None:
            raise ValueError("Provide either apparent_power_va or apparent_power_kva, not both.")
        apparent_power_va = apparent_power_kva * 1000.0

    # Validate mutual exclusivity
    provided = [x is not None for x in (power_w, apparent_power_va, current_a)]
    if sum(provided) != 1:
        raise ValueError(
            "Must provide exactly one of: active power (W/kW), apparent power (VA/kVA), or current (A)."
        )

    # Direct current
    if current_a is not None:
        if current_a <= 0.0:
            raise ValueError(f"current_a must be strictly positive, got {current_a}")
        return round(float(current_a), 3)

    # Check power bounds
    if power_w is not None and power_w <= 0.0:
        raise ValueError(f"power_w must be strictly positive, got {power_w}")
    if apparent_power_va is not None and apparent_power_va <= 0.0:
        raise ValueError(f"apparent_power_va must be strictly positive, got {apparent_power_va}")

    # Normalize system identifier via PhaseSystem
    try:
        phase_sys = system if isinstance(system, PhaseSystem) else PhaseSystem(system)
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Unsupported system type: {system}") from exc

    if phase_sys == PhaseSystem.DC:
        if power_w is not None:
            ib = power_w / voltage_v
        else:
            raise ValueError("DC circuits require active power (W/kW) or direct current (A).")
        return round(ib, 3)

    # Validate power factor for AC circuits
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError(f"cos_phi must be in the open-closed interval (0.0, 1.0], got {cos_phi}")

    if phase_sys == PhaseSystem.SINGLE_PHASE:
        if power_w is not None:
            ib = power_w / (voltage_v * cos_phi)
        else:  # apparent_power_va is not None
            ib = apparent_power_va / voltage_v
    elif phase_sys == PhaseSystem.THREE_PHASE:
        sqrt3 = math.sqrt(3.0)
        if power_w is not None:
            ib = power_w / (sqrt3 * voltage_v * cos_phi)
        else:  # apparent_power_va is not None
            ib = apparent_power_va / (sqrt3 * voltage_v)
    else:
        raise ValueError(f"Unsupported system type: {system}")

    return round(ib, 3)


def calculate_harmonic_derating(ib_a: float, ih3_ratio: float) -> HarmonicResult:
    """
    Computes neutral current and cable derating factor for 3rd harmonics
    in three-phase circuits per IEC 60364-5-52 Table E.52.1 & NF C 15-100 §523.5.

    Parameters
    ----------
    ib_a : float
        Fundamental phase design current (A).
    ih3_ratio : float
        Third-harmonic current ratio Ih3 / Ib (e.g. 0.20 for 20%).

    Returns
    -------
    HarmonicResult
        Contains kh, in_neutral_a, ib_effective_a, and sizing_basis.
        Supports unpacking: kh, basis, ib_eff = calculate_harmonic_derating(...)
    """
    if ib_a <= 0.0:
        raise ValueError(f"ib_a must be strictly positive, got {ib_a}")
    if ih3_ratio < 0.0:
        raise ValueError(f"ih3_ratio must be non-negative, got {ih3_ratio}")

    in_neutral = 3.0 * ih3_ratio * ib_a

    if ih3_ratio <= 0.15:
        kh = 1.00
        ib_effective = ib_a
        basis = "phase"
    elif ih3_ratio <= 0.33:
        kh = 0.86
        ib_effective = ib_a / 0.86
        basis = "phase"
    elif ih3_ratio <= 0.45:
        kh = 0.86
        ib_effective = in_neutral / 0.86
        basis = "neutral"
    else:  # ih3_ratio > 0.45
        kh = 1.00
        ib_effective = in_neutral
        basis = "neutral"

    return HarmonicResult(
        kh=kh,
        in_neutral_a=round(in_neutral, 3),
        ib_effective_a=round(ib_effective, 3),
        sizing_basis=basis,
    )


# ==============================================================================
# 3. Voltage Drop Calculations (dU)
# ==============================================================================

def calculate_sin_phi(cos_phi: float) -> float:
    """
    Computes reactive factor sin(phi) from cos(phi): sin_phi = sqrt(1 - cos_phi^2).
    """
    if not (0.0 <= cos_phi <= 1.0):
        raise ValueError(f"cos_phi must be between 0.0 and 1.0, got {cos_phi}")
    return math.sqrt(max(0.0, 1.0 - (cos_phi ** 2)))


def get_conductor_resistivity(
    material: ConductorMaterial | str,
    operating_temp_c: float | None = None,
) -> float:
    """
    Returns conductor resistivity rho1 in Ω·mm²/m per UTE C 15-105 §5.3.

    Default returns normative conventional values:
      - Cu: 0.023 Ω·mm²/m
      - Al: 0.037 Ω·mm²/m
    If operating_temp_c is provided, computes exact temperature-adjusted resistivity:
      rho(theta) = rho20 * [1 + alpha20 * (theta - 20)]
    """
    try:
        mat = material if isinstance(material, ConductorMaterial) else ConductorMaterial(material)
        mat_str = mat.value  # strictly "Cu" or "Al"
    except (ValueError, TypeError, KeyError):
        mat_str = str(material)

    if mat_str == "Cu":
        if operating_temp_c is None:
            return RHO1_CU
        rho20, alpha20 = 0.01851, 0.00393
        return round(rho20 * (1.0 + alpha20 * (operating_temp_c - 20.0)), 5)
    elif mat_str == "Al":
        if operating_temp_c is None:
            return RHO1_AL
        rho20, alpha20 = 0.02941, 0.00403
        return round(rho20 * (1.0 + alpha20 * (operating_temp_c - 20.0)), 5)
    else:
        raise ValueError(f"Unknown conductor material: {material}")


def get_linear_reactance(section_mm2: float, multicore: bool = True) -> float:
    """
    Returns linear reactance lambda in Ω/m according to UTE C 15-105 §5.3.

    The simplified calculation method uses a constant value of 0.08 mΩ/m
    for all conductor cross-sections.
    """
    return REACTANCE_DEFAULT


def calculate_voltage_drop(
    system: PhaseSystem | str | int | None = None,
    length_m: float = 0.0,
    section_mm2: float = 0.0,
    ib_a: float = 0.0,
    cos_phi: float = 1.0,
    material: ConductorMaterial | str = ConductorMaterial.CU,
    voltage_v: float = 400.0,
    du_max_percent: float = 5.0,
    operating_temp_c: float | None = None,
    u_ref: float | None = None,
    phases: PhaseSystem | str | int | None = None,
    conductor: ConductorMaterial | str | None = None,
    insulation: InsulationType | str | None = None,
    multicore: bool = True,
    reactance_ohm_m: float | None = None,
) -> VoltageDropResult:
    """
    Calculates exact voltage drop dU in Volts and % per UTE C 15-105 §5.3.

    Formula:
      dU = b * [ rho1 * (L / S) * cos_phi + lambda * L * sin_phi ] * Ib

    Parameters
    ----------
    system : PhaseSystem | str | int, optional
        Phase arrangement (PhaseSystem.SINGLE_PHASE, THREE_PHASE, DC).
    length_m : float
        One-way cable route length in meters (m >= 0).
    section_mm2 : float
        Conductor cross-section in mm² (S > 0).
    ib_a : float
        Operating design current in Amperes (Ib >= 0).
    cos_phi : float
        Displacement power factor (0.0 < cos_phi <= 1.0).
    material : ConductorMaterial | str
        Conductor material: Cu or Al.
    voltage_v : float, default 400.0
        Nominal system voltage (V).
    du_max_percent : float, default 5.0
        Maximum allowable relative voltage drop limit in percentage (%).
    operating_temp_c : float, optional
        Conductor operating temperature in °C for temperature-adjusted resistivity.
    u_ref : float, optional
        Custom reference voltage for relative percentage evaluation.
    phases : PhaseSystem | str | int, optional
        Alias for system parameter.
    conductor : ConductorMaterial | str, optional
        Alias for material parameter.

    Returns
    -------
    VoltageDropResult
        Contains du_volts, du_percent, du_max_percent, is_compliant, and margin_percent.
    """
    if phases is not None:
        system = phases
    if conductor is not None:
        material = conductor
    if system is None:
        raise ValueError("Must provide system or phases.")

    # Input boundary validations
    if length_m < 0.0:
        raise ValueError(f"length_m must be non-negative, got {length_m}")
    if section_mm2 <= 0.0:
        raise ValueError(f"section_mm2 must be strictly positive, got {section_mm2}")
    if ib_a < 0.0:
        raise ValueError(f"ib_a must be non-negative, got {ib_a}")
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError(f"cos_phi must be in (0.0, 1.0], got {cos_phi}")
    if voltage_v <= 0.0:
        raise ValueError(f"voltage_v must be strictly positive, got {voltage_v}")
    if u_ref is not None and u_ref <= 0.0:
        raise ValueError(f"u_ref must be strictly positive, got {u_ref}")
    if du_max_percent <= 0.0:
        raise ValueError(f"du_max_percent must be strictly positive, got {du_max_percent}")

    # Coerce system through PhaseSystem
    try:
        phase_sys = system if isinstance(system, PhaseSystem) else PhaseSystem(system)
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Unsupported system type: {system}") from exc

    if phase_sys == PhaseSystem.THREE_PHASE:
        b = 1.0
        default_u_ref = 230.0 if math.isclose(voltage_v, 400.0, rel_tol=0.1) else (voltage_v / math.sqrt(3.0))
    elif phase_sys in (PhaseSystem.SINGLE_PHASE, PhaseSystem.DC):
        b = 2.0
        default_u_ref = voltage_v
    else:
        raise ValueError(f"Unsupported system type: {system}")

    ref_voltage = u_ref if u_ref is not None else default_u_ref

    if length_m == 0.0 or ib_a == 0.0:
        return VoltageDropResult(
            du_volts=0.0,
            du_percent=0.0,
            du_max_percent=round(du_max_percent, 2),
            is_compliant=True,
            margin_percent=round(du_max_percent, 2),
            b_factor=b,
        )

    rho = get_conductor_resistivity(material, operating_temp_c)

    if phase_sys == PhaseSystem.DC:
        # DC circuits have zero frequency: reactance is identically zero, cos_phi = 1.0
        resistance_term = (rho * length_m / section_mm2)
        reactance_term = 0.0
    else:
        sin_phi = calculate_sin_phi(cos_phi)
        lambda_val = (
            reactance_ohm_m
            if reactance_ohm_m is not None
            else get_linear_reactance(section_mm2, multicore=multicore)
        )
        resistance_term = (rho * length_m / section_mm2) * cos_phi
        reactance_term = (lambda_val * length_m) * sin_phi

    du_volts = b * (resistance_term + reactance_term) * ib_a
    du_percent = (du_volts / ref_voltage) * 100.0
    is_compliant = du_percent <= (du_max_percent + 1e-9)

    return VoltageDropResult(
        du_volts=round(du_volts, 3),
        du_percent=round(du_percent, 3),
        du_max_percent=round(du_max_percent, 2),
        is_compliant=is_compliant,
        margin_percent=round(du_max_percent - du_percent, 3),
        b_factor=b,
    )


# ==============================================================================
# 4. Short-Circuit Thermal Stress (I²t <= k²S²)
# ==============================================================================

def calculate_thermal_stress_min_section(
    ik_a: float,
    time_s: float,
    material: ConductorMaterial | str,
    insulation: InsulationType | str,
) -> float:
    """
    Calculates minimum required cross-section for short-circuit withstand
    under adiabatic conditions (NF C 15-100 §434.5.2 & §543):
      S_min = sqrt(I_k^2 * t) / k = (I_k * sqrt(t)) / k

    Parameters
    ----------
    ik_a : float
        Prospective short-circuit current at cable head in Amperes (A).
    time_s : float
        Fault clearing / disconnection duration in seconds (0 < t <= 5.0 s).
    material : ConductorMaterial | str
        Conductor core metal ('Cu' or 'Al').
    insulation : InsulationType | str
        Insulation material ('PVC' or 'XLPE').

    Returns
    -------
    float
        Minimum cross-section S_min in mm² rounded to 2 decimal places.
    """
    if ik_a <= 0.0:
        raise ValueError(f"ik_a must be strictly positive, got {ik_a}")
    if time_s <= 0.0:
        raise ValueError(f"time_s must be strictly positive, got {time_s}")
    if time_s > 5.0:
        raise ValueError(
            f"time_s={time_s}s exceeds maximum 5.0s limit for adiabatic assumption (NF C 15-100 §434.5.2)"
        )

    # Coerce material and insulation through standard Enums
    try:
        mat = material if isinstance(material, ConductorMaterial) else ConductorMaterial(material)
        mat_str = mat.value  # strictly "Cu" or "Al"
    except (ValueError, TypeError, KeyError):
        mat_str = str(material)

    try:
        ins = insulation if isinstance(insulation, InsulationType) else InsulationType(insulation)
        ins_str = ins.value  # strictly "PVC" or "XLPE"
    except (ValueError, TypeError, KeyError):
        ins_str = str(insulation)

    key = (mat_str, ins_str)
    if key not in K_THERMAL_FACTORS:
        raise ValueError(f"Unknown material/insulation combination: {key}")

    k = K_THERMAL_FACTORS[key]
    s_min = (ik_a * math.sqrt(time_s)) / k
    return round(s_min, 2)


def calculate_thermal_stress(
    ik_a: float,
    time_s: float,
    material: ConductorMaterial | str | None = None,
    insulation: InsulationType | str | None = None,
    selected_section_mm2: float = 0.0,
    conductor: ConductorMaterial | str | None = None,
) -> ThermalStressResult:
    """
    Evaluates adiabatic short-circuit thermal withstand and produces a ThermalStressResult.
    """
    if conductor is not None:
        material = conductor
    if material is None:
        raise ValueError("Must provide material or conductor.")
    if insulation is None:
        raise ValueError("Must provide insulation.")

    # Coerce material and insulation through standard Enums
    try:
        mat = material if isinstance(material, ConductorMaterial) else ConductorMaterial(material)
        mat_str = mat.value
    except (ValueError, TypeError, KeyError):
        mat_str = str(material)

    try:
        ins = insulation if isinstance(insulation, InsulationType) else InsulationType(insulation)
        ins_str = ins.value
    except (ValueError, TypeError, KeyError):
        ins_str = str(insulation)

    key = (mat_str, ins_str)
    k = K_THERMAL_FACTORS.get(key)
    if k is None:
        raise ValueError(f"Unknown material/insulation combination: {key}")

    s_min = calculate_thermal_stress_min_section(ik_a, time_s, mat, ins)
    i2t = (ik_a ** 2) * time_s
    is_compliant = selected_section_mm2 >= s_min

    return ThermalStressResult(
        ik_a=float(ik_a),
        time_s=float(time_s),
        i2t=round(i2t, 2),
        k_factor=k,
        s_min_mm2=s_min,
        is_compliant=is_compliant,
    )


# ==============================================================================
# 5. Ambient Temperature Factor (k3)
# ==============================================================================

def calculate_k3_temp_factor(
    insulation: InsulationType | str,
    temp_c: float | None = None,
    in_ground: bool = False,
    rounded: bool = True,
    ambient_temp_c: float | None = None,
) -> float:
    """
    Computes ambient temperature correction factor k3 per NF C 15-100 Table 52K
    and UTE C 15-105 Table BF using the exact normative square root relation:
      k3 = sqrt((theta_max - theta_ambient) / (theta_max - theta_0))

    Parameters
    ----------
    insulation : InsulationType | str
        Insulation material: 'PVC' (70°C max) or 'XLPE' (90°C max).
    temp_c : float, optional
        Ambient operating temperature in °C.
    in_ground : bool, default False
        True if buried in soil (theta_0 = 20°C), False for ambient in air (theta_0 = 30°C).
    rounded : bool, default True
        If True, rounds to 2 decimal places matching normative Table 52K lookup.
        If False, returns raw floating-point analytical value.
    ambient_temp_c : float, optional
        Alias for temp_c parameter.

    Returns
    -------
    float
        Temperature correction factor k3.
    """
    if ambient_temp_c is not None:
        temp_c = ambient_temp_c
    if temp_c is None:
        raise ValueError("Must provide temp_c or ambient_temp_c.")

    ins_str = insulation.value if hasattr(insulation, "value") else str(insulation)
    ins_str = ins_str.strip().upper()

    if ins_str not in MAX_OPERATING_TEMP_C:
        raise ValueError(f"Unknown insulation type: {insulation}. Expected 'PVC' or 'XLPE'.")

    theta_max = MAX_OPERATING_TEMP_C[ins_str]
    theta_0 = 20.0 if in_ground else 30.0

    if temp_c >= theta_max:
        raise ValueError(
            f"Ambient temperature {temp_c}°C equals or exceeds maximum continuous conductor "
            f"operating temperature ({theta_max}°C) for {ins_str} insulation."
        )

    delta_t = theta_max - temp_c
    delta_ref = theta_max - theta_0
    k3 = math.sqrt(delta_t / delta_ref)

    return round(k3, 2) if rounded else k3
