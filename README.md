# 🌴 IslandGuard 🇲🇺

**Système de surveillance de la résilience climatique pour l'île Maurice**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)

> **Code4Good Hackathon 2025** - Solution de gestion de crise climatique avec IA générative

---

## 🎯 Fonctionnalités Principales

### 👤 Mode Citoyen
- 🗺️ **Carte interactive** de résilience en temps réel
- 📍 **Géolocalisation** pour conseils de sécurité personnalisés
- 🚨 **Boutons d'alerte** (En danger / En sécurité)
- 🤖 **Assistant IA Gemini** avec recommandations adaptées
- 🌀 **Simulation cyclone** pour préparation

### 🚨 Mode Secours/Gouvernement
- 📊 **Dashboard opérationnel** avec alertes citoyennes agrégées
- 🗺️ **Carte tactique** avec zones de danger et abris
- 🚁 **Liste d'évacuation** priorisée
- 📈 **Analyse comparative** avant/après cyclone
- 📄 **Rapport IA tactique** (export PDF)
- 🔄 **Nettoyage alertes** automatique

---

## 🏗️ Architecture
```
islandguard/
├── app.py                          # 🎯 Interface Streamlit principale
├── data/
│   ├── mauritius_regions.geojson  # 🗺️ Géométries des régions
│   ├── resilience_scores.csv      # 📊 Données résilience (E, V, A)
│   ├── alerts.json                 # 🚨 Alertes citoyennes (généré auto)
│   └── mock/
│       └── hazard_zones.geojson   # ⚠️ Zones de danger (optionnel)
├── src/
│   ├── data_loader.py              # 📥 Chargement et fusion données
│   ├── resilience.py               # 🧮 Calcul indice de résilience
│   ├── map_generator.py            # 🗺️ Génération cartes Folium
│   ├── alerts.py                   # 📊 Statistiques et évacuations
│   └── citizen_alerts.py           # 🚨 Gestion alertes citoyennes
├── ai/
│   ├── security_advisor_ai.py      # 🤖 Conseils IA géolocalisés
│   └── report_ai.py                # 📄 Rapports opérationnels IA
├── utils/
│   └── config.py                   # ⚙️ Configuration centralisée
├── requirements.txt                # 📦 Dépendances Python
├── .env                            # 🔑 API Key Gemini (à créer)
└── README.md                       # 📖 Ce fichier
```

---

## 🚀 Installation

### Prérequis
- Python 3.9 ou supérieur
- Compte Google Cloud (pour API Gemini)

### 1️⃣ Cloner le projet
```bash
git clone https://github.com/votre-repo/islandguard.git
cd islandguard
```

### 2️⃣ Créer un environnement virtuel
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4️⃣ Configurer l'API Gemini

1. Créer un fichier `.env` à la racine :
```bash
GOOGLE_API_KEY=votre_cle_api_ici
```

2. Obtenir une clé API :
   - Aller sur [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Créer une nouvelle clé API
   - Copier dans `.env`

### 5️⃣ Préparer les données

Placer vos fichiers dans `data/` :

- `mauritius_regions.geojson` : GeoJSON avec géométries
- `resilience_scores.csv` : CSV avec colonnes :
```
  region_id,region_name,exposure,vulnerability,adaptation
```

**Format CSV minimal** :
```csv
region_id,region_name,exposure,vulnerability,adaptation
MUPL,Port Louis,85,75,35
MUMO,Moka,55,45,60
```

### 6️⃣ Lancer l'application
```bash
streamlit run app.py
```

L'app s'ouvre automatiquement dans votre navigateur à `http://localhost:8501`

---

## 📊 Formule de Résilience

### Calcul de l'Indice
```
Risque Composite = (0.45 × Exposition) + (0.35 × Vulnérabilité) - (0.20 × Adaptation)
Indice de Résilience = 100 - Risque Composite
```

### Catégorisation (4 niveaux)

| Score | Catégorie | Couleur | Signification |
|-------|-----------|---------|---------------|
| 0-30  | 🔴 **CRITIQUE** | Rouge | Évacuation immédiate |
| 30-50 | 🟠 **FAIBLE** | Orange | Action urgente |
| 50-70 | 🟡 **MOYEN** | Jaune | Surveillance |
| 70-100 | 🟢 **ÉLEVÉ** | Vert | Zone sûre |

### Simulation Cyclone
```python
Nouvelle Exposition = Exposition + (Intensité Cyclone × 0.8)
```

---

## 🤖 Intégration IA (Google Gemini)

### 1. Conseils de Sécurité Géolocalisés
```python
from ai.security_advisor_ai import SecurityAdvisor

advisor = SecurityAdvisor()
advice = advisor.get_advice_for_location(
    lat=-20.1612, 
    lon=57.5012, 
    disaster_type="cyclone",
    cyclone_severity=70
)
```

**Résultat** :
- Niveau de risque adapté
- Actions immédiates
- Zones sûres proches
- Itinéraires d'évacuation
- Numéros d'urgence

### 2. Rapports Opérationnels Tactiques
```python
from ai.report_ai import ReportAI

ai = ReportAI()
report = ai.generate_security_advice(region_id="MUPL")
```

**Génère** :
- Résumé exécutif
- Évaluation des menaces
- Allocation de ressources
- Checklist de préparation
- Export PDF

---

## 🗺️ Format des Données

### GeoJSON Régions
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "region_id": "MUPL",
        "region_name": "Port Louis"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [...]
      }
    }
  ]
}
```

### CSV Résilience
```csv
region_id,region_name,exposure,vulnerability,adaptation,population
MUPL,Port Louis,85,75,35,150000
MUMO,Moka,55,45,60,83000
```

**Colonnes obligatoires** : `region_id`, `exposure`, `vulnerability`, `adaptation`  
**Colonnes optionnelles** : `region_name`, `population`

---

## 🛠️ Développement

### Tester les modules individuellement
```bash
# Test chargement données
python src/data_loader.py

