# IslandGuard 🇲🇺

**Système de surveillance climatique pour l'île Maurice avec IA**

## Quick Start
```bash
# 1. Cloner
git clone https://github.com/votre-repo/islandguard.git
cd islandguard

# 2. Installer
pip install -r requirements.txt

# 3. Configurer API Gemini
echo "GOOGLE_API_KEY=votre_cle_ici" > .env

# 4. Lancer
streamlit run app.py
```

**Obtenir clé API** : [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## Fonctionnalités

### Mode Citoyen
- Carte de résilience temps réel
- Conseils IA géolocalisés (Gemini)
- Alertes "En danger" / "En sécurité"
- Simulation cyclone

### Mode Secours
- Dashboard alertes citoyennes
- Liste d'évacuation priorisée
- Rapports IA tactiques (export PDF)
- Analyse avant/après cyclone

---

## Structure Fichiers
```
islandguard/
├── app.py                        # App principale
├── data/
│   ├── mauritius_regions.geojson # Géométries (SANS region_id)
│   └── resilience_scores.csv     # Données E, V, A
├── src/                          # Modules métier
├── ai/                           # IA Gemini
└── .env                          # API Key (à créer)
```

---

## Format des Données

### `mauritius_regions.geojson`

**Format attendu** : GeoJSON **SANS `region_id`** dans properties
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [
          [
            [
              [57.337360, -20.467916],
              [57.337360, -20.468196]
            ]
          ]
        ]
      }
    }
  ]
}
```

** Note** : Le système génère automatiquement les `region_id` (TEMP_00, TEMP_01, ...) et les associe par **ordre d'index** avec le CSV.

### `resilience_scores.csv`

**Format strict** :
```csv
region_id,region_name,exposure,vulnerability,adaptation
MUAG,North Islands,85,40,30
MUBL,Black River,80,60,55
MUFL,Flacq,70,55,50
```

**Colonnes obligatoires** : `region_id`, `region_name`, `exposure`, `vulnerability`, `adaptation`

**⚠️ IMPORTANT** : L'ordre des lignes dans le CSV **doit correspondre** à l'ordre des features dans le GeoJSON !
```
GeoJSON Feature 0 ← → CSV Ligne 0 (MUAG)
GeoJSON Feature 1 ← → CSV Ligne 1 (MUBL)
GeoJSON Feature 2 ← → CSV Ligne 2 (MUFL)
```

---

## Formule de Résilience
```
Risque = (0.45 × Exposition) + (0.35 × Vulnérabilité) - (0.20 × Adaptation)
Résilience = 100 - Risque
```

### Catégories

| Score | Couleur | Catégorie |
|-------|---------|-----------|
| 0-30  | 🔴 Rouge | CRITIQUE |
| 30-50 | 🟠 Orange | FAIBLE |
| 50-70 | 🟡 Jaune | MOYEN |
| 70-100 | 🟢 Vert | ÉLEVÉ |

---

## Développement

### Tester les modules
```bash
# Test chargement (affiche correspondance GeoJSON ↔ CSV)
python src/data_loader.py

# Test calcul résilience
python src/resilience.py

# Debug complet
python debug.py
```

### Dépendances principales
```txt
streamlit>=1.28.0
folium>=0.14.0
streamlit-folium>=0.15.0
geopandas>=0.14.0
pandas>=2.0.0
google-generativeai
streamlit-geolocation
fpdf
```

---

## Problèmes Courants

### "Colonnes manquantes: region_id"

**Cause** : GeoJSON n'a pas de `region_id` (normal si données brutes)

**Solution** : Le système les génère automatiquement ! Vérifie juste que :
- CSV a bien la colonne `region_id`
- **L'ordre CSV = ordre GeoJSON**

### Couleurs ne s'affichent pas

**Solution** : 
```bash
python debug.py  # Affiche catégories + couleurs
```

Vérifie que `utils/config.py` contient :
```python
COLOR_SCHEME = {
    'critical': '#d73027',  # Rouge
    'low': '#fc8d59',       # Orange
    'medium': '#fee08b',    # Jaune
    'high': '#1a9850'       # Vert
}
```

### "GOOGLE_API_KEY not set"

**Solution** :
```bash
# Créer .env à la racine
echo "GOOGLE_API_KEY=AIzaSy..." > .env
```

---

## Déploiement Streamlit Cloud

1. Push sur GitHub
2. [share.streamlit.io](https://share.streamlit.io) → Deploy
3. Ajouter dans **Secrets** :
```toml
   GOOGLE_API_KEY = "votre_cle"
```

---

## Correspondance Automatique GeoJSON ↔ CSV

Le système fonctionne comme suit :
```python
# 1. Chargement GeoJSON (12 features sans IDs)
regions_gdf = load_regions_geojson()
# → TEMP_00, TEMP_01, ..., TEMP_11

# 2. Chargement CSV (12 lignes avec IDs réels)
resilience_df = load_resilience_data()
# → MUAG, MUBL, MUFL, ...

# 3. Fusion par INDEX (pas par region_id)
merged_gdf[0] prend données de resilience_df[0]
merged_gdf[1] prend données de resilience_df[1]
```

**Résultat** : Chaque feature GeoJSON récupère automatiquement les données de la ligne CSV correspondante (même position).

---

## Équipe

- **KIADY** 
- **JUNIOR** 
- **MATHIEU** 
- **BRYAN** 

<p align="center">
  <img src="image/softcore_team.jpg" />
</p>
