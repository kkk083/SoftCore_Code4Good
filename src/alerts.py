"""
Module de gestion des alertes citoyens
🎯 DÉVELOPPÉ PAR: DEV 4
🔧 FIX: Support 4 catégories
"""

import pandas as pd
from utils.config import ALERT_THRESHOLDS


def check_region_risk(region_row):
    """Vérifie si une région est à risque."""
    return region_row['category'] in ['low', 'critical']


def generate_alert_message(region_name, resilience_score, population=None):
    """Génère message d'alerte pour une région."""
    if resilience_score >= 70:
        emoji = "✅"
        level = "SÉCURISÉ"
        action = "Aucune action nécessaire"
    elif resilience_score >= 50:
        emoji = "⚠️"
        level = "VIGILANCE"
        action = "Surveillance recommandée"
    elif resilience_score >= 30:
        emoji = "🟠"
        level = "ATTENTION"
        action = "Préparation recommandée"
    else:
        emoji = "🚨"
        level = "ALERTE CRITIQUE"
        action = "Évacuation recommandée"
    
    message = f"{emoji} {level}: {region_name} (résilience: {resilience_score:.1f}/100)\n"
    
    if population:
        message += f"{population:,} personnes concernées. "
    
    message += action
    
    return message


def get_alert_level(population_at_risk):
    """Détermine niveau d'alerte selon population affectée."""
    if population_at_risk >= ALERT_THRESHOLDS['critical']:
        return 'critical'
    elif population_at_risk >= ALERT_THRESHOLDS['high']:
        return 'high'
    elif population_at_risk >= ALERT_THRESHOLDS['medium']:
        return 'medium'
    else:
        return 'low'


def generate_summary_stats(df):
    """Génère statistiques d'ensemble pour affichage."""
    stats = {
        'total_regions': len(df),
        'safe_regions': len(df[df['category'] == 'high']),
        'medium_regions': len(df[df['category'] == 'medium']),
        'at_risk_regions': len(df[df['category'].isin(['low', 'critical'])]),  # ← CHANGÉ
        'avg_resilience': df['resilience_index'].mean()
    }
    
    # Si population disponible
    if 'population' in df.columns:
        stats['total_population_at_risk'] = df[df['category'].isin(['low', 'critical'])]['population'].sum()
    
    return stats


def get_evacuation_list(df, threshold=50):
    """Retourne liste régions nécessitant évacuation."""
    urgent_regions = df[df['resilience_index'] < threshold].copy()
    urgent_regions = urgent_regions.sort_values('resilience_index')
    
    return urgent_regions[['region_name', 'resilience_index', 'category', 'population']]


def generate_citizen_alert(df, user_region):
    """Génère alerte personnalisée pour un citoyen."""
    region_data = df[df['region_name'] == user_region]
    
    if len(region_data) == 0:
        return {
            'alert_level': 'unknown',
            'message': f"Région '{user_region}' introuvable",
            'actions': []
        }
    
    row = region_data.iloc[0]
    resilience = row['resilience_index']
    category = row['category']
    
    if category == 'critical':
        return {
            'alert_level': 'critical',
            'message': f"🚨 DANGER CRITIQUE: Votre région ({user_region}) - {resilience:.1f}/100",
            'actions': [
                "🆘 ÉVACUEZ IMMÉDIATEMENT si ordre donné",
                "📦 Kit d'urgence prêt (eau, nourriture, médicaments)",
                "📍 Abri le plus proche identifié",
                "📻 Radio/TV en continu"
            ]
        }
    elif category == 'low':
        return {
            'alert_level': 'warning',
            'message': f"🟠 ATTENTION: Votre région ({user_region}) - {resilience:.1f}/100",
            'actions': [
                "Préparez un kit d'urgence",
                "Identifiez l'abri le plus proche",
                "Restez informé",
                "Préparez-vous à évacuer si nécessaire"
            ]
        }
    elif category == 'medium':
        return {
            'alert_level': 'caution',
            'message': f"⚠️ VIGILANCE: Votre région ({user_region}) - {resilience:.1f}/100",
            'actions': [
                "Surveillez les bulletins météo",
                "Vérifiez votre kit d'urgence",
                "Soyez prêt à agir rapidement"
            ]
        }
    else:
        return {
            'alert_level': 'safe',
            'message': f"✅ SÉCURISÉ: Votre région ({user_region}) - {resilience:.1f}/100",
            'actions': [
                "Restez vigilant",
                "Restez informé"
            ]
        }