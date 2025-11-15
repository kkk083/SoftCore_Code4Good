import folium
from folium import LayerControl
from utils.config import MAURITIUS_CENTER

# Création de la base de carte
def create_base_map() -> folium.Map:
    m = folium.Map(
        location=MAURITIUS_CENTER,
        zoom_start=10,
        tiles="CartoDB Positron",
        control_scale=True
    )

    folium.LatLngPopup().add_to(m)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OSM"
    ).add_to(m)

    # LayerControl pour activer/désactiver les couches
    LayerControl(collapsed=False).add_to(m)

    return m