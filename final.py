# streamlit_app.py

import pandas as pd                            # Aqui importo pandas para manejar y procesar mis datos en DataFrame
import plotly.express as px                   # Aqui importo plotly.express para crear graficos interactivos facilmente
import streamlit as st                        # Aqui importo streamlit para construir la interfaz web de mi aplicacion
import json                                   # Aqui importo json para leer archivos GeoJSON si los uso
import folium                                 # Aqui importo folium para generar mapas interactivos
from streamlit_folium import folium_static    # Aqui importo folium_static para incrustar mapas de folium en Streamlit

# 0. Limpieza de datos
st.subheader("0. Procesamiento y limpieza de la base de datos")
st.write("Eliminamos columnas añadidas automaticamente por Excel y normalizamos los textos.")

# 0.1 Leo el CSV limpio que el profesor subio al repo
df_raw = pd.read_csv("dataset2.csv")         # Aqui cargo el archivo 'dataset2.csv' con todas las columnas que necesito

# 0.2 Quito las columnas vacias que Excel dejo sin nombre
df = df_raw.loc[:, ~df_raw.columns.str.contains(r"^unnamed")]  # Aqui descarto cualquier columna cuyo nombre empiece por 'unnamed'

# 0.3 Convierto EDAD y ANO a valores numericos para poder graficar y filtrar
df["EDAD"] = pd.to_numeric(df["EDAD"], errors="coerce")
df["ANO"]  = pd.to_numeric(df["ANO"], errors="coerce")   

# 0.4 Elimino filas que falten datos criticos para mis analisis
df = df.dropna(subset=["EDAD", "ANO", "NOMBRE_DIAGNOSTIC", "SEXO", "DISTRITO"])  # Aqui me aseguro de que no haya valores nulos en columnas clave

# 0.5 Normalizo los textos para que todos los nombres queden bien presentados
text_cols = ["DEPARTAMENTO", "PROVINCIA", "DISTRITO", "NOMBRE_DIAGNOSTIC", "SEXO", "NOMBRE_ESTABLECIMIENTO"]
for col in text_cols:
    df[col] = df[col].astype(str).str.strip().str.title()  # Aqui quito espacios extra y pongo mayuscula inicial en cada palabra

# 0.6 Muestro al profesor como quedo mi DataFrame tras la limpieza
st.write("Columnas finales:", df.columns.tolist())
st.write(f"Numero de registros: {df.shape[0]}")
st.dataframe(df.head())  # Aqui enseño las primeras filas para verificar que todo este bien

# 1. Titulo e introduccion
st.title("Analisis Epidemiologico de Piura")
st.write("""
Trabajo final del curso de Pensamiento Computacional 2025-1  
Impartido por Emerson Trujillo  

Este proyecto procesa y limpia la informacion del Gobierno Regional de Piura 
y visualiza interactivamente patrones de las enfermedades metaxenicas, su distribucion temporal y geografica.
""")  # Aqui contextualizo el proyecto y cito al curso y al profesor

# 2. Exploracion Edad vs Enfermedad
st.subheader("1. Relacion Edad vs Enfermedad")
# Aqui creo un slider para que el usuario elija un rango de edad
age_min, age_max = st.slider(
    "Selecciona el rango de edad (años):",
    int(df["EDAD"].min()), int(df["EDAD"].max()),
    (int(df["EDAD"].quantile(0.05)), int(df["EDAD"].quantile(0.95)))
)
# Aqui filtro mi DataFrame segun el rango seleccionado
df_age = df[(df["EDAD"] >= age_min) & (df["EDAD"] <= age_max)]

if not df_age.empty:
    st.write("¿Como varia la incidencia de cada enfermedad segun la edad?")
    # Aqui agrupo por edad y enfermedad para contar casos
    age_disease = (
        df_age.groupby(["EDAD", "NOMBRE_DIAGNOSTIC"])  
              .size().reset_index(name="Casos")
    )
    # Aqui creo el grafico de burbujas con plotly
    bubble = px.scatter(
        age_disease,
        x="EDAD", y="Casos", size="Casos",
        color="NOMBRE_DIAGNOSTIC",
        hover_name="NOMBRE_DIAGNOSTIC",
        title="Incidencia por edad y enfermedad"
    )
    st.plotly_chart(bubble, use_container_width=True)

    # Aqui muestro un grafico de barras con el total de casos por enfermedad en el rango
    bar = px.bar(
        df_age["NOMBRE_DIAGNOSTIC"].value_counts()
            .rename_axis("Enfermedad").reset_index(name="Casos"),
        x="Casos", y="Enfermedad", orientation="h",
        title="Total de casos por enfermedad"
    )
    st.plotly_chart(bar, use_container_width=True)
