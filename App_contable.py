import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import numpy as np

st.set_page_config(page_title="ERP Pronades SAS", layout="wide", page_icon="📈")

# ==========================================
# ⚙️ CONFIGURACIÓN DE LISTAS (MAESTROS)
# ==========================================
# NOTA: Los USUARIOS ya no están aquí, están en los Secrets por seguridad.

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
# 🔌 CONEXIÓN
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
# 🔐 LOGIN (AHORA LEE DESDE SECRETS)
# ==========================================
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

if st.session_state.usuario_actual is None:
    st.title("🔐 ERP Pronades - Acceso Seguro")
    
    # Cargamos usuarios desde la bóveda secreta
    try:
        usuarios_secretos = st.secrets["usuarios"]
    except:
        st.error("❌ Error de configuración: No se encontraron usuarios en Secrets.")
        st.stop()

    c1, c2 = st.columns([1,2])
    u = c1.text_input("Usuario")
    p = c1.text_input("Contraseña", type="password")
    
    if c1.button("Entrar"):
        # Verificamos contra la lista secreta
        if u in usuarios_secretos and usuarios_secretos[u] == p:
            st.session_state.usuario_actual = u
            st.rerun()
        else:
            st.error("❌ Acceso Denegado")
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
# 👥 TERCEROS
# ==========================================
if menu == "👥 Gestión Terceros":
    st.title("Directorio de Terceros")
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
                    st.success(f"✅ Tercero {razon} guardado.")
                    st.cache_data.clear()
                    st.rerun()
    df_terceros = cargar_df("Terceros")
    if not df_terceros.empty:
        st.dataframe(df_terceros, use_container_width=True)
    else:
        st.info("No hay terceros creados.")

# ==========================================
# 📝 NUEVO ASIENTO
# ==========================================
elif menu == "📝 Nuevo Asiento":
    st.title("📝 Registrar Comprobante")

    if 'ultimo_registro' in st.session_state and st.session_state.ultimo_registro is not None:
        st.success("✅ ¡Asiento guardado exitosamente!")
        st.markdown("**Resumen guardado:**")
        st.dataframe(st.session_state.ultimo_registro, use_container_width=True)
        if st.button("Cerrar Confirmación"):
            st.session_state.ultimo_registro = None
            st.rerun()
        st.markdown("---")

    df_t = cargar_df("Terceros")
    lista_terceros = (df_t['NIT'].astype(str) + " - " + df_t['Razon_Social']).tolist() if not df_t.empty else ["Consumidor Final"]

    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha", datetime.now())
    tercero = c2.selectbox("Tercero", lista_terceros)
    doc = c3.text_input("Documento", placeholder="Ej: FC-100")
    desc_global = st.text_input("Descripción Global")

    if 'df_asiento' not in st.session_state:
        st.session_state.df_asiento = pd.DataFrame([{'Cuenta': PUC[0], 'Detalle': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': CENTROS[0], 'Unidad_Negocio': UNIDADES[0]}])

    col_cfg = {
        "Cuenta": st.column_config.SelectboxColumn("Cuenta", options=PUC, width="large"),
        "Detalle": st.column_config.TextColumn("Detalle", width="medium"),
        "Debito": st.column_config.NumberColumn("Débito", format="$%.2f"),
        "Credito": st.column_config.NumberColumn("Crédito", format="$%.2f"),
        "Centro_Costo": st.column_config.SelectboxColumn("C. Costo", options=CENTROS),
        "Unidad_Negocio": st.column_config.SelectboxColumn("U. Negocio", options=UNIDADES),
    }

    edited = st.data_editor(st.session_state.df_asiento, num_rows="dynamic", column_config=col_cfg, use_container_width=True, key="grid_v7")
    edited = edited.fillna(0.0)
    deb, cred = edited['Debito'].sum(), edited['Credito'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Débito", f"${deb:,.2f}")
    c2.metric("Crédito", f"${cred:,.2f}")
    
    if round(deb - cred, 2) == 0 and deb > 0:
        if st.button("💾 GUARDAR ASIENTO", type="primary", use_container_width=True):
            sheet = conectar_google("Hoja 1")
            if sheet:
                lote = []
                vis = []
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
                        vis.append({'Cuenta': row['Cuenta'], 'Detalle': row['Detalle'], 'Debito': d_val, 'Credito': c_val})
                try:
                    sheet.append_rows(lote)
                    st.session_state.ultimo_registro = pd.DataFrame(vis)
                    st.session_state.df_asiento = pd.DataFrame([{'Cuenta': PUC[0], 'Detalle': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': CENTROS[0], 'Unidad_Negocio': UNIDADES[0]}])
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    elif round(deb - cred, 2) != 0:
        st.error(f"❌ Descuadrado por ${deb - cred:,.2f}")

# ==========================================
# 📊 REPORTES
# ==========================================
elif menu == "📊 Reportes e Impuestos":
    st.title("Estados Financieros")
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()
    df = cargar_df("Hoja 1")
    if not df.empty:
        df['Debito'] = pd.to_numeric(df['Debito'])
        df['Credito'] = pd.to_numeric(df['Credito'])
        tab1, tab2 = st.tabs(["💰 PyG", "🏛️ Impuestos"])
        with tab1:
            pyg = df[df['Cuenta'].astype(str).str.startswith(('4','5','6'))].copy()
            if not pyg.empty:
                resumen = pyg.groupby("Cuenta")[["Debito", "Credito"]].sum()
                resumen['Saldo'] = resumen['Credito'] - resumen['Debito']
                st.dataframe(resumen, use_container_width=True)
                st.metric("Resultado Neto", f"${resumen['Saldo'].sum():,.2f}")
            else:
                st.info("Sin datos.")
        with tab2:
            imp = df[df['Cuenta'].astype(str).str.startswith(('23','24'))].copy()
            if not imp.empty:
                resumen_imp = imp.groupby("Cuenta")[["Debito", "Credito"]].sum()
                resumen_imp['A Pagar'] = resumen_imp['Credito'] - resumen_imp['Debito']
                st.dataframe(resumen_imp, use_container_width=True)
            else:
                st.info("Sin datos.")

# ==========================================
# 📂 VER MOVIMIENTOS
# ==========================================
elif menu == "📂 Ver Movimientos":
    st.title("Histórico")
    st.markdown("[Editar en Google Sheets](https://docs.google.com/spreadsheets/)")
    if st.button("Actualizar"):
        st.cache_data.clear()
        st.rerun()
    st.dataframe(cargar_df("Hoja 1"), use_container_width=True)
