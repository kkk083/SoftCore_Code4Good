# FORMULE DE RÉSILIENCE
RESILIENCE_WEIGHTS = {
    'exposure': 0.45,
    'vulnerability': 0.35,
    'adaptation': 0.20
}


# CATÉGORISATION (4 NIVEAUX)
RESILIENCE_THRESHOLDS = {
    'critical': (0, 30),      # 0-30: ROUGE (critique)
    'low': (30, 50),          # 30-50: ORANGE (faible)
    'medium': (50, 70),       # 50-70: JAUNE (moyen)
    'high': (70, 100)         # 70-100: VERT (élevé)
}


# COULEURS CARTE (4 COULEURS)
COLOR_SCHEME = {
    'critical': '#d73027',    # Rouge vif - DANGER
    'low': '#fc8d59',         # Orange - ATTENTION
    'medium': '#fee08b',      # Jaune - VIGILANCE
    'high': '#1a9850'         # Vert - SÉCURITÉ
}

# COORDONNÉES MAURICE
MAURITIUS_CENTER = [-20.1609, 57.5012]
MAURITIUS_ZOOM_START = 10


# CHEMINS
DATA_PATHS = {
    'mock': 'data/mock/',
    'raw': 'data/raw/',
    'processed': 'data/processed/',
    'alerts': 'data/alerts.json'
}


# CYCLONE
CYCLONE_IMPACT_FACTOR = 0.8


# ALERTES
ALERT_THRESHOLDS = {
    'critical': 50000,
    'high': 20000,
    'medium': 5000
}