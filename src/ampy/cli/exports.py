"""
ampy.cli.exports
================

Generate Mermaid diagrams and HTML reports from network analysis results.
"""

from __future__ import annotations

from ampy.network import NetworkResult


def generate_mermaid(result: NetworkResult) -> str:
    """Generate a Mermaid.js flowchart representing the electrical network."""
    lines = [
        "graph TD",
        f"    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;"
    ]

    # Source node
    lines.append(
        f"    {result.network_name}[\"⚡ <b>{result.network_name}</b><br/>"
        f"Ik3={result.source_ik3_a/1000:.1f}kA\"]"
    )

    # We need to map from_node -> to_node to create the graph edges.
    # Since NetworkResult only gives node results, we have to deduce the edges 
    # from the original network definition. Wait, NetworkResult doesn't contain the original tree structure natively,
    # but we can pass it or reconstruct it. Actually, `NodeResult` has `sizing` which doesn't include from_node.
    # Let's pass the NetworkDefinition as well, or we can just link it if we know the topology.
    # But wait, `generate_mermaid` signature can take `(result, net_def)`.
    pass


def generate_mermaid_from_def(result: NetworkResult, net_def: "NetworkDefinition") -> str:
    """Generate Mermaid flowchart."""
    lines = [
        "flowchart TD",
    ]

    # Use a dictionary to map real names to safe IDs (N0, N1, ...)
    id_map = {}
    def get_id(name: str) -> str:
        if name not in id_map:
            id_map[name] = f"N{len(id_map)}"
        return id_map[name]

    source_name = net_def.source.name
    ik3_src = result.source_ik3_a / 1000.0
    
    src_id = get_id(source_name)
    lines.append(f"    {src_id}[\"{source_name}<br/>Ik3 = {ik3_src:.1f} kA\"]")

    for link in net_def.links:
        f_id = get_id(link.from_node)
        t_id = get_id(link.to_node)
        node_res = result.node_results.get(link.to_node)
        
        edge_text = ""
        if node_res and node_res.sizing:
            s_ph = f"{node_res.sizing.selected_section_mm2:g}"
            s_n = f"{node_res.sizing.neutral_section_mm2:g}" if node_res.sizing.neutral_section_mm2 else "-"
            s_pe = f"{node_res.sizing.pe_section_mm2:g}" if node_res.sizing.pe_section_mm2 else "-"
            
            breaker = node_res.sizing.breaker_ref or f"{node_res.sizing.in_a:.0f}A"
            edge_text = f"|\"{breaker}<br/>{s_ph}/{s_n}/{s_pe} mm2\"|"
            
        if node_res:
            ik3 = node_res.short_circuit.ik3_max_a / 1000.0
            ik1 = node_res.short_circuit.ik1_min_a
            du = node_res.cumulative_du_percent
            node_text = f"{link.to_node}<br/>Ik3={ik3:.1f}kA , Ik1={ik1:.0f}A<br/>dU={du:.1f}%"
        else:
            node_text = f"{link.to_node}"

        node_text_clean = node_text.replace('"', '')
        
        if edge_text:
            lines.append(f"    {f_id} -->{edge_text} {t_id}[\"{node_text_clean}\"]")
        else:
            lines.append(f"    {f_id} --> {t_id}[\"{node_text_clean}\"]")

    return "\n".join(lines)


