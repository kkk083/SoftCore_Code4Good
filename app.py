import streamlit as st
import pandas as pd
import numpy as np
from streamlit_folium import st_folium
from ai.report_ai import ReportAI
from ai.security_advisor_ai import SecurityAdvisor
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime
from io import BytesIO
from src.data_loader import merge_data, load_hazard_zones
from src.resilience import calculate_resilience_batch, simulate_cyclone_impact, get_cyclone_category
from src.map_generator import create_base_map, add_resilience_layer, add_hazard_layer, add_legend
from src.alerts import generate_summary_stats, get_evacuation_list
from src.citizen_alerts import (
    save_alert,
    get_all_alerts_summary,
    get_region_alert_stats,
    clear_old_alerts
)



# CONFIGURATION
st.set_page_config(
    page_title="IslandGuard 🇲🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)



# CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a9850 0%, #0d5c2c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 1rem;
    }
    .main-header h1 {
        font-size: clamp(1.5rem, 4vw, 2.5rem);
        margin: 0;
    }
    .main-header p {
        font-size: clamp(0.9rem, 2vw, 1.1rem);
        margin: 0.5rem 0 0 0;
    }
    .role-badge-citizen {
        background-color: #1a9850;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .role-badge-rescue {
        background-color: #d73027;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
    }
    @media (max-width: 768px) {
        .stButton button { width: 100% !important; }
    }
