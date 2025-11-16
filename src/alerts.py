import pandas as pd


def generate_summary_stats(df):
    """
    Génère les statistiques globales sur les régions
    
    """
    total_regions = len(df)
    safe_regions = len(df[df['category'] == 'high'])
    at_risk_regions = len(df[df['category'].isin(['low', 'critical'])])
    avg_resilience = df['resilience_index'].mean()
    
    return {
        'total_regions': total_regions,
        'safe_regions': safe_regions,
        'at_risk_regions': at_risk_regions,
        'avg_resilience': avg_resilience
    }


def get_evacuation_list(df, threshold=40):
    """
    Retourne la liste des régions nécessitant une évacuation
    
    """
    evacuation_needed = df[df['resilience_index'] < threshold].copy()
    evacuation_needed = evacuation_needed.sort_values('resilience_index')
    
    return evacuation_needed


def generate_citizen_alert(region_name, resilience_index, category):
    """
    Génère un message d'alerte pour les citoyens
    
    """
    if category == 'critical':
        return f"🚨 ALERTE CRITIQUE - {region_name}: Évacuation immédiate recommandée (résilience: {resilience_index:.1f}/100)"
    elif category == 'low':
        return f"🟠 ALERTE - {region_name}: Préparez-vous à évacuer (résilience: {resilience_index:.1f}/100)"
    elif category == 'medium':
        return f"⚠️ VIGILANCE - {region_name}: Restez informé (résilience: {resilience_index:.1f}/100)"
    else:
        return f"✅ {region_name}: Zone sûre (résilience: {resilience_index:.1f}/100)"