def generate_html_report(result: NetworkResult, net_def: "NetworkDefinition") -> str:
    """Generate a clean HTML calculation note."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Note de Calcul - {result.network_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; }}
        h1 {{ border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f8f9fa; font-weight: 600; }}
        tr:nth-child(even) {{ background-color: #fcfcfc; }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .warning {{ color: #e67e22; font-weight: bold; }}
        .error {{ color: #e74c3c; font-weight: bold; }}
        .metadata {{ margin-bottom: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Note de Calcul Électrique</h1>
    
    <div class="metadata">
        <p><strong>Installation :</strong> {result.network_name}</p>
        <p><strong>Source :</strong> {net_def.source.name} (Ik3 = {result.source_ik3_a/1000:.2f} kA)</p>
        <p><strong>Conformité Globale :</strong> <span class="{'success' if result.is_compliant else 'error'}">
            {'CONFORME' if result.is_compliant else 'NON CONFORME'}</span>
        </p>
    </div>

    <h2>Résultats par circuit</h2>
    <table>
        <thead>
            <tr>
                <th>Nœud / Départ</th>
                <th>Câble S/N/PE (mm²)</th>
                <th>Disjoncteur</th>
                <th>Sélectivité</th>
                <th>Ik3 max (kA)</th>
                <th>Ik1 min (A)</th>
                <th>ΔU Cumul (%)</th>
                <th>Statut</th>
            </tr>
        </thead>
        <tbody>
"""

    for link in net_def.links:
        node = result.node_results.get(link.to_node)
        if not node:
            continue
            
        if node.sizing:
            s_ph = f"{node.sizing.selected_section_mm2:g}"
            s_n = f"{node.sizing.neutral_section_mm2:g}" if node.sizing.neutral_section_mm2 else "-"
            s_pe = f"{node.sizing.pe_section_mm2:g}" if node.sizing.pe_section_mm2 else "-"
            section = f"{s_ph} / {s_n} / {s_pe}"
            breaker = f"{node.sizing.breaker_ref}<br><small>({node.sizing.breaker_icu_ka}kA)</small>" if node.sizing.breaker_ref else f"{node.sizing.in_a:.0f}A"
        else:
            section = "-"
            breaker = "-"

        sel = "-"
        if node.selectivity:
            if node.selectivity.status.value == "TOTAL":
                sel = "<span class='success'>TOTALE</span>"
            elif node.selectivity.status.value == "PARTIAL":
                sel = f"<span class='warning'>PARTIELLE<br><small>(&lt;{node.selectivity.limit_ka:.1f}kA)</small></span>"
            else:
                sel = "<span class='error'>AUCUNE</span>"

        ik3 = f"{node.short_circuit.ik3_max_a/1000:.1f}"
        ik1 = f"{node.short_circuit.ik1_min_a:.0f}"
        du = f"{node.cumulative_du_percent:.2f}"
        ok = "✅" if (node.sizing and node.sizing.is_compliant) else "⚠️"

        html += f"""
            <tr>
                <td><strong>{link.to_node}</strong></td>
                <td>{section}</td>
                <td>{breaker}</td>
                <td>{sel}</td>
                <td>{ik3}</td>
                <td>{ik1}</td>
                <td>{du}</td>
                <td>{ok}</td>
            </tr>
"""

    html += """
        </tbody>
    </table>
    
    <h2 style="margin-top: 50px;">Fiches Détaillées par Circuit</h2>
"""

    for link in net_def.links:
        node = result.node_results.get(link.to_node)
        if not node or not node.sizing:
            continue
            
        c = link.circuit
        s = node.sizing
        sc = node.short_circuit
        
        sel = "Aucune"
        if node.selectivity:
            if node.selectivity.status.value == "TOTAL":
                sel = "Totale"
            elif node.selectivity.status.value == "PARTIAL":
                sel = f"Partielle (Limite: {node.selectivity.limit_ka:.1f} kA)"
                
        ind_contact = "Conforme" if s.is_compliant else "Non Conforme"

        html += f"""
    <div style="border: 1px solid #ccc; border-radius: 8px; margin-bottom: 20px; padding: 20px; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; color: #2980b9;">Départ : {link.to_node}</h3>
        <p><strong>Origine :</strong> {link.from_node} &nbsp;|&nbsp; <strong>Destination :</strong> {link.to_node}</p>
        
        <table style="width: 100%; border: none; margin-top: 10px;">
            <tr>
                <td style="border: none; padding: 0; vertical-align: top; width: 50%;">
                    <h4 style="margin-bottom: 5px; color: #34495e;">⚡ Charge & Câble</h4>
                    <ul>
                        <li><strong>Puissance :</strong> {c.load.power_kw} kW (Cos φ: {c.load.cos_phi})</li>
                        <li><strong>Longueur :</strong> {c.cable.length_m} m</li>
                        <li><strong>Matériau / Isolant :</strong> {c.cable.conductor.name} / {c.cable.insulation.name}</li>
                        <li><strong>Mode de pose :</strong> {c.installation.method.name}</li>
                    </ul>
                    
                    <h4 style="margin-bottom: 5px; color: #34495e;">📐 Dimensionnement</h4>
                    <ul>
                        <li><strong>Courant d'emploi (Ib) :</strong> {s.ib_a:.1f} A</li>
                        <li><strong>Courant admissible (Iz) :</strong> {s.iz_effective_a:.1f} A</li>
                        <li><strong>Section (Ph / N / PE) :</strong> {s.selected_section_mm2} / {s.neutral_section_mm2 or '-'} / {s.pe_section_mm2 or '-'} mm²</li>
                        <li><strong>Chute de tension :</strong> {s.voltage_drop.du_percent:.2f}% (Cumul: {node.cumulative_du_percent:.2f}%)</li>
                    </ul>
                </td>
                <td style="border: none; padding: 0; vertical-align: top; width: 50%;">
                    <h4 style="margin-bottom: 5px; color: #34495e;">🛡️ Protection</h4>
                    <ul>
                        <li><strong>Disjoncteur :</strong> {s.breaker_ref}</li>
                        <li><strong>Calibre (In) :</strong> {s.in_a} A</li>
                        <li><strong>Pouv. de coupure (Icu) :</strong> {s.breaker_icu_ka} kA</li>
                        <li><strong>Sélectivité avec amont :</strong> {sel}</li>
                    </ul>
                    
                    <h4 style="margin-bottom: 5px; color: #34495e;">🔥 Court-circuit & Sécurité</h4>
                    <ul>
                        <li><strong>Ik3 aval :</strong> {sc.ik3_max_a/1000:.2f} kA</li>
                        <li><strong>Ik2 aval :</strong> {sc.ik2_max_a/1000:.2f} kA</li>
                        <li><strong>Ik1 min aval :</strong> {sc.ik1_min_a:.1f} A</li>
                        <li><strong>Contacts indirects :</strong> <span class="{'success' if s.is_compliant else 'error'}">{ind_contact}</span></li>
                    </ul>
                </td>
            </tr>
        </table>
    </div>
"""

    html += """
</body>
</html>
"""
    return html
