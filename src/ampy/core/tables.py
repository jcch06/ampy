"""
ampy.core.tables
================

Normative lookup tables and correction factor functions per:
- NF C 15-100 Part 5-52 (Tables 52C, 52H, 52K, 52N)
- UTE C 15-105 (Tables BD, BF)
- IEC 60364-5-52 (Tables B.52.2 to B.52.5)

All values are sourced directly from the 2026 edition of NF C 15-100.
"""

from __future__ import annotations

import math
from typing import Union

from ampy.core.models import (
    ConductorMaterial,
    InstallationMethod,
    InsulationType,
)

# ==============================================================================
# 1. Standard Normative Series
# ==============================================================================

STANDARD_SECTIONS: list[float] = [
    1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300,
]
"""Standard conductor cross-sections in mm² (NF C 15-100 Table 52G)."""

STANDARD_IN_RATINGS: list[float] = [
    1, 2, 3, 4, 6, 10, 13, 16, 20, 25, 32, 40, 50, 63,
    80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
]
"""Standard circuit breaker nominal current ratings In in Amperes (NF EN 60898 & NF EN 60947-2)."""


# ==============================================================================
# 2. Reference Current I0 Tables (NF C 15-100 Table 52H)
# ==============================================================================
# Structure: _I0_TABLE[(material, insulation, loaded_conductors, method)] = [values per section]
# Each list has 16 values corresponding to STANDARD_SECTIONS (1.5 to 300 mm²).
# For Aluminium, index 0 (1.5mm²) is None (not standard).

_I0_TABLE: dict[tuple[str, str, int, str], list[float | None]] = {}

# --- Copper (Cu), PVC, 3 loaded conductors ---
_I0_TABLE[("Cu", "PVC", 3, "B")] = [15.5, 21, 28, 36, 50, 68, 89, 110, 134, 171, 207, 239, 272, 310, 364, 419]
_I0_TABLE[("Cu", "PVC", 3, "C")] = [17.5, 24, 32, 41, 57, 76, 96, 119, 144, 184, 223, 259, 299, 341, 403, 464]
_I0_TABLE[("Cu", "PVC", 3, "E")] = [18.5, 25, 34, 43, 60, 80, 101, 126, 153, 196, 238, 276, 319, 364, 430, 497]
_I0_TABLE[("Cu", "PVC", 3, "F")] = [22, 30, 40, 51, 70, 94, 119, 148, 180, 232, 282, 328, 379, 434, 514, 593]

# --- Copper (Cu), PVC, 2 loaded conductors ---
_I0_TABLE[("Cu", "PVC", 2, "B")] = [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400, 461]
_I0_TABLE[("Cu", "PVC", 2, "C")] = [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 392, 461, 530]
# Methods E and F for 2 loaded conductors: use same values as 3 loaded (NF C 15-100 note)
_I0_TABLE[("Cu", "PVC", 2, "E")] = _I0_TABLE[("Cu", "PVC", 3, "E")]
_I0_TABLE[("Cu", "PVC", 2, "F")] = _I0_TABLE[("Cu", "PVC", 3, "F")]

# --- Copper (Cu), XLPE, 3 loaded conductors ---
_I0_TABLE[("Cu", "XLPE", 3, "B")] = [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 392, 461, 530]
_I0_TABLE[("Cu", "XLPE", 3, "C")] = [22, 30, 40, 52, 71, 96, 119, 148, 180, 232, 282, 328, 379, 434, 514, 593]
_I0_TABLE[("Cu", "XLPE", 3, "E")] = [23, 31, 42, 54, 75, 100, 127, 154, 188, 244, 298, 346, 399, 456, 538, 621]
_I0_TABLE[("Cu", "XLPE", 3, "F")] = [28, 38, 52, 67, 91, 121, 160, 200, 242, 310, 377, 437, 504, 575, 679, 783]

# --- Copper (Cu), XLPE, 2 loaded conductors ---
_I0_TABLE[("Cu", "XLPE", 2, "B")] = [22, 30, 40, 51, 70, 94, 119, 148, 180, 232, 282, 328, 379, 434, 514, 593]
_I0_TABLE[("Cu", "XLPE", 2, "C")] = [25, 34, 45, 58, 79, 105, 140, 174, 210, 269, 328, 382, 441, 506, 599, 693]
_I0_TABLE[("Cu", "XLPE", 2, "E")] = _I0_TABLE[("Cu", "XLPE", 3, "E")]
_I0_TABLE[("Cu", "XLPE", 2, "F")] = _I0_TABLE[("Cu", "XLPE", 3, "F")]

