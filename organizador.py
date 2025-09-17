import streamlit as st
import pandas as pd
import os
from datetime import date
import plotly.express as px

# ==========================
# Configuración inicial
# ==========================
ARCHIVO = "tareas.csv"
CARPETA_SOPORTES = "soportes"
PERSONAS = ["Carlos", "Alfredo", "Victoria", "Catalina", "Camilo"]

# Crear carpeta si no existe
os.makedirs(CARPETA_SOPORTES, exist_ok=True)

# Cargar o crear archivo
if os.path.exists(ARCHIVO):
    df = pd.read_csv(ARCHIVO)
else:
    df = pd.DataFrame(columns=["Tarea", "Responsable", "Fecha Límite", "Soporte", "Prioridad", "Estado", "Finalizada"])

# Asegurar que la columna Soporte y Finalizada existan
if "Soporte" not in df.columns:
    df["Soporte"] = ""
if "Finalizada" not in df.columns:
    df["Finalizada"] = False

# ==========================
# Interfaz Streamlit
# ==========================
st.title("📋 Organizador de Tareas - Equipo")

# --- Filtro por persona ---
filtro_persona = st.selectbox(
    "👤 Ver tareas de:", 
    ["Todos"] + PERSONAS, 
    key="filtro_persona"
)
if filtro_persona != "Todos":
    df_filtrado = df[df["Responsable"] == filtro_persona]
else:
    df_filtrado = df

# --- Mostrar tabla ---
st.subheader("📊 Tareas registradas")
# Verificar si la columna "Prioridad" existe antes de intentar eliminarla
if "Prioridad" in df.columns:
    df_filtrado_sin_prioridad = df_filtrado.drop(columns=["Prioridad"])  # Eliminar columna de prioridad
else:
    df_filtrado_sin_prioridad = df_filtrado  # Si no existe, simplemente no la eliminamos

# Mostrar el DataFrame resultante
st.dataframe(df_filtrado_sin_prioridad)



# ==========================
# Zona de informes
# ==========================
st.subheader("📈 Informes")

if not df.empty:
    # Asegurar formato de fecha
    df["Fecha Límite"] = pd.to_datetime(df["Fecha Límite"], errors="coerce")
    hoy = date.today()

    # Filtrar tareas activas (sin estar finalizadas y con fecha válida)
    tareas_activas = df[(df["Fecha Límite"] >= pd.to_datetime(hoy)) & 
                        (df["Finalizada"] == False) & 
                        (df["Fecha Límite"].notna())]  # Asegurarse que la fecha no sea NaT

    # Número de tareas vencidas (sin estar finalizadas y con fecha válida)
    vencidas = df[(df["Fecha Límite"] < pd.to_datetime(hoy)) & 
                  (df["Finalizada"] == False) & 
                  (df["Fecha Límite"].notna())]  # Asegurarse que la fecha no sea NaT

    col1, col2 = st.columns(2)
    with col1:
        st.metric("👥 Total Tareas activas", len(tareas_activas))
    with col2:
        st.metric("⏳ Tareas vencidas", len(vencidas))


    # Gráfico: tareas por persona
    st.write("### 👤 Tareas por persona")
    tareas_por_persona = df["Responsable"].value_counts()
    st.bar_chart(tareas_por_persona)

# ==========================
# Formulario para nueva tarea
# ==========================
st.subheader("➕ Agregar nueva tarea")
with st.form("nueva_tarea"):
    tarea = st.text_input("Descripción de la tarea")
    responsable = st.selectbox("Asignar a:", PERSONAS, key="nuevo_responsable")
    fecha = st.date_input("Fecha límite")
    soporte = st.file_uploader("📎 Adjuntar soporte", type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx"], key="nuevo_soporte")

    submitted = st.form_submit_button("Guardar")

    if submitted and tarea.strip():
        soporte_path = ""
        if soporte is not None:
            soporte_path = os.path.join(CARPETA_SOPORTES, soporte.name)
            with open(soporte_path, "wb") as f:
                f.write(soporte.getbuffer())

        # Aseguramos que las columnas estén bien ordenadas y los valores correctos
        nueva = pd.DataFrame([[tarea, responsable, str(fecha), soporte_path, "Alta", "En curso", False]],
                             columns=["Tarea", "Responsable", "Fecha Límite", "Soporte", "Prioridad", "Estado", "Finalizada"])
        
        # Añadimos la nueva tarea al DataFrame y lo guardamos
        df = pd.concat([df, nueva], ignore_index=True)
        df.to_csv(ARCHIVO, index=False)
        st.success("✅ Tarea agregada con éxito")
        st.rerun()

# ==========================
# Buscar tarea y mostrar soportes
# ==========================
st.subheader("🔍 Buscar tareas y ver soportes")

# Crear un buscador de tareas
tarea_selec = st.selectbox("Seleccionar tarea:", df["Tarea"])

# Mostrar soportes de la tarea seleccionada
if tarea_selec:
    soportes_str = str(df[df["Tarea"] == tarea_selec]["Soporte"].values[0]) if pd.notna(df[df["Tarea"] == tarea_selec]["Soporte"].values[0]) else ""
    soportes = [s for s in soportes_str.split(";") if s.strip() != ""]
    
    if soportes:
        st.write(f"**Soportes de la tarea '{tarea_selec}':**")
        for soporte_path in soportes:
            if os.path.exists(soporte_path):
                with open(soporte_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ {os.path.basename(soporte_path)}",
                        data=f,
                        file_name=os.path.basename(soporte_path),
                        key=f"descargar_{soporte_path}"
                    )

# ==========================
# Finalizar tarea
# ==========================
st.subheader("✅ Finalizar tarea")

tarea_finalizar = st.selectbox("Seleccionar tarea para finalizar:", df[df["Finalizada"] == False]["Tarea"])

if tarea_finalizar:
    if st.button("Finalizar tarea"):
        # Marcar tarea como finalizada
        df.loc[df["Tarea"] == tarea_finalizar, "Finalizada"] = True
        df.to_csv(ARCHIVO, index=False)
        st.success("✅ Tarea finalizada correctamente")
        st.rerun()