</style>
""", unsafe_allow_html=True)



# SESSION STATE
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Citoyen'
if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = False



# FONCTIONS UTILITAIRES
@st.cache_data
def load_base_data():
    """Charge les données de base"""
    try:
        df = merge_data()
        df = calculate_resilience_batch(df)
        return df
    except Exception as e:
        st.error(f"Erreur chargement données: {e}")
        return None


def play_alert_sound():
    """Notification sonore pour alertes critiques"""
    st.markdown("""
        <audio autoplay>
            <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869.wav" type="audio/wav">
        </audio>
    """, unsafe_allow_html=True)


def generate_pdf_report(advice, region_name, cyclone_severity):
    """
    Génère un PDF du rapport IA
    
    Returns:
        BytesIO: Buffer contenant le PDF
    """
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "IslandGuard - Rapport de Securite", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
        pdf.cell(0, 5, f"Region: {region_name}", ln=True, align="C")
        pdf.cell(0, 5, f"Cyclone: {cyclone_severity}/100", ln=True, align="C")
        pdf.ln(10)
        
        # Résumé exécutif
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Resume Executif", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, advice.get("executive_summary", "N/A"))
        pdf.ln(5)
        
        # Évaluation menace
        threat = advice.get("threat_assessment", {})
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Evaluation de la Menace", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"Severite: {threat.get('severity_level', 'N/A')}", ln=True)
        pdf.cell(0, 5, f"Delai: {threat.get('timeframe', 'N/A')}", ln=True)
        
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, "Risques immediats:", ln=True)
        pdf.set_font("Arial", "", 10)
        for risk in threat.get("immediate_risks", [])[:5]:
            pdf.multi_cell(0, 5, f"  - {risk}")
        pdf.ln(5)
        
        # Priorités évacuation
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Priorites d'Evacuation", ln=True)
        pdf.set_font("Arial", "", 10)
        for i, region in enumerate(advice.get("evacuation_priorities", [])[:10], 1):
            pdf.cell(0, 5, f"{i}. {region}", ln=True)
        pdf.ln(5)
        
        # Recommandations critiques
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Recommandations Critiques", ln=True)
        pdf.set_font("Arial", "", 10)
        for rec in advice.get("critical_recommendations", [])[:5]:
            pdf.multi_cell(0, 5, f"  - {rec}")
        
        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, "Powered by Google Gemini AI - IslandGuard 2025", align="C")
        
        # Sauvegarder dans buffer
        pdf_output = BytesIO()
        pdf_string = pdf.output(dest='S').encode('latin-1')
        pdf_output.write(pdf_string)
        pdf_output.seek(0)
        
        return pdf_output
        
    except Exception as e:
        st.error(f" Erreur génération PDF: {e}")
        return None


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def main():
    """Fonction principale"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1> IslandGuard 🇲🇺</h1>
        <p>Système de surveillance de la résilience climatique de l'île Maurice</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chargement données
    with st.spinner(" Chargement des données..."):
        base_df = load_base_data()
    
    if base_df is None or len(base_df) == 0:
        st.error(" Impossible de charger les données.")
        return
    

    # SIDEBAR
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Flag_of_Mauritius.svg/320px-Flag_of_Mauritius.svg.png", 
                 width=200)
        
        st.header(" Sélection Rôle")
        
        # Dropdown rôle
        user_role = st.selectbox(
            "Vous êtes:",
            options=["Citoyen", "Secours/Gouvernement"],
            index=0 if st.session_state.user_role == "Citoyen" else 1
        )
        st.session_state.user_role = user_role
        
        # Badge rôle
        if user_role == "Citoyen":
            st.markdown('<span class="role-badge-citizen"> MODE CITOYEN</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="role-badge-rescue"> MODE SECOURS</span>', unsafe_allow_html=True)
        
        st.divider()
        
        # SIMULATEUR CYCLONE
        st.subheader(" Simulateur Cyclone")
        cyclone_severity = st.slider(
            "Intensité du cyclone",
            min_value=0,
            max_value=100,
            value=0,
            step=5
        )
        
        cyclone_cat = get_cyclone_category(cyclone_severity)
        
        if cyclone_severity == 0:
            st.info(f" {cyclone_cat}")
        elif cyclone_severity < 60:
            st.warning(f" {cyclone_cat}")
        else:
            st.error(f" {cyclone_cat}")
            play_alert_sound()
        
        # Appliquer simulation
        if cyclone_severity > 0:
            df = simulate_cyclone_impact(base_df, cyclone_severity)
        else:
            df = base_df.copy()
        
        # Ajouter alertes citoyennes
        df = get_all_alerts_summary(df)
        
        st.divider()
        
        # SÉLECTION RÉGION (pour citoyen)
        if user_role == "Citoyen":
            st.subheader(" Ma Région")
            regions_list = sorted(df['region_name'].unique())
            selected_region = st.selectbox("Sélectionnez votre région", regions_list)
        
        st.divider()
        
        # STATS GLOBALES
        st.subheader(" Statistiques")
        stats = generate_summary_stats(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(" Régions", stats['total_regions'])
            st.metric(" Sûres", stats['safe_regions'])
        with col2:
            st.metric(" À risque", stats['at_risk_regions'])
            st.metric(" Moy.", f"{stats['avg_resilience']:.1f}")
    
  
    # ROUTAGE INTERFACES
    if user_role == "Citoyen":
        render_citizen_interface(df, selected_region, cyclone_severity)
    else:
        render_rescue_interface(df, cyclone_severity, base_df)
    
 
    # FOOTER
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <p style="color: gray; margin-bottom: 10px;">IslandGuard 🇲🇺 | Code4Good Hackathon 2025</p>
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 10px 20px; 
                        border-radius: 20px; 
                        display: inline-block;">
                <span style="color: white; font-weight: bold;">⚡ Powered by Google Gemini AI</span>
            </div>
        </div>
        """, unsafe_allow_html=True)



# INTERFACE CITOYEN
def render_citizen_interface(df, selected_region, cyclone_severity):
    """Interface pour les citoyens"""
    
    st.header(" Interface Citoyen")
    
    # INFO RÉGION
    region_data = df[df['region_name'] == selected_region].iloc[0]
    resilience = region_data['resilience_index']
    category = region_data['category']
    
    # Son d'alerte si critique
    if category == 'critical':
        play_alert_sound()
    
    alert_stats = get_region_alert_stats(region_data['region_id'])
    
    # AFFICHAGE INFO RÉGION
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f" {selected_region}")
        
        if category == 'critical':
            st.error(f" Résilience: {resilience:.1f}/100 - DANGER CRITIQUE")
        elif category == 'low':
            st.warning(f" Résilience: {resilience:.1f}/100 - ATTENTION")
        elif category == 'medium':
            st.warning(f" Résilience: {resilience:.1f}/100 - VIGILANCE")
        else:
            st.success(f" Résilience: {resilience:.1f}/100 - ZONE SÛRE")
        
        st.write(f"**Exposition:** {region_data['exposure']:.0f}/100")
        st.write(f"**Vulnérabilité:** {region_data['vulnerability']:.0f}/100")
        st.write(f"**Adaptation:** {region_data['adaptation']:.0f}/100")
    
    with col2:
        st.metric(" Alertes Danger", alert_stats['danger_count'])
        st.metric(" Alertes Sécurité", alert_stats['safe_count'])
    
    with col3:
        st.metric(" Total Signalements", alert_stats['total_count'])
    
    st.divider()
    
    # BOUTONS D'ALERTE
    st.subheader(" Signaler votre situation")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚨 JE SUIS EN DANGER", use_container_width=True, type="primary"):
            if save_alert(region_data['region_id'], 'danger'):
                st.success("Alerte envoyée aux secours!")
                play_alert_sound()
                st.balloons()
                st.rerun()
    
    with col2:
        if st.button("✅ JE SUIS EN SÉCURITÉ", use_container_width=True):
            if save_alert(region_data['region_id'], 'safe'):
                st.success(" Merci pour votre signalement!")
                st.rerun()
    
    st.info(" Vos signalements aident les secours à prioriser les interventions")
    
    st.divider()
    
    # CARTE
    st.subheader(" Carte de Résilience")
    
    map_obj = create_base_map()
    map_obj = add_resilience_layer(map_obj, df)
    map_obj = add_legend(map_obj)
    
    st_folium(map_obj, width=None, height=500, use_container_width=True, key="citizen_map")
    
    st.divider()
    
    # CONSEILS SÉCURITÉ IA
    st.title(" Conseils de Sécurité IA")

    try:
        advisor = SecurityAdvisor()

        st.write(" Autorisez la géolocalisation pour obtenir des conseils personnalisés.")

        loc = streamlit_geolocation()

        disaster_type = st.selectbox(
            " Type de catastrophe",
            ["cyclone", "inondation", "tsunami", "glissement de terrain", "tremblement de terre"]
        )

        if loc and loc.get("latitude") and loc.get("longitude"):
            latitude = loc["latitude"]
            longitude = loc["longitude"]
            
            # Trouver région
            temp_advisor = SecurityAdvisor()
            nearest_region = temp_advisor._find_nearest_region(latitude, longitude)
            
            if nearest_region:
                st.success(f" Vous êtes à: **{nearest_region['region_name']}**")
                st.caption(f"Coordonnées: {latitude:.4f}, {longitude:.4f}")
            else:
                st.success(f" Position détectée: {latitude:.4f}, {longitude:.4f}")
            
            if st.button(" Obtenir Conseils de Sécurité", type="primary"):
                with st.spinner("📡 Analyse en cours..."):
                    try:
                        advice = advisor.get_advice_for_location(
                            latitude, longitude, disaster_type, cyclone_severity=cyclone_severity
                        )
                        
                        st.markdown(f"##  {advice['location']}")
                        st.markdown(f"### {advice['risk_level']}")
                        
                        if cyclone_severity > 0:
                            st.error(f" **CYCLONE ACTIF** - Intensité: {cyclone_severity}/100")
                        
                        st.markdown("###  À Faire Maintenant")
                        st.error(advice['immediate_action'])
                        
                        st.markdown("###  Comment vous Protéger")
                        for tip in advice['protection_tips']:
                            st.write(f"• {tip}")
                        
                        st.markdown("###  Zones Sûres")
                        for zone in advice['safe_zones']:
                            with st.expander(f" {zone['name']} ({zone['distance_km']:.1f} km)"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Distance", f"{zone['distance_km']:.1f} km")
                                with col2:
                                    st.metric("Résilience", f"{zone['resilience_score']:.0f}/100")
                                with col3:
                                    st.metric("Durée", zone['travel_time'])
                        
                        st.markdown("### 📞 Numéros d'Urgence")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Police", "999")
                        with col2:
                            st.metric("Ambulance", "114")
                        with col3:
                            st.metric("Gestion Crise", "116")
                    
                    except Exception as e:
                        st.error(f" Erreur: {e}")
        else:
            st.warning(" Veuillez autoriser la géolocalisation.")
    
    except Exception as e:
        st.error(f" Erreur SecurityAdvisor: {e}")



# INTERFACE SECOURS
def render_rescue_interface(df, cyclone_severity, base_df):
    """Interface pour les secours"""
    
    st.header(" Interface Secours / Gouvernement")
    
    # COMPTEURS LIVE
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_alerts = int(df['citizen_danger'].sum() + df['citizen_safe'].sum())
        st.metric(" Alertes Total", total_alerts)

    with col2:
        danger_count = int(df['citizen_danger'].sum())
        st.metric(" En Danger", danger_count)

    with col3:
        safe_count = int(df['citizen_safe'].sum())
        st.metric(" En Sécurité", safe_count)

    with col4:
        critical_regions = len(df[df['category'].isin(['low', 'critical'])])
        st.metric(" Régions Critiques", critical_regions)
        if critical_regions > 0:
            play_alert_sound()

    st.divider()
    
    # TABS
    tabs = st.tabs([
        "🗺️ Carte", 
        "📊 Alertes", 
        "🚁 Évacuations", 
        "📈 Analyse", 
        "🔄 Avant/Après", 
        "🤖 Rapport IA"
    ])
    
    # TAB 1: CARTE
    with tabs[0]:
        st.subheader(" Carte Opérationnelle")
        
        map_obj = create_base_map()
        map_obj = add_resilience_layer(map_obj, df)
        
        try:
            hazard_gdf = load_hazard_zones()
            if len(hazard_gdf) > 0:
                map_obj = add_hazard_layer(map_obj, hazard_gdf)
        except:
            pass
        
        map_obj = add_legend(map_obj)
        st_folium(map_obj, width=None, height=600, use_container_width=True, key="rescue_map")
    
    # TAB 2: ALERTES
    with tabs[1]:
        st.subheader(" Alertes Citoyennes")
        
        critical_regions = df[
            (df['citizen_danger_ratio'] > 0.5) | (df['category'].isin(['low', 'critical']))
        ].sort_values('citizen_danger_ratio', ascending=False)
        
        if len(critical_regions) > 0:
            st.error(f" {len(critical_regions)} région(s) critiques")
            
            for _, region in critical_regions.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{region['region_name']}**")
                with col2:
                    st.metric("🚨", int(region['citizen_danger']))
                with col3:
                    st.metric("✅", int(region['citizen_safe']))
                with col4:
                    ratio = region['citizen_danger_ratio']
                    if ratio > 0.7:
                        st.error(f"{ratio*100:.0f}%")
                    elif ratio > 0.4:
                        st.warning(f"{ratio*100:.0f}%")
                    else:
                        st.info(f"{ratio*100:.0f}%")
        else:
            st.success(" Aucune alerte critique")
        
        st.divider()
        
        if st.button(" Nettoyer alertes > 24h"):
            deleted = clear_old_alerts(24)
            st.success(f" {deleted} alertes supprimées")
            st.rerun()
    
    # TAB 3: ÉVACUATIONS
    with tabs[2]:
        st.subheader(" Évacuations")
        
        evacuation_list = get_evacuation_list(df)
        
        if len(evacuation_list) > 0:
            st.error(f" {len(evacuation_list)} région(s) à évacuer")
            for _, region in evacuation_list.iterrows():
                st.warning(f"**{region['region_name']}** - {region['resilience_index']:.1f}/100")
        else:
            st.success(" Aucune évacuation nécessaire")
    
    # TAB 4: ANALYSE
    with tabs[3]:
        st.subheader(" Analyse")
        
        display_df = df[[
            'region_name', 'resilience_index', 'category',
            'citizen_danger', 'citizen_safe',
            'exposure', 'vulnerability', 'adaptation'
        ]].copy()
        
        display_df.columns = [
            'Région', 'Résilience', 'Catégorie',
            ' Danger', ' Sécurité',
            'Exposition', 'Vulnérabilité', 'Adaptation'
        ]
        
        st.dataframe(display_df, use_container_width=True)
        
        csv = display_df.to_csv(index=False)
        st.download_button(
            " Exporter CSV",
            data=csv,
            file_name=f"rapport_cyclone_{cyclone_severity}.csv",
            mime="text/csv"
        )
    
    # TAB 5: AVANT/APRÈS
    with tabs[4]:
        st.subheader(" Comparaison Avant/Après")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("###  AVANT")
            before_stats = generate_summary_stats(base_df)
            st.metric("Résilience", f"{before_stats['avg_resilience']:.1f}")
            st.metric("Sûres", before_stats['safe_regions'])
            st.metric("À risque", before_stats['at_risk_regions'])
            
            map_before = create_base_map()
            map_before = add_resilience_layer(map_before, base_df)
            map_before = add_legend(map_before)
            st_folium(map_before, width=350, height=300, key="map_before")
        
        with col2:
            st.markdown(f"###  APRÈS ({cyclone_severity})")
            after_stats = generate_summary_stats(df)
            st.metric("Résilience", f"{after_stats['avg_resilience']:.1f}", 
                     delta=f"{after_stats['avg_resilience'] - before_stats['avg_resilience']:.1f}")
            st.metric("Sûres", after_stats['safe_regions'],
                     delta=after_stats['safe_regions'] - before_stats['safe_regions'])
            st.metric("À risque", after_stats['at_risk_regions'],
                     delta=after_stats['at_risk_regions'] - before_stats['at_risk_regions'])
            
            map_after = create_base_map()
            map_after = add_resilience_layer(map_after, df)
            map_after = add_legend(map_after)
            st_folium(map_after, width=350, height=300, key="map_after")
    
    # TAB 6: RAPPORT IA
    with tabs[5]:
        st.subheader(" Rapport IA")

        try:
            advisor = ReportAI()

            regions = ["Île Maurice (toutes régions)"] + list(advisor.resilience_data["region_name"].unique())
            selected = st.selectbox(" Région:", regions)

            region_id = None
            if selected != "Île Maurice (toutes régions)":
                region_id = advisor.resilience_data[
                    advisor.resilience_data["region_name"] == selected
                ]["region_id"].values[0]

            if st.button(" Générer Rapport IA"):
                with st.spinner(" Analyse IA en cours..."):
                    try:
                        advice = advisor.generate_security_advice(region_id)
                        
                        st.success(" Rapport généré!")
                        
                        # BOUTON EXPORT PDF
                        pdf_buffer = generate_pdf_report(advice, selected, cyclone_severity)
                        if pdf_buffer:
                            st.download_button(
                                label=" Télécharger Rapport PDF",
                                data=pdf_buffer,
                                file_name=f"rapport_islandguard_{selected}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf",
                                type="primary"
                            )
                        
                        st.divider()
                        
                        # AFFICHAGE
                        st.subheader(" Résumé")
                        st.info(advice.get("executive_summary", "N/A"))
                        
                        col1, col2 = st.columns(2)
                        threat = advice.get("threat_assessment", {})
                        with col1:
                            st.metric("Sévérité", threat.get("severity_level", "N/A"))
                        with col2:
                            st.metric("Délai", threat.get("timeframe", "N/A"))
                        
                        st.subheader(" Priorités Évacuation")
                        for i, region in enumerate(advice.get("evacuation_priorities", [])[:5], 1):
                            st.write(f"{i}. {region}")
                        
                        st.subheader(" Recommandations")
                        for rec in advice.get("critical_recommendations", []):
                            st.error(rec)
                            
                    except Exception as e:
                        st.error(f" Erreur: {e}")
        
        except Exception as e:
            st.error(f" Erreur ReportAI: {e}")


if __name__ == "__main__":
    main()