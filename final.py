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
""")  # Aquí explico el propósito del blog y menciono al curso y al profesor

# 2. Relación Edad vs Enfermedad
st.subheader("1. Relación Edad vs Enfermedad")
# Slider para rango de edad
df_min, df_max = int(df["EDAD"].min()), int(df["EDAD"].max())
q05, q95 = int(df["EDAD"].quantile(0.05)), int(df["EDAD"].quantile(0.95))
age_min, age_max = st.slider("Selecciona el rango de edad (años):", df_min, df_max, (q05, q95))
# Filtro datos según rango elegido
df_age = df[(df["EDAD"] >= age_min) & (df["EDAD"] <= age_max)]
if not df_age.empty:
    st.write("**¿Cómo varía la incidencia de cada enfermedad según la edad?**")
    # Agrupo por edad y enfermedad
    df_age_counts = df_age.groupby(["EDAD", "NOMBRE_DIAGNOSTIC"]).size().reset_index(name="Casos")
    # Gráfico de burbujas: cada burbuja muestra casos por edad y enfermedad
    bubble = px.scatter(
        df_age_counts,
        x="EDAD", y="Casos", size="Casos",
        color="NOMBRE_DIAGNOSTIC", hover_name="NOMBRE_DIAGNOSTIC",
        title="Incidencia de enfermedades según edad"
    )
    st.plotly_chart(bubble, use_container_width=True)
    # Además presento un gráfico de barras
    enf_bar = df_age["NOMBRE_DIAGNOSTIC"].value_counts().rename_axis("Enfermedad").reset_index(name="Casos")
    bar = px.bar(
        enf_bar, x="Casos", y="Enfermedad", orientation="h",
        title="Total de casos por enfermedad en el rango de edad"
    )
    st.plotly_chart(bar, use_container_width=True)
else:
    st.warning("No hay datos en el rango de edad seleccionado. Ajusta el slider para ampliar la muestra.")

# 3. Evolución de casos por Sexo y Año
st.subheader("2. Evolución de casos por sexo y año")
# El usuario selecciona un sexo para ver la tendencia
df_sex_list = sorted(df["SEXO"].unique())
sexo_sel = st.selectbox("Selecciona sexo:", df_sex_list)
df_sexo = df[df["SEXO"] == sexo_sel]
# Agrupo por año
t_year = df_sexo.groupby("ANO").size().reset_index(name="Casos")
# Grafico línea con marcadores
graph_line = px.line(
    t_year, x="ANO", y="Casos", markers=True,
    title=f"Tendencia anual de casos ({sexo_sel})"
)
st.plotly_chart(graph_line, use_container_width=True)

# 4. Distribución de casos por Distrito
st.subheader("3. Distribución de casos por distrito")
# Agrupo casos por distrito
district_counts = df.groupby("DISTRITO").size().reset_index(name="Casos")
# Diccionario con coordenadas aproximadas de los distritos de Piura
# (Completa este diccionario con todos los distritos de tu CSV para que aparezcan en el mapa)
district_coords = {
    "Piura": [-5.1945, -80.6328],
    "Castilla": [-5.2050, -80.6250],
    "Veintiséis De Octubre": [-5.1840, -80.6300],
    "La Arena": [-5.1240, -80.6750],
    "Catacaos": [-5.1575, -80.6216],
    "Cura Mori": [-5.3150, -80.7010],
    "El Tallan": [-5.2900, -80.6300],
    "La Unión": [-5.2078, -80.5672],
    "Las Lomas": [-5.2465, -80.5798],
    "Tambogrande": [-4.9680, -80.6198],
    # ...Agrega aquí los demás distritos
}
# Inicializo el mapa centrado en la región de Piura
dept_center = [-5.1945, -80.6328]
mapa = folium.Map(location=dept_center, zoom_start=9)
# Agrego un marcador por distrito mostrando el número total de casos
for _, row in district_counts.iterrows():
    distrito = row["DISTRITO"]
    casos = row["Casos"]
    coords = district_coords.get(distrito)
    if coords:
        folium.Marker(
            location=coords,
            popup=f"{distrito}: {casos} casos"
        ).add_to(mapa)
# Muestro el mapa con los marcadores
folium_static(mapa)

# Además, presento un gráfico de pastel para ver proporciones
title_pie = "Proporción de casos por distrito"
pie = px.pie(
    district_counts,
    values="Casos", names="DISTRITO",
    title=title_pie
)
st.plotly_chart(pie, use_container_width=True)

# 5. Selección de enfermedad y foto del zancudo Selección de enfermedad y foto del zancudo Selección de enfermedad y foto del zancudo Selección de enfermedad y foto del zancudo
st.subheader("4. Elige una enfermedad y conoce el zancudo asociado")
# Diccionario manual de enfermedades a imágenes
zancudos = {
    "Bartonelosis":   "bartonelosis.jpg",
    "Chagas":         "chagas.jpg",
    "Chikungunya":    "chikungunya.jpg",
    "Dengue":         "dengue.jpg",
    "Guillain_Barre": "guillain_barre.jpg",
    "Leishmaniasis":  "leishmaniasis.jpg",
    "Paludismo":      "paludismo.jpg",
    "Zika":           "zika.jpg",
}
enf_keys = list(zancudos.keys())
enf_sel = st.selectbox("Enfermedad:", enf_keys)
# Muestro la imagen del zancudo
st.image(zancudos[enf_sel], caption=f"Zancudo: {enf_sel}", use_container_width=True)

# 6. Conclusiones y recomendaciones
st.subheader("5. Conclusiones y recomendaciones")
# Cálculo de métricas clave
top_diseases = df["NOMBRE_DIAGNOSTIC"].value_counts().head(3).index.tolist()
top_districts = df["DISTRITO"].value_counts().head(3).index.tolist()
median_age = df["EDAD"].median()
# Despliego hallazgos
st.write(f"- Las tres enfermedades con mayor incidencia son: {', '.join(top_diseases)}.")
st.write(f"- Los tres distritos más afectados son: {', '.join(top_districts)}.")
st.write(f"- La mediana de edad de los casos es de aproximadamente {median_age:.1f} años.")
# Sugerencias finales
st.write("**Recomendaciones:**")
st.write("1. Fortalecer la vigilancia epidemiológica en los distritos más críticos.")
st.write("2. Orientar campañas educativas a los grupos de edad más vulnerables.")
st.write("3. Mantener actualizada la base de datos y considerar agregar otras capas geoespaciales.")
```