# --- Aluminium (Al), PVC, 3 loaded conductors (1.5mm² = None) ---
_I0_TABLE[("Al", "PVC", 3, "B")] = [None, 16.5, 22, 28, 39, 53, 70, 86, 104, 133, 161, 186, 212, 240, 282, 324]
_I0_TABLE[("Al", "PVC", 3, "C")] = [None, 18.5, 25, 32, 44, 59, 75, 93, 112, 142, 173, 201, 232, 264, 312, 360]
_I0_TABLE[("Al", "PVC", 3, "E")] = [None, 19.5, 26, 33, 46, 61, 78, 96, 117, 150, 183, 212, 245, 280, 330, 381]
_I0_TABLE[("Al", "PVC", 3, "F")] = [None, 23, 31, 39, 54, 73, 93, 116, 141, 180, 220, 255, 295, 340, 401, 463]

# --- Aluminium (Al), PVC, 2 loaded conductors ---
_I0_TABLE[("Al", "PVC", 2, "B")] = [None, 18.5, 25, 32, 44, 59, 79, 97, 118, 149, 180, 209, 236, 268, 315, 360]
_I0_TABLE[("Al", "PVC", 2, "C")] = [None, 21, 28, 36, 49, 66, 87, 107, 130, 165, 200, 232, 266, 304, 358, 412]
_I0_TABLE[("Al", "PVC", 2, "E")] = _I0_TABLE[("Al", "PVC", 3, "E")]
_I0_TABLE[("Al", "PVC", 2, "F")] = _I0_TABLE[("Al", "PVC", 3, "F")]

# --- Aluminium (Al), XLPE, 3 loaded conductors ---
_I0_TABLE[("Al", "XLPE", 3, "B")] = [None, 21, 28, 36, 49, 66, 87, 107, 130, 165, 200, 232, 266, 304, 358, 412]
_I0_TABLE[("Al", "XLPE", 3, "C")] = [None, 23, 31, 39, 54, 73, 93, 116, 141, 180, 220, 255, 295, 340, 401, 463]
_I0_TABLE[("Al", "XLPE", 3, "E")] = [None, 26, 35, 44, 60, 81, 99, 121, 148, 191, 234, 271, 313, 357, 421, 486]
_I0_TABLE[("Al", "XLPE", 3, "F")] = [None, 30, 40, 52, 71, 95, 125, 157, 190, 244, 296, 344, 397, 454, 536, 618]

# --- Aluminium (Al), XLPE, 2 loaded conductors ---
_I0_TABLE[("Al", "XLPE", 2, "B")] = [None, 23, 31, 39, 54, 73, 93, 116, 141, 180, 220, 255, 295, 340, 401, 463]
_I0_TABLE[("Al", "XLPE", 2, "C")] = [None, 26, 35, 45, 61, 82, 109, 135, 164, 208, 253, 296, 342, 393, 465, 540]
_I0_TABLE[("Al", "XLPE", 2, "E")] = _I0_TABLE[("Al", "XLPE", 3, "E")]
_I0_TABLE[("Al", "XLPE", 2, "F")] = _I0_TABLE[("Al", "XLPE", 3, "F")]


def _coerce_material(material: Union[ConductorMaterial, str]) -> str:
    """Normalize material to canonical string 'Cu' or 'Al'."""
    if isinstance(material, ConductorMaterial):
        return material.value
    try:
        return ConductorMaterial(material).value
    except (ValueError, KeyError):
        raise ValueError(f"Unknown conductor material: {material}")


def _coerce_insulation(insulation: Union[InsulationType, str]) -> str:
    """Normalize insulation to canonical string 'PVC' or 'XLPE'."""
    if isinstance(insulation, InsulationType):
        return insulation.value
    try:
        return InsulationType(insulation).value
    except (ValueError, KeyError):
        raise ValueError(f"Unknown insulation type: {insulation}")


def _coerce_method(method: Union[InstallationMethod, str]) -> str:
    """Normalize installation method to canonical string 'B', 'C', 'E', 'F'."""
    if isinstance(method, InstallationMethod):
        return method.value
    try:
        return InstallationMethod(method).value
    except (ValueError, KeyError):
        raise ValueError(f"Unknown installation method: {method}")


