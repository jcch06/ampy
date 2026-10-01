"""
ampy.cli.formatters
===================

Rich terminal formatting for cable sizing results.
Outputs in French (tool targets NF C 15-100 French normative context).
"""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ampy.core.models import CircuitDefinition, LimitingConstraint, SizingResult

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

console = Console()

_CONSTRAINT_LABELS: dict[str, str] = {
    "ampacity": "Courant admissible (Iz)",
    "voltage_drop": "Chute de tension (ΔU)",
    "thermal_stress": "Contrainte thermique (I²t)",
}


def _badge(ok: bool) -> str:
    return "✅" if ok else "❌"


def print_sizing_result(result: SizingResult, circuit: CircuitDefinition) -> None:
    """
    Render a comprehensive sizing report in the terminal using Rich.

    Parameters
    ----------
    result : SizingResult
        Output from SizingEngine.size_circuit().
    circuit : CircuitDefinition
        Input circuit definition for context.
    """
    # --- Header Panel ---
    status = "✅ CONFORME" if result.is_compliant else "❌ NON CONFORME"
    header = Text()
    header.append(f"  {result.circuit_name}  ", style="bold white")
    header.append(f"  [{status}]", style="bold green" if result.is_compliant else "bold red")

    console.print()
    console.print(Panel(header, title="⚡ Dimensionnement Câble — NF C 15-100", border_style="blue"))

    # --- Summary Table ---
    summary = Table(title="Résultats de Dimensionnement", show_header=True, header_style="bold cyan")
    summary.add_column("Paramètre", style="bold", min_width=30)
    summary.add_column("Valeur", justify="right", min_width=15)
    summary.add_column("Unité", min_width=8)

    summary.add_row("Courant d'emploi Ib", f"{result.ib_a:.2f}", "A")
    summary.add_row("Calibre de protection In", f"{result.in_a:.0f}", "A")
    summary.add_row("Section retenue S", f"{result.selected_section_mm2:.1f}", "mm²")
    summary.add_row("Courant de réf. I0", f"{result.i0_reference_a:.0f}", "A")
    summary.add_row("Courant admissible Iz", f"{result.iz_effective_a:.2f}", "A")
    summary.add_row(
        "Chute de tension ΔU",
        f"{result.voltage_drop.du_volts:.2f} V  ({result.voltage_drop.du_percent:.2f}%)",
        f"/ {result.voltage_drop.du_max_percent:.1f}%",
    )
    constraint_label = _CONSTRAINT_LABELS.get(
        result.limiting_constraint.value, result.limiting_constraint.value
    )
    summary.add_row("Contrainte limitante", constraint_label, "")

    console.print(summary)

    # --- Correction Factors Table ---
    factors = Table(title="Facteurs de Correction", show_header=True, header_style="bold yellow")
    factors.add_column("Facteur", style="bold", min_width=25)
    factors.add_column("Valeur", justify="right", min_width=10)
    factors.add_column("Référence", min_width=20)

    f = result.intermediate_factors
    factors.add_row("k1 (mode de pose)", f"{f.k1_method:.2f}", "UTE C 15-105 Tab. BD")
    factors.add_row("k2 (groupement)", f"{f.k2_grouping:.2f}", "NF C 15-100 Tab. 52N")
    factors.add_row("k3 (température)", f"{f.k3_temperature:.2f}", "NF C 15-100 Tab. 52K")
    if f.kh_harmonic != 1.0:
        factors.add_row("kh (harmoniques H3)", f"{f.kh_harmonic:.2f}", "IEC 60364-5-52 Tab. E.52.1")
    if f.k_custom != 1.0:
        factors.add_row("k perso.", f"{f.k_custom:.2f}", "Utilisateur")
    factors.add_row("k total (produit)", f"{f.k_total:.4f}", "Πki", style="bold")

    console.print(factors)

    # --- Compliance Badges ---
    badges = Table(title="Vérifications de Conformité", show_header=True, header_style="bold magenta")
    badges.add_column("Vérification", min_width=30)
    badges.add_column("Résultat", justify="center", min_width=10)

    badges.add_row(
        f"Coordination Ib ≤ In ≤ Iz  ({result.ib_a:.1f} ≤ {result.in_a:.0f} ≤ {result.iz_effective_a:.1f})",
        _badge(result.ampacity_compliant),
    )
    badges.add_row(
        f"Chute de tension ΔU%  ({result.voltage_drop.du_percent:.2f}% ≤ {result.voltage_drop.du_max_percent:.1f}%)",
        _badge(result.voltage_drop.is_compliant),
    )
    if result.thermal_stress is not None:
        badges.add_row(
            f"Contrainte thermique I²t  (Smin={result.thermal_stress.s_min_mm2:.1f} mm²)",
            _badge(result.thermal_stress.is_compliant),
        )

    console.print(badges)

    # --- Notes ---
    if result.notes:
        console.print()
        console.print("[bold]Notes :[/bold]")
        for note in result.notes:
            console.print(f"  • {note}")

    console.print()
