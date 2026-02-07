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
    "11050501 - Caja general Buga"  ,	
"11050503 - Caja Efectivo"  ,	
"11051001 - Caja Menor Logística"  ,	
"11100501 - Bancolombia"  ,	
"11100503 - Banco BBVA"  ,	
"13050501 - CxC Nacionales"  ,	
"13300501 - Anticipo a proveedores de mercancías"  ,	
"13309501 - Anticipo a otros"  ,	
"13551503 - Ret. por Comisiones"  ,	
"13551504 - Ret. por Servicios en General"  ,	
"13551506 - Ret. por Arrendamiento de Bienes Muebles"  ,	
"13551507 - Ret. por Ventas"  ,	
"13551510 - Ret. por Servicios de Transporte"  ,	
"13551512 - Ret. por Ventas de petróleo y derivados"  ,	
"13551701 - Impuesto a las Ventas Retenido"  ,	
"13551801 - Impuesto de Industria y Comercio retenido Buga"  ,	
"13559003 - Autorretención especial a título de renta (CREE 0.55% - antiguo 0.4%)"  ,	
"13559501 - Otros anticipos"  ,	
"13802001 - Cuentas por cobrar de terceros"  ,	
"14050101 - Materias primas"  ,	
"14150101 - Obras de construcción en curso"  ,	
"14350101 - Mercancia gravada"  ,	
"14350102 - Mercancía exenta"  ,	
"14350103 - Mercancía excluida"  ,	
"14350803 - Combustible Gas Propano"  ,	
"14550101 - Herramientas"  ,	
"14550102 - Dotación EPP"  ,	
"14550103 - Dotación Uniformes"  ,	
"14550104 - Elementos de Papelería"  ,	
"14991001 - Para Diferencia de Inventario Físico"  ,	
"15040501 - Terreno Empresa"  ,	
"15040502 - Terrenos Modelo del Costo"  ,	
"15121504 - Equipo de computación y comunicación"  ,	
"15160602 - Construcciones y Edificaciones en Leasing"  ,	
"15160607 - Modelo de Revaluación"  ,	
"15200101 - Maquinaria y Equipo"  ,	
"15200102 - Herramientas"  ,	
"15200105 - Modelo de Revaluacion"  ,	
"15240501 - Muebles y Enseres"  ,	
"15240599 - Iva Mayor Valor de Muebles y Enseres"  ,	
"15241001 - Aire Acondicionado"  ,	
"15241002 - Aire acondicionado palm"  ,	
"15249505 - Torno"  ,	
"15280501 - Equipo de Procesamiento de Datos"  ,	
"15280502 - Equipo de procesamiento de datos"  ,	
"15280599 - Iva Mayor Valor de Equipo de procesamiento de datos"  ,	
"15400501 - Camionetas"  ,	
"15400801 - Camiónes Grúa"  ,	
"15400805 - Modelo de Revaluacion"  ,	
"15402001 - Montacargas"  ,	
"15402005 - Modelo de Revaluacion"  ,	
"15403001 - Motocicletas"  ,	
"15920501 - Construcciones y edificaciones"  ,	
"15921001 - Maquinaria y equipo"  ,	
"15921501 - Equipo de oficina"  ,	
"15922001 - Equipo de computación y comunicación"  ,	
"15923501 - Camioneta"  ,	
"15923502 - Montacargas"  ,	
"15923503 - Camiones"  ,	
"15923504 - Motocicletas"  ,	
"15923601 - Flota y Equipo de Transporte"  ,	
"21050505 - Bancos"  ,	
"22050501 - Proveedores Nacionales"  ,	
"22100501 - Proveedores del Exterior"  ,	
"23350501 - Gastos financieros"  ,	
"23351001 - Gastos legales"  ,	
"23353001 - Servicios técnicos"  ,	
"23353501 - Servicios de Mantenimiento"  ,	
"23354502 - Fletes"  ,	
"23355001 - Servicios públicos Energía"  ,	
"23355002 - Servicios públicos Acueducto"  ,	
"23355004 - Servicios públicos Celular corporativo"  ,	
"23355501 - Seguros"  ,	
"23356001 - Gastos de viaje"  ,	
"23359501 - Otros"  ,	
"23551001 - Socios"  ,	
"23654001 - Compras"  ,	
"23658001 - Retenciones por pagar"  ,	
"23659003 - Autorretención especial a título de renta (CREE 0.55% - antiguo 0.4%)"  ,	
"23680101 - Impuesto de industria y comercio retenido Compras"  ,	
"23689001 - Reteica por pagar"  ,	
"23700501 - Aportes a entidades promotoras de salud EPS Patrono"  ,	
"23700502 - Aportes a entidades promotoras de salud EPS Trabajador"  ,	
"23700601 - Aportes a Administradoras de Riesgos Laborales ARL"  ,	
"23701001 - Aportes a Cajas de Compensación"  ,	
"23703001 - Libranzas"  ,	
"23750101 - Cuotas por cobrar de Tercero"  ,	
"23803001 - Fondos de cesantías y/o pensiones Patrono"  ,	
"23803002 - Fondos de cesantías y/o pensiones Trabajador"  ,	
"23809503 - Cuentas por pagar a terceros"  ,	
"23809506 - Cuentas por pagar a terceros"  ,	
"24080117 - IVA por pagar"  ,	
"24080119 - Ingresos con IVA 19%"  ,	
"24080217 - IVA en compras en el exterior"  ,	
"24080219 - Compras con IVA 19%"  ,	
"24080220 - IVA descontable en gastos 19%"  ,	
"25050101 - Salarios por pagar"  ,	
"26100501 - Cesantías"  ,	
"26101001 - Intereses sobre cesantías"  ,	
"26101501 - Vacaciones"  ,	
"26102001 - Prima de servicios"  ,	
"28050501 - De clientes"  ,	
"28059502 - Anticipo Pago de Incapacidades"  ,	
"31150501 - Aporte social accionistas"  ,	
"33050501 - Reserva legal"  ,	
"36050101 - Utilidad del ejercicio"  ,	
"37050101 - Utilidades  acumuladas"  ,	
"37100105 - Pérdidas acumuladas "  ,	
"37250501 - Cambio en Políticas Contables"  ,	
"38100401 - Terrenos"  ,	
"38100801 - Construcciones y Edificaciones"  ,	
"38103201 - Flota y Equipo de Transporte"  ,	
"41350601 - Arrendamientos"  ,	
"41350602 - Club"  ,	
"41350603 - Hacienda"  ,
"41350801 - Otros"  ,
"42100501 - Intereses"  ,	
"42102001 - Diferencia en cambio"  ,	
"42104001 - Descuentos comerciales condicionados"  ,	
"51050601 - Sueldos"  ,	
"51050602 - Aportes a Estudiantes Aprendices"  ,	
"51052401 - Incapacidades"  ,	
"51053001 - Cesantías"  ,	
"51053301 - Intereses sobre cesantías"  ,	
"51053601 - Prima de servicios"  ,	
"51053901 - Vacaciones"  ,	
"51054501 - Auxilios"  ,	
"51054801 - Bonificaciones"  ,	
"51055101 - Dotación"  ,	
"51055102 - Elementos de Proteccion Personal"  ,	
"51055103 - Extintores"  ,	
"51055104 - Otros"  ,	
"51056001 - Indemnizaciones laborales"  ,	
"51056301 - Capacitación al personal"  ,	
"51056801 - Aportes a administradoras de riesgos profesionales arl"  ,	
"51056901 - Aportes a entidades promotoras de salud eps"  ,	
"51057001 - Aportes a fondos de pensiones y/o cesantías"  ,	
"51057201 - Aportes cajas de compensación familiar"  ,	
"51058403 - Gastos Examenes"  ,	
"51059501 - Otros"  ,	
"51150501 - Industria y comercio"  ,	
"51151501 - A la propiedad raíz"  ,	
"51157504 - Impuesto al consumo 4%"  ,	
"51201101 - Arrendamientos Local"  ,	
"51202001 - Equipo de oficina"  ,	
"51202501 - Equipo de computación y comunicación"  ,	
"51251001 - Afiliaciones y sostenimiento"  ,	
"51302501 - Incendio"  ,	
"51303001 - Terremoto"  ,	
"51303501 - Sustracción"  ,	
"51304001 - Seguros Pólizas"  ,	
"51304002 - Seguros Soat"  ,	
"51306001 - Responsabilidad civil y extracontractual"  ,	
"51307001 - Rotura de maquinaria"  ,	
"51309501 - Equipo Electronico"  ,	
"51309599 - Otros"  ,	
"51350501 - Aseo"  ,	
"51351501 - Asistencia Técnica"  ,	
"51351502 - Asistencia técnica Software"  ,	
"51352501 - Acueducto y alcantarillado"  ,	
"51353001 - Energía Eléctrica"  ,	
"51353501 - Teléfono"  ,	
"51353502 - Celular Corporativo"  ,	
"51354001 - Correo"  ,	
"51354501 - Internet"  ,	
"51355002 - Fletes"  ,	
"51359501 - Otros"  ,	
"51400501 - Notariales"  ,	
"51401001 - Registro Mercantil"  ,	
"51401002 - Certificados Mercantiles"  ,	
"51401502 - Licencias"  ,	
"51409501 - Otros"  ,	
"51451501 - Maquinaria y equipo"  ,	
"51452001 - Equipo de oficina"  ,	
"51452501 - Equipo de computación"  ,	
"51452502 - Impresoras"  ,	
"51454001 - Mantenimiento de Vehiculos"  ,	
"51454002 - Revisión Técnico Mecánica"  ,	
"51500501 - Instalaciones Eléctricas"  ,	
"51501001 - Arreglos Ornamentales"  ,	
"51501501 - Reparaciones Locativas"  ,	
"51509501 - Otras adecuaciones"  ,	
"51509503 - Otras reparaciones"  ,	
"51559501 - Otros"  ,	
"51559502 - Peajes"  ,	
"51601001 - Maquinaria y Equipo"  ,	
"51601501 - Equipo de Oficina"  ,	
"51602001 - Equipo de Computación y Comunicación"  ,	
"51603501 - Flota y Equipo de Transporte"  ,	
"51651001 - Intangibles"  ,	
"51951001 - Pagina Web-Hosting y Dominio"  ,	
"51952001 - Gastos de representación"  ,	
"51952501 - Elementos de aseo"  ,	
"51952502 - Cafetería"  ,	
"51953001 - Papelería"  ,	
"51953501 - Combustibles y Lubricantes"  ,	
"51954001 - Envases y Empaques"  ,	
"51956501 - Parqueaderos"  ,	
"51959505 - Gastos de Personal"  ,	
"51959535 - Servicios"  ,	
"51959545 - Mantenimiento y Reparaciones"  ,	
"51959550 - Adecuaciones e Instalaciones"  ,	
"51959555 - Gastos de Viaje"  ,	
"51959595 - Diversos"  ,	
"52050601 - Sueldos"  ,	
"52051501 - Horas Extras y Recargos"  ,	
"52052401 - Incapacidades"  ,	
"52052701 - Auxilio de transporte"  ,	
"52053001 - Cesantías"  ,	
"52053301 - Intereses sobre cesantías"  ,	
"52053601 - Prima de servicios"  ,	
"52053901 - Vacaciones"  ,	
"52054501 - Auxilios"  ,	
"52054801 - Bonificaciones"  ,	
"52055101 - Dotacion"  ,	
"52055102 - Elementos de Proteccion Personal"  ,	
"52055103 - Extintores"  ,	
"52055104 - Otros"  ,	
"52056301 - Capacitación al personal"  ,	
"52056801 - Aportes a Administradoras de Riesgos Profesionales arp"  ,	
"52057001 - Aportes a Fondos de Pensiones y/o Cesantías"  ,	
"52057201 - Aportes Cajas de Compensación Familiar"  ,	
"52058403 - Gastos Exámenes"  ,	
"52109501 - Otros"  ,	
"52151001 - De Timbres"  ,	
"52154001 - De vehículos"  ,	
"52201005 - Alquiler Edificios y Locales"  ,	
"52201501 - Maquinaria y equipo"  ,	
"52202001 - Equipo de oficina"  ,	
"52202501 - Equipo de computación y comunicación"  ,	
"52204001 - Flota y equipo de transporte"  ,	
"52251001 - Afiliaciones y sostenimiento"  ,	
"52304001 - Flota y equipo de transporte"  ,	
"52304002 - Seguros Soat"  ,	
"52306001 - Responsabilidad civil y extracontractual"  ,	
"52350501 - Aseo"  ,	
"52351501 - Asistencia técnica"  ,	
"52353001 - Energía eléctrica"  ,	
"52353501 - Teléfono"  ,	
"52354501 - Internet"  ,	
"52355001 - Transporte"  ,	
"52355002 - Fletes"  ,	
"52356001 - Publicidad, propaganda y promoción"  ,	
"52359502 - Gastos Manejo"  ,	
"52359503 - Otros"  ,	
"52451501 - Maquinaria y equipo"  ,	
"52452001 - Equipo de oficina"  ,	
"52452501 - Equipo de computación y comunicación"  ,	
"52452502 - Impresoras"  ,	
"52454001 - Camionetas y Camperos"  ,	
"52454002 - Camión"  ,	
"52454003 - Montacargas"  ,	
"52454004 - Motos"  ,	
"52454099 - Otros"  ,	
"52501501 - Reparaciones locativas"  ,	
"52509501 - Otras adecuaciones"  ,	
"52509502 - Copias de Llaves"  ,	
"52550501 - Alojamiento y manutención"  ,	
"52552001 - Pasajes terrestres"  ,	
"52559501 - Peajes"  ,	
"52952001 - Gastos de representación y relaciones públicas"  ,	
"52952501 - Elementos de aseo"  ,	
"52952502 - Cafetería"  ,	
"52953001 - Papelería"  ,	
"52953501 - Combustible Acpm"  ,	
"52953502 - Combustible Corriente"  ,	
"52956001 - Restaurante"  ,	
"52956501 - Parqueaderos"  ,	
"52958101 - Ajuste al peso"  ,	
"52959501 - Otros"  ,	
"52959502 - Gastos no deducibles"  ,	
"52991501 - Deterioro Inventarios"  ,	
"53050501 - Gastos bancarios"  ,	
"53050502 - Chequera"  ,	
"53051501 - Comisiones"  ,	
"53052001 - Intereses Corrientes"  ,	
"53052002 - Intereses de Sobregiros"  ,	
"53052003 - Intereses de Mora"  ,	
"53052004 - Intereses de Particulares"  ,	
"53052005 - Intereses por mora no deducibles"  ,	
"53052501 - Diferencia en Cambio"  ,	
"53053501 - Descuentos comerciales condicionados"  ,	
"53054001 - Gravamen Movimiento Financiero"  ,	
"53055501 - Fondo Nal de Garantías"  ,	
"53055502 - Seguros Financieros"  ,	
"53055503 - Cuota de Manejo Tarjeta de Crédito"  ,	
"53059501 - Otros"  ,	
"53152001 - Impuestos asumidos"  ,	
"53159501 - Otros"  ,	
"53159502 - Gastos no Deducibles"  ,	
"53959501 - Otros"  ,	
"54050501 - Impuesto de renta y complementarios"  ,	
"61350601 - Venta de partes, gravados"  ,	
"61350602 - Venta de partes, exentas"  ,	
"61350803 - Combustible Gas Propano"  ,	
"61354801 - Venta de herramientas y artículos de ferretería"  ,	
"61450501 - Servicio de transporte por carretera"  ,	
"61559001 - Mantenimiento y reparación de maquinaria y equipo"  ,	
"62050101 - De mercancías"  ,	
"62454002 - Vr Reparaciones y/o Servicios"  ,	
"62559501 - Peajes"  ,	
"62559502 - Restaurante"  ,	
"71010101 - Materia prima"  ,	
"72050601 - Sueldos"  ,	
"72051501 - Hora Extra Ordinaria"  ,	
"72051502 - Hora Extra Noctura Ordinaria"  ,	
"72051503 - Hora Diurna Dominical y Festivo"  ,	
"72051504 - Hora Extra Diurna Dominical y Festivo"  ,	
"72051506 - Hora Extra Dominical/Festiva Nocturna"  ,	
"72051801 - Comisiones"  ,	
"72052401 - Incapacidades"  ,	
"72052701 - Auxilio de Transporte"  ,	
"72053001 - Cesantías"  ,	
"72053301 - Intereses sobre Cesantías"  ,	
"72053601 - Prima de Servicios"  ,	
"72053901 - Vacaciones"  ,	
"72054501 - Auxilios"  ,	
"72054801 - Bonificaciones"  ,	
"72055101 - Dotación"  ,	
"72055102 - Elementos de Protección Personal"  ,	
"72055103 - Extintores"  ,	
"72056801 - Aportes a Administradoras de Riesgos Laborales ARL"  ,	
"72057001 - Aportes a Fondos de Pensiones y/o Cesantías"  ,	
"72057201 - Aportes Cajas de Compensación Familiar"  ,	
"72058403 - Gastos Exámenes"  ,	
"72353001 - Energía Eléctrica"  ,	
"72953001 - Utiles, papelería y fotocopias"  ,	

]
CENTROS = ["Club", "Apt1", "Apt2", "Apt3", "Obras Civiles", "Hacienda","JD"]
UNIDADES = ["Pesebreras", "Estimulacion Equinoterapia", "Volting", "adiestramiento", "Salto Equestre", "Salto Equestre","Olimpa ",
"Shalon ",
"Max ",
"Leal ",
"Maxima ",
"Achita ",
"Misterio ",
"Gamin ",
"Nativo ",
"Valiente ",
"Neptuno&Lucky ",
"Colina ",
"Tagua ",
"Vampiro ",
"Don Juan y Joshua",
]
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