def get_reference_current_i0(
    material: Union[ConductorMaterial, str],
    insulation: Union[InsulationType, str],
    loaded_conductors: int,
    method: Union[InstallationMethod, str],
    section_mm2: float,
) -> float:
    """
    Look up reference admissible current I0 from NF C 15-100 Table 52H.

    Parameters
    ----------
    material : ConductorMaterial | str
        Conductor material ('Cu' or 'Al').
    insulation : InsulationType | str
        Insulation type ('PVC' or 'XLPE').
    loaded_conductors : int
        Number of loaded conductors: 2 (single-phase/DC) or 3 (three-phase).
    method : InstallationMethod | str
        Reference installation method letter ('B', 'C', 'E', 'F').
    section_mm2 : float
        Conductor cross-section in mm².

    Returns
    -------
    float
        Reference admissible current I0 in Amperes (A).

    Raises
    ------
    ValueError
        If the combination is not found in the normative tables.
    """
    mat = _coerce_material(material)
    ins = _coerce_insulation(insulation)
    mth = _coerce_method(method)

    if loaded_conductors not in (2, 3):
        raise ValueError(f"loaded_conductors must be 2 or 3, got {loaded_conductors}")

    if section_mm2 not in STANDARD_SECTIONS:
        raise ValueError(
            f"Section {section_mm2} mm² is not a standard section. "
            f"Valid sections: {STANDARD_SECTIONS}"
        )

    key = (mat, ins, loaded_conductors, mth)
    if key not in _I0_TABLE:
        raise ValueError(
            f"No I0 table entry for combination: material={mat}, insulation={ins}, "
            f"loaded_conductors={loaded_conductors}, method={mth}"
        )

    idx = STANDARD_SECTIONS.index(section_mm2)
    value = _I0_TABLE[key][idx]

    if value is None:
        raise ValueError(
            f"Aluminium conductors at {section_mm2} mm² are not standard per NF C 15-100. "
            f"Minimum aluminium section is 2.5 mm²."
        )

    return float(value)


# ==============================================================================
# 3. Installation Method Factor k1 (NF C 15-100 / UTE C 15-105 Table BD)
# ==============================================================================

def get_k1_factor(method: Union[InstallationMethod, str]) -> float:
    """
    Return installation method correction factor k1 per UTE C 15-105 Table BD.

    In the simplified approach used by this engine, k1 = 1.0 for all reference
    methods because the method-specific derating is already incorporated into
    the I0 reference current table (Table 52H).

    Parameters
    ----------
    method : InstallationMethod | str
        Reference installation method letter ('B', 'C', 'E', 'F').

    Returns
    -------
    float
        k1 correction factor (always 1.0 in simplified approach).
    """
    _coerce_method(method)  # Validate the method exists
    return 1.0


# ==============================================================================
# 4. Grouping Factor k2 (NF C 15-100 Table 52N)
# ==============================================================================

# Grouping reduction factors for multi-core cables or groups of single-core cables,
# single layer on perforated tray (NF C 15-100 Table 52N, column for perforated tray).
_K2_TOUCHING_TABLE: dict[int, float] = {
    1: 1.00,
    2: 0.88,
    3: 0.82,
    4: 0.77,
    5: 0.75,
    6: 0.73,
    7: 0.72,
    8: 0.71,
    9: 0.70,
}
# Ranges: 10-12 -> 0.70, 13-16 -> 0.68, 17-20 -> 0.66

# Alternative table for cables in enclosed trenching / conduit / bundles
_K2_BUNDLES_TABLE: dict[int, float] = {
    1: 1.00,
    2: 0.80,
    3: 0.70,
    4: 0.65,
    5: 0.60,
    6: 0.57,
    7: 0.54,
    8: 0.52,
    9: 0.50,
}
# Ranges: 10-12 -> 0.45, 13-16 -> 0.41, 17-20 -> 0.38


def get_k2_factor(
    n_circuits: int,
    touching: bool = True,
    method: Union[InstallationMethod, str, None] = None,
) -> float:
    """
    Return multi-circuit grouping reduction factor k2 per NF C 15-100 Table 52N.

    Parameters
    ----------
    n_circuits : int
        Number of circuits or multi-core cables grouped together (>= 1).
    touching : bool, default True
        True if cables are touching (jointifs), False if spaced (d >= De).
    method : InstallationMethod | str, optional
        Installation method (reserved for future method-specific tables).

    Returns
    -------
    float
        Grouping reduction factor k2.
    """
    if n_circuits < 1:
        raise ValueError(f"n_circuits must be >= 1, got {n_circuits}")

    if not touching or n_circuits == 1:
        return 1.00

    # Direct lookup for n <= 9
    if n_circuits in _K2_TOUCHING_TABLE:
        return _K2_TOUCHING_TABLE[n_circuits]

    # Range-based lookup (perforated tray single layer)
    if 10 <= n_circuits <= 12:
        return 0.70
    if 13 <= n_circuits <= 16:
        return 0.68
    if 17 <= n_circuits <= 20:
        return 0.66

    # For n > 20: empirical formula k2 = 1 / sqrt(n)
    return round(1.0 / math.sqrt(n_circuits), 2)


# ==============================================================================
# 5. Temperature Factor k3 (NF C 15-100 Table 52K)
# ==============================================================================

