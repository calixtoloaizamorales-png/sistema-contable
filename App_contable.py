import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Contable Pronades", layout="wide", page_icon="📊")

# ==========================================
# ⚙️ ZONA DE CONFIGURACIÓN (EDITA AQUÍ)
# ==========================================

# 1. LISTA DE USUARIOS (Usuario : Contraseña)
USUARIOS = {
    "admin": "admin123",
    "contador": "conta2026",
    "gerente": "pronades",
    "auxiliar": "dato1",   # <--- Agrega aquí nuevos usuarios
    "carlos": "ganado2026"
}

# 2. CUENTAS PUC (Puedes agregar las que necesites)
PUC = [
    "1105 - Caja General", 
    "1110 - Bancos", 
    "1305 - Clientes Nacionales", 
    "1355 - Anticipo Impuestos", 
    "1435 - Inventario Semovientes", 
    "1440 - Inventario Insumos",
    "1540 - Flota y Equipo",
    "2205 - Proveedores", 
    "2335 - Cuentas por Pagar", 
    "2365 - Retención Fuente", 
    "2408 - IVA Generado",
    "2409 - IVA Descontable",
    "3115 - Aportes Sociales", 
    "4135 - Ingresos (Ventas Ganado)", 
    "4210 - Ingresos Financieros",
    "5105 - Gastos Personal", 
    "5135 - Servicios Públicos", 
    "5195 - Diversos",
    "5295 - Compra de Ganado", 
    "6135 - Costo de Ventas"
]

# 3. CENTROS DE COSTO Y UNIDADES
CENTROS_COSTO = ["General", "Administración", "Ventas", "Operativo", "Mantenimiento"]
UNIDADES_NEGOCIO = ["General", "Ganadería Cría", "Ganadería Ceba", "Agricultura", "Servicios"]
TERCEROS = ["Consumidor Final", "DIAN", "Banco", "Proveedor Insumos", "Nomina", "Varios"]

