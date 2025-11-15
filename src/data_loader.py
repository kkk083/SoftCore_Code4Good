# src/data_loader.py

import geopandas as gpd
import pandas as pd  # tu en auras besoin plus tard pour le CSV de résilience

from utils.config import DATA_PATHS


def load_regions_geojson() -> gpd.GeoDataFrame:
    """
    Charge le GeoJSON des régions de Maurice depuis mu.json
    et renvoie un GeoDataFrame avec les colonnes standard du projet.

    Colonnes retournées :
    - region_id
    - region_name
    - population
    - area_km2
    - geometry
    """
  
    path = DATA_PATHS["regions_geojson"]

    
    gdf = gpd.read_file(path)

    # 3) Adapter les noms de colonnes pour coller à ton projet
    # Dans mu.json, c'est "id" et "name"
    gdf = gdf.rename(columns={
        "id": "region_id",
        "name": "region_name",
    })

    # 4) Ajouter population / area_km2 si elles n'existent pas encore
    if "population" not in gdf.columns:
        gdf["population"] = 0  # mock pour le hackathon
    if "area_km2" not in gdf.columns:
        gdf["area_km2"] = 0.0  # mock aussi

    # 5) Garder seulement les colonnes utiles, dans le bon ordre
    gdf = gdf[["region_id", "region_name", "population", "area_km2", "geometry"]]

    return gdf


def load_resilience_data() -> pd.DataFrame:
    """
    Charge les données de résilience depuis le CSV.

    Pour l'instant, on suppose que le fichier existe déjà dans
    data/mock/resilience_scores.csv et qu'il a les colonnes :
    - region_id
    - region_name
    - exposure
    - vulnerability
    - adaptation
    """
    path = DATA_PATHS["resilience_csv"]
    df = pd.read_csv(path)

    # Types propres
    if "region_id" in df.columns:
        df["region_id"] = df["region_id"].astype(str)
    if "region_name" in df.columns:
        df["region_name"] = df["region_name"].astype(str)

    for col in ["exposure", "vulnerability", "adaptation"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def load_hazard_zones() -> gpd.GeoDataFrame:
    """
    Charge les zones à risque (inondations, etc.) depuis un GeoJSON.
    """
    path = DATA_PATHS["hazard_zones_geojson"]
    gdf = gpd.read_file(path)
    return gdf
