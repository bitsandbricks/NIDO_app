import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from branca.element import Element

# Set the page configuration for a wider and more professional layout
st.set_page_config(
    page_title="Visualizador NIDO",
    page_icon="🗺️",
    layout="wide"
)

# --- App Title and Description ---
st.title("🗺️ Visualizador Espacial del Indice NIDO")
st.markdown("Use el panel de la izquierda para definir la importancia de cada aspecto. El índice se calcula a nivel nacional y luego se visualiza para la provincia seleccionada.")

# --- Data Loading and Cleaning ---
@st.cache_data
def load_data(filepath):
    """
    Loads a GeoDataFrame, re-projects it, and cleans the geometries.
    """
    try:
        with st.spinner("Cargando y limpiando datos (esto solo se ejecuta una vez)..."):
            gdf = gpd.read_file(filepath)
            gdf = gdf.to_crs(epsg=4326)
            gdf['geometry'] = gdf.geometry.buffer(0)
        return gdf
    except Exception as e:
        st.error(f"❌ Error al cargar o limpiar el archivo GeoPackage: {e}")
        return None

# --- Function to create a clean province boundary layer ---
@st.cache_data
def create_province_boundaries(_cleaned_gdf):
    """
    Dissolves the GeoDataFrame by 'NOMPROV' to create a layer for clipping and borders.
    """
    if 'NOMPROV' not in _cleaned_gdf.columns:
        return None
    provinces = _cleaned_gdf.dissolve(by='NOMPROV').reset_index()
    return provinces[['NOMPROV', 'geometry']]

# --- Core processing function now ONLY calculates at national level ---
@st.cache_data
def calculate_national_index(_gdf, w_salud, w_educ, w_contexto, w_ambiente):
    """
    Calculates a custom NIDO index on the entire dataset, then bins and dissolves.
    This ensures the scale is consistent nationwide.
    """
    gdf = _gdf.copy()
        
    variables = {
        "salud": ["cobertura_salud", "cercania_a_salud"],
        "educacion": ["asiste_educ_0_5", "cercania_a_j_maternal", "cercania_a_j_infantes"],
        "contexto": ["clima_educ_alto_muy_alto", "tasa_pob_activa_empleada", "tasa_empleados_sectores_sec_ter"],
        "ambiente": ["cercania_a_EV"]
    }
    weight_map = {"Nula": 0, "Baja": 33, "Media": 66, "Alta": 100}

    gdf['custom_NIDO_raw'] = (
        gdf[variables['salud']].mean(axis=1) * weight_map[w_salud] +
        gdf[variables['educacion']].mean(axis=1) * weight_map[w_educ] +
        gdf[variables['contexto']].mean(axis=1) * weight_map[w_contexto] +
        gdf[variables['ambiente']].mean(axis=1) * weight_map[w_ambiente]
    )

    min_val, max_val = gdf['custom_NIDO_raw'].min(), gdf['custom_NIDO_raw'].max()
    if max_val > min_val:
        gdf['custom_NIDO'] = (gdf['custom_NIDO_raw'] - min_val) / (max_val - min_val)
    else:
        gdf['custom_NIDO'] = 0.5

    labels = ["Muy bajo", "Bajo", "Medio", "Alto", "Muy alto"]
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    gdf['NIDO_scale'] = pd.cut(gdf['custom_NIDO'], bins=bins, labels=labels, include_lowest=True, right=True)

    dissolved_gdf = gdf.dissolve(by='NIDO_scale', observed=True).reset_index()
    return dissolved_gdf

# --- Main App Logic ---
gdf = load_data("data/indicadores.gpkg")

