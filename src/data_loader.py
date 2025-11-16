import pandas as pd
import geopandas as gpd
from pathlib import Path


def load_regions_geojson(filepath='data/mauritius_regions.geojson'):
    """
    Charge les régions géographiques depuis GeoJSON.

    """
    try:
        gdf = gpd.read_file(filepath)
        
        print(f"GeoJSON chargé: {len(gdf)} features")
        print(f"Colonnes: {gdf.columns.tolist()}")
        
        
        # Si PAS de region_id → CRÉER automatiquement
        if 'region_id' not in gdf.columns:
            print("Aucun region_id trouvé → Génération automatique")
            
            # Créer IDs temporaires basés sur l'INDEX
            gdf['region_id'] = [f"TEMP_{i:02d}" for i in range(len(gdf))]
            gdf['region_name'] = [f"Région {i+1}" for i in range(len(gdf))]
            
            print(f"{len(gdf)} IDs générés: TEMP_00, TEMP_01, ...")
        
        # Si region_id existe mais pas region_name
        elif 'region_name' not in gdf.columns:
            gdf['region_name'] = gdf['region_id']
            print("region_name créé depuis region_id")
        
        # Vérifier geometry
        if gdf.geometry.isnull().any():
            print(f"{gdf.geometry.isnull().sum()} géométries nulles supprimées")
            gdf = gdf[~gdf.geometry.isnull()]
        
        # Simplifier géométries pour performance
        print("Simplification géométries...")
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)
        
        print(f"{len(gdf)} régions prêtes")
        
        return gdf
    
    except FileNotFoundError:
        print(f"Fichier introuvable: {filepath}")
        return gpd.GeoDataFrame()
    
    except Exception as e:
        print(f"Erreur chargement GeoJSON: {e}")
        import traceback
        traceback.print_exc()
        return gpd.GeoDataFrame()


