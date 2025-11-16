import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
from src.resilience import calculate_resilience 

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not set in .env")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

class ReportAI:
    """IA pour générer des rapports opérationnels tactiques pour les services de secours"""
    
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent
        self.region_names = self._load_region_names()
        self.resilience_data = self._load_resilience_data()
        self._add_region_names_to_data()
        self.hazard_zones = self._load_hazard_zones()
        self.alerts = self._load_alerts()
    
    def _load_resilience_data(self) -> pd.DataFrame:
        """Charge et prépare les données de résilience"""
        csv_path = self.base_path / "data" / "resilience_scores.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Fichier manquant: {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        # Calculer l'indice de résilience
        df["resilience_index"] = df.apply(
            lambda row: calculate_resilience(
                row["exposure"],
                row["vulnerability"],
                row["adaptation"]
            ),
            axis=1
        )

        
        # Ajouter catégorie de résilience
        df["resilience_category"] = df["resilience_index"].apply(self._categorize_resilience)
        
        return df
    
    def _add_region_names_to_data(self):
        """Ajoute les noms de régions au DataFrame après chargement"""
        if "region_name" not in self.resilience_data.columns:
            self.resilience_data["region_name"] = self.resilience_data["region_id"].map(
                lambda rid: self.region_names.get(rid, rid)
            )
    
    def _load_region_names(self) -> dict:
        """Charge les noms corrects des régions depuis le GeoJSON"""
        geojson_path = self.base_path / "data" / "mock" / "regions.geojson"
        region_names = {}
        
        default_names = {
            "MUAG": "North Islands",
            "MUBL": "Black River",
            "MUCC": "Saint Brandon Islands",
            "MUFL": "Flacq",
            "MUGP": "Grand Port",
            "MUMO": "Moka",
            "MUPA": "Pamplemousses",
            "MUPL": "Port Louis",
            "MUPW": "Plaines Wilhems",
            "MURO": "Rodriguez Island",
            "MURR": "Riviere du Rempart",
            "MUSA": "Savanne"
        }

        
        if geojson_path.exists():
            try:
                with open(geojson_path, "r", encoding="utf-8") as f:
                    geojson = json.load(f)
                    for feature in geojson.get("features", []):
                        props = feature.get("properties", {})
                        region_id = props.get("region_id")
                        region_name = props.get("region_name")
                        if region_id and region_name:
                            region_names[region_id] = region_name
            except Exception as e:
                print(f"Erreur chargement GeoJSON: {e}")
        
        return {**default_names, **region_names}
    
    def _load_hazard_zones(self) -> dict:
        """Charge les zones de risque depuis GeoJSON"""
        geojson_path = self.base_path / "data" / "mock" / "hasard_zone.geojson"
        if geojson_path.exists():
            with open(geojson_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"type": "FeatureCollection", "features": []}
    
    def _load_alerts(self) -> list:
        """Charge les alertes actuelles"""
        alerts_path = self.base_path / "data" / "alerts.json"
        if alerts_path.exists():
            with open(alerts_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    
    def _categorize_resilience(self, score):
        """Catégorise le score de résilience"""
        if score < 40:
            return "CRITIQUE"
        elif score < 60:
            return "FAIBLE"
        elif score < 80:
            return "MODÉRÉ"
        else:
            return "ÉLEVÉ"
    
    def _get_region_name(self, region_id: str) -> str:
        """Récupère le nom correct de la région"""
        return self.region_names.get(region_id, region_id)
    
    def generate_security_advice(self, region_id: str = None) -> dict:
        """
        Génère un rapport opérationnel tactique pour une région ou toutes les régions.
        """
        if region_id:
            data = self.resilience_data[self.resilience_data.get("region_id") == region_id]
            if data.empty:
                return {"error": f"Région {region_id} non trouvée"}
        else:
            data = self.resilience_data
        
        context = self._prepare_context(data)
        advice = self._call_gemini(context, region_id)
        
        return advice
    
    def _prepare_context(self, data):
        """Prépare les données pour le prompt"""
        context = {
            "regions": [],
            "critical_zones": [],
            "adaptation_gaps": [],
            "active_alerts": self.alerts,
            "hazard_zones": len(self.hazard_zones.get("features", [])),
            "total_regions": len(data),
            "avg_resilience": float(data["resilience_index"].mean())
        }
        
        for _, row in data.iterrows():
            region_id = row.get("region_id", "N/A")
            region_name = self._get_region_name(region_id)
            
            region_info = {
                "id": region_id,
                "name": region_name,
                "resilience_index": float(row.get("resilience_index", 0)),
                "category": row.get("resilience_category", "INCONNU"),
                "exposure": float(row.get("exposure", 0)),
                "vulnerability": float(row.get("vulnerability", 0)),
                "adaptation": float(row.get("adaptation", 0))
            }
            context["regions"].append(region_info)
            
            # Zones critiques (résilience < 40)
            if region_info["resilience_index"] < 40:
                context["critical_zones"].append({
                    "name": region_name,
                    "score": region_info["resilience_index"],
                    "main_risk": self._identify_main_risk(row)
                })
            
            # Gaps d'adaptation (adaptation < 50)
            if region_info["adaptation"] < 50:
                context["adaptation_gaps"].append({
                    "region": region_name,
                    "adaptation_score": region_info["adaptation"],
                    "exposure": region_info["exposure"],
                    "vulnerability": region_info["vulnerability"]
                })
        
        # Trier par priorité
        context["regions"].sort(key=lambda x: x["resilience_index"])
        context["critical_zones"].sort(key=lambda x: x["score"])
        
        return context
    
    def _identify_main_risk(self, row):
        """Identifie le risque principal"""
        exposure = float(row.get("exposure", 0))
        vulnerability = float(row.get("vulnerability", 0))
        adaptation = float(row.get("adaptation", 0))
        
        if exposure > 80 and vulnerability > 60:
            return "Exposition critique + Infrastructure fragile → Intervention prioritaire"
        elif exposure > 80:
            return "Exposition très élevée → Risque cyclones/inondations majeur"
        elif vulnerability > 70:
            return "Infrastructure défaillante → Renforcement défensif urgent"
        elif adaptation < 40:
            return "Capacité d'adaptation insuffisante → Formation/équipement requis"
        else:
            return "Risque modéré → Surveillance continue"
    
    def _call_gemini(self, context, region_id=None):
        """Appelle Gemini pour générer le rapport opérationnel"""
        
        if region_id and context['regions']:
            scope = f"Région: {context['regions'][0]['name']}"
        else:
            scope = "Île Maurice - Analyse globale"
        
        prompt = f"""Tu es un analyste stratégique en gestion de crise pour les services de secours mauriciens.

DONNÉES TERRAIN:
{json.dumps(context, indent=2, ensure_ascii=False)}

Génère un RAPPORT OPÉRATIONNEL TACTIQUE pour: {scope}

Format JSON strict (AUCUN markdown):
{{
  "scope": "{scope}",
  "executive_summary": "Synthèse stratégique de la situation (3-4 lignes, ton professionnel)",
  "threat_assessment": {{
    "immediate_risks": ["Risque opérationnel 1", "Risque 2", "Risque 3"],
    "timeframe": "Fenêtre d'intervention critique (ex: 0-6h, 6-24h, 24-48h)",
    "severity_level": "CRITIQUE | ÉLEVÉ | MODÉRÉ"
  }},
  "region_specific_advice": [
    {{
      "region": "Nom région exacte",
      "resilience_score": score_numérique,
      "key_vulnerabilities": ["Vulnérabilité tactique 1", "Vulnérabilité 2", "Vulnérabilité 3"],
      "immediate_actions": ["Action opérationnelle 1", "Action 2", "Action 3"],
      "resource_needs": ["Ressource spécifique 1", "Ressource 2"]
    }}
  ],
  "evacuation_priorities": ["Région priorité 1", "Région priorité 2", "Région priorité 3"],
  "resource_allocation": {{
    "helicopters": nombre,
    "ambulances": nombre,
    "rescue_teams": nombre,
    "boats": nombre,
    "emergency_shelters": nombre
  }},
  "critical_recommendations": ["Recommandation stratégique 1", "Recommandation 2", "Recommandation 3"],
  "preparedness_checklist": ["Action vérifiable 1", "Action 2", "Action 3", "Action 4", "Action 5"]
}}

DIRECTIVES:
- Ton professionnel et factuel (pas de langage grand public)
- Prioriser par niveau de risque décroissant
- Quantifier les ressources nécessaires
- Identifier les goulots d'étranglement opérationnels
- Utiliser les noms de régions EXACTS du contexte
- Focaliser sur l'actionable (pas de généralités)"""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Nettoyer markdown si présent
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.split("```")[0]
            
            advice = json.loads(response_text)
            return advice
            
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            return self._generate_fallback_advice(context, region_id)
    
    def _generate_fallback_advice(self, context, region_id):
        """Rapport de secours basique"""
        critical = [r for r in context["regions"] if r["resilience_index"] < 40]
        high_risk = [r for r in context["regions"] if 40 <= r["resilience_index"] < 60]
        
        scope = context["regions"][0]["name"] if region_id and context["regions"] else "Île Maurice - Analyse globale"
        
        severity = "CRITIQUE" if len(critical) >= 3 else "ÉLEVÉ" if len(critical) > 0 else "MODÉRÉ"
        
        return {
            "scope": scope,
            "executive_summary": f"Situation opérationnelle: {len(critical)} zone(s) critique(s), {len(high_risk)} zone(s) à risque élevé. Résilience moyenne: {context['avg_resilience']:.1f}/100. Déploiement tactique requis selon matrice de priorisation.",
            "threat_assessment": {
                "immediate_risks": [
                    "Défaillance infrastructures critiques en zones exposées",
                    "Capacité d'évacuation limitée dans secteurs vulnérables",
                    "Rupture logistique potentielle en cas d'événement majeur"
                ],
                "timeframe": "0-6h pour zones critiques, 6-24h pour zones à risque",
                "severity_level": severity
            },
            "region_specific_advice": [
                {
                    "region": r["name"],
                    "resilience_score": r["resilience_index"],
                    "key_vulnerabilities": [
                        f"Exposition: {r['exposure']:.0f}/100 - Risque environnemental élevé",
                        f"Vulnérabilité: {r['vulnerability']:.0f}/100 - Infrastructure fragile",
                        f"Adaptation: {r['adaptation']:.0f}/100 - Capacité de réponse limitée"
                    ],
                    "immediate_actions": [
                        "Pré-positionnement équipes de sauvetage en stand-by",
                        "Activation protocole d'évacuation préventive si dégradation",
                        "Sécurisation itinéraires d'accès pour moyens lourds",
                        "Mise en place cellule de commandement avancée"
                    ],
                    "resource_needs": [
                        f"Équipes USAR (Urban Search And Rescue) - {max(1, int(r['vulnerability']/30))} unités",
                        f"Moyens héliportés - {1 if r['resilience_index'] < 35 else 0} hélicoptère(s)",
                        f"Ambulances SMUR - {max(2, int(r['exposure']/25))} véhicules",
                        "Kit d'intervention en milieu hostile"
                    ]
                }
                for r in (critical + high_risk[:3])  # Top zones critiques + 3 suivantes
            ],
            "evacuation_priorities": [r["name"] for r in critical] + [r["name"] for r in high_risk[:2]],
            "resource_allocation": {
                "helicopters": min(3, len(critical)),
                "ambulances": 3 * len(critical) + 2 * len(high_risk),
                "rescue_teams": 2 * len(critical) + len(high_risk),
                "boats": 2 if any(r["name"] in ["Port Louis", "Mahebourg", "Grand Port"] for r in critical) else 1,
                "emergency_shelters": len(critical) + len(high_risk)
            },
            "critical_recommendations": [
                f"PRIORITÉ 1: Déploiement immédiat dans {len(critical)} zone(s) critique(s)",
                "PRIORITÉ 2: Activation Plan ORSEC (Organisation de la Réponse de Sécurité Civile)",
                "PRIORITÉ 3: Coordination interservices (Police, Pompiers, Santé, Armée)",
                f"PRIORITÉ 4: Pré-positionnement ressources dans zones tampon ({len(high_risk)} secteurs)",
                "PRIORITÉ 5: Test communications redondantes (radio, satellite)"
            ],
            "preparedness_checklist": [
                "✅ Inventaire matériel d'urgence (stocks, véhicules, équipements)",
                "✅ Vérification disponibilité personnel (rappel effectifs, stand-by)",
                "⚠️ Sécurisation axes routiers prioritaires et itinéraires de repli",
                "⚠️ Activation centres de coordination opérationnelle (CCO)",
                "⚠️ Test procédures d'alerte de masse (SMS, sirènes, médias)",
                "⚠️ Pré-accord avec hôpitaux pour plans blancs (afflux massif)",
                "⚠️ Coordination avec autorités locales (maires, préfets)"
            ]
        }