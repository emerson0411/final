import pandas as pd                            # Uso pandas para leer y procesar mis datos
import plotly.express as px                   # Uso plotly.express para crear gráficos interactivos
import streamlit as st                        # Uso Streamlit para montar la interfaz web
import json                                   # Uso json para leer archivos GeoJSON
import folium                                 # Uso Folium para generar mapas interactivos
from streamlit_folium import folium_static    # Uso folium_static para incrustar mapas en Streamlit

# 0. Procesamiento y limpieza de datos (interno, no mostrado al usuario)
df_raw = pd.read_csv("dataset2.csv")  # Cargo datos ya depurados en Excel
# Quito columnas sobrantes que Excel añadió automáticamente
df = df_raw.loc[:, ~df_raw.columns.str.contains(r"^Unnamed")]  
# Convierto EDAD y ANO a valores numéricos para poder filtrar y graficar
df["EDAD"] = pd.to_numeric(df["EDAD"], errors="coerce")
df["ANO"]  = pd.to_numeric(df["ANO"], errors="coerce")
# Elimino filas sin datos críticos en columnas clave
df = df.dropna(subset=["EDAD", "ANO", "NOMBRE_DIAGNOSTIC", "SEXO", "DISTRITO"])
# Normalizo texto: quito espacios extra y pongo formato título
text_cols = ["DEPARTAMENTO", "PROVINCIA", "DISTRITO", "NOMBRE_DIAGNOSTIC", "SEXO", "NOMBRE_ESTABLECIMIENTO"]
for col in text_cols:
    df[col] = df[col].astype(str).str.strip().str.title()

# 1. Título e introducción
st.title("Análisis Epidemiológico de Piura")
st.write("""
Trabajo final del curso de Pensamiento Computacional 2025-1  
Impartido por Emerson Trujillo  

Este proyecto procesa y limpia la información del Gobierno Regional de Piura 
y muestra hallazgos clave de las enfermedades metaxénicas: tendencias de edad, sexo y distribución geográfica.
""")

# 2. Relación Edad vs Enfermedad
st.subheader("1. Relación Edad vs Enfermedad")
# Slider para rango de edad
min_age, max_age = int(df["EDAD"].min()), int(df["EDAD"].max())
start_age, end_age = int(df["EDAD"].quantile(0.05)), int(df["EDAD"].quantile(0.95))
age_min, age_max = st.slider("Selecciona el rango de edad (años):", min_age, max_age, (start_age, end_age))
# Filtro datos por edad seleccionada
df_age = df[(df["EDAD"] >= age_min) & (df["EDAD"] <= age_max)]
if not df_age.empty:
    st.write("**¿Cómo varía la incidencia de cada enfermedad según la edad?**")
    # Agrupo por edad y enfermedad para contar casos
    df_age_counts = (
        df_age.groupby(["EDAD", "NOMBRE_DIAGNOSTIC"])  
              .size().reset_index(name="Casos")
    )
    # Gráfico de burbujas: tamaño y color según casos
    bubble = px.scatter(
        df_age_counts,
        x="EDAD", y="Casos", size="Casos",
        color="NOMBRE_DIAGNOSTIC",
        hover_name="NOMBRE_DIAGNOSTIC",
        title="Incidencia de enfermedades según edad"
    )
    st.plotly_chart(bubble, use_container_width=True)

    # Gráfico de barras horizontales con total de casos por enfermedad
    enf_bar = (
        df_age["NOMBRE_DIAGNOSTIC"].value_counts()
        .rename_axis("Enfermedad").reset_index(name="Casos")
    )
    bar = px.bar(
        enf_bar,
        x="Casos", y="Enfermedad", orientation="h",
        title="Total de casos por enfermedad en el rango de edad"
    )
    st.plotly_chart(bar, use_container_width=True)
else:
    st.warning("No hay datos en el rango de edad seleccionado. Ajusta el slider para ampliar la muestra.")

# 3. Evolución de casos por Sexo y Año
st.subheader("2. Evolución de casos por sexo y año")
sexo_sel = st.selectbox("Selecciona sexo:", sorted(df["SEXO"].unique()))  # Selección de sexo
# Filtro registros por el sexo elegido
df_sexo = df[df["SEXO"] == sexo_sel]
# Agrupo por año y cuento casos
yearly_trend = df_sexo.groupby("ANO").size().reset_index(name="Casos")
# Gráfico de línea para mostrar la tendencia anual
line = px.line(
    yearly_trend,
    x="ANO", y="Casos",
    markers=True,
    title=f"Tendencia anual de casos ({sexo_sel})"
)
st.plotly_chart(line, use_container_width=True)

# 4. Distribución geográfica por Distrito
st.subheader("3. Distribución de casos por distrito")
choropleth_df = df.groupby("DISTRITO").size().reset_index(name="Casos")  # Conteo por distrito
try:
    geojson = json.load(open("piura_distritos.geojson", encoding="utf-8"))  # Leo GeoJSON
    m = folium.Map(location=[-5.1945, -80.6328], zoom_start=9)  # Mapa centrado en Piura
    folium.Choropleth(
        geo_data=geojson,
        data=choropleth_df,
        columns=["DISTRITO", "Casos"],
        key_on="feature.properties.NOMDIST",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Casos"
    ).add_to(m)
    folium_static(m)  # Incrusto mapa en Streamlit
except Exception:
    st.error("No se pudo cargar el mapa. Mostrando gráfico de pastel como respaldo.")
    pie = px.pie(
        choropleth_df,
        values="Casos", names="DISTRITO",
        title="Proporción de casos por distrito (fallback)"
    )
    st.plotly_chart(pie, use_container_width=True)

# 5. Selección de enfermedad y foto del vector
st.subheader("4. Elige una enfermedad y conoce su vector")
zancudos = {  # Diccionario manual de vectores
    "Bartonelosis":   "bartonelosis.jpg",
    "Chagas":         "chagas.jpg",
    "Chikungunya":    "chikungunya.jpg",
    "Dengue":         "dengue.jpg",
    "Guillain_Barre": "guillain_barre.jpg",
    "Leishmaniasis":  "leishmaniasis.jpg",
    "Paludismo":      "paludismo.jpg",
    "Zika":           "zika.jpg",
}
enf_sel = st.selectbox("Enfermedad:", list(zancudos.keys()))  # Menú solo del diccionario
if enf_sel in zancudos:
    st.image(zancudos[enf_sel], caption=f"Vector asociado a {enf_sel}", use_column_width=True)

# 6. Conclusiones y recomendaciones
st.subheader("5. Conclusiones y recomendaciones")
# Cálculo de métricas clave
top_diseases = df["NOMBRE_DIAGNOSTIC"].value_counts().head(3).index.tolist()
top_districts = df["DISTRITO"].value_counts().head(3).index.tolist()
median_age = df["EDAD"].median()
# Presento las conclusiones
st.write(f"- Las tres enfermedades con mayor incidencia son: {', '.join(top_diseases)}.")
st.write(f"- Los tres distritos más afectados son: {', '.join(top_districts)}.")
st.write(f"- La mediana de edad de los casos es de aproximadamente {median_age:.1f} años.")
st.write("**Recomendaciones:**")
st.write("1. Fortalecer la vigilancia epidemiológica y laboratorio en los distritos más críticos.")
st.write("2. Enfocar campañas educativas en los grupos etarios con mayor incidencia.")
st.write("3. Mantener actualizada la base de datos y explorar la inclusión de mapas geoespaciales con GeoJSON.")
```