def load_resilience_data(filepath='data/resilience_scores.csv'):
    """
    Charge les données de résilience (E, V, A).

    """
    try:
        df = pd.read_csv(filepath, low_memory=False)
        
        print(f"CSV chargé: {len(df)} lignes")
        print(f"Colonnes: {df.columns.tolist()}")
        
        # Vérifier colonnes obligatoires
        required = ['region_id', 'exposure', 'vulnerability', 'adaptation']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            raise ValueError(f"Colonnes manquantes: {missing}")
        
        # Ajouter region_name si absent
        if 'region_name' not in df.columns:
            df['region_name'] = df['region_id']
            print("region_name créé depuis region_id")
        
        # Convertir en numérique
        for col in ['exposure', 'vulnerability', 'adaptation']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Supprimer NaN
        before = len(df)
        df = df.dropna(subset=['exposure', 'vulnerability', 'adaptation'])
        if len(df) < before:
            print(f"{before - len(df)} lignes avec NaN supprimées")
        
        # Clip valeurs 0-100
        for col in ['exposure', 'vulnerability', 'adaptation']:
            df[col] = df[col].clip(0, 100)
        
        print(f"{len(df)} régions valides")
        
        return df
    
    except FileNotFoundError:
        print(f"Fichier introuvable: {filepath}")
        return pd.DataFrame()
    
    except Exception as e:
        print(f"Erreur chargement CSV: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def merge_data():
    """
   Fonction d'integration complete

    """
    print("\nFUSION DES DONNÉES...")
    
    # 1. Charger géométrie
    regions_gdf = load_regions_geojson('data/mauritius_regions.geojson')
    if len(regions_gdf) == 0:
        print("Impossible de continuer sans régions")
        return gpd.GeoDataFrame()
    
    # 2. Charger données résilience
    resilience_df = load_resilience_data('data/resilience_scores.csv')
    if len(resilience_df) == 0:
        print("Impossible de continuer sans données résilience")
        return gpd.GeoDataFrame()
    
    
    # Vérifier si GeoJSON a des IDs temporaires
    if regions_gdf['region_id'].iloc[0].startswith('TEMP_'):
        print("\nGeoJSON sans IDs réels détecté")
        print("MERGE PAR ORDRE (index)")
        
        # Vérifier que les longueurs correspondent
        if len(regions_gdf) != len(resilience_df):
            print(f"ERREUR: {len(regions_gdf)} géométries ≠ {len(resilience_df)} données CSV")
            print("On prend seulement les correspondances possibles")
            
            # Prendre le minimum
            n = min(len(regions_gdf), len(resilience_df))
            regions_gdf = regions_gdf.head(n)
            resilience_df = resilience_df.head(n)
        
        # MERGE PAR INDEX
        # Réinitialiser les index
        regions_gdf = regions_gdf.reset_index(drop=True)
        resilience_df = resilience_df.reset_index(drop=True)
        
        # Copier les vraies données du CSV dans le GeoDataFrame
        regions_gdf['region_id'] = resilience_df['region_id'].values
        regions_gdf['region_name'] = resilience_df['region_name'].values
        regions_gdf['exposure'] = resilience_df['exposure'].values
        regions_gdf['vulnerability'] = resilience_df['vulnerability'].values
        regions_gdf['adaptation'] = resilience_df['adaptation'].values
        
        # Ajouter population si présente
        if 'population' in resilience_df.columns:
            regions_gdf['population'] = resilience_df['population'].values
        else:
            # Population par défaut
            regions_gdf['population'] = 50000
        
        merged_gdf = regions_gdf
        
        print(f"{len(merged_gdf)} régions fusionnées par INDEX")
    
    else:
        # MERGE NORMAL par region_id
        print("\nMERGE NORMAL par region_id")
        
        # Normaliser IDs
        regions_gdf['region_id'] = regions_gdf['region_id'].astype(str).str.strip().str.upper()
        resilience_df['region_id'] = resilience_df['region_id'].astype(str).str.strip().str.upper()
        
        # Merge
        merged_gdf = regions_gdf.merge(
            resilience_df,
            on='region_id',
            how='inner',
            suffixes=('_geo', '_data')
        )
        
        # Gérer les colonnes dupliquées
        if 'region_name_data' in merged_gdf.columns:
            merged_gdf['region_name'] = merged_gdf['region_name_data']
            merged_gdf = merged_gdf.drop(columns=['region_name_geo', 'region_name_data'])
        
        # Ajouter population si absente
        if 'population' not in merged_gdf.columns:
            merged_gdf['population'] = 50000
        
        print(f"{len(merged_gdf)} régions fusionnées")
        
        # Vérifier pertes
        lost_geom = len(regions_gdf) - len(merged_gdf)
        lost_data = len(resilience_df) - len(merged_gdf)
        
        if lost_geom > 0:
            print(f"{lost_geom} géométries sans données (ignorées)")
        if lost_data > 0:
            print(f"{lost_data} données sans géométrie (ignorées)")
    
    # Vérification finale
    print(f"\nFUSION TERMINÉE: {len(merged_gdf)} régions")
    print(f"Colonnes: {merged_gdf.columns.tolist()}")
    
    # Vérifier colonnes essentielles
    required = ['region_id', 'region_name', 'geometry', 'exposure', 'vulnerability', 'adaptation']
    missing = [col for col in required if col not in merged_gdf.columns]
    
    if missing:
        print(f"ERREUR: Colonnes manquantes: {missing}")
    else:
        print(f"Toutes les colonnes requises présentes")
    
    return merged_gdf


def load_hazard_zones(filepath='data/mock/hazard_zones.geojson'):
    """Charge zones de danger (optionnel)"""
    try:
        gdf = gpd.read_file(filepath)
        print(f"{len(gdf)} zones de danger chargées")
        return gdf
    except:
        return gpd.GeoDataFrame()


# TESTS
if __name__ == "__main__":
    print("=" * 60)
    print("TESTS DATA LOADER (VERSION FIXÉE)")
    print("=" * 60)
    
    # Test fusion
    df = merge_data()
    
    if len(df) > 0:
        print("\nRÉSULTAT FINAL:")
        print(df[['region_id', 'region_name', 'exposure', 'vulnerability', 'adaptation']].head(10))
        
        print(f"\n{len(df)} régions prêtes pour l'app!")
    else:
        print("\nÉchec du chargement")
    
    print("\n" + "=" * 60)