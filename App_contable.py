import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json  # <--- ESTA LIBRERÍA ES VITAL PARA EL TRUCO DEL SECRETO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Contable Cloud", layout="wide")

# --- CONEXIÓN CON GOOGLE SHEETS ---
def conectar_google_sheet():
    try:
        # Definir el alcance (permisos)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Cargar credenciales desde los Secretos de Streamlit (Usando el truco del texto JSON)
        # OJO: Aquí buscamos la clave 'contenido_json' dentro de 'gcp_service_account'
        json_texto = st.secrets["gcp_service_account"]["contenido_json"]
        
        # Convertir ese texto largo en un diccionario real
        creds_dict = json.loads(json_texto)
        
        # Crear las credenciales
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        # Autorizar cliente y abrir hoja
        client = gspread.authorize(creds)
        sheet = client.open("Base_Datos_Contabilidad").sheet1
        return sheet
        
    except Exception as e:
        st.error(f"❌ Error CRÍTICO de Conexión: {e}")
        st.info("Revisa: 1. Que el secreto en Streamlit empiece con [gcp_service_account] y tenga la clave contenido_json. 2. Que hayas compartido la hoja con el email del robot.")
        return None

# --- FUNCIONES DE DATOS ---
def cargar_datos():
    sheet = conectar_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            if not data:
                return pd.DataFrame(columns=['Fecha', 'Documento', 'Tercero', 'Cuenta', 'Descripcion', 'Debito', 'Credito', 'Centro_Costo', 'Unidad_Negocio', 'Usuario_Registro'])
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error leyendo datos: {e}")
    return pd.DataFrame()

def guardar_registro(fila_datos):
    sheet = conectar_google_sheet()
    if sheet:
        try:
            valores = [
                str(fila_datos['Fecha']),
                str(fila_datos['Documento']),
                str(fila_datos['Tercero']),
                str(fila_datos['Cuenta']),
                str(fila_datos['Descripcion']),
                float(fila_datos['Debito']),
                float(fila_datos['Credito']),
                str(fila_datos['Centro_Costo']),
                str(fila_datos['Unidad_Negocio']),
                str(fila_datos['Usuario_Registro'])
            ]
            sheet.append_row(valores)
            return True
        except Exception as e:
            st.error(f"No se pudo escribir en la hoja: {e}")
            return False
    return False

# --- SEGURIDAD ---
USUARIOS = {"admin": "admin123", "contador": "conta2026", "gerente": "pronades"}

def login():
    if 'usuario_actual' not in st.session_state:
        st.session_state.usuario_actual = None
    if st.session_state.usuario_actual is None:
        st.header("🔐 Iniciar Sesión - Cloud")
        c1, c2 = st.columns([1,2])
        u = c1.text_input("Usuario", key="log_u")
        p = c1.text_input("Contraseña", type="password", key="log_p")
        if c1.button("Entrar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state.usuario_actual = u
                st.rerun()
            else:
                st.error("Acceso denegado")
        return False
    return True

if not login():
    st.stop()

st.sidebar.info(f"Conectado como: {st.session_state.usuario_actual}")
if st.sidebar.button("Salir"):
    st.session_state.usuario_actual = None
    st.rerun()

# --- INTERFAZ ---
PUC_BASE = ["1105 - Caja", "1110 - Bancos", "1305 - Clientes", "2365 - Retefuente", "2408 - IVA", "4135 - Ventas", "5195 - Gastos", "5295 - Diversos"]
LISTAS = {
    "terceros": ["Varios", "DIAN", "Banco"],
    "cc": ["General", "Ventas", "Producción"],
    "un": ["General", "Ganadería", "Agricultura"]
}

st.title("☁️ Sistema Contable (Conectado a Drive)")
menu = st.sidebar.radio("Menú", ["Registrar", "Ver Datos"], key="menu_nav")

if menu == "Registrar":
    st.subheader("Nuevo Movimiento")
    
    # Formulario
    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha")
    tercero = c2.selectbox("Tercero", LISTAS['terceros'])
    doc = c3.text_input("Doc Ref")
    
    with st.form("form_linea"):
        col_A, col_B = st.columns(2)
        cuenta = col_A.selectbox("Cuenta", PUC_BASE)
        desc = col_B.text_input("Descripción")
        
        col_C, col_D = st.columns(2)
        deb = col_C.number_input("Débito", min_value=0.0, step=1000.0)
        cred = col_D.number_input("Crédito", min_value=0.0, step=1000.0)
        
        col_E, col_F = st.columns(2)
        cc = col_E.selectbox("Centro Costo", LISTAS['cc'])
        un = col_F.selectbox("Unidad Negocio", LISTAS['un'])
        
        enviar = st.form_submit_button("💾 Registrar en la Nube")
        
        if enviar:
            if deb == 0 and cred == 0:
                st.warning("El valor no puede ser cero")
            else:
                datos = {
                    'Fecha': fecha, 'Documento': doc, 'Tercero': tercero,
                    'Cuenta': cuenta, 'Descripcion': desc,
                    'Debito': deb, 'Credito': cred,
                    'Centro_Costo': cc, 'Unidad_Negocio': un,
                    'Usuario_Registro': st.session_state.usuario_actual
                }
                with st.spinner("Guardando en Google Drive..."):
                    if guardar_registro(datos):
                        st.success("✅ ¡Guardado EXITOSAMENTE!")

elif menu == "Ver Datos":
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()
    
    df = cargar_datos()
    if not df.empty:
        st.dataframe(df)
        t_deb = pd.to_numeric(df['Debito']).sum()
        t_cred = pd.to_numeric(df['Credito']).sum()
        st.info(f"Débitos: ${t_deb:,.2f} | Créditos: ${t_cred:,.2f} | Diferencia: ${t_deb - t_cred:,.2f}")
    else:
        st.warning("No hay datos o no hay conexión.")