def obtener_siguiente_consecutivo():
    df = cargar_df("Hoja 1")
    if df.empty or 'ID_Comprobante' not in df.columns:
        return 1
    else:
        try:
            serie = pd.to_numeric(df['ID_Comprobante'], errors='coerce')
            maximo = serie.max()
            if pd.isna(maximo): return 1
            return int(maximo) + 1
        except:
            return 1

# ==========================================
# 🔐 LOGIN
# ==========================================
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

if st.session_state.usuario_actual is None:
    st.title("🔐 ERP Pronades - Acceso Seguro")
    try:
        usuarios_secretos = st.secrets["usuarios"]
    except:
        st.error("Configura los usuarios en Secrets.")
        st.stop()

    c1, c2 = st.columns([1,2])
    u = c1.text_input("Usuario")
    p = c1.text_input("Contraseña", type="password")
    
    if c1.button("Entrar"):
        if u in usuarios_secretos and usuarios_secretos[u] == p:
            st.session_state.usuario_actual = u
            st.rerun()
        else:
            st.error("Acceso Denegado")
    st.stop()

# ==========================================
# 🖥️ MENÚ
# ==========================================
st.sidebar.title(f"👤 {st.session_state.usuario_actual}")
if st.sidebar.button("Salir"):
    st.session_state.usuario_actual = None
    st.rerun()