# ==========================================
# 🔌 CONEXIÓN CON GOOGLE SHEETS
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
    """Guarda múltiples filas de una sola vez"""
    sheet = conectar_google_sheet()
    if sheet:
        try:
            filas_preparadas = []
            for d in lista_datos:
                filas_preparadas.append([
                    str(d['Fecha']), str(d['Documento']), str(d['Tercero']),
                    str(d['Cuenta']), str(d['Descripcion']),
                    float(d['Debito']), float(d['Credito']),
                    str(d['Centro_Costo']), str(d['Unidad_Negocio']),
                    str(d['Usuario_Registro'])
                ])
            # Usamos append_rows (plural) para mayor velocidad
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
        st.title("🔐 Pronades SAS - Acceso")
        c1, c2 = st.columns([1,2])
        u = c1.text_input("Usuario")
        p = c1.text_input("Contraseña", type="password")
        if c1.button("Ingresar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state.usuario_actual = u
                st.rerun()
            else:
                st.error("Datos incorrectos")
        return False
    return True

if not login():
    st.stop()

# ==========================================
# 🖥️ INTERFAZ PRINCIPAL
# ==========================================
st.sidebar.success(f"Usuario: {st.session_state.usuario_actual.upper()}")
if st.sidebar.button("Salir"):
    st.session_state.usuario_actual = None
    st.rerun()

menu = st.sidebar.radio("Menú", ["📝 Nuevo Asiento (Cuadrado)", "📂 Ver Movimientos", "⚙️ Configuración"])

if menu == "📝 Nuevo Asiento (Cuadrado)":
    st.title("📝 Registrar Comprobante Contable")
    
    # 1. Cabecera del Documento
    col1, col2, col3 = st.columns(3)
    fecha_doc = col1.date_input("Fecha", datetime.now())
    tercero_doc = col2.selectbox("Tercero General", TERCEROS)
    ref_doc = col3.text_input("Documento Referencia", placeholder="Ej: FC-1020")
    desc_global = st.text_input("Descripción Global", placeholder="Ej: Venta de ganado lote 5")

    st.markdown("---")
    st.info("👇 Agrega las líneas del asiento en la tabla. El botón 'Guardar' solo aparecerá si Débitos = Créditos.")

    # 2. Inicializar la Tabla Temporal en Memoria
    if 'df_asiento' not in st.session_state:
        # Estructura inicial con una fila vacía para empezar
        st.session_state.df_asiento = pd.DataFrame(
            [{'Cuenta': PUC[0], 'Detalle': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': CENTROS_COSTO[0], 'Unidad_Negocio': UNIDADES_NEGOCIO[0]}]
        )

    # 3. Configurar Columnas de la Tabla Editable
    column_config = {
        "Cuenta": st.column_config.SelectboxColumn("Cuenta PUC", options=PUC, required=True, width="large"),
        "Detalle": st.column_config.TextColumn("Detalle (Opcional)", width="medium"),
        "Debito": st.column_config.NumberColumn("Débito", min_value=0.0, format="$%.2f"),
        "Credito": st.column_config.NumberColumn("Crédito", min_value=0.0, format="$%.2f"),
        "Centro_Costo": st.column_config.SelectboxColumn("C. Costo", options=CENTROS_COSTO),
        "Unidad_Negocio": st.column_config.SelectboxColumn("U. Negocio", options=UNIDADES_NEGOCIO),
    }

    # 4. Mostrar la Tabla Editable
    edited_df = st.data_editor(
        st.session_state.df_asiento,
        num_rows="dynamic", # Permite agregar/quitar filas
        column_config=column_config,
        use_container_width=True,
        key="editor_asiento"
    )

    # 5. Cálculos de Cuadre
    total_deb = edited_df['Debito'].sum()
    total_cred = edited_df['Credito'].sum()
    diferencia = total_deb - total_cred

    c_tot1, c_tot2, c_tot3 = st.columns(3)
    c_tot1.metric("Total Débito", f"${total_deb:,.2f}")
    c_tot2.metric("Total Crédito", f"${total_cred:,.2f}")
    
    # Lógica del Semáforo
    if round(diferencia, 2) == 0:
        c_tot3.success(f"✅ Balanceado ($0.00)")
        btn_disabled = False
        if total_deb == 0: # Si está en cero pero vacío, no dejar guardar
            btn_disabled = True
    else:
        c_tot3.error(f"❌ Descuadrado por: ${diferencia:,.2f}")
        btn_disabled = True

    # 6. Botón de Guardado (Solo si está cuadrado)
    st.markdown("<br>", unsafe_allow_html=True)
    if not btn_disabled:
        if st.button("💾 GUARDAR COMPROBANTE EN LA NUBE", type="primary", use_container_width=True):
            with st.spinner("Subiendo datos a Google Drive..."):
                # Preparamos los datos finales
                lista_para_guardar = []
                for index, row in edited_df.iterrows():
                    # Solo guardamos líneas que tengan valor > 0
                    if row['Debito'] > 0 or row['Credito'] > 0:
                        linea = {
                            'Fecha': fecha_doc,
                            'Documento': ref_doc,
                            'Tercero': tercero_doc,
                            'Cuenta': row['Cuenta'],
                            'Descripcion': row['Detalle'] if row['Detalle'] else desc_global,
                            'Debito': row['Debito'],
                            'Credito': row['Credito'],
                            'Centro_Costo': row['Centro_Costo'],
                            'Unidad_Negocio': row['Unidad_Negocio'],
                            'Usuario_Registro': st.session_state.usuario_actual
                        }
                        lista_para_guardar.append(linea)
                
                if lista_para_guardar:
                    if guardar_lote(lista_para_guardar):
                        st.success("✅ ¡Comprobante guardado exitosamente!")
                        st.balloons()
                        # Limpiar la tabla para el siguiente
                        st.session_state.df_asiento = pd.DataFrame(
                            [{'Cuenta': PUC[0], 'Detalle': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': CENTROS_COSTO[0], 'Unidad_Negocio': UNIDADES_NEGOCIO[0]}]
                        )
                        st.rerun()
                else:
                    st.warning("El asiento está vacío (valores en cero).")
    elif total_deb > 0:
        st.warning("⚠️ Debes cuadrar el asiento (Diferencia debe ser 0) para poder guardar.")

elif menu == "📂 Ver Movimientos":
    st.title("📂 Base de Datos Contable")
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()
    st.dataframe(cargar_datos(), use_container_width=True)

elif menu == "⚙️ Configuración":
    st.header("⚙️ Gestión de Maestros")
    st.info("Para agregar nuevos Usuarios, Cuentas o Centros de Costo, debes editar el archivo 'app_contable.py' en GitHub en la sección superior marcada como 'ZONA DE CONFIGURACIÓN'.")
    st.markdown("""
    **Pasos:**
    1. Ve a GitHub.
    2. Abre `app_contable.py`.
    3. Edita las listas `USUARIOS`, `PUC`, `CENTROS_COSTO`.
    4. Guarda los cambios (Commit).
    """)
    st.subheader("Valores Actuales:")
    st.write("**Usuarios:**", list(USUARIOS.keys()))
    st.write("**Centros de Costo:**", CENTROS_COSTO)
    st.write("**Unidades de Negocio:**", UNIDADES_NEGOCIO)