# Tabulated k3 values for common temperatures (NF C 15-100 Table 52K)
_K3_TABLE_AIR: dict[tuple[str, int], float] = {
    # PVC (theta_max = 70°C), reference 30°C in air
    ("PVC", 10): 1.22, ("PVC", 15): 1.17, ("PVC", 20): 1.12,
    ("PVC", 25): 1.06, ("PVC", 30): 1.00, ("PVC", 35): 0.94,
    ("PVC", 40): 0.87, ("PVC", 45): 0.79, ("PVC", 50): 0.71,
    ("PVC", 55): 0.61, ("PVC", 60): 0.50,
    # XLPE (theta_max = 90°C), reference 30°C in air
    ("XLPE", 10): 1.15, ("XLPE", 15): 1.12, ("XLPE", 20): 1.08,
    ("XLPE", 25): 1.04, ("XLPE", 30): 1.00, ("XLPE", 35): 0.96,
    ("XLPE", 40): 0.91, ("XLPE", 45): 0.87, ("XLPE", 50): 0.82,
    ("XLPE", 55): 0.76, ("XLPE", 60): 0.71, ("XLPE", 65): 0.65,
    ("XLPE", 70): 0.58, ("XLPE", 75): 0.50, ("XLPE", 80): 0.41,
}

# Maximum operating temperatures per insulation type
_THETA_MAX: dict[str, float] = {"PVC": 70.0, "XLPE": 90.0}


def get_k3_factor(
    insulation: Union[InsulationType, str],
    ambient_temp_c: float,
    in_ground: bool = False,
) -> float:
    """
    Return ambient temperature correction factor k3 per NF C 15-100 Table 52K.

    Uses tabulated values for exact temperature matches (in air, integer °C).
    For non-tabulated temperatures, computes analytically:
        k3 = sqrt((theta_max - theta_ambient) / (theta_max - theta_0))

    Parameters
    ----------
    insulation : InsulationType | str
        Insulation material ('PVC' or 'XLPE').
    ambient_temp_c : float
        Ambient temperature in °C.
    in_ground : bool, default False
        True if buried in soil (theta_0 = 20°C), False for ambient in air (theta_0 = 30°C).

    Returns
    -------
    float
        Temperature correction factor k3, rounded to 2 decimal places.
    """
    ins = _coerce_insulation(insulation)
    theta_max = _THETA_MAX[ins]
    theta_0 = 20.0 if in_ground else 30.0

    if ambient_temp_c >= theta_max:
        raise ValueError(
            f"Ambient temperature {ambient_temp_c}°C equals or exceeds maximum "
            f"continuous operating temperature ({theta_max}°C) for {ins} insulation."
        )

    # Try tabulated lookup for exact integer temperature in air
    if not in_ground and ambient_temp_c == int(ambient_temp_c):
        key = (ins, int(ambient_temp_c))
        if key in _K3_TABLE_AIR:
            return _K3_TABLE_AIR[key]

    # Analytical formula
    k3 = math.sqrt((theta_max - ambient_temp_c) / (theta_max - theta_0))
    return round(k3, 2)


# ==============================================================================
# 6. Helper Functions
# ==============================================================================

def get_next_standard_section(min_section_mm2: float) -> float:
    """
    Return the smallest standard cross-section >= min_section_mm2.

    Parameters
    ----------
    min_section_mm2 : float
        Minimum required cross-section in mm².

    Returns
    -------
    float
        Next standard cross-section in mm².

    Raises
    ------
    ValueError
        If no standard section is large enough.
    """
    for s in STANDARD_SECTIONS:
        if s >= min_section_mm2 - 1e-9:
            return s
    raise ValueError(
        f"No standard section >= {min_section_mm2} mm². "
        f"Maximum available: {STANDARD_SECTIONS[-1]} mm²."
    )


def get_next_standard_in(min_in_a: float) -> float:
    """
    Return the smallest standard protection rating In >= min_in_a.

    Parameters
    ----------
    min_in_a : float
        Minimum required protection rating in Amperes.

    Returns
    -------
    float
        Next standard In rating in Amperes.

    Raises
    ------
    ValueError
        If no standard In is large enough.
    """
    for rating in STANDARD_IN_RATINGS:
        if rating >= min_in_a - 1e-9:
            return rating
    raise ValueError(
        f"No standard In rating >= {min_in_a} A. "
        f"Maximum available: {STANDARD_IN_RATINGS[-1]} A."
    )


def get_sections_for_material(
    material: Union[ConductorMaterial, str],
) -> list[float]:
    """
    Return list of valid standard sections for a given conductor material.

    Aluminium conductors start at 2.5 mm² per NF C 15-100.

    Parameters
    ----------
    material : ConductorMaterial | str
        Conductor material ('Cu' or 'Al').

    Returns
    -------
    list[float]
        List of valid standard cross-sections in mm².
    """
    mat = _coerce_material(material)
    if mat == "Al":
        return [s for s in STANDARD_SECTIONS if s >= 2.5]
    return list(STANDARD_SECTIONS)
