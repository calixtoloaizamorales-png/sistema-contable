import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import numpy as np

st.set_page_config(page_title="ERP Pronades SAS", layout="wide", page_icon="📈")

# ==========================================
# ⚙️ CONFIGURACIÓN FIJA
# ==========================================
USUARIOS = {"admin": "admin123", "contador": "conta2026", "gerente": "pronades"}

PUC = [
    "1105 - Caja General", "1110 - Bancos", "1305 - Clientes", 
    "1355 - Anticipo Impuestos", "1435 - Inventario Semovientes", 
    "1540 - Flota y Equipo", "2205 - Proveedores", "2335 - Ctas x Pagar", 
    "2365 - Retefuente", "2408 - IVA Generado", "2409 - IVA Descontable",
    "3115 - Aportes Sociales", "4135 - Ingresos Ventas", 
    "5105 - Gastos Personal", "5135 - Servicios", "5195 - Diversos",
    "5295 - Compra Ganado", "6135 - Costo Ventas"
]
CENTROS = ["General", "Administración", "Ventas", "Operativo"]
UNIDADES = ["General", "Ganadería Cría", "Ganadería Ceba", "Agricultura"]

# ==========================================
# 🔌 CONEXIÓN MULTI-HOJA
# ==========================================
def conectar_google(nombre_hoja):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        json_texto = st.secrets["gcp_service_account"]["contenido_json"]
        try:
            creds_dict = json.loads(json_texto)
        except:
            creds_dict = json.loads(json_texto, strict=False)
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Abre el archivo y selecciona la hoja específica
        sheet = client.open("Base_Datos_Contabilidad").worksheet(nombre_hoja)
        return sheet
    except Exception as e:
        return None

def cargar_df(nombre_hoja):
    sheet = conectar_google(nombre_hoja)
    if sheet:
        try:
            data = sheet.get_all_records()
            return pd.DataFrame(data) if data else pd.DataFrame()
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# ==========================================
# 🔐 LOGIN
# ==========================================
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

if st.session_state.usuario_actual is None:
    st.title("🔐 ERP Pronades - Acceso")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state.usuario_actual = u
            st.rerun()
    st.stop()

# ==========================================
# 🖥️ MENÚ PRINCIPAL
# ==========================================
st.sidebar.title(f"👤 {st.session_state.usuario_actual}")
if st.sidebar.button("Salir"):
    st.session_state.usuario_actual = None
    st.rerun()

menu = st.sidebar.radio("Navegación", 
    ["📝 Nuevo Asiento", "👥 Gestión Terceros", "📊 Reportes e Impuestos", "📂 Ver Movimientos"])

# ==========================================
# 👥 GESTIÓN DE TERCEROS (NUEVO)
# ==========================================
if menu == "👥 Gestión Terceros":
    st.title("Directorio de Terceros")
    
    # Formulario para crear tercero
    with st.expander("➕ Registrar Nuevo Tercero", expanded=False):
        with st.form("nuevo_tercero"):
            c1, c2 = st.columns(2)
            nit = c1.text_input("NIT / Cédula")
            razon = c2.text_input("Razón Social / Nombre")
            dir = c1.text_input("Dirección")
            tel = c2.text_input("Teléfono")
            tipo = st.selectbox("Tipo", ["Cliente", "Proveedor", "Empleado", "Otro"])
            
            if st.form_submit_button("Guardar Tercero"):
                sheet = conectar_google("Terceros")
                if sheet:
                    sheet.append_row([str(nit), razon, dir, tel, tipo])
                    st.success(f"Tercero {razon} guardado.")
                    st.cache_data.clear()
                    st.rerun()

    # Mostrar listado
    df_terceros = cargar_df("Terceros")
    if not df_terceros.empty:
        st.dataframe(df_terceros, use_container_width=True)
    else:
        st.info("No hay terceros creados. Crea el primero arriba.")

