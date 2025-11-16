import pandas as pd
import numpy as np
from utils.config import (
    RESILIENCE_WEIGHTS,
    RESILIENCE_THRESHOLDS,
    CYCLONE_IMPACT_FACTOR
)


def calculate_resilience(exposure, vulnerability, adaptation):
    """Calcule l'indice de résilience pour UNE région."""
    composite_risk = (
        RESILIENCE_WEIGHTS['exposure'] * exposure +
        RESILIENCE_WEIGHTS['vulnerability'] * vulnerability -
        RESILIENCE_WEIGHTS['adaptation'] * adaptation
    )
    
    resilience_index = 100 - composite_risk
    resilience_index = max(0, min(100, resilience_index))
    
    return round(resilience_index, 2)


def calculate_resilience_batch(df):
    """Calcule résilience pour TOUTES les régions."""
    required = ['exposure', 'vulnerability', 'adaptation']
    missing = [col for col in required if col not in df.columns]
    
    if missing:
        raise ValueError(f"DEV 2: Colonnes manquantes: {missing}")
    
    # Calcul vectorisé
    composite_risk = (
        RESILIENCE_WEIGHTS['exposure'] * df['exposure'] +
        RESILIENCE_WEIGHTS['vulnerability'] * df['vulnerability'] -
        RESILIENCE_WEIGHTS['adaptation'] * df['adaptation']
    )
    
    df['resilience_index'] = 100 - composite_risk
    df['resilience_index'] = df['resilience_index'].clip(0, 100).round(2)
    
    # Ajouter catégorie (4 niveaux)
    df['category'] = df['resilience_index'].apply(get_resilience_category)
    
    print(f"DEV 2: Résilience calculée pour {len(df)} régions")
    
    return df


def get_resilience_category(score):
    """
    Catégorise le score en 4 niveaux
    
    """
    if score < 30:
        return 'critical'    # Rouge
    elif score < 50:
        return 'low'         # Orange
    elif score < 70:
        return 'medium'      # Jaune
    else:
        return 'high'        # Vert


def simulate_cyclone_impact(df, cyclone_severity):
    """Simule l'impact d'un cyclone."""
    if not 0 <= cyclone_severity <= 100:
        raise ValueError("Severity doit être entre 0-100")
    
    df_simulated = df.copy()
    
    # Calculer impact
    impact = cyclone_severity * CYCLONE_IMPACT_FACTOR
    df_simulated['exposure'] = df_simulated['exposure'] + impact
    df_simulated['exposure'] = df_simulated['exposure'].clip(0, 100)
    
    # Recalculer résilience
    df_simulated = calculate_resilience_batch(df_simulated)
    
    print(f"DEV 2: Cyclone severity={cyclone_severity} simulé")
    
    return df_simulated


def get_cyclone_category(severity):
    """Nom du cyclone selon intensité."""
    if severity == 0:
        return "Pas de cyclone"
    elif severity < 20:
        return "Dépression tropicale"
    elif severity < 40:
        return "Tempête tropicale"
    elif severity < 60:
        return "Cyclone catégorie 1-2"
    elif severity < 80:
        return "Cyclone catégorie 3-4"
    else:
        return "Cyclone catégorie 5 (EXTRÊME)"


def calculate_combined_resilience(df, alerts_df):
    """Calcule résilience combinée avec alertes citoyennes."""
    merged = df.merge(alerts_df, on='region_id', how='left').fillna(0)
    
    merged['combined_risk'] = merged.apply(
        lambda row: calculate_combined_risk(
            row['resilience_index'],
            row.get('citizen_danger_ratio', 0)
        ),
        axis=1
    )
    
    merged['combined_category'] = merged['combined_risk'].apply(
        lambda x: 'critical' if x >= 60 else 
                  'high' if x >= 40 else
                  'medium' if x >= 20 else 'low'
    )
    
    return merged


def calculate_combined_risk(resilience_index, citizen_danger_ratio):
    """Calcule risque combiné."""
    resilience_risk = 100 - resilience_index
    citizen_risk = citizen_danger_ratio * 100
    combined = (0.6 * resilience_risk) + (0.4 * citizen_risk)
    return round(combined, 2)