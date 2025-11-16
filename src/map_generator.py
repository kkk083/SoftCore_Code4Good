import folium
import geopandas as gpd
from utils.config import (
    MAURITIUS_CENTER,
    MAURITIUS_ZOOM_START,
    COLOR_SCHEME
)


def create_base_map():
    """Crée la carte de base centrée sur Maurice."""
    base_map = folium.Map(
        location=MAURITIUS_CENTER,
        zoom_start=MAURITIUS_ZOOM_START,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    print("DEV 3: Carte de base créée")
    return base_map


def get_color_for_category(category):
    """
    Retourne couleur HEX selon catégorie (4 niveaux)
    """
    category = str(category).lower().strip()
    
    if category == 'critical':
        return COLOR_SCHEME['critical']  # Rouge
    elif category == 'low':
        return COLOR_SCHEME['low']       # Orange
    elif category == 'medium':
        return COLOR_SCHEME['medium']    # Jaune
    elif category == 'high':
        return COLOR_SCHEME['high']      # Vert
    else:
        return COLOR_SCHEME['medium']    # Défaut: jaune


def add_resilience_layer(map_obj, gdf):
    """
    Ajoute la couche de résilience colorée sur la carte.

    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        gdf = gpd.GeoDataFrame(gdf, geometry='geometry')
    
    required = ['geometry', 'resilience_index', 'category', 'region_name']
    missing = [col for col in required if col not in gdf.columns]
    
    if missing:
        raise ValueError(f"DEV 3: Colonnes manquantes: {missing}")
    
    # Debug couleurs
    print("\nCOULEURS PAR RÉGION:")
    for _, row in gdf.iterrows():
        cat = row['category']
        color = get_color_for_category(cat)
        print(f"  {row['region_name']:25s} → {cat:8s} → {color}")
    
    # Convertir en GeoJSON
    geojson_data = gdf.__geo_interface__
    
    # Style fonction
    def style_function(feature):
        props = feature['properties']
        category = props.get('category', 'medium')
        color = get_color_for_category(category)
        
        return {
            'fillColor': color,
            'color': 'black',
            'weight': 1.5,
            'fillOpacity': 0.45,    
            'opacity': 1
        }
    
    def highlight_function(feature):
        props = feature['properties']
        category = props.get('category', 'medium')
        color = get_color_for_category(category)
        
        return {
            'fillColor': color,
            'color': '#ffffff',
            'weight': 3,
            'fillOpacity': 0.7,     
            'opacity': 1
        }
    
    # Tooltip fields
    tooltip_fields = ['region_name', 'resilience_index', 'category']
    tooltip_aliases = ['Région:', 'Résilience:', 'Catégorie:']
    
    if 'exposure' in gdf.columns:
        tooltip_fields.extend(['exposure', 'vulnerability', 'adaptation'])
        tooltip_aliases.extend(['Exposition:', 'Vulnérabilité:', 'Adaptation:'])
    
    # Ajouter la couche GeoJson
    folium.GeoJson(
        geojson_data,
        name='Résilience Climatique',
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=False,
            labels=True,
            style="""
                background-color: white;
                border: 2px solid black;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            """
        )
    ).add_to(map_obj)
    
    print(f"DEV 3: Couche résilience ajoutée ({len(gdf)} régions)")
    
    return map_obj


def add_hazard_layer(map_obj, hazard_gdf):
    """Ajoute couche zones de danger (optionnel)"""
    if len(hazard_gdf) == 0:
        return map_obj
    
    icon_map = {
        'flood_zone': {'icon': 'tint', 'color': 'red'},
        'cyclone_shelter': {'icon': 'home', 'color': 'green'},
        'hospital': {'icon': 'plus-square', 'color': 'blue'},
        'fire_station': {'icon': 'fire-extinguisher', 'color': 'orange'}
    }
    
    for idx, row in hazard_gdf.iterrows():
        hazard_type = row.get('hazard_type', 'unknown')
        icon_config = icon_map.get(hazard_type, {'icon': 'info-sign', 'color': 'gray'})
        
        popup_text = f"<b>{hazard_type.replace('_', ' ').title()}</b><br>"
        if 'severity' in row:
            popup_text += f"Sévérité: {row['severity']}<br>"
        if 'capacity' in row:
            popup_text += f"Capacité: {row['capacity']} personnes"
        
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=folium.Popup(popup_text, max_width=200),
            icon=folium.Icon(
                icon=icon_config['icon'],
                prefix='fa',
                color=icon_config['color']
            )
        ).add_to(map_obj)
    
    print(f"DEV 3: {len(hazard_gdf)} zones de danger ajoutées")
    return map_obj


def add_legend(map_obj):
    """
    Légende compacte à DROITE
    """
    from branca.element import MacroElement, Template
    
    template = """
    {% macro html(this, kwargs) %}
    
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    
    <div id='maplegend' style='
        position: absolute;
        z-index: 9999;
        background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
        border-radius: 10px;
        border: 2.5px solid #2c3e50;
        top: 20px;
        right: 20px;
        padding: 12px;
        font-size: 13px;
        font-family: "Segoe UI", Arial, sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
        min-width: 180px;
    '>
    
    <div style='
        margin-bottom: 10px; 
        font-weight: bold; 
        font-size: 15px; 
        text-align: center; 
        color: #2c3e50;
        border-bottom: 2px solid #3498db; 
        padding-bottom: 6px;
    '>
        Résilience
    </div>
    
    <div style='margin: 6px 0; display: flex; align-items: center;'>
      <span style='color: #1a9850; font-size: 18px; font-weight: bold; margin-right: 8px;'>█</span>
      <span style='font-weight: 600; color: #1a9850; font-size: 13px;'>Élevé</span>
      <span style='color: #999; font-size: 11px; margin-left: 4px;'>(70+)</span>
    </div>
    
    <div style='margin: 6px 0; display: flex; align-items: center;'>
      <span style='color: #fee08b; font-size: 18px; font-weight: bold; margin-right: 8px; text-shadow: 0 0 2px rgba(0,0,0,0.2);'>█</span>
      <span style='font-weight: 600; color: #d68910; font-size: 13px;'>Moyen</span>
      <span style='color: #999; font-size: 11px; margin-left: 4px;'>(50-70)</span>
    </div>
    
    <div style='margin: 6px 0; display: flex; align-items: center;'>
      <span style='color: #fc8d59; font-size: 18px; font-weight: bold; margin-right: 8px;'>█</span>
      <span style='font-weight: 600; color: #e67e22; font-size: 13px;'>Faible</span>
      <span style='color: #999; font-size: 11px; margin-left: 4px;'>(30-50)</span>
    </div>
    
    <div style='margin: 6px 0; display: flex; align-items: center;'>
      <span style='color: #d73027; font-size: 18px; font-weight: bold; margin-right: 8px;'>█</span>
      <span style='font-weight: 600; color: #c0392b; font-size: 13px;'>Critique</span>
      <span style='color: #999; font-size: 11px; margin-left: 4px;'>(0-30)</span>
    </div>
    
    </div>
    
    </body>
    </html>
    
    <style type='text/css'>
      #maplegend {
        display: block !important;
      }
    </style>
    {% endmacro %}
    """
    
    macro = MacroElement()
    macro._template = Template(template)
    
    map_obj.get_root().add_child(macro)
    
    print("DEV 3: Légende à droite ajoutée")
    
    return map_obj