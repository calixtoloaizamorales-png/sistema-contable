import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import numpy as np # Importante para detectar los NaN

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Contable Pronades", layout="wide", page_icon="📊")

# ==========================================
# ⚙️ ZONA DE CONFIGURACIÓN
# ==========================================
USUARIOS = {
    "admin": "admin123",
    "contador": "conta2026",
    "gerente": "pronades",
    "auxiliar": "dato1"
}

PUC = [
    "1105 - Caja General", 
    "1110 - Bancos", 
    "1305 - Clientes", 
    "2205 - Proveedores", 
    "2365 - Retefuente", 
    "4135 - Ingresos", 
    "5105 - Gastos",
    "5295 - Compras"
    # ... (Agrega tus cuentas aquí)
]

CENTROS_COSTO = ["General", "Administración", "Ventas", "Operativo"]
UNIDADES_NEGOCIO = ["General", "Ganadería", "Agricultura", "Servicios"]
TERCEROS = ["Consumidor Final", "DIAN", "Banco", "Varios"]

# ==========================================
# 🔌 CONEXIÓN GOOGLE
# ==========================================
def conectar_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        json_texto = st.secrets["gcp_service_account"]["contenido_json"]
        try:
            creds_dict = json.loads(json_texto)
        except:
            creds_dict = json.loads(json_texto, strict=False)
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Base_Datos_Contabilidad").sheet1
        return sheet
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

def cargar_datos():
    sheet = conectar_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            if not data:
                return pd.DataFrame(columns=['Fecha', 'Documento', 'Tercero', 'Cuenta', 'Descripcion', 'Debito', 'Credito', 'Centro_Costo', 'Unidad_Negocio', 'Usuario_Registro'])
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def guardar_lote(lista_datos):
    sheet = conectar_google_sheet()
    if sheet:
        try:
            filas_preparadas = []
            for d in lista_datos:
                # AQUÍ ESTÁ LA CORRECCIÓN DEL ERROR "NaN"
                # Si el valor no es un número válido, ponemos 0.0
                deb = 0.0 if pd.isna(d['Debito']) else float(d['Debito'])
                cred = 0.0 if pd.isna(d['Credito']) else float(d['Credito'])
                
                filas_preparadas.append([
                    str(d['Fecha']), str(d['Documento']), str(d['Tercero']),
                    str(d['Cuenta']), str(d['Descripcion']),
                    deb, cred,  # Usamos las variables limpias
                    str(d['Centro_Costo']), str(d['Unidad_Negocio']),
                    str(d['Usuario_Registro'])
                ])
            sheet.append_rows(filas_preparadas)
            return True
        except Exception as e:
            st.error(f"Error guardando lote: {e}")
            return False
    return False

