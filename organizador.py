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
    df = pd.DataFrame(columns=["Tarea", "Responsable", "Prioridad", "Estado", "Fecha Límite", "Soporte"])
# Normalizar columna Estado
if "Estado" in df.columns:
    df["Estado"] = df["Estado"].astype(str).str.strip().str.capitalize()

# Asegurar que la columna Soporte exista
if "Soporte" not in df.columns:
    df["Soporte"] = ""

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
st.dataframe(df_filtrado)

# ==========================
# Zona de informes
# ==========================
st.subheader("📈 Informes")

if not df.empty:
    # Asegurar formato de fecha
    df["Fecha Límite"] = pd.to_datetime(df["Fecha Límite"], errors="coerce")
    hoy = date.today()

    # Número de tareas por persona
    tareas_por_persona = df["Responsable"].value_counts()

    # Número de tareas por prioridad
    tareas_por_prioridad = df["Prioridad"].value_counts()

    # Número de tareas vencidas
    vencidas = df[(df["Fecha Límite"] < pd.to_datetime(hoy)) & (df["Estado"] != "Terminado")]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Total Tareas", len(df))
    with col2:
     pendientes = df[df["Estado"] == "Pendiente"]
     st.metric("⚡ Pendientes", len(pendientes))

    with col3:
        st.metric("⏳ Vencidas", len(vencidas))

    # Gráfico: tareas por persona
    st.write("### 👤 Tareas por persona")
    st.bar_chart(tareas_por_persona)

    # Gráfico: tareas por prioridad
    st.write("### ⚡ Distribución por prioridad")
    fig = px.pie(df, names="Prioridad", title="Prioridad de tareas")
    st.plotly_chart(fig)

# ==========================
# Formulario para nueva tarea
# ==========================
st.subheader("➕ Agregar nueva tarea")
with st.form("nueva_tarea"):
    tarea = st.text_input("Descripción de la tarea")
    responsable = st.selectbox("Asignar a:", PERSONAS, key="nuevo_responsable")
    prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"], key="nueva_prioridad")
    estado = st.selectbox("Estado", ["Pendiente", "En curso", "Terminado"], key="nuevo_estado")
    fecha = st.date_input("Fecha límite")
    soporte = st.file_uploader("📎 Adjuntar soporte", type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx"], key="nuevo_soporte")

    submitted = st.form_submit_button("Guardar")

    if submitted and tarea.strip():
        soporte_path = ""
        if soporte is not None:
            soporte_path = os.path.join(CARPETA_SOPORTES, soporte.name)
            with open(soporte_path, "wb") as f:
                f.write(soporte.getbuffer())

        nueva = pd.DataFrame([[tarea, responsable, prioridad, estado, fecha, soporte_path]],
                             columns=df.columns)
        df = pd.concat([df, nueva], ignore_index=True)
        df.to_csv(ARCHIVO, index=False)
        st.success("✅ Tarea agregada con éxito")
        st.rerun()

# ==========================
# Cambiar estado de tareas y agregar soportes
# ==========================
st.subheader("✏️ Actualizar tarea")
if not df.empty:
    tarea_selec = st.selectbox("Seleccionar tarea:", df["Tarea"], key="editar_tarea")
    nuevo_estado = st.selectbox("Nuevo estado:", ["Pendiente", "En curso", "Terminado"], key="editar_estado")
    nuevo_soporte = st.file_uploader("📎 Adjuntar nuevo soporte", type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx"], key="editar_soporte")

    if st.button("Actualizar", key="boton_actualizar"):
        # Actualizar estado
        df.loc[df["Tarea"] == tarea_selec, "Estado"] = nuevo_estado

        # Si cargó un nuevo soporte
        if nuevo_soporte is not None:
            soporte_path = os.path.join(CARPETA_SOPORTES, nuevo_soporte.name)
            with open(soporte_path, "wb") as f:
                f.write(nuevo_soporte.getbuffer())

            # Agregar al listado existente
            idx = df[df["Tarea"] == tarea_selec].index[0]
            soportes_actuales = str(df.at[idx, "Soporte"]) if pd.notna(df.at[idx, "Soporte"]) else ""
            if soportes_actuales.strip() == "":
                df.at[idx, "Soporte"] = soporte_path
            else:
                df.at[idx, "Soporte"] = soportes_actuales + ";" + soporte_path

        # Guardar cambios
        df.to_csv(ARCHIVO, index=False)
        st.success("✅ Tarea actualizada con éxito")
        st.rerun()


# ==========================
# Descargar soportes discriminados por tarea
# ==========================
st.subheader("📂 Soportes por tarea")

for i, row in df.iterrows():
    soportes_str = str(row["Soporte"]) if pd.notna(row["Soporte"]) else ""
    soportes = [s for s in soportes_str.split(";") if s.strip() != ""]

    if soportes:
        st.write(f"**{row['Tarea']}**")
        for j, soporte_path in enumerate(soportes):
            if os.path.exists(soporte_path):
                with open(soporte_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ {os.path.basename(soporte_path)}",
                        data=f,
                        file_name=os.path.basename(soporte_path),
                        key=f"descargar_{i}_{j}"
                    )
