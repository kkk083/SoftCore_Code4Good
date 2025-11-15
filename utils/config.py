from pathlib import Path

BASE_DIR = Path(_file_).resolve().parent.parent

DATA_PATHS = {
    "regions_geojson": BASE_DIR / "data" / "mock" / "mu.json",
    "resilience_csv": BASE_DIR / "data" / "mock" / "resilience_scores.csv",
    "hazard_zones_geojson": BASE_DIR / "data" / "mock" / "hazard_zones.geojson",
}

"""
Configuration centralisée pour IslandGuard
Contient toutes les constantes du projet
"""

# Poids de la formule de résilience (NE PAS MODIFIER!)
RESILIENCE_WEIGHTS = {
    'exposure': 0.45,
    'vulnerability': 0.35,
    'adaptation': 0.20
}

# Seuils de catégorisation
RESILIENCE_THRESHOLDS = {
    'low': (0, 40),      # 0-40: Faible résilience
    'medium': (40, 70),  # 40-70: Résilience moyenne
    'high': (70, 100)    # 70-100: Haute résilience
}

# Schéma de couleurs pour la carte
COLOR_SCHEME = {
    'low': '#d73027',     # Rouge
    'medium': '#fee08b',  # Jaune
    'high': '#1a9850'     # Vert
}

# Coordonnées Maurice
MAURITIUS_CENTER = [-20.1609, 57.5012]
MAURITIUS_ZOOM_START = 10

# Chemins de données
DATA_PATHS = {
    'mock': 'data/mock/',
    'raw': 'data/raw/',
    'processed': 'data/processed/',
    'alerts': 'data/alerts.json'
}