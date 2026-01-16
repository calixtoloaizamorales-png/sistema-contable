import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("🕵️‍♂️ Detective V2: Reparación Automática")

st.info("Analizando Secretos...")

# PASO 1: Obtener el texto
try:
    if "gcp_service_account" not in st.secrets:
        st.error("❌ Falta la sección [gcp_service_account] en Secrets.")
        st.stop()
    
    json_texto = st.secrets["gcp_service_account"]["contenido_json"]
    st.success("✅ PASO 1: Secreto encontrado.")
except Exception as e:
    st.error(f"❌ Error leyendo Secrets: {e}")
    st.stop()

# PASO 2: Intentar reparar el JSON roto
try:
    # Intento 1: Lectura normal
    creds_dict = json.loads(json_texto)
    st.success("✅ PASO 2: El JSON está perfecto.")
except Exception as e:
    st.warning(f"⚠️ El JSON tiene errores de formato (probablemente Enters invisibles). Intentando reparar...")
    try:
        # Intento 2: Modo permisivo (strict=False)
        creds_dict = json.loads(json_texto, strict=False)
        st.success("✅ PASO 2: Reparado con modo 'strict=False'.")
    except:
        try:
            # Intento 3: Limpieza manual de saltos de línea en la clave privada
            # Esto es cirugía mayor para unir la clave si se partió
            st.warning("⚠️ Intentando cirugía mayor en el texto...")
            texto_reparado = json_texto.replace('\n', '\\n') 
            # (Nota: esto es arriesgado si afecta la estructura, pero suele funcionar si es solo un copy-paste sucio)
            # Mejor estrategia: eliminar saltos de linea reales dentro de las comillas
            # Vamos a probar simplemente limpiando caracteres de control comunes
            texto_limpio = json_texto.replace('\r', '').replace('\t', '')
            creds_dict = json.loads(texto_limpio, strict=False)
            st.success("✅ PASO 2: Reparado con limpieza de caracteres.")
        except Exception as e2:
            st.error(f"❌ NO SE PUDO REPARAR. El error persiste: {e2}")
            st.error("SOLUCIÓN MANUAL: Ve a Secrets, borra todo y vuelve a pegar el JSON asegurándote de copiarlo SIN espacios extra.")
            st.stop()

# PASO 3: Probar conexión con la credencial (reparada o no)
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    st.success("✅ PASO 3: Autenticación exitosa con Google.")
    
    # Abrir hoja
    sheet = client.open("Base_Datos_Contabilidad").sheet1
    st.success("✅ PASO 4: Conexión con la Hoja confirmada.")
    st.balloons()
    st.markdown("## 🟢 ¡SISTEMA LISTO!")
    st.markdown("Ya puedes volver a GitHub y poner el **Código Definitivo** (El del Sistema Contable) que te pasé antes.")
    
except Exception as e:
    st.error(f"❌ Falló la conexión final: {e}")