else:
    st.warning("No hay datos para ese rango de edad. Ajusta el slider.")  # Aqui aviso si no hay registros para el rango elegido

# 3. Evolucion Sexo vs Año
st.subheader("2. Evolucion de casos por sexo y año")
# Aqui permito elegir un sexo para ver su tendencia anual
sexo_sel = st.selectbox("Selecciona sexo:", sorted(df["SEXO"].unique()))
# Aqui filtro el DataFrame segun el sexo elegido
df_sexo = df[df["SEXO"] == sexo_sel]
# Aqui agrupo por año y cuento casos
trend = df_sexo.groupby("ANO").size().reset_index(name="Casos")
# Aqui creo la grafica de linea con plotly
line = px.line(
    trend,
    x="ANO", y="Casos",
    title=f"Tendencia anual de casos ({sexo_sel})"
)
st.plotly_chart(line, use_container_width=True)

# 4. Distribucion geografica con Folium + GeoJSON
st.subheader("3. Distribucion de casos por distrito")
# Aqui preparo los datos para el choropleth
choropleth_df = df.groupby("DISTRITO").size().reset_index(name="Casos")
try:
    # Aqui leo el GeoJSON de los distritos de Piura
    geojson = json.load(open("piura_distritos.geojson", encoding="utf-8"))
    # Aqui inicializo el mapa centrado en Piura
    m = folium.Map(location=[-5.1945, -80.6328], zoom_start=9)
    # Aqui creo el choropleth para colorear distritos segun casos
    folium.Choropleth(
        geo_data=geojson,
        data=choropleth_df,
        columns=["DISTRITO", "Casos"],
        key_on="feature.properties.NOMDIST",  # Ajusta segun tu GeoJSON
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Casos"
    ).add_to(m)
    # Aqui incrusto el mapa en Streamlit
    folium_static(m)
except Exception:
    # Si falla, muestro un error y un grafico de barras como respaldo
    st.error("No se pudo cargar el mapa con GeoJSON. Mostrando grafico de barras como respaldo.")
    bar_geo = px.bar(
        choropleth_df.sort_values("Casos", ascending=False),
        x="Casos", y="DISTRITO", orientation="h",
        title="Casos por distrito (fallback)"
    )
    st.plotly_chart(bar_geo, use_container_width=True)

# 5. Seleccion de enfermedad y foto del vector
st.subheader("4. Elige una enfermedad y conoce su vector")
# Aqui defino manualmente el diccionario que asocia enfermedades a imagenes
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
# Aqui permito al usuario escoger la enfermedad de la lista
enf_sel = st.selectbox("Enfermedad:", sorted(df["NOMBRE_DIAGNOSTIC"].unique()))
# Aqui obtengo el archivo de imagen correspondiente
img_file = zancudos.get(enf_sel)
if img_file:
    # Aqui muestro la imagen del vector si existe en el diccionario
    st.image(img_file, caption=f"Vector: zancudo de {enf_sel}", use_column_width=True)

# 6. Conclusiones y recomendaciones
st.subheader("5. Conclusiones y recomendaciones")
st.write("""
- Se identificaron las enfermedades con mayor incidencia y sus grupos etarios mas afectados.  
- Los distritos con mayor numero de casos son X, Y y Z.  
- Se observa tendencia creciente/estable/disminuyente en ciertas enfermedades segun el sexo.  

**Recomendaciones:**  
1. Fortalecer la vigilancia en los distritos mas afectados.  
2. Orientar campañas educativas a los rangos de edad con mayor incidencia.  
3. Intensificar monitoreo en establecimientos de salud prioritarios.
""")  # Aqui presento mis conclusiones finales y sugerencias basadas en los resultados
