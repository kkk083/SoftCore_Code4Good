"""
IslandGuard - Application de résilience climatique pour l'île Maurice
🇲🇺 Code4Good Hackathon 2025

SYSTÈME À 2 ACTEURS:
- 👤 CITOYEN: Voir risques + signaler danger/sécurité
- 🚨 SECOURS: Dashboard complet + gestion alertes
"""

import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

# Imports des modules IslandGuard
from src.data_loader import merge_data, load_hazard_zones
from src.resilience import calculate_resilience_batch, simulate_cyclone_impact, get_cyclone_category
from src.map_generator import create_base_map, add_resilience_layer, add_hazard_layer, add_legend
from src.alerts import generate_summary_stats, get_evacuation_list, generate_citizen_alert
from src.citizen_alerts import (
    save_alert,
    get_all_alerts_summary,
    get_region_alert_stats,
    clear_old_alerts
)


# Configuration de la page
st.set_page_config(
    page_title="IslandGuard 🇲🇺",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)


# CSS personnalisé
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
    /* Responsive containers */
    @media (max-width: 768px) {
        .stButton button {
            width: 100% !important;
        }
    }
    /* Fix streamlit columns on mobile */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 auto !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialiser session state
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Citoyen'
if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = False


# Chargement des données (avec cache)
@st.cache_data
def load_base_data():
    """Charge les données de base"""
    try:
        df = merge_data()
        df = calculate_resilience_batch(df)
        return df
    except Exception as e:
        st.error(f"❌ Erreur chargement données: {e}")
        return None


def main():
    """Fonction principale de l'application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌴 IslandGuard 🇲🇺</h1>
        <p>Système de surveillance de la résilience climatique de l'île Maurice</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chargement données
    with st.spinner("🔄 Chargement des données..."):
        base_df = load_base_data()
    
    if base_df is None or len(base_df) == 0:
        st.error("❌ Impossible de charger les données.")
        return
    
    # ============================================================
    # SIDEBAR - Sélection rôle + contrôles communs
    # ============================================================
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Flag_of_Mauritius.svg/320px-Flag_of_Mauritius.svg.png", 
                 width=200)
        
        st.header("👤 Sélection Rôle")
        
        # Dropdown rôle
        user_role = st.selectbox(
            "Vous êtes:",
            options=["Citoyen", "Secours/Gouvernement"],
            index=0 if st.session_state.user_role == "Citoyen" else 1
        )
        st.session_state.user_role = user_role
        
        # Badge rôle
        if user_role == "Citoyen":
            st.markdown('<span class="role-badge-citizen">👤 MODE CITOYEN</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="role-badge-rescue">🚨 MODE SECOURS</span>', unsafe_allow_html=True)
        
        st.divider()
        
        # Simulateur cyclone (commun aux 2 rôles)
        st.subheader("🌀 Simulateur Cyclone")
        cyclone_severity = st.slider(
            "Intensité du cyclone",
            min_value=0,
            max_value=100,
            value=0,
            step=5
        )
        
        cyclone_cat = get_cyclone_category(cyclone_severity)
        
        if cyclone_severity == 0:
            st.info(f"✅ {cyclone_cat}")
        elif cyclone_severity < 60:
            st.warning(f"⚠️ {cyclone_cat}")
        else:
            st.error(f"🚨 {cyclone_cat}")
        
        # Appliquer simulation
        if cyclone_severity > 0:
            df = simulate_cyclone_impact(base_df, cyclone_severity)
        else:
            df = base_df.copy()
        
        # Ajouter alertes citoyennes
        df = get_all_alerts_summary(df)
        
        st.divider()
        
        # Sélection région (pour citoyen)
        if user_role == "Citoyen":
            st.subheader("📍 Ma Région")
            regions_list = sorted(df['region_name'].unique())
            selected_region = st.selectbox("Sélectionnez votre région", regions_list)
        
        st.divider()
        
        # Stats globales
        st.subheader("📊 Statistiques")
        stats = generate_summary_stats(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🏝️ Régions", stats['total_regions'])
            st.metric("✅ Sûres", stats['safe_regions'])
        with col2:
            st.metric("🚨 À risque", stats['at_risk_regions'])
            st.metric("📊 Moy.", f"{stats['avg_resilience']:.1f}")
    
    # ============================================================
    # INTERFACE CITOYEN
    # ============================================================
    if user_role == "Citoyen":
        render_citizen_interface(df, selected_region, cyclone_severity)
    
    # ============================================================
    # INTERFACE SECOURS
    # ============================================================
    else:
        render_rescue_interface(df, cyclone_severity)
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: gray; padding: 20px;">
        <p>IslandGuard 🇲🇺 | Code4Good Hackathon 2025</p>
    </div>
    """, unsafe_allow_html=True)


