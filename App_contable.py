import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Contable Web", layout="wide")

# --- GESTIÓN DE USUARIOS (SEGURIDAD) ---
USUARIOS = {
    "admin": "admin123",
    "contador": "conta2026",
    "gerente": "pronades"
}

def login():
    if 'usuario_actual' not in st.session_state:
        st.session_state.usuario_actual = None

    if st.session_state.usuario_actual is None:
        st.header("🔐 Iniciar Sesión - Pronades SAS")
        col1, col2 = st.columns([1, 2])
        with col1:
            # Agregamos key para evitar conflicto
            user = st.text_input("Usuario", key="login_user")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Entrar", key="login_btn"):
                if user in USUARIOS and USUARIOS[user] == password:
                    st.session_state.usuario_actual = user
                    st.success("Acceso concedido")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        return False
    return True

if not login():
    st.stop()

# --- MENÚ LATERAL ---
st.sidebar.success(f"👤 Usuario: {st.session_state.usuario_actual.upper()}")
if st.sidebar.button("Cerrar Sesión", key="logout_btn"):
    st.session_state.usuario_actual = None
    st.rerun()

# --- LOGICA DEL SISTEMA ---
ARCHIVO_DB = 'contabilidad_db.csv'

# PUC BASE
PUC_BASE = [
    "1105 - Caja General", "1110 - Bancos", "1305 - Clientes Nacionales",
    "1355 - Anticipo Impuestos", "2205 - Proveedores", "2335 - Cuentas por Pagar",
    "2365 - Retención Fuente", "2408 - IVA por Pagar", "4135 - Ventas",
    "5105 - Gastos Personal", "5135 - Servicios", "5195 - Diversos", 
    "5200 - Ventas"
]

def cargar_datos():
    if os.path.exists(ARCHIVO_DB):
        df = pd.read_csv(ARCHIVO_DB)
        return df
    return pd.DataFrame(columns=['Fecha', 'Documento', 'Tercero', 'Cuenta', 'Descripcion', 'Debito', 'Credito', 'Centro_Costo', 'Unidad_Negocio', 'Usuario_Registro'])

def guardar_datos(df):
    df.to_csv(ARCHIVO_DB, index=False)

def cargar_listas():
    if 'config_listas' not in st.session_state:
        st.session_state['config_listas'] = {
            "centros_costo": ["General", "Administración", "Ventas", "Producción"],
            "unidades_negocio": ["General", "Ganadería", "Agricultura", "Servicios"],
            "terceros": ["Consumidor Final", "DIAN", "Banco"],
            "cuentas_puc": PUC_BASE
        }
    return st.session_state['config_listas']

# --- INTERFAZ PRINCIPAL ---
st.title(f"📊 Panel de Control - {st.session_state.usuario_actual.capitalize()}")
menu = st.sidebar.radio("Navegación", ["📝 Registrar Asiento", "⚙️ Maestros", "📈 Reportes"], key="nav_menu")
listas = cargar_listas()

# SECCIÓN: MAESTROS
if menu == "⚙️ Maestros":
    st.header("Gestión de Maestros")
    tab1, tab2 = st.tabs(["📚 PUC", "👥 Terceros"])
    
    with tab1:
        nueva = st.text_input("Nueva Cuenta", key="input_nueva_cuenta")
        if st.button("Agregar Cuenta", key="btn_add_cuenta"):
            listas['cuentas_puc'].append(nueva)
            st.success("Cuenta agregada")
        st.write(listas['cuentas_puc'])
        
    with tab2:
        nuevo_t = st.text_input("Nuevo Tercero", key="input_nuevo_tercero")
        if st.button("Agregar Tercero", key="btn_add_tercero"):
            listas['terceros'].append(nuevo_t)
            st.success("Tercero Agregado")

# SECCIÓN: REGISTRAR ASIENTO
elif menu == "📝 Registrar Asiento":
    st.subheader("Nuevo Comprobante Contable")
    
    # Cabecera
    c1, c2, c3 = st.columns(3)
    # AQUÍ ESTABA EL ERROR: Agregamos key única
    fecha = c1.date_input("Fecha", datetime.now(), key="fecha_asiento_input")
    tercero = c2.selectbox("Tercero", listas['terceros'], key="tercero_asiento_input")
    doc = c3.text_input("Doc Ref", key="doc_asiento_input")
    desc = st.text_input("Descripción Global", key="desc_asiento_input")

    if 'df_asiento' not in st.session_state:
        st.session_state.df_asiento = pd.DataFrame([{'Cuenta': '1105 - Caja General', 'Descripcion': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': 'General', 'Unidad_Negocio': 'General'}])

    # Configuración de la tabla editable
    col_cfg = {
        "Cuenta": st.column_config.SelectboxColumn("Cuenta", options=listas['cuentas_puc'], required=True),
        "Centro_Costo": st.column_config.SelectboxColumn("CC", options=listas['centros_costo']),
        "Unidad_Negocio": st.column_config.SelectboxColumn("UN", options=listas['unidades_negocio']),
        "Debito": st.column_config.NumberColumn("Débito", format="$%.2f"),
        "Credito": st.column_config.NumberColumn("Crédito", format="$%.2f")
    }

    edited = st.data_editor(st.session_state.df_asiento, num_rows="dynamic", column_config=col_cfg, use_container_width=True, key="editor_grid_asiento")

    # Cálculos y Validación
    deb, cred = edited['Debito'].sum(), edited['Credito'].sum()
    st.metric("Diferencia (Debe ser $0)", f"${deb - cred:,.2f}")

    if round(deb - cred, 2) == 0 and deb > 0:
        if st.button("💾 Guardar Comprobante", type="primary", key="btn_guardar_asiento"):
            final = edited.copy()
            final['Fecha'] = fecha
            final['Tercero'] = tercero
            final['Documento'] = doc
            final['Descripcion'] = final['Descripcion'].replace('', desc)
            final['Usuario_Registro'] = st.session_state.usuario_actual
            
            # Guardar
            guardar_datos(pd.concat([cargar_datos(), final], ignore_index=True))
            st.success("✅ Guardado exitosamente")
            
            # Limpiar tabla
            st.session_state.df_asiento = pd.DataFrame([{'Cuenta': '1105 - Caja General', 'Descripcion': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': 'General', 'Unidad_Negocio': 'General'}])
            st.rerun()
    elif round(deb - cred, 2) != 0:
        st.error("⚠️ El asiento está descuadrado. No se puede guardar.")

# SECCIÓN: REPORTES
elif menu == "📈 Reportes":
    st.subheader("Movimientos Registrados")
    df = cargar_datos()
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        st.download_button("Descargar CSV", df.to_csv(index=False), "contabilidad.csv", key="btn_download")