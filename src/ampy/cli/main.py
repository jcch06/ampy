"""
ampy.cli.main
=============

Typer CLI application for the ampy electrical cable sizing engine.
Entry point: `ampy size ...`

Usage examples:
    # Quick one-shot sizing via CLI flags
    ampy size --power 18.5 --voltage 400 --phases 3 --cos-phi 0.85 \\
              --length 45 --conductor Cu --insulation XLPE --method E

    # From a YAML/JSON configuration file
    ampy size --config examples/motor_18kw.yaml

    # Machine-readable JSON output
    ampy size --config examples/motor_18kw.yaml --json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console

from ampy.cli.formatters import print_sizing_result
from ampy.core.engine import SizingEngine
from ampy.core.models import (
    CableSpecs,
    CircuitDefinition,
    ConductorMaterial,
    ElectricalLoad,
    InstallationConditions,
    InstallationMethod,
    InsulationType,
    PhaseSystem,
)

app = typer.Typer(
    name="ampy",
    help="⚡ Moteur de dimensionnement électrique industriel — NF C 15-100 & UTE C 15-105",
    add_completion=False,
)
console = Console()


def _load_config_file(path: str) -> CircuitDefinition:
    """Load a CircuitDefinition from a YAML or JSON configuration file."""
    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[red]Erreur : fichier introuvable '{path}'[/red]")
        raise typer.Exit(code=1)

    content = file_path.read_text(encoding="utf-8")

    if file_path.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(content)
    elif file_path.suffix.lower() == ".json":
        data = json.loads(content)
    else:
        console.print(f"[red]Format non supporté : '{file_path.suffix}'. Utilisez .yaml, .yml ou .json[/red]")
        raise typer.Exit(code=1)

    try:
        return CircuitDefinition(**data)
    except Exception as e:
        console.print(f"[red]Erreur de validation du fichier de configuration :[/red]")
        console.print(f"  {e}")
        raise typer.Exit(code=1)


def _build_circuit_from_flags(
    power_kw: float | None,
    apparent_power_kva: float | None,
    current_a: float | None,
    voltage_v: float,
    phases: str,
    cos_phi: float,
    length_m: float,
    conductor: str,
    insulation: str,
    method: str,
    ambient_temp: float,
    grouping: int,
    du_max: float,
    name: str,
) -> CircuitDefinition:
    """Build a CircuitDefinition from CLI flags."""
    # Resolve phase system
    phase_map = {"1": "single_phase", "3": "three_phase", "dc": "dc"}
    phase_str = phase_map.get(phases.lower(), phases.lower())

    load_kwargs: dict = {
        "voltage_v": voltage_v,
        "phases": phase_str,
        "cos_phi": cos_phi,
    }
    if power_kw is not None:
        load_kwargs["power_kw"] = power_kw
    elif apparent_power_kva is not None:
        load_kwargs["apparent_power_kva"] = apparent_power_kva
    elif current_a is not None:
        load_kwargs["current_a"] = current_a
    else:
        console.print("[red]Erreur : spécifiez --power, --apparent-power, ou --current[/red]")
        raise typer.Exit(code=1)

    return CircuitDefinition(
        name=name,
        load=ElectricalLoad(**load_kwargs),
        cable=CableSpecs(
            length_m=length_m,
            conductor=conductor,
            insulation=insulation,
        ),
        installation=InstallationConditions(
            method=method,
            ambient_temp_c=ambient_temp,
            grouping_circuits=grouping,
        ),
        du_max_percent=du_max,
    )


@app.command()
def size(
    # Load parameters
    power_kw: Optional[float] = typer.Option(None, "--power", "-P", help="Puissance active en kW"),
    apparent_power_kva: Optional[float] = typer.Option(None, "--apparent-power", "-S", help="Puissance apparente en kVA"),
    current_a: Optional[float] = typer.Option(None, "--current", "-I", help="Courant de dimensionnement en A"),
    voltage_v: float = typer.Option(400.0, "--voltage", "-U", help="Tension nominale en V"),
    phases: str = typer.Option("3", "--phases", "-p", help="Système de phases : 1, 3, ou dc"),
    cos_phi: float = typer.Option(0.85, "--cos-phi", help="Facteur de puissance cos(φ)"),
    # Cable parameters
    length_m: float = typer.Option(0.0, "--length", "-L", help="Longueur du câble en mètres"),
    conductor: str = typer.Option("Cu", "--conductor", "-c", help="Matériau : Cu ou Al"),
    insulation: str = typer.Option("XLPE", "--insulation", "-i", help="Isolant : PVC ou XLPE"),
    # Installation parameters
    method: str = typer.Option("C", "--method", "-m", help="Méthode de pose : B, C, E, F"),
    ambient_temp: float = typer.Option(30.0, "--temp", "-t", help="Température ambiante °C"),
    grouping: int = typer.Option(1, "--grouping", "-g", help="Nombre de circuits groupés"),
    # Voltage drop limit
    du_max: float = typer.Option(5.0, "--du-max", help="Chute de tension max en %%"),
    # Circuit name
    name: str = typer.Option("Circuit", "--name", "-n", help="Nom du circuit"),
    # Config file input
    config: Optional[str] = typer.Option(None, "--config", "-f", help="Fichier de configuration YAML/JSON"),
    # Output format
    json_output: bool = typer.Option(False, "--json", help="Sortie au format JSON"),
) -> None:
    """
    ⚡ Dimensionner une canalisation électrique selon la NF C 15-100.

    Calcule la section optimale, le calibre de protection, et vérifie la
    conformité normative (courant admissible, chute de tension, contrainte thermique).
    """
    try:
        if config is not None:
            circuit = _load_config_file(config)
        else:
            if length_m <= 0:
                console.print("[red]Erreur : --length est requis et doit être > 0[/red]")
                raise typer.Exit(code=1)
            circuit = _build_circuit_from_flags(
                power_kw=power_kw,
                apparent_power_kva=apparent_power_kva,
                current_a=current_a,
                voltage_v=voltage_v,
                phases=phases,
                cos_phi=cos_phi,
                length_m=length_m,
                conductor=conductor,
                insulation=insulation,
                method=method,
                ambient_temp=ambient_temp,
                grouping=grouping,
                du_max=du_max,
                name=name,
            )

        engine = SizingEngine()
        result = engine.size_circuit(circuit)

        if json_output:
            print(result.model_dump_json(indent=2))
        else:
            print_sizing_result(result, circuit)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Erreur de calcul : {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def network(
    config: str = typer.Argument(..., help="Fichier de configuration réseau YAML/JSON"),
    json_output: bool = typer.Option(False, "--json", help="Sortie au format JSON"),
    mermaid_out: str = typer.Option(None, "--mermaid", help="Fichier de sortie pour le schéma unifilaire (Mermaid)"),
    html_out: str = typer.Option(None, "--html", help="Fichier de sortie pour la note de calcul (HTML)"),
) -> None:
    """
    ⚡ Analyser un réseau de distribution complet (impédances, Ik, ΔU cumulatif).

    Propage les impédances à travers l'arborescence radiale, calcule les
    courants de court-circuit (Ik3max, Ik1min) à chaque nœud, et dimensionne
    automatiquement tous les circuits.
    """
    from rich.table import Table

    from ampy.network import (
        GeneratorSource,
        NetworkDefinition,
        NetworkLink,
        TransformerSource,
        UtilitySource,
    )
    from ampy.network.solver import NetworkSolver
    from ampy.cli.exports import generate_mermaid_from_def, generate_html_report

    try:
        file_path = Path(config)
        if not file_path.exists():
            console.print(f"[red]Erreur : fichier introuvable '{config}'[/red]")
            raise typer.Exit(code=1)

        content = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)

        # Build source
        src_data = data.get("source", {})
        src_type = src_data.pop("type", "transformer")
        if src_type == "transformer":
            source = TransformerSource(**src_data)
        elif src_type == "generator":
            source = GeneratorSource(**src_data)
        else:
            source = UtilitySource(**src_data)

        # Build links
        links = []
        for lk in data.get("links", []):
            circuit_data = lk.pop("circuit")
            circuit = CircuitDefinition(**circuit_data)
            links.append(NetworkLink(circuit=circuit, **lk))

        net = NetworkDefinition(name=data.get("name", "Réseau"), source=source, links=links)

        solver = NetworkSolver()
        result = solver.solve(net)

        if json_output:
            print(result.model_dump_json(indent=2))
        else:
            _print_network_result(result, net)

        if mermaid_out:
            mermaid_str = generate_mermaid_from_def(result, net)
            Path(mermaid_out).write_text(mermaid_str, encoding="utf-8")
            console.print(f"[green]Schéma unifilaire (Mermaid) exporté : {mermaid_out}[/green]")

        if html_out:
            html_str = generate_html_report(result, net)
            Path(html_out).write_text(html_str, encoding="utf-8")
            console.print(f"[green]Note de calcul HTML exportée : {html_out}[/green]")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Erreur : {e}[/red]")
        raise typer.Exit(code=1)


def _print_network_result(result: "NetworkResult", net: "NetworkDefinition") -> None:
    """Rich-formatted network analysis report."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    from ampy.network import NetworkResult

    status = "✅ CONFORME" if result.is_compliant else "❌ NON CONFORME"
    header = Text()
    header.append(f"  {result.network_name}  ", style="bold white")
    header.append(f"  [{status}]", style="bold green" if result.is_compliant else "bold red")

    console.print()
    console.print(Panel(header, title="⚡ Analyse Réseau — NF C 15-100 / UTE C 15-105", border_style="blue"))

    # Source info
    console.print(f"  Ik3 source: [bold]{result.source_ik3_a:.0f} A ({result.source_ik3_a/1000:.1f} kA)[/bold]")
    console.print(f"  Z source: {result.source_impedance.r_total_ohm*1000:.2f} + j{result.source_impedance.x_total_ohm*1000:.2f} mΩ")
    console.print()

    # Node results table
    tbl = Table(title="Résultats par Nœud", show_header=True, header_style="bold cyan")
    tbl.add_column("Nœud", style="bold", min_width=20)
    tbl.add_column("S/N/PE (mm²)", justify="center")
    tbl.add_column("Disjoncteur", justify="left")
    tbl.add_column("Sélectivité", justify="center")
    tbl.add_column("Ik3max (kA)", justify="right")
    tbl.add_column("Ik1min (A)", justify="right")
    tbl.add_column("ΔU cumul (%)", justify="right")
    tbl.add_column("Status", justify="center")

    for name, node in result.node_results.items():
        if node.sizing:
            s_ph = f"{node.sizing.selected_section_mm2:.0f}"
            s_n = f"{node.sizing.neutral_section_mm2:.0f}" if node.sizing.neutral_section_mm2 else "-"
            s_pe = f"{node.sizing.pe_section_mm2:.0f}" if node.sizing.pe_section_mm2 else "-"
            section = f"{s_ph} / {s_n} / {s_pe}"
            breaker = f"{node.sizing.breaker_ref}\n({node.sizing.breaker_icu_ka}kA)" if node.sizing.breaker_ref else f"{node.sizing.in_a:.0f}A"
        else:
            section = "-"
            breaker = "-"
            
        sel = "-"
        if node.selectivity:
            if node.selectivity.status.value == "TOTAL":
                sel = "[green]TOTALE[/green]"
            elif node.selectivity.status.value == "PARTIAL":
                sel = f"[yellow]PART. (<{node.selectivity.limit_ka:.1f}kA)[/yellow]"
            else:
                sel = "[red]AUCUNE[/red]"
            
        ik3 = f"{node.short_circuit.ik3_max_a/1000:.1f}"
        ik1 = f"{node.short_circuit.ik1_min_a:.0f}"
        du = f"{node.cumulative_du_percent:.2f}"
        ok = "✅" if (node.sizing and node.sizing.is_compliant) else "⚠️"
        tbl.add_row(name, section, breaker, sel, ik3, ik1, du, ok)

    console.print(tbl)
    console.print()


@app.command()
def web(
    port: int = typer.Option(8501, "--port", "-p", help="Port pour l'interface web"),
) -> None:
    """Lancer l'interface web (Streamlit) de Ampy."""
    import subprocess
    import sys
    from pathlib import Path
    
    app_path = Path(__file__).parent.parent / "web" / "app.py"
    if not app_path.exists():
        console.print(f"[red]Erreur : Le fichier de l'application web '{app_path}' est introuvable.[/red]")
        raise typer.Exit(code=1)
        
    console.print(f"[green]Lancement de l'interface web sur le port {port}...[/green]")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", str(port)])
    except KeyboardInterrupt:
        console.print("[yellow]Arrêt du serveur web.[/yellow]")


@app.command()
def version() -> None:
    """Afficher la version d'ampy."""
    from ampy import __version__
    console.print(f"ampy v{__version__}")


if __name__ == "__main__":
    app()
