import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Contable Cloud", layout="wide", page_icon="📊")

# --- CONEXIÓN BLINDADA CON GOOGLE SHEETS ---
def conectar_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Leemos el secreto
        json_texto = st.secrets["gcp_service_account"]["contenido_json"]
        
        # INTELIGENCIA DE REPARACIÓN (Lo que aprendimos del Detective)
        try:
            creds_dict = json.loads(json_texto)
        except:
            # Si falla, usamos el modo permisivo para arreglar los "Enters" invisibles
            creds_dict = json.loads(json_texto, strict=False)
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # IMPORTANTE: El nombre debe ser exacto
        sheet = client.open("Base_Datos_Contabilidad").sheet1
        return sheet
    except Exception as e:
        st.error(f"❌ Error de Conexión: {e}")
        return None

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_datos():
    sheet = conectar_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            # Si la hoja está vacía (solo encabezados), devolvemos estructura vacía
            if not data:
                return pd.DataFrame(columns=['Fecha', 'Documento', 'Tercero', 'Cuenta', 'Descripcion', 'Debito', 'Credito', 'Centro_Costo', 'Unidad_Negocio', 'Usuario_Registro'])
            return pd.DataFrame(data)
        except Exception as e:
            st.warning("La hoja parece estar vacía o hubo un error leyéndola.")
            return pd.DataFrame()
    return pd.DataFrame()

def guardar_registro(fila_datos):
    sheet = conectar_google_sheet()
    if sheet:
        try:
            # Convertimos todo a texto/numero para evitar errores de formato en Google
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
            st.error(f"Error guardando: {e}")
            return False
    return False

# --- GESTIÓN DE USUARIOS ---
USUARIOS = {
    "admin": "admin123",
    "contador": "conta2026",
    "gerente": "pronades"
}

def login():
    if 'usuario_actual' not in st.session_state:
        st.session_state.usuario_actual = None

    if st.session_state.usuario_actual is None:
        st.markdown("<h1 style='text-align: center;'>🔐 Pronades SAS</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Sistema Contable & Financiero</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login_form"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                btn = st.form_submit_button("Ingresar al Sistema", type="primary")
                
                if btn:
                    if u in USUARIOS and USUARIOS[u] == p:
                        st.session_state.usuario_actual = u
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
        return False
    return True

if not login():
    st.stop()

# --- BARRA LATERAL (EL MENÚ) ---
st.sidebar.title(f"👤 {st.session_state.usuario_actual.capitalize()}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.usuario_actual = None
    st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegación", ["📝 Nuevo Asiento", "📂 Ver Movimientos", "📊 Reporte Financiero"])

# --- LISTAS MAESTRAS (PUEDES EDITARLAS AQUÍ) ---
PUC = [
    "1105 - Caja General", "1110 - Bancos", "1305 - Clientes", 
    "1355 - Anticipo Impuestos", "1435 - Inventario", "1540 - Flota y Equipo",
    "2205 - Proveedores", "2335 - Ctas x Pagar", "2365 - Retefuente x Pagar",
    "2408 - IVA x Pagar", "3115 - Aportes Sociales", "3605 - Utilidad Ejercicio",
    "4135 - Ingresos (Ventas)", "4210 - Ingresos Financieros",
    "5105 - Gastos Personal", "5135 - Servicios", "5195 - Diversos",
    "5295 - Costos", "6135 - Costo de Ventas"
]
TERCEROS = ["Consumidor Final", "DIAN", "Banco", "Varios", "Nomina"]
CENTROS = ["General", "Administración", "Ventas", "Producción"]
UNIDADES = ["General", "Ganadería", "Agricultura", "Servicios"]

# --- PANTALLA 1: REGISTRAR ---
if menu == "📝 Nuevo Asiento":
    st.title("📝 Registrar Operación")
    
    # Datos de Cabecera
    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha de Operación")
    tercero = c2.selectbox("Tercero", TERCEROS)
    doc = c3.text_input("Documento Ref (Fac/Recibo)")
    
    st.markdown("---")
    
    # Formulario de Línea (Diseño para guardar línea a línea en la nube)
    st.info("Ingresa los detalles del movimiento contable:")
    
    with st.form("form_registro", clear_on_submit=True):
        col_A, col_B = st.columns([1, 2])
        cuenta = col_A.selectbox("Cuenta PUC", PUC)
        desc = col_B.text_input("Descripción del movimiento")
        
        col_C, col_D = st.columns(2)
        debito = col_C.number_input("Débito ($)", min_value=0.0, step=1000.0, format="%.2f")
        credito = col_D.number_input("Crédito ($)", min_value=0.0, step=1000.0, format="%.2f")
        
        col_E, col_F = st.columns(2)
        cc = col_E.selectbox("Centro de Costos", CENTROS)
        un = col_F.selectbox("Unidad de Negocio", UNIDADES)
        
        # Botón de Guardado
        submitted = st.form_submit_button("💾 GUARDAR MOVIMIENTO EN LA NUBE", type="primary")
        
        if submitted:
            if debito == 0 and credito == 0:
                st.error("⚠️ El movimiento debe tener valor en Débito o Crédito.")
            else:
                # Preparamos el paquete de datos
                datos_linea = {
                    'Fecha': fecha,
                    'Documento': doc,
                    'Tercero': tercero,
                    'Cuenta': cuenta,
                    'Descripcion': desc,
                    'Debito': debito,
                    'Credito': credito,
                    'Centro_Costo': cc,
                    'Unidad_Negocio': un,
                    'Usuario_Registro': st.session_state.usuario_actual
                }
                
                # Enviamos a la nube
                with st.spinner("Conectando con Google Drive..."):
                    exito = guardar_registro(datos_linea)
                
                if exito:
                    st.success("✅ ¡Registro guardado exitosamente!")
                    st.toast("Guardado en Google Sheets", icon="☁️")
                else:
                    st.error("❌ Hubo un error al guardar. Revisa tu conexión.")

# --- PANTALLA 2: VER DATOS ---
elif menu == "📂 Ver Movimientos":
    st.title("📂 Libro Diario (Google Sheets)")
    
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()
        
    df = cargar_datos()
    
    if not df.empty:
        # Filtros
        filtro = st.text_input("🔍 Buscar (Tercero, Cuenta o Descripción):")
        if filtro:
            df = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False, na=False)).any(axis=1)]
            
        st.dataframe(df, use_container_width=True)
        
        # Totales
        total_deb = pd.to_numeric(df['Debito']).sum()
        total_cred = pd.to_numeric(df['Credito']).sum()
        diferencia = total_deb - total_cred
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Débitos", f"${total_deb:,.2f}")
        c2.metric("Total Créditos", f"${total_cred:,.2f}")
        c3.metric("Balance (Debe ser 0)", f"${diferencia:,.2f}", delta_color="inverse")
        
        if round(diferencia, 2) != 0:
            st.error("⚠️ Atención: La contabilidad está descuadrada.")
    else:
        st.info("No hay datos registrados aún o la hoja está vacía.")