menu = st.sidebar.radio("Navegación", 
    ["📝 Nuevo Asiento", "👥 Gestión Terceros", "📊 Reportes", "📂 Histórico"])

# ==========================================
# 👥 TERCEROS (SEPARADO Y DESPLEGABLE)
# ==========================================
if menu == "👥 Gestión Terceros":
    st.title("Directorio de Terceros")
    
    with st.expander("➕ Crear Nuevo Tercero", expanded=True):
        # 1. LISTA DESPLEGABLE (Lo que pediste)
        tipo_persona = st.selectbox("Tipo de Persona", ["Natural", "Jurídica"])
        
        with st.form("form_tercero"):
            c1, c2, c3 = st.columns([2, 1, 2])
            nit = c1.text_input("NIT / Cédula (Sin puntos)")
            dv = c2.text_input("DV", max_chars=1)
            tipo_tercero = c3.selectbox("Clasificación", ["Cliente", "Proveedor", "Empleado", "Socio", "Otro"])

            # Variables para guardar
            razon_social = ""
            nom1, nom2, ape1, ape2 = "", "", "", ""
            nombre_visual = ""
            
            if tipo_persona == "Jurídica":
                razon_social = st.text_input("Razón Social (Nombre Empresa)")
                nombre_visual = razon_social
            else:
                st.markdown("**Nombres y Apellidos Separados:**")
                n1, n2 = st.columns(2)
                nom1 = n1.text_input("Primer Nombre")
                nom2 = n2.text_input("Segundo Nombre (Opcional)")
                a1, a2 = st.columns(2)
                ape1 = a1.text_input("Primer Apellido")
                ape2 = a2.text_input("Segundo Apellido (Opcional)")
                
                # Armamos el nombre visual para mostrar en la app
                parts = [p for p in [nom1, nom2, ape1, ape2] if p]
                nombre_visual = " ".join(parts)

            st.markdown("---")
            c4, c5 = st.columns(2)
            direccion = c4.text_input("Dirección")
            ciudad = c5.text_input("Ciudad / Municipio")
            
            c6, c7 = st.columns(2)
            telefono = c6.text_input("Teléfono")
            email = c7.text_input("Email")
            
            if st.form_submit_button("Guardar Tercero"):
                if not nit:
                    st.error("El NIT es obligatorio")
                else:
                    sheet = conectar_google("Terceros")
                    if sheet:
                        # Guardamos CADA CAMPO EN SU COLUMNA
                        datos = [
                            str(nit), str(dv), tipo_persona, 
                            razon_social.upper(), 
                            nom1.upper(), nom2.upper(), ape1.upper(), ape2.upper(), # <--- Separados
                            direccion.upper(), ciudad.upper(), 
                            str(telefono), str(email).lower(), 
                            tipo_tercero,
                            nombre_visual.upper() # Columna K (Nombre_Visual)
                        ]
                        sheet.append_row(datos)
                        st.success(f"✅ Tercero {nombre_visual} guardado correctamente.")
                        st.cache_data.clear()
                        st.rerun()

    # Visualizar lista
    st.markdown("### Base de Datos")
    df_t = cargar_df("Terceros")
    if not df_t.empty:
        # Mostramos lo más importante
        cols_mostrar = ['NIT', 'Nombre_Visual', 'Telefono', 'Ciudad']
        # Filtramos solo columnas que existan para evitar errores si no has actualizado el sheet
        cols_validas = [c for c in cols_mostrar if c in df_t.columns]
        st.dataframe(df_t[cols_validas], use_container_width=True)
    else:
        st.info("No hay terceros registrados.")