if gdf is not None:
    provincias_gdf = create_province_boundaries(gdf)

    st.sidebar.header("Opciones de Filtro")
    province_list = sorted(gdf["NOMPROV"].unique().tolist())
    province_options = ["Todas"] + province_list
    selected_province = st.sidebar.selectbox(
        "Provincia:", province_options,
        help="Seleccione una provincia para hacer zoom y visualizar el índice."
    )

    st.sidebar.header("Priorización")
    weight_options = ["Nula", "Baja", "Media", "Alta"]
    
    w_salud = st.sidebar.radio("Salud", weight_options, index=3, horizontal=True)
    w_educ = st.sidebar.radio("Educación temprana", weight_options, index=2, horizontal=True)
    w_contexto = st.sidebar.radio("Contexto socioeconómico", weight_options, index=2, horizontal=True)
    w_ambiente = st.sidebar.radio("Ambiente saludable", weight_options, index=1, horizontal=True)

    # --- Processing Logic ---
    map_data_gdf = None
    with st.spinner('Generando índice nacional y preparando visualización...'):
        processed_national_gdf = calculate_national_index(gdf, w_salud, w_educ, w_contexto, w_ambiente)

        if selected_province == "Todas":
            map_data_gdf = processed_national_gdf
        elif processed_national_gdf is not None and not processed_national_gdf.empty and provincias_gdf is not None:
            province_boundary = provincias_gdf[provincias_gdf['NOMPROV'] == selected_province]
            if not province_boundary.empty:
                map_data_gdf = gpd.clip(processed_national_gdf, province_boundary)
                if not map_data_gdf.empty:
                    map_data_gdf['geometry'] = map_data_gdf.geometry.buffer(0)
                    map_data_gdf = map_data_gdf[~map_data_gdf.geometry.is_empty]

    # --- Map Visualization ---
    if map_data_gdf is not None and not map_data_gdf.empty:
        bounds = map_data_gdf.total_bounds
        map_center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        
        m = folium.Map(location=map_center, zoom_start=6, tiles="cartodbpositronnolabels")

        color_dict = {"Muy alto": "#3288bd", "Alto": "#99d594", "Medio": "#fee08b", "Bajo": "#fc8d59", "Muy bajo": "#d53e4f"}

        def style_function(feature):
            nido_level = feature['properties']['NIDO_scale']
            # Set weight to 0 to make polygon boundaries transparent
            return {
                'fillColor': color_dict.get(nido_level, 'grey'),
                'weight': 0, # <-- This makes the borders invisible
                'fillOpacity': 0.8
            }

        folium.GeoJson(map_data_gdf, style_function=style_function).add_to(m)
        
        # This layer for province boundaries still has a visible border
        if selected_province == "Todas" and provincias_gdf is not None:
            folium.GeoJson(
                provincias_gdf,
                style_function=lambda x: {'color': 'black', 'weight': 1, 'fillOpacity': 0}
            ).add_to(m)

        folium.map.CustomPane("labels").add_to(m)
        folium.TileLayer("cartodbpositrononlylabels", pane="labels").add_to(m)

        present_labels = sorted(map_data_gdf['NIDO_scale'].unique(), key=list(color_dict.keys()).index)
        legend_html = '''<div style="position: fixed; bottom: 50px; right: 50px; width: 160px; border:2px solid grey; z-index:9999; font-size:14px; color:black; background-color:white; border-radius: 5px;"><h4 style="margin: 5px 10px;">Indice NIDO</h4><ul style="list-style-type: none; padding-left: 10px; margin-top: 5px; margin-bottom: 5px;">'''
        for label in present_labels:
            color = color_dict.get(label, 'grey')
            legend_html += f'<li><span style="background-color: {color}; width: 20px; height: 13px; display: inline-block; vertical-align: middle;"></span> {label}</li>'
        legend_html += '</ul></div>'
        m.get_root().html.add_child(Element(legend_html))

        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        st_folium(m, width=1200, height=700, returned_objects=[])
    
    else:
        st.warning(f"⚠️ No hay datos disponibles para procesar con la configuración actual en {selected_province}.")
else:
    st.info("ℹ️ Esperando la carga del archivo 'data/indicadores.gpkg'.")
    
