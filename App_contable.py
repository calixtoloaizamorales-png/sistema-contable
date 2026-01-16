import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("🕵️‍♂️ Detective de Conexión Google")

st.write("Iniciando pruebas de diagnóstico...")

# PRUEBA 1: Leer el Secreto de Streamlit
try:
    if "gcp_service_account" in st.secrets:
        st.success("✅ PASO 1: La bóveda de secretos existe.")
        
        if "contenido_json" in st.secrets["gcp_service_account"]:
            st.success("✅ PASO 2: La llave 'contenido_json' fue encontrada.")
            json_texto = st.secrets["gcp_service_account"]["contenido_json"]
        else:
            st.error("❌ ERROR PASO 2: No encuentro 'contenido_json' dentro de gcp_service_account. Revisa el archivo Secrets.")
            st.stop()
    else:
        st.error("❌ ERROR PASO 1: No encuentro la sección [gcp_service_account] en los Secrets.")
        st.stop()
except Exception as e:
    st.error(f"❌ ERROR CRÍTICO LEYENDO SECRETOS: {e}")
    st.stop()

# PRUEBA 3: Convertir Texto a JSON
try:
    creds_dict = json.loads(json_texto)
    st.success("✅ PASO 3: El texto del secreto es un JSON válido.")
except Exception as e:
    st.error(f"❌ ERROR PASO 3: El texto copiado no es un JSON válido. Revisa comillas o corchetes. Error: {e}")
    st.stop()

# PRUEBA 4: Autenticar con Google
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    st.success("✅ PASO 4: Autenticación con Google exitosa (El Robot entró).")
except Exception as e:
    st.error(f"❌ ERROR PASO 4: El Robot fue rechazado por Google. Error: {e}")
    st.stop()

# PRUEBA 5: Encontrar la Hoja
try:
    nombre_hoja = "Base_Datos_Contabilidad" # <--- OJO: Debe llamarse IDÉNTICO
    sheet = client.open(nombre_hoja).sheet1
    st.success(f"✅ PASO 5: Encontré la hoja '{nombre_hoja}'.")
except Exception as e:
    st.error(f"❌ ERROR PASO 5: No encuentro la hoja '{nombre_hoja}'. Asegúrate de haberla creado en Drive y compartido con el email del robot como EDITOR. Error: {e}")
    st.stop()

# PRUEBA 6: Escribir algo
try:
    st.info("Intentando escribir en la celda K1...")
    sheet.update_acell('K1', 'PRUEBA_EXITOSA')
    st.balloons()
    st.success("🎉 ¡PASO 6: CONEXIÓN PERFECTA! Ya puedes volver a poner el código de contabilidad.")
except Exception as e:
    st.error(f"❌ ERROR PASO 6: No pude escribir. Verifica que el robot sea 'Editor' y no solo 'Lector'. Error: {e}")