def render_citizen_interface(df, selected_region, cyclone_severity):
    """Interface pour les citoyens"""
    
    st.header("👤 Interface Citoyen")
    
    # Info région personnelle
    region_data = df[df['region_name'] == selected_region].iloc[0]
    resilience = region_data['resilience_index']
    category = region_data['category']
    
    # Stats alertes citoyennes pour cette région
    alert_stats = get_region_alert_stats(region_data['region_id'])
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"📍 {selected_region}")
        
        # ✅ FIX: Support 4 catégories
        if category == 'critical':
            st.error(f"🚨 Résilience: {resilience:.1f}/100 - DANGER CRITIQUE")
        elif category == 'low':
            st.warning(f"🟠 Résilience: {resilience:.1f}/100 - ATTENTION")
        elif category == 'medium':
            st.warning(f"⚠️ Résilience: {resilience:.1f}/100 - VIGILANCE")
        else:
            st.success(f"✅ Résilience: {resilience:.1f}/100 - ZONE SÛRE")
        
        st.write(f"**Exposition:** {region_data['exposure']:.0f}/100")
        st.write(f"**Vulnérabilité:** {region_data['vulnerability']:.0f}/100")
        st.write(f"**Adaptation:** {region_data['adaptation']:.0f}/100")
    
    with col2:
        st.metric("🚨 Alertes Danger", alert_stats['danger_count'])
        st.metric("✅ Alertes Sécurité", alert_stats['safe_count'])
    
    with col3:
        st.metric("👥 Total Signalements", alert_stats['total_count'])
    
    st.divider()
    
    # Boutons d'alerte citoyenne
    st.subheader("📢 Signaler votre situation")
    st.write("Aidez les secours en signalant votre état actuel:")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚨 JE SUIS EN DANGER", use_container_width=True, type="primary"):
            if save_alert(region_data['region_id'], 'danger'):
                st.success("✅ Alerte envoyée aux secours!")
                st.balloons()
                st.session_state.alert_sent = True
                st.rerun()
    
    with col2:
        if st.button("✅ JE SUIS EN SÉCURITÉ", use_container_width=True):
            if save_alert(region_data['region_id'], 'safe'):
                st.success("✅ Merci pour votre signalement!")
                st.session_state.alert_sent = True
                st.rerun()
    
    st.info("💡 Vos signalements aident les secours à prioriser les interventions")
    
    st.divider()
    
    # Carte simplifiée
    st.subheader("🗺️ Carte de Résilience")
    
    map_obj = create_base_map()
    map_obj = add_resilience_layer(map_obj, df)
    map_obj = add_legend(map_obj)  # ← LÉGENDE ICI
    
    st_folium(map_obj, width=None, height=500, use_container_width=True)
    
    # Chatbot LangChain (placeholder)
    st.divider()
    st.subheader("💬 Assistant IA - Conseils Personnalisés")
    st.info("🚧 Chatbot LangChain en cours d'intégration...")

    with st.expander("💬 Poser une question"):
        user_question = st.text_input("Posez votre question sur la sécurité cyclonique")
        if st.button("Envoyer"):
            st.warning("⏳ Chatbot en développement - Intégration LangChain prochainement")


def render_rescue_interface(df, cyclone_severity):
    """Interface pour les secours/gouvernement"""
    
    st.header("🚨 Interface Secours / Gouvernement")
    
    tabs = st.tabs(["🗺️ Carte Opérationnelle", "📊 Alertes Citoyennes", "🚁 Évacuations", "📈 Analyse"])
    
    with tabs[0]:
        st.subheader("🗺️ Carte Opérationnelle")
        
        # Carte complète
        map_obj = create_base_map()
        map_obj = add_resilience_layer(map_obj, df)
        
        try:
            hazard_gdf = load_hazard_zones()
            if len(hazard_gdf) > 0:
                map_obj = add_hazard_layer(map_obj, hazard_gdf)
        except:
            pass
        
        map_obj = add_legend(map_obj)  # ← LÉGENDE ICI
        
        st_folium(map_obj, width=None, height=600, use_container_width=True)
    
    with tabs[1]:
        st.subheader("📊 Alertes Citoyennes en Temps Réel")
        
        # ✅ FIX: Filtre régions critiques (4 catégories)
        critical_regions = df[
            (df['citizen_danger_ratio'] > 0.5) | (df['category'].isin(['low', 'critical']))
        ].sort_values('citizen_danger_ratio', ascending=False)
        
        if len(critical_regions) > 0:
            st.error(f"🚨 {len(critical_regions)} région(s) avec alertes critiques")
            
            for _, region in critical_regions.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{region['region_name']}**")
                    with col2:
                        st.metric("🚨 Danger", int(region['citizen_danger']))
                    with col3:
                        st.metric("✅ Sécurité", int(region['citizen_safe']))
                    with col4:
                        ratio = region['citizen_danger_ratio']
                        if ratio > 0.7:
                            st.error(f"⚠️ {ratio*100:.0f}%")
                        elif ratio > 0.4:
                            st.warning(f"⚠️ {ratio*100:.0f}%")
                        else:
                            st.info(f"{ratio*100:.0f}%")
        else:
            st.success("✅ Aucune alerte critique actuellement")
        
        st.divider()
        
        # Nettoyage alertes anciennes
        if st.button("🧹 Nettoyer alertes > 24h"):
            deleted = clear_old_alerts(24)
            st.success(f"✅ {deleted} alertes supprimées")
            st.rerun()
    
    with tabs[2]:
        st.subheader("🚁 Liste d'Évacuation")
        
        evacuation_list = get_evacuation_list(df)
        
        if len(evacuation_list) > 0:
            st.error(f"⚠️ {len(evacuation_list)} région(s) nécessitent une évacuation")
            
            for _, region in evacuation_list.iterrows():
                st.warning(f"**{region['region_name']}** - Résilience: {region['resilience_index']:.1f}/100")
        else:
            st.success("✅ Aucune évacuation nécessaire")
    
    with tabs[3]:
        st.subheader("📈 Analyse Comparative")
        
        # Tableau détaillé
        display_df = df[[
            'region_name', 'resilience_index', 'category',
            'citizen_danger', 'citizen_safe', 'citizen_danger_ratio',
            'exposure', 'vulnerability', 'adaptation'
        ]].copy()
        
        display_df.columns = [
            'Région', 'Résilience', 'Catégorie',
            '🚨 Danger', '✅ Sécurité', '% Danger',
            'Exposition', 'Vulnérabilité', 'Adaptation'
        ]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Export
        csv = display_df.to_csv(index=False)
        st.download_button(
            "📥 Exporter rapport complet",
            data=csv,
            file_name=f"rapport_secours_cyclone{cyclone_severity}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()