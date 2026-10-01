"""
Streamlit Web Application for Ampy.
"""

import yaml
import streamlit as st
import streamlit.components.v1 as components
from copy import deepcopy

from ampy.network import (
    GeneratorSource,
    NetworkDefinition,
    NetworkLink,
    TransformerSource,
    UtilitySource,
)
from ampy.network.solver import NetworkSolver
from ampy.core.models import CircuitDefinition
from ampy.cli.exports import generate_mermaid_from_def, generate_html_report

st.set_page_config(
    page_title="Ampy - Dimensionnement Électrique",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Ampy - Moteur de Dimensionnement Électrique")
st.markdown("Interface d'analyse de réseaux électriques industriels (NF C 15-100 & UTE C 15-105).")

# --- INITIALIZATION ---
DEFAULT_NETWORK = {
    "name": "Mon Installation",
    "source": {
        "type": "transformer",
        "name": "Transfo Principal",
        "nominal_power_kva": 630.0,
        "voltage_v": 400.0,
        "ucc_percent": 4.0,
        "pcu_w": 6500.0,
        "earthing": "TN-S"
    },
    "links": [
        {
            "from_node": "Transfo Principal",
            "to_node": "TGBT",
            "is_load": False,
            "circuit": {
                "name": "Liaison Transfo-TGBT",
                "load": {
                    "power_kw": 250.0,
                    "voltage_v": 400.0,
                    "phases": "three_phase",
                    "cos_phi": 0.85
                },
                "cable": {
                    "length_m": 10.0,
                    "conductor": "Cu",
                    "insulation": "XLPE"
                },
                "installation": {
                    "method": "F"
                }
            }
        }
    ]
}

if "network_data" not in st.session_state:
    st.session_state.network_data = deepcopy(DEFAULT_NETWORK)

def get_node_list():
    """Returns a list of all existing nodes to act as parents."""
    nodes = [st.session_state.network_data["source"]["name"]]
    for lk in st.session_state.network_data.get("links", []):
        if lk["to_node"] not in nodes:
            nodes.append(lk["to_node"])
    return nodes

# --- SIDEBAR: MODE SELECTION ---
st.sidebar.header("⚙️ Mode d'Édition")
edit_mode = st.sidebar.radio("Interface :", ["Mode Visuel (Boutons)", "Mode Avancé (YAML)"])

st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Réinitialiser le réseau", use_container_width=True):
    st.session_state.network_data = deepcopy(DEFAULT_NETWORK)
    st.rerun()

# --- BUILDER LOGIC ---
if edit_mode == "Mode Visuel (Boutons)":
    
    col_src, col_link = st.columns([1, 1])
    
    # 1. SOURCE CONFIGURATION
    with col_src:
        with st.expander("🏭 Configuration de la Source", expanded=True):
            src = st.session_state.network_data["source"]
            new_type = st.selectbox("Type de source", ["transformer", "generator", "utility"], 
                                    index=["transformer", "generator", "utility"].index(src.get("type", "transformer")))
            new_name = st.text_input("Nom de la source", src.get("name", "Transfo Principal"))
            new_v = st.number_input("Tension (V)", value=float(src.get("voltage_v", 400.0)), step=10.0)
            new_earthing = st.selectbox("Régime de Neutre", ["TN-S", "TN-C", "TT", "IT"], 
                                        index=["TN-S", "TN-C", "TT", "IT"].index(src.get("earthing", "TN-S")))
            
            if new_type == "transformer":
                new_kva = st.number_input("Puissance Apparente (kVA)", value=float(src.get("nominal_power_kva", 630.0)), step=50.0)
                new_ucc = st.number_input("Ucc (%)", value=float(src.get("ucc_percent", 4.0)), step=0.5)
            elif new_type == "generator":
                new_kva = st.number_input("Puissance Apparente (kVA)", value=float(src.get("nominal_power_kva", 630.0)), step=50.0)
                new_xd = st.number_input("X''d (%)", value=float(src.get("xd_subtransient_percent", 15.0)), step=1.0)
            else:
                new_ik3 = st.number_input("Ik3 Réseau (kA)", value=float(src.get("ik3_ka", 20.0)), step=1.0)
                
            if st.button("💾 Mettre à jour la source", use_container_width=True):
                st.session_state.network_data["source"]["type"] = new_type
                st.session_state.network_data["source"]["name"] = new_name
                st.session_state.network_data["source"]["voltage_v"] = new_v
                st.session_state.network_data["source"]["earthing"] = new_earthing
                if new_type == "transformer":
                    st.session_state.network_data["source"]["nominal_power_kva"] = new_kva
                    st.session_state.network_data["source"]["ucc_percent"] = new_ucc
                elif new_type == "generator":
                    st.session_state.network_data["source"]["nominal_power_kva"] = new_kva
                    st.session_state.network_data["source"]["xd_subtransient_percent"] = new_xd
                else:
                    st.session_state.network_data["source"]["ik3_ka"] = new_ik3
                st.rerun()

    # 2. LINK ADDITION
    with col_link:
        with st.expander("➕ Ajouter un Départ (Circuit)", expanded=True):
            with st.form("add_link_form", clear_on_submit=True):
                parent = st.selectbox("Nœud Parent (Amont)", get_node_list())
                child = st.text_input("Nom du nouveau départ (Aval)", "Départ 1")
                is_load = st.checkbox("Est-ce une charge terminale (ex: Moteur) ?", value=True)
                
                st.markdown("**Charge**")
                p_kw = st.number_input("Puissance (kW)", value=10.0, step=1.0)
                cos_phi = st.number_input("Cos Phi", value=0.85, step=0.05)
                
                st.markdown("**Câble**")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    length = st.number_input("Longueur (m)", value=20.0, step=5.0)
                    mat = st.selectbox("Matériau", ["Cu", "Al"])
                with col_c2:
                    ins = st.selectbox("Isolant", ["XLPE", "PVC"])
                    method = st.selectbox("Méthode", ["E", "F", "C", "B"])
                
                submitted = st.form_submit_button("Ajouter au réseau", use_container_width=True)
                if submitted:
                    if child in get_node_list():
                        st.error("Ce nom de départ existe déjà.")
                    else:
                        new_link = {
                            "from_node": parent,
                            "to_node": child,
                            "is_load": is_load,
                            "circuit": {
                                "name": f"Liaison {parent}-{child}",
                                "load": {
                                    "power_kw": p_kw,
                                    "voltage_v": st.session_state.network_data["source"].get("voltage_v", 400.0),
                                    "phases": "three_phase",
                                    "cos_phi": cos_phi
                                },
                                "cable": {
                                    "length_m": length,
                                    "conductor": mat,
                                    "insulation": ins
                                },
                                "installation": {
                                    "method": method
                                }
                            }
                        }
                        if "links" not in st.session_state.network_data:
                            st.session_state.network_data["links"] = []
                        st.session_state.network_data["links"].append(new_link)
                        st.rerun()

    # 3. MANAGE EXISTING LINKS
    with st.expander("⚙️ Gérer les départs existants"):
        if not st.session_state.network_data.get("links"):
            st.info("Aucun départ n'a été ajouté pour le moment.")
        else:
            for idx, lk in enumerate(st.session_state.network_data["links"]):
                col1, col2 = st.columns([4, 1])
                circ = lk["circuit"]
                desc = f"**{lk['from_node']} ➔ {lk['to_node']}** : {circ['load'].get('power_kw', '?')} kW, {circ['cable']['length_m']}m {circ['cable']['conductor']}"
                col1.markdown(desc)
                if col2.button("Supprimer", key=f"del_{idx}"):
                    st.session_state.network_data["links"].pop(idx)
                    st.rerun()

else:
    # --- ADVANCED MODE (YAML) ---
    yaml_str = yaml.dump(st.session_state.network_data, allow_unicode=True, sort_keys=False)
    edited_yaml = st.text_area("Éditeur de réseau (YAML)", value=yaml_str, height=500)
    if st.button("Appliquer les modifications YAML"):
        try:
            parsed = yaml.safe_load(edited_yaml)
            st.session_state.network_data = parsed
            st.rerun()
        except Exception as e:
            st.error(f"Erreur YAML : {e}")


# --- ENGINE RESOLUTION ---
def solve_network(data: dict):
    try:
        data_copy = deepcopy(data)
        src_data = data_copy.get("source", {})
        src_type = src_data.pop("type", "transformer")
        
        if src_type == "transformer":
            source = TransformerSource(**src_data)
        elif src_type == "generator":
            source = GeneratorSource(**src_data)
        else:
            source = UtilitySource(**src_data)

        raw_links = data_copy.get("links", [])
        if not raw_links:
            return None, None

        links = []
        for lk in raw_links:
            circuit_data = lk.pop("circuit")
            circuit = CircuitDefinition(**circuit_data)
            links.append(NetworkLink(circuit=circuit, **lk))

        net = NetworkDefinition(name=data_copy.get("name", "Réseau"), source=source, links=links)
        solver = NetworkSolver()
        result = solver.solve(net)
        return net, result
        
    except Exception as e:
        st.error(f"Erreur de calcul : {e}")
        return None, None

st.markdown("---")
st.header("Analyse & Résultats")

net_def, net_res = None, None
if not st.session_state.network_data.get("links"):
    st.info("Le réseau est vide. Veuillez ajouter au moins un départ pour lancer l'analyse.")
else:
    net_def, net_res = solve_network(st.session_state.network_data)

if net_def and net_res:
    # Summary
    if net_res.is_compliant:
        st.success(f"✅ L'installation '{net_res.network_name}' est CONFORME.")
    else:
        st.error(f"❌ L'installation '{net_res.network_name}' présente des NON-CONFORMITÉS.")
        
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Résultats par Nœud", "📐 Schéma Unifilaire", "📄 Note de Calcul"])
    
    with tab1:
        st.subheader("Paramètres de Source")
        st.info(f"**Ik3 source** : {net_res.source_ik3_a/1000:.2f} kA  |  **Z source** : {net_res.source_impedance.z_total_ohm*1000:.2f} mΩ")
        
        data_table = []
        for name, node in net_res.node_results.items():
            if node.sizing:
                s_ph = f"{node.sizing.selected_section_mm2:g}"
                s_n = f"{node.sizing.neutral_section_mm2:g}" if node.sizing.neutral_section_mm2 else "-"
                s_pe = f"{node.sizing.pe_section_mm2:g}" if node.sizing.pe_section_mm2 else "-"
                section = f"{s_ph} / {s_n} / {s_pe}"
                breaker = f"{node.sizing.breaker_ref} ({node.sizing.breaker_icu_ka}kA)" if node.sizing.breaker_ref else f"{node.sizing.in_a:.0f}A"
            else:
                section = "-"
                breaker = "-"
                
            sel = "-"
            if node.selectivity:
                if node.selectivity.status.value == "TOTAL":
                    sel = "TOTALE"
                elif node.selectivity.status.value == "PARTIAL":
                    sel = f"PARTIELLE (<{node.selectivity.limit_ka:.1f}kA)"
                else:
                    sel = "AUCUNE"
                    
            ik3 = round(node.short_circuit.ik3_max_a / 1000.0, 2)
            ik1 = round(node.short_circuit.ik1_min_a, 0)
            du = round(node.cumulative_du_percent, 2)
            ok = "✅" if (node.sizing and node.sizing.is_compliant) else "❌"
            
            data_table.append({
                "Nœud": name,
                "Section S/N/PE (mm²)": section,
                "Disjoncteur": breaker,
                "Sélectivité": sel,
                "Ik3max (kA)": ik3,
                "Ik1min (A)": ik1,
                "ΔU cumul (%)": du,
                "Conforme": ok
            })
            
        if data_table:
            st.dataframe(data_table, use_container_width=True)
        else:
            st.info("Ajoutez des départs pour voir les résultats.")
        
    with tab2:
        import html
        mermaid_code = generate_mermaid_from_def(net_res, net_def)
        escaped_mermaid = html.escape(mermaid_code)
        htmlcode = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin: 0; padding: 20px; background: white;">
            <pre class="mermaid" style="text-align: center;">
{escaped_mermaid}
            </pre>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
            </script>
        </body>
        </html>
        """
        components.html(htmlcode, height=600, scrolling=True)

    with tab3:
        html_report = generate_html_report(net_res, net_def)
        components.html(html_report, height=800, scrolling=True)
        st.download_button("Télécharger la Note de Calcul (HTML)", html_report, file_name="note_de_calcul.html", mime="text/html")
        st.download_button("Télécharger le réseau (YAML)", yaml.dump(st.session_state.network_data, sort_keys=False), file_name="reseau.yaml", mime="application/x-yaml")

