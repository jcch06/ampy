"""
ampy.core.protection
====================

Protection against indirect contacts and calculation of Neutral / PE sections
according to NF C 15-100 Part 4-41 and UTE C 15-105.
"""

from __future__ import annotations

from typing import Tuple

from ampy.core.models import ConductorMaterial, CurveType, EarthingSystem


def get_neutral_section(phase_section_mm2: float, conductor: ConductorMaterial, has_neutral: bool = True) -> float | None:
    """
    Calculate Neutral conductor section according to NF C 15-100 §524.
    
    If S_phase <= 16 mm2 (Cu) or 25 mm2 (Al), S_neutral = S_phase.
    If S_phase > 16 mm2 (Cu) or 25 mm2 (Al), S_neutral = S_phase / 2 is permitted
    if harmonic content is low (assumed true here).
    """
    if not has_neutral:
        return None

    threshold = 16.0 if conductor == ConductorMaterial.CU else 25.0

    if phase_section_mm2 <= threshold:
        return phase_section_mm2
    else:
        # Standard sizes half rule: 25->16, 35->16, 50->25, 70->35, 95->50, 120->70, 150->70, 185->95, 240->120, 300->150
        # For simplicity, we just use the half value or map to the nearest standard section below it.
        # But UTE allows exact half if available, or next standard size.
        # A simpler mapping based on NF C 15-100 Table 52J:
        half_map = {
            25.0: 16.0,
            35.0: 16.0,
            50.0: 25.0,
            70.0: 35.0,
            95.0: 50.0,
            120.0: 70.0,
            150.0: 70.0,
            185.0: 95.0,
            240.0: 120.0,
            300.0: 150.0
        }
        return half_map.get(phase_section_mm2, phase_section_mm2 / 2.0)


def get_pe_section(phase_section_mm2: float) -> float:
    """
    Calculate Protective Earth (PE) conductor section according to NF C 15-100 §543 Table 54F.
    
    - S_phase <= 16 mm2 -> S_PE = S_phase
    - 16 < S_phase <= 35 mm2 -> S_PE = 16 mm2
    - S_phase > 35 mm2 -> S_PE = S_phase / 2
    """
    if phase_section_mm2 <= 16.0:
        return phase_section_mm2
    elif phase_section_mm2 <= 35.0:
        return 16.0
    else:
        return phase_section_mm2 / 2.0


def get_magnetic_tripping_current(in_a: float, curve: CurveType) -> float:
    """
    Get the upper limit of the magnetic tripping threshold (Im) for circuit breakers.
    We take the worst-case (upper) multiplier to ensure tripping.
    """
    multipliers = {
        CurveType.B: 5.0,   # 3 to 5 In
        CurveType.C: 10.0,  # 5 to 10 In
        CurveType.D: 14.0,  # 10 to 14 In (could be up to 20 for specific cases, using 14 as standard)
    }
    return in_a * multipliers[curve]


def check_indirect_contact(
    earthing: EarthingSystem,
    ik1_min_a: float,
    in_a: float,
    curve: CurveType,
    rcd_sensitivity_a: float | None = None
) -> Tuple[bool, list[str]]:
    """
    Check if the protection against indirect contacts is ensured.
    
    Returns:
        (is_compliant, list_of_notes)
    """
    notes = []
    
    if earthing == EarthingSystem.TN_S or earthing == EarthingSystem.TN_C:
        im = get_magnetic_tripping_current(in_a, curve)
        if ik1_min_a >= im:
            notes.append(f"Contact indirect (TN) : Conforme. Ik1min ({ik1_min_a:.0f}A) >= Im ({im:.0f}A).")
            return True, notes
        else:
            notes.append(f"Contact indirect (TN) : NON CONFORME. Ik1min ({ik1_min_a:.0f}A) < Im ({im:.0f}A). "
                         "Augmenter la section, réduire la longueur, ou changer de courbe (ex: B).")
            return False, notes

    elif earthing == EarthingSystem.TT:
        if rcd_sensitivity_a is None:
            # Recommend an RCD
            notes.append("Contact indirect (TT) : DDR requis mais non spécifié. Un DDR est obligatoire en régime TT.")
            return False, notes
        
        # Max touch voltage U_L is typically 50V for AC in normal conditions
        ul = 50.0
        # R_A * I_delta_n <= U_L
        max_ra = ul / rcd_sensitivity_a
        notes.append(f"Contact indirect (TT) : Conforme avec DDR {rcd_sensitivity_a}A. "
                     f"La résistance de terre R_A doit être <= {max_ra:.0f} ohms.")
        return True, notes
        
    elif earthing == EarthingSystem.IT:
        notes.append("Contact indirect (IT) : Régime IT détecté. Le premier défaut nécessite une alarme (CPI). "
                     "Le déclenchement n'est obligatoire qu'au double défaut.")
        return True, notes
        
    return False, ["Schéma de liaison à la terre inconnu."]