# ==========================================
# 📝 NUEVO ASIENTO (CONECTADO A TERCEROS)
# ==========================================
elif menu == "📝 Nuevo Asiento":
    st.title("📝 Registrar Comprobante")
    
    # Cargar terceros para el selectbox
    df_t = cargar_df("Terceros")
    if df_t.empty:
        lista_terceros = ["Consumidor Final (Crear terceros en menú)"]
    else:
        # Crea una lista combinando NIT y Nombre
        lista_terceros = (df_t['NIT'].astype(str) + " - " + df_t['Razon_Social']).tolist()

    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha", datetime.now())
    tercero = c2.selectbox("Tercero", lista_terceros)
    doc = c3.text_input("Documento", placeholder="Ej: FC-100")
    desc_global = st.text_input("Descripción Global")

    st.markdown("---")

    # Tabla Editable (Reset si es necesario)
    if 'df_asiento' not in st.session_state:
        st.session_state.df_asiento = pd.DataFrame([{'Cuenta': PUC[0], 'Detalle': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': CENTROS[0], 'Unidad_Negocio': UNIDADES[0]}])

    col_cfg = {
        "Cuenta": st.column_config.SelectboxColumn("Cuenta", options=PUC, width="large"),
        "Debito": st.column_config.NumberColumn("Débito", format="$%.2f"),
        "Credito": st.column_config.NumberColumn("Crédito", format="$%.2f"),
        "Centro_Costo": st.column_config.SelectboxColumn("C. Costo", options=CENTROS),
        "Unidad_Negocio": st.column_config.SelectboxColumn("U. Negocio", options=UNIDADES),
    }

    edited = st.data_editor(st.session_state.df_asiento, num_rows="dynamic", column_config=col_cfg, use_container_width=True, key="grid_v5")

    # Validaciones y Guardado
    edited = edited.fillna(0.0)
    deb = edited['Debito'].sum()
    cred = edited['Credito'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Débito", f"${deb:,.2f}")
    c2.metric("Crédito", f"${cred:,.2f}")
    
    if round(deb - cred, 2) == 0 and deb > 0:
        if st.button("💾 GUARDAR ASIENTO", type="primary"):
            sheet = conectar_google("Hoja 1") # OJO: Nombre de tu hoja de movimientos
            if sheet:
                lote = []
                for idx, row in edited.iterrows():
                    d_val = 0.0 if pd.isna(row['Debito']) else row['Debito']
                    c_val = 0.0 if pd.isna(row['Credito']) else row['Credito']
                    if d_val > 0 or c_val > 0:
                        lote.append([
                            str(fecha), str(doc), str(tercero), str(row['Cuenta']),
                            str(row['Detalle'] if row['Detalle'] else desc_global),
                            d_val, c_val, str(row['Centro_Costo']), str(row['Unidad_Negocio']),
                            str(st.session_state.usuario_actual)
                        ])
                sheet.append_rows(lote)
                st.success("Guardado Exitosamente")
                st.session_state.df_asiento = pd.DataFrame([{'Cuenta': PUC[0], 'Detalle': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': CENTROS[0], 'Unidad_Negocio': UNIDADES[0]}])
                st.rerun()
    elif round(deb - cred, 2) != 0:
        st.error(f"❌ Descuadrado por ${deb - cred:,.2f}")

# ==========================================
# 📊 REPORTES E IMPUESTOS
# ==========================================
elif menu == "📊 Reportes e Impuestos":
    st.title("Estados Financieros")
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()
        
    df = cargar_df("Hoja 1")
    if not df.empty:
        # Convertir a numeros
        df['Debito'] = pd.to_numeric(df['Debito'])
        df['Credito'] = pd.to_numeric(df['Credito'])
        
        tab1, tab2, tab3 = st.tabs(["💰 PyG (Resultados)", "🏛️ Impuestos", "📈 Por Unidad"])
        
        with tab1:
            st.subheader("Estado de Resultados (Aprox)")
            # Filtramos cuentas 4, 5, 6
            pyg = df[df['Cuenta'].astype(str).str.startswith(('4','5','6'))].copy()
            if not pyg.empty:
                resumen = pyg.groupby("Cuenta")[["Debito", "Credito"]].sum()
                resumen['Saldo'] = resumen['Credito'] - resumen['Debito'] # Ingreso naturaleza Credito
                st.dataframe(resumen)
                
                utilidad = resumen['Saldo'].sum()
                st.metric("Utilidad/Pérdida Neta", f"${utilidad:,.2f}")
            else:
                st.info("No hay datos de resultados.")

        with tab2:
            st.subheader("Balance de Impuestos (Retenciones e IVA)")
            imp = df[df['Cuenta'].astype(str).str.startswith(('23','24'))].copy()
            if not imp.empty:
                resumen_imp = imp.groupby("Cuenta")[["Debito", "Credito"]].sum()
                resumen_imp['A Pagar'] = resumen_imp['Credito'] - resumen_imp['Debito']
                st.dataframe(resumen_imp)
            else:
                st.info("No hay datos de impuestos.")
                
        with tab3:
            st.subheader("Rentabilidad por Unidad")
            # Ingresos - Gastos por Unidad
            ingresos = df[df['Cuenta'].str.startswith('4')].groupby("Unidad_Negocio")['Credito'].sum()
            gastos = df[df['Cuenta'].str.startswith(('5','6'))].groupby("Unidad_Negocio")['Debito'].sum()
            
            balance_un = pd.DataFrame({'Ingresos': ingresos, 'Gastos': gastos}).fillna(0)
            balance_un['Utilidad'] = balance_un['Ingresos'] - balance_un['Gastos']
            st.dataframe(balance_un)
            st.bar_chart(balance_un['Utilidad'])

# ==========================================
# 📂 VER Y EDITAR
# ==========================================
elif menu == "📂 Ver Movimientos":
    st.title("Histórico de Movimientos")
    st.info("ℹ️ Para **EDITAR** o **ELIMINAR** un asiento, por seguridad debes hacerlo directamente en Google Sheets.")
    st.markdown("[Abrir Google Sheets](https://docs.google.com/spreadsheets/)")
    
    if st.button("Actualizar Lista"):
        st.cache_data.clear()
        st.rerun()
        
    df = cargar_df("Hoja 1")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