# Test calcul résilience
python src/resilience.py

# Test génération carte
python src/map_generator.py

# Test alertes
python src/citizen_alerts.py

# Debug résilience
python debug.py
```

### Structure du code

- **Modules src/** : Fonctions métier (données, calculs, cartes)
- **Modules ai/** : Intégration Gemini AI
- **app.py** : Orchestration Streamlit
- **utils/config.py** : Paramètres globaux

---

## 📦 Dépendances Principales

| Package | Version | Usage |
|---------|---------|-------|
| `streamlit` | 1.28+ | Interface web |
| `folium` | 0.14+ | Cartes interactives |
| `streamlit-folium` | 0.15+ | Intégration Folium |
| `geopandas` | 0.14+ | Données géographiques |
| `pandas` | 2.0+ | Manipulation données |
| `google-generativeai` | Latest | API Gemini |
| `streamlit-geolocation` | Latest | Géolocalisation |
| `fpdf` | Latest | Export PDF |

---

## 🚀 Déploiement Streamlit Cloud

### 1. Préparer le dépôt
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2. Configurer Streamlit Cloud

1. Aller sur [share.streamlit.io](https://share.streamlit.io)
2. Connecter votre repo GitHub
3. Sélectionner `app.py`
4. Ajouter dans **Secrets** :
```toml
GOOGLE_API_KEY = "votre_cle_api"
```

### 3. Déployer

Cliquer sur **Deploy** → L'app est en ligne ! 🎉

---

## 🐛 Résolution de Problèmes

### Erreur : "GOOGLE_API_KEY not set"

**Solution** : Créer un fichier `.env` avec votre clé API :
```bash
GOOGLE_API_KEY=AIzaSy...
```

### Erreur : "Colonnes manquantes" dans data_loader

**Solution** : Vérifier que votre CSV contient :
```csv
region_id,exposure,vulnerability,adaptation
```

### Carte ne charge pas

**Solution** : 
1. Vérifier que `mauritius_regions.geojson` existe dans `data/`
2. Tester avec : `python src/data_loader.py`

### Couleurs ne s'affichent pas sur la carte

**Solution** : 
1. Vérifier `utils/config.py` → `COLOR_SCHEME`
2. Vérifier que la colonne `category` existe après calcul résilience

### IA ne répond pas

**Solution** :
1. Vérifier la clé API Gemini
2. Vérifier la connexion internet
3. Essayer avec un modèle différent dans `security_advisor_ai.py` :
```python
   model = genai.GenerativeModel("gemini-2.0-flash-exp")
```

---

## 📝 Licence

MIT License - Code4Good Hackathon 2025

---

## 👥 Équipe

**IslandGuard Team** - Code4Good Hackathon 2025

- **DEV 1** : Chargement et fusion de données
- **DEV 2** : Calculs de résilience
- **DEV 3** : Cartographie interactive
- **DEV 4** : Système d'alertes citoyennes

---

## 🙏 Remerciements

- **Google Gemini AI** pour l'IA générative
- **Streamlit** pour le framework web
- **Folium** pour les cartes interactives
- **Code4Good** pour l'organisation du hackathon
- **Île Maurice** 🇲🇺 pour l'inspiration

---

## 📧 Contact

Pour questions ou support :
- 📧 Email : votre-email@example.com
- 🐙 GitHub : [github.com/votre-repo](https://github.com/votre-repo)

---

**Made with ❤️ for Mauritius** 🇲🇺🌴

*Powered by Google Gemini AI ⚡*
