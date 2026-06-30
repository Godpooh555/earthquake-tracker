import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import pandas as pd

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
PLATES_URL = "https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_boundaries.json"

st.set_page_config(page_title="Earthquake Tracker", layout="wide")
st.title("Live Earthquake Tracker")

min_magnitude = st.sidebar.slider("Minimum Magnitude Threshold", 2.5, 9.0, 4.0, 0.1)

@st.cache_data(ttl=3600)
def load_data():
    quakes = gpd.read_file(USGS_URL)
    plates = gpd.read_file(PLATES_URL)
    
    quakes['depth'] = quakes['geometry'].apply(lambda geom: geom.z if geom.has_z else 0)
    
    return quakes, plates

try:
    gdf_quakes, gdf_plates = load_data()

    significant_quakes = gdf_quakes[gdf_quakes['mag'] >= min_magnitude].copy() 
    
    significant_quakes['Depth Category'] = pd.cut(
        significant_quakes['depth'],
        bins=[-10, 33, 70, 300, 1000],
        labels=['Shallow (<33km)', 'Intermediate (33-70km)', 'Deep (70-300km)', 'Ultra-Deep (>300km)']
    )
    
    st.sidebar.write(f"Total events (last 2.5 days): {len(gdf_quakes)}")
    st.sidebar.write(f"Events shown: {len(significant_quakes)}")

    if not significant_quakes.empty:
        map_overlay = gdf_plates.explore(
            color="blue", 
            style_kwds={"weight": 1.5}, 
            name="Tectonic Plates"
        )
        
        significant_quakes.explore(
            m=map_overlay, 
            column="Depth Category",  # Map the color to our new text categories
            cmap="viridis_r",
            categorical=True,         # This is the magic word that fixes the legend!
            marker_kwds={"radius": 8},
            style_kwds={"style_function": lambda x: {"radius": int(x["properties"]["mag"]) * 2}},
            tooltip=["place", "mag", "depth", "Depth Category"],
            name="Significant Earthquakes"
        )
        
        st_folium(map_overlay, width=1000, height=600)
    else:
        st.warning(f"No earthquakes met the criteria (>= {min_magnitude}).")

except Exception as e:
    st.error(f"An error occurred while fetching data: {e}")
