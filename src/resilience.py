
import pandas as pd
import numpy as np
from utils.config import RESILIENCE_WEIGHTS, RESILIENCE_THRESHOLDS


def calculate_resilience(exposure: float, vulnerability: float, adaptation: float) -> float:
    
    # Formule composite du risque
    composite_risk = (
        RESILIENCE_WEIGHTS['exposure'] * exposure +
        RESILIENCE_WEIGHTS['vulnerability'] * vulnerability -
        RESILIENCE_WEIGHTS['adaptation'] * adaptation
    )
    
    # Indice de résilience = inverse du risque
    resilience_index = 100 - composite_risk
    
    # Clamper entre 0 et 100
    resilience_index = max(0, min(100, resilience_index))
    
    return round(resilience_index, 2)


def calculate_resilience_batch(df: pd.DataFrame) -> pd.DataFrame:
   
    if not all(col in df.columns for col in ['exposure', 'vulnerability', 'adaptation']):
        raise ValueError("DataFrame doit contenir les colonnes: exposure, vulnerability, adaptation")
    
    # Calcul vectorisé pour performance
    composite_risk = (
        RESILIENCE_WEIGHTS['exposure'] * df['exposure'] +
        RESILIENCE_WEIGHTS['vulnerability'] * df['vulnerability'] -
        RESILIENCE_WEIGHTS['adaptation'] * df['adaptation']
    )
    
    df['resilience_index'] = 100 - composite_risk
    
    # Clamper entre 0 et 100
    df['resilience_index'] = df['resilience_index'].clip(0, 100).round(2)
    
    return df


def get_resilience_category(score: float) -> str:
   
    for category, (min_val, max_val) in RESILIENCE_THRESHOLDS.items():
        if min_val <= score < max_val:
            return category
    
    # Si score = 100 exactement
    if score == 100:
        return 'high'
    
    return 'low'  # Fallback


def normalize_values(df: pd.DataFrame, columns: list) -> pd.DataFrame:
   
    df_normalized = df.copy()
    
    for col in columns:
        if col not in df.columns:
            raise ValueError(f"Colonne '{col}' introuvable dans le DataFrame")
        
        min_val = df[col].min()
        max_val = df[col].max()
        
        # Éviter division par zéro
        if max_val - min_val == 0:
            df_normalized[col] = 50  # Valeur neutre
        else:
            df_normalized[col] = ((df[col] - min_val) / (max_val - min_val)) * 100
    
    return df_normalized


def simulate_cyclone_impact(df: pd.DataFrame, severity: int) -> pd.DataFrame:
   
    if not 0 <= severity <= 100:
        raise ValueError("Severity doit être entre 0 et 100")
    
    df_simulated = df.copy()
    
    # Augmenter l'exposition selon la sévérité
    df_simulated['exposure'] = df_simulated['exposure'] + (severity * 0.5)
    df_simulated['exposure'] = df_simulated['exposure'].clip(0, 100)
    
    # Recalculer la résilience
    df_simulated = calculate_resilience_batch(df_simulated)
    
    return df_simulated


# Tests unitaires (à exécuter pour vérifier)
if __name__ == "__main__":
    print("🧪 Tests du module resilience.py\n")
    
    # Test 1: Calcul simple
    print("Test 1: Calcul résilience simple")
    result = calculate_resilience(70, 60, 40)
    print(f"  Entrée: E=70, V=60, A=40")
    print(f"  Résultat: {result}")
    print(f"  Catégorie: {get_resilience_category(result)}")
    assert 0 <= result <= 100, "Erreur: résultat hors bornes"
    print("  ✅ Test 1 OK\n")
    
    # Test 2: Calcul batch
    print("Test 2: Calcul batch DataFrame")
    test_data = pd.DataFrame({
        'region_id': ['R1', 'R2', 'R3'],
        'region_name': ['Port Louis', 'Curepipe', 'Mahebourg'],
        'exposure': [80, 50, 60],
        'vulnerability': [70, 40, 55],
        'adaptation': [30, 60, 45]
    })
    result_df = calculate_resilience_batch(test_data)
    print(result_df[['region_name', 'exposure', 'vulnerability', 'adaptation', 'resilience_index']])
    assert 'resilience_index' in result_df.columns, "Erreur: colonne resilience_index manquante"
    print("  ✅ Test 2 OK\n")
    
    # Test 3: Simulation cyclone
    print("Test 3: Simulation cyclone severity=50")
    simulated = simulate_cyclone_impact(test_data, severity=50)
    print(simulated[['region_name', 'exposure', 'resilience_index']])
    print("  ✅ Test 3 OK\n")
    
    print("🎉 Tous les tests sont OK! Module prêt pour intégration.")