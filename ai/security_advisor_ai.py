# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
from scipy.spatial.distance import cdist
import numpy as np
from src.resilience import calculate_resilience, simulate_cyclone_impact, calculate_resilience_batch

# Charger .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not set in .env")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")


class SecurityAdvisor:
    """IA pour conseils de sécurité basés sur localisation temps réel + données résilience"""
    
    def __init__(self, data_path="data/resilience_scores.csv"):
        # Charger les données
        self.resilience_data = pd.read_csv(data_path)
        self.resilience_data["resilience_index"] = self.resilience_data.apply(
            lambda row: calculate_resilience(
                row["exposure"],
                row["vulnerability"],
                row["adaptation"]
            ),
            axis=1
        )
        
        # Coordonnées centrales des régions
        self.region_coords = {
            "MUPL": (-20.1612, 57.5012),   # Port Louis
            "MUMO": (-20.3000, 57.4800),   # Moka
            "MUFL": (-20.3400, 57.7500),   # Flacq
            "MUGP": (-20.4000, 57.6800),   # Grand Port
            "MURO": (-19.7300, 63.4200),   # Rodriguez
            "MURR": (-20.1200, 57.4200),   # Rivière du Rempart
            "MUPW": (-20.4100, 57.4200),   # Plaines Wilhems
            "MUBL": (-20.3500, 57.3000),   # Black River
            "MUSA": (-20.5200, 57.4200),   # Savanne
            "MUPA": (-20.0900, 57.5600),   # Pamplemousses
            "MUAG": (-20.0200, 57.7500),   # North Islands
            "MUCC": (-15.8500, 59.6200),   # Saint Brandon
        }
    
    def get_advice_for_location(self, lat: float, lon: float, disaster_type: str = "cyclone", 
                                cyclone_severity: int = 0) -> dict:
        """
        Génère des conseils de sécurité pour une localisation GPS en temps réel.
        
        """
        # Appliquer simulation cyclone avant génération conseils
        if cyclone_severity > 0:
            df = pd.DataFrame(self.resilience_data)
            df = calculate_resilience_batch(df)
            df = simulate_cyclone_impact(df, cyclone_severity)
            self.resilience_data = df
        
        region_data = self._find_nearest_region(lat, lon)
        
        if not region_data:
            return self._generate_generic_advice(disaster_type)
        
        # Trouver les zones sûres (résilience haute) les plus proches
        safe_zones = self._find_safe_zones(lat, lon, exclude_region=region_data["region_id"])
        
        # Trouver les zones à risque (résilience basse)
        risk_zones = self._find_risk_zones()
        
        # Générer conseils avec IA
        advice = self._call_gemini_for_advice(
            region_data=region_data,
            disaster_type=disaster_type,
            lat=lat,
            lon=lon,
            safe_zones=safe_zones,
            risk_zones=risk_zones,
            cyclone_severity=cyclone_severity
        )
        
        return advice
    
    def _find_nearest_region(self, lat: float, lon: float) -> dict:
        """Trouve la région la plus proche et retourne ses données"""
        user_pos = np.array([[lat, lon]])
        distances = []
        
        for region_id, (r_lat, r_lon) in self.region_coords.items():
            dist = cdist(user_pos, [[r_lat, r_lon]], metric='euclidean')[0][0]
            distances.append((region_id, dist))
        
        nearest_id, _ = min(distances, key=lambda x: x[1])
        region_row = self.resilience_data[
            self.resilience_data["region_id"] == nearest_id
        ]
        
        if region_row.empty:
            return None
        
        row = region_row.iloc[0]
        return {
            "region_id": nearest_id,
            "region_name": row["region_name"],
            "exposure": row["exposure"],
            "vulnerability": row["vulnerability"],
            "adaptation": row["adaptation"],
            "resilience_index": row["resilience_index"],
            "lat": self.region_coords[nearest_id][0],
            "lon": self.region_coords[nearest_id][1]
        }
    
    def _find_safe_zones(self, lat: float, lon: float, exclude_region: str = None, top_n: int = 3) -> list:
        """Trouve les régions sûres (résilience élevée) les plus proches"""
        user_pos = np.array([[lat, lon]])
        safe_candidates = []
        
        # Filtrer les régions avec résilience >= 60 (zones sûres)
        safe_regions = self.resilience_data[self.resilience_data["resilience_index"] >= 60]
        
        for _, row in safe_regions.iterrows():
            region_id = row["region_id"]
            if region_id == exclude_region:
                continue
            
            if region_id not in self.region_coords:
                continue
            
            r_lat, r_lon = self.region_coords[region_id]
            
            # Calculer distance en km (formule approximée)
            dist_km = cdist(user_pos, [[r_lat, r_lon]], metric='euclidean')[0][0] * 111
            
            safe_candidates.append({
                "region_id": region_id,
                "region_name": row["region_name"],
                "resilience_index": row["resilience_index"],
                "distance_km": dist_km,
                "lat": r_lat,
                "lon": r_lon
            })
        
        # Trier par distance et retourner les top_n
        safe_candidates.sort(key=lambda x: x["distance_km"])
        return safe_candidates[:top_n]
    
    def _find_risk_zones(self, top_n: int = 3) -> list:
        """Trouve les régions à risque (résilience basse)"""
        risk_regions = self.resilience_data[
            self.resilience_data["resilience_index"] < 40
        ].sort_values("resilience_index")
        
        risk_zones = []
        for _, row in risk_regions.head(top_n).iterrows():
            risk_zones.append({
                "region_name": row["region_name"],
                "resilience_index": row["resilience_index"],
                "exposure": row["exposure"],
                "vulnerability": row["vulnerability"]
            })
        
        return risk_zones
    
    def _call_gemini_for_advice(self, region_data: dict, disaster_type: str, lat: float, lon: float,
                                safe_zones: list, risk_zones: list, cyclone_severity: int = 0) -> dict:
        """Appelle Gemini pour générer les conseils"""
        
        resilience = region_data["resilience_index"]
        

        if cyclone_severity > 80:
            risk_level = "CRITIQUE - Évacuation IMMÉDIATE requise"
            immediate_action = f"Évacuez IMMÉDIATEMENT vers une zone sûre. Cyclone extrême détecté (intensité {cyclone_severity}/100)."
        elif cyclone_severity > 50:
            risk_level = "TRÈS ÉLEVÉ - Évacuation recommandée"
            immediate_action = f"Préparez-vous à évacuer. Cyclone sévère en approche (intensité {cyclone_severity}/100)."
        elif cyclone_severity > 20:
            risk_level = "ÉLEVÉ - Restez en alerte"
            immediate_action = f"Restez à l'intérieur et suivez les consignes. Cyclone modéré (intensité {cyclone_severity}/100)."
        elif resilience < 40:
            risk_level = "MODÉRÉ - Zone vulnérable"
            immediate_action = "Restez vigilant. Votre zone a une faible résilience. Préparez un kit d'urgence."
        elif resilience < 60:
            risk_level = "FAIBLE - Restez informé"
            immediate_action = "Suivez les actualités et restez informé des évolutions météo."
        else:
            risk_level = "BASSE - Vous êtes en zone sûre"
            immediate_action = "Vous êtes dans une zone à haute résilience. Restez informé mais pas d'évacuation nécessaire."
        
        # Formater zones sûres
        safe_zones_text = "\n".join([
            f"- {z['region_name']}: Score {z['resilience_index']:.0f}/100, Distance: {z['distance_km']:.1f} km"
            for z in safe_zones
        ]) if safe_zones else "Aucune zone sûre à proximité"
        
        # Formater zones à risque
        risk_zones_text = "\n".join([
            f"- {z['region_name']}: Score {z['resilience_index']:.0f}/100"
            for z in risk_zones
        ]) if risk_zones else "Aucune zone à risque critique"
        
        cyclone_info = f"\nCYCLONE EN COURS - Intensité: {cyclone_severity}/100" if cyclone_severity > 0 else ""
        
        prompt = f"""Tu es un expert en sécurité civile. Génère des conseils ADAPTÉS à la situation réelle.

SITUATION ACTUELLE:
- Localisation: {region_data['region_name']}
- Résilience de la zone: {resilience:.0f}/100
- Type de catastrophe: {disaster_type}{cyclone_info}
- Niveau de risque déterminé: {risk_level}

IMPORTANT - LOGIQUE À SUIVRE:
- Si résilience > 60 ET cyclone < 20: Zone SÛRE, PAS d'évacuation
- Si résilience < 60 OU cyclone > 20: Zone À RISQUE, conseils adaptés
- Si cyclone > 50: ÉVACUATION IMMÉDIATE peu importe la résilience

ZONES SÛRES PROCHES:
{safe_zones_text}

ZONES À ÉVITER:
{risk_zones_text}

Génère un JSON avec des conseils COHÉRENTS avec le niveau de risque:

{{
  "location": "{region_data['region_name']}",
  "risk_level": "{risk_level}",
  "immediate_action": "Action cohérente avec le niveau de risque (si zone sûre, ne PAS demander d'évacuer)",
  "protection_tips": [
    "Conseil adapté 1",
    "Conseil adapté 2",
    "Conseil adapté 3"
  ],
  "safe_zones": [
    {{
      "name": "Nom zone",
      "distance_km": 0.0,
      "resilience_score": 0,
      "direction": "Direction",
      "travel_time": "Temps"
    }}
  ],
  "during_disaster": [
    "Action pendant {disaster_type} 1",
    "Action pendant {disaster_type} 2"
  ],
  "emergency_contacts": {{
    "police": "999",
    "ambulance": "114",
    "disaster_management": "116"
  }},
  "evacuation_route": "Direction adaptée au niveau de risque",
  "at_risk_zones": ["Zone 1"]
}}

RAPPEL: Si la zone est SÛRE (résilience > 60 et cyclone faible), ne pas recommander d'évacuation!
JSON uniquement, pas de markdown."""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.split("```")[0]
            
            advice = json.loads(response_text)
            
          
            advice['immediate_action'] = immediate_action
            
            return advice
            
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            return self._generate_fallback_advice(region_data, disaster_type, risk_level, safe_zones, immediate_action)
    
    def _generate_fallback_advice(self, region_data: dict, disaster_type: str, risk_level: str, 
                                 safe_zones: list = None, immediate_action: str = None) -> dict:
        """Conseils de secours cohérents"""
        if safe_zones is None:
            safe_zones = []
        
        if immediate_action is None:
            resilience = region_data["resilience_index"]
            if resilience > 60:
                immediate_action = "Vous êtes en zone sûre. Restez informé mais pas d'évacuation nécessaire."
            else:
                immediate_action = "Préparez-vous à évacuer si la situation se dégrade."
        
        safe_zones_advice = []
        for z in safe_zones[:3]:
            safe_zones_advice.append({
                "name": z["region_name"],
                "distance_km": z["distance_km"],
                "resilience_score": z["resilience_index"],
                "direction": "Utilisez GPS pour direction exacte",
                "travel_time": f"~{int(z['distance_km']/50*60)} min en voiture"
            })
        
        return {
            "location": region_data["region_name"],
            "risk_level": risk_level,
            "immediate_action": immediate_action,
            "protection_tips": [
                "Restez à l'intérieur si conditions dangereuses",
                "Gardez votre téléphone chargé",
                "Restez en contact avec votre famille",
                "Écoutez les bulletins d'information"
            ],
            "safe_zones": safe_zones_advice if safe_zones_advice else [{
                "name": "Centre d'évacuation le plus proche",
                "distance_km": 5.0,
                "resilience_score": 70,
                "direction": "Consultez les autorités",
                "travel_time": "Variable"
            }],
            "during_disaster": [
                f"Pendant {disaster_type}: Restez à l'abri",
                f"Pendant {disaster_type}: Suivez consignes autorités",
                "Évitez les zones inondables et côtières"
            ],
            "emergency_contacts": {
                "police": "999",
                "ambulance": "114",
                "disaster_management": "116"
            },
            "evacuation_route": "Suivez les panneaux d'évacuation officiels",
            "at_risk_zones": ["Zones côtières", "Zones basses"]
        }
    
    def _generate_generic_advice(self, disaster_type: str) -> dict:
        """Conseils génériques"""
        return {
            "location": "Maurice - Localisation inconnue",
            "risk_level": "INCONNU - Prenez les précautions maximales",
            "immediate_action": "Contactez les autorités et suivez leurs instructions.",
            "protection_tips": [
                "Cherchez un abri en hauteur",
                "Appelez les services d'urgence",
                "Restez en famille",
                "Évitez les déplacements inutiles"
            ],
            "safe_zones": [{
                "name": "Zone de refuge",
                "distance_km": 0,
                "resilience_score": 70,
                "direction": "À proximité",
                "travel_time": "Variable"
            }],
            "during_disaster": [
                f"Pendant le {disaster_type}: Restez à l'intérieur",
                f"Pendant le {disaster_type}: Écoutez la radio",
                "Attendez signal évacuation des autorités"
            ],
            "emergency_contacts": {
                "police": "999",
                "ambulance": "114",
                "disaster_management": "116"
            },
            "evacuation_route": "Suivez panneaux d'évacuation.",
            "at_risk_zones": []
        }