# --- PANTALLA 3: REPORTES ---
elif menu == "📊 Reporte Financiero":
    st.title("📊 Resumen Gerencial")
    
    if st.button("🔄 Calcular Reportes"):
        st.cache_data.clear()
        st.rerun()
        
    df = cargar_datos()
    
    if not df.empty:
        # Limpieza de datos
        df['Debito'] = pd.to_numeric(df['Debito'])
        df['Credito'] = pd.to_numeric(df['Credito'])
        
        tab1, tab2 = st.tabs(["Por Unidad de Negocio", "Impuestos (Aproximado)"])
        
        with tab1:
            # Lógica simple: (Crédito - Débito) para Ingresos (4)
            # Asumimos que Cuentas 4xxx son Ingresos
            ingresos = df[df['Cuenta'].astype(str).str.startswith('4')].copy()
            ingresos['Valor'] = ingresos['Credito'] - ingresos['Debito']
            
            # Gastos (5) y Costos (6)
            gastos = df[df['Cuenta'].astype(str).str.startswith(('5', '6'))].copy()
            gastos['Valor'] = gastos['Debito'] - gastos['Credito']
            
            st.subheader("Ingresos por Unidad")
            if not ingresos.empty:
                st.bar_chart(ingresos.groupby("Unidad_Negocio")["Valor"].sum())
            else:
                st.info("No hay ingresos registrados.")
                
        with tab2:
            st.subheader("Saldos de Impuestos (Cuentas 23 y 24)")
            impuestos = df[df['Cuenta'].astype(str).str.startswith(('23', '24'))]
            if not impuestos.empty:
                resumen = impuestos.groupby("Cuenta")[["Debito", "Credito"]].sum()
                resumen['Saldo a Pagar'] = resumen['Credito'] - resumen['Debito']
                st.table(resumen)
            else:
                st.info("No hay movimientos de impuestos.")
