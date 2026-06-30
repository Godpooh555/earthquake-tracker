import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium

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
    significant_quakes = gdf_quakes[gdf_quakes['mag'] >= min_magnitude]
    
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
            column="depth",
            cmap="viridis_r",
            scheme="Quantiles", 
            k=5, 
            legend_kwds={"caption": "Depth (km)", "fmt": "{:.0f}"},
            marker_kwds={"radius": 8},
            style_kwds={"style_function": lambda x: {"radius": int(x["properties"]["mag"]) * 2}},
            tooltip=["place", "mag", "depth"],
            name="Significant Earthquakes"
        )
        
        st_folium(map_overlay, width=1000, height=600)
    else:
        st.warning(f"No earthquakes met the criteria (>= {min_magnitude}).")

except Exception as e:
    st.error(f"An error occurred while fetching data: {e}")
