import streamlit as st
from streamlit_folium import st_folium
from src.map_generator import create_base_map

st.set_page_config(layout="wide")
st.title("IslandGuard")

m = create_base_map()
st_folium(m, width=1400, height=700)