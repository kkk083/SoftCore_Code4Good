"""
🔍 DEBUG - Vérifier calculs de résilience
"""

import pandas as pd
from src.data_loader import merge_data
from src.resilience import calculate_resilience_batch

# Charger données
print("=" * 60)
print("🔍 DEBUG RÉSILIENCE")
print("=" * 60)

df = merge_data()
df = calculate_resilience_batch(df)

# Afficher résultats
print("\n📊 RÉSULTATS PAR RÉGION:")
print("-" * 60)

for _, row in df.iterrows():
    E = row['exposure']
    V = row['vulnerability']
    A = row['adaptation']
    
    # Calcul manuel
    risk = (0.45 * E) + (0.35 * V) - (0.20 * A)
    resilience = 100 - risk
    
    # Catégorie
    if resilience < 40:
        cat = "🔴 LOW (ROUGE)"
    elif resilience < 70:
        cat = "🟡 MEDIUM (JAUNE)"
    else:
        cat = "🟢 HIGH (VERT)"
    
    print(f"{row['region_name']:25s} | E={E:5.1f} V={V:5.1f} A={A:5.1f} → Résilience={resilience:5.1f} {cat}")

print("\n📈 STATISTIQUES:")
print(f"Résilience MIN:  {df['resilience_index'].min():.1f}")
print(f"Résilience MAX:  {df['resilience_index'].max():.1f}")
print(f"Résilience MOY:  {df['resilience_index'].mean():.1f}")

print("\n🎨 DISTRIBUTION PAR CATÉGORIE:")
print(df['category'].value_counts())

print("\n" + "=" * 60)