# ==========================================
# 📝 NUEVO ASIENTO
# ==========================================
elif menu == "📝 Nuevo Asiento":
    st.title("📝 Registrar Comprobante")

    if 'ultimo_registro' in st.session_state and st.session_state.ultimo_registro is not None:
        st.success(f"✅ ¡Comprobante #{st.session_state.ultimo_id} guardado!")
        st.dataframe(st.session_state.ultimo_registro)
        if st.button("Nuevo Registro"):
            st.session_state.ultimo_registro = None
            st.rerun()
        st.markdown("---")

    # Cargar terceros
    df_t = cargar_df("Terceros")
    if df_t.empty:
        lista_terceros = ["Consumidor Final"]
    else:
        # Usamos la columna 'Nombre_Visual' (La última, Columna N)
        if 'Nombre_Visual' in df_t.columns:
            lista_terceros = (df_t['NIT'].astype(str) + " - " + df_t['Nombre_Visual']).tolist()
        else:
            lista_terceros = df_t['NIT'].astype(str).tolist()

    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha", datetime.now())
    tercero = c2.selectbox("Tercero", lista_terceros)
    doc_ref = c3.text_input("Doc. Ref")
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

    edited = st.data_editor(st.session_state.df_asiento, num_rows="dynamic", column_config=col_cfg, use_container_width=True, key="grid_v10")
    edited = edited.fillna(0.0)
    deb, cred = edited['Debito'].sum(), edited['Credito'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Débito", f"${deb:,.2f}")
    c2.metric("Crédito", f"${cred:,.2f}")
    
    if round(deb - cred, 2) == 0 and deb > 0:
        if st.button("💾 GUARDAR", type="primary"):
            sheet = conectar_google("Hoja 1")
            if sheet:
                with st.spinner("Guardando..."):
                    nuevo_id = obtener_siguiente_consecutivo()
                    lote = []
                    vis = []
                    for idx, row in edited.iterrows():
                        d = 0.0 if pd.isna(row['Debito']) else row['Debito']
                        c = 0.0 if pd.isna(row['Credito']) else row['Credito']
                        if d > 0 or c > 0:
                            lote.append([
                                int(nuevo_id), str(fecha), str(doc_ref), str(tercero), 
                                str(row['Cuenta']), str(row['Detalle'] if row['Detalle'] else desc_global),
                                d, c, str(row['Centro_Costo']), str(row['Unidad_Negocio']),
                                str(st.session_state.usuario_actual)
                            ])
                            vis.append({'Cuenta': row['Cuenta'], 'Debito': d, 'Credito': c})
                    try:
                        sheet.append_rows(lote)
                        st.session_state.ultimo_registro = pd.DataFrame(vis)
                        st.session_state.ultimo_id = nuevo_id
                        st.session_state.df_asiento = pd.DataFrame([{'Cuenta': PUC[0], 'Detalle': '', 'Debito': 0.0, 'Credito': 0.0, 'Centro_Costo': CENTROS[0], 'Unidad_Negocio': UNIDADES[0]}])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    elif round(deb - cred, 2) != 0:
        st.error(f"❌ Descuadrado")

# ==========================================
# 📊 REPORTES Y HISTÓRICO
# ==========================================
elif menu == "📂 Histórico":
    st.title("Histórico")
    if st.button("Actualizar"): st.cache_data.clear(); st.rerun()
    st.dataframe(cargar_df("Hoja 1").sort_values(by='ID_Comprobante', ascending=False), use_container_width=True)

elif menu == "📊 Reportes":
    st.title("Reportes")
    if st.button("🔄"): st.cache_data.clear(); st.rerun()
    df = cargar_df("Hoja 1")
    if not df.empty:
        df['Debito'] = pd.to_numeric(df['Debito'])
        df['Credito'] = pd.to_numeric(df['Credito'])
        res = df.groupby("Cuenta")[["Debito", "Credito"]].sum()
        res['Saldo'] = res['Credito'] - res['Debito']
        st.dataframe(res)