# ==========================================
# 🔐 LOGIN
# ==========================================
def login():
    if 'usuario_actual' not in st.session_state:
        st.session_state.usuario_actual = None
    if st.session_state.usuario_actual is None:
        st.title("🔐 Acceso")
        c1, c2 = st.columns([1,2])
        u = c1.text_input("Usuario")
        p = c1.text_input("Contraseña", type="password")
        if c1.button("Ingresar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state.usuario_actual = u
                st.rerun()
        return False
    return True

if not login():
    st.stop()

# ==========================================
# 🖥️ INTERFAZ PRINCIPAL
# ==========================================
st.sidebar.success(f"👤 {st.session_state.usuario_actual}")
if st.sidebar.button("Salir"):
    st.session_state.usuario_actual = None
    st.rerun()

menu = st.sidebar.radio("Menú", ["📝 Nuevo Asiento", "📂 Ver Movimientos", "⚙️ Configuración"])

if menu == "📝 Nuevo Asiento":
    st.title("📝 Registrar Comprobante")
    
    # Cabecera
    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha", datetime.now())
    tercero = c2.selectbox("Tercero", TERCEROS)
    doc = c3.text_input("Documento", placeholder="Ej: FC-001")
    desc_global = st.text_input("Descripción Global")

    st.markdown("---")

    # --- LÓGICA DE REPARACIÓN DE TABLA ---
    # Si la tabla en memoria está dañada o le faltan columnas viejas, la reseteamos
    columnas_necesarias = ['Cuenta', 'Detalle', 'Debito', 'Credito', 'Centro_Costo', 'Unidad_Negocio']
    
    if 'df_asiento' not in st.session_state:
        resetear = True
    else:
        # Verificar si falta alguna columna
        faltantes = [c for c in columnas_necesarias if c not in st.session_state.df_asiento.columns]
        resetear = len(faltantes) > 0
    
    if resetear:
        st.session_state.df_asiento = pd.DataFrame([{
            'Cuenta': PUC[0], 
            'Detalle': '', 
            'Debito': 0.0, 
            'Credito': 0.0, 
            'Centro_Costo': CENTROS_COSTO[0], 
            'Unidad_Negocio': UNIDADES_NEGOCIO[0]
        }])

    # Configuración de Columnas
    col_cfg = {
        "Cuenta": st.column_config.SelectboxColumn("Cuenta", options=PUC, required=True, width="large"),
        "Detalle": st.column_config.TextColumn("Detalle", width="medium"),
        "Debito": st.column_config.NumberColumn("Débito", min_value=0.0, format="$%.2f"),
        "Credito": st.column_config.NumberColumn("Crédito", min_value=0.0, format="$%.2f"),
        "Centro_Costo": st.column_config.SelectboxColumn("C. Costo", options=CENTROS_COSTO, required=True),
        "Unidad_Negocio": st.column_config.SelectboxColumn("U. Negocio", options=UNIDADES_NEGOCIO, required=True),
    }

    # Tabla Editable
    edited = st.data_editor(st.session_state.df_asiento, num_rows="dynamic", column_config=col_cfg, use_container_width=True, key="grid_v4")

    # Cálculos (Con protección contra NaN)
    df_calc = edited.fillna(0.0) # Convertir vacíos a ceros para calcular
    deb = df_calc['Debito'].sum()
    cred = df_calc['Credito'].sum()
    dif = deb - cred

    c1, c2, c3 = st.columns(3)
    c1.metric("Débito", f"${deb:,.2f}")
    c2.metric("Crédito", f"${cred:,.2f}")
    
    if round(dif, 2) == 0:
        c3.success("✅ Balanceado")
        if deb > 0:
            if st.button("💾 GUARDAR", type="primary", use_container_width=True):
                with st.spinner("Guardando..."):
                    # Preparamos datos
                    lote = []
                    for idx, row in edited.iterrows():
                        # Limpieza individual de cada fila
                        d_val = 0.0 if pd.isna(row['Debito']) else row['Debito']
                        c_val = 0.0 if pd.isna(row['Credito']) else row['Credito']
                        
                        if d_val > 0 or c_val > 0:
                            lote.append({
                                'Fecha': fecha, 'Documento': doc, 'Tercero': tercero,
                                'Cuenta': row['Cuenta'],
                                'Descripcion': row['Detalle'] if row['Detalle'] else desc_global,
                                'Debito': d_val, 'Credito': c_val,
                                'Centro_Costo': row['Centro_Costo'],
                                'Unidad_Negocio': row['Unidad_Negocio'],
                                'Usuario_Registro': st.session_state.usuario_actual
                            })
                    
                    if guardar_lote(lote):
                        st.success("Guardado Exitosamente")
                        # Reset tabla
                        st.session_state.df_asiento = pd.DataFrame([{
                            'Cuenta': PUC[0], 'Detalle': '', 'Debito': 0.0, 'Credito': 0.0, 
                            'Centro_Costo': CENTROS_COSTO[0], 'Unidad_Negocio': UNIDADES_NEGOCIO[0]
                        }])
                        st.rerun()
    else:
        c3.error(f"❌ Diferencia: ${dif:,.2f}")

elif menu == "📂 Ver Movimientos":
    st.header("Movimientos")
    if st.button("Actualizar"):
        st.cache_data.clear()
        st.rerun()
    st.dataframe(cargar_datos(), use_container_width=True)

elif menu == "⚙️ Configuración":
    st.write("Edita las listas en GitHub para cambiar Usuarios o PUC.")
