#! Se encarga de la prevalidacion - Si no hay evento programado, espera y vuelve a intentar
#Codigo, funcional, para tomar eventos de un Json, ejecutar el archivo en tiempo real,
#  hasta acabar el evento y guarda en una BD

import hashlib
import requests
import json
import urllib3
import pyodbc
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
from logging.handlers import RotatingFileHandler


#! === CONFIGURACIÓN DE LOGGING ===
LOG_FILENAME = "Monitoreo nemesio camacho.log"

# RotatingFileHandler (10 MB máx, 5 archivos de backup)
file_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10_000_000, backupCount=5)
file_handler.setLevel(logging.INFO)

#! Formato del log
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# Stream a consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Logger global
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== CONFIGURACIÓN GENERAL ====
SERVER_ID     = "8AMjadEURXKv89qhpPkKKA"
BASE_URL = "https://10.16.203.10:8443/mt/api/rest/v1/events/search"
CAMERA_FILE = "ids_camaras_permitidas.json"
EVENTS_JSON = "eventos_programados.json"
INTERVAL_SECONDS = 60



#!Funcion que nos permite generar el token de autenticación, y con el token generado, nos permite obtener el token de sesión
def generate_auth_token(user_nonce, user_key, integration_id=None):

    #* Obtener el timestamp actual en formato Unix
    timestamp = str(int(time.time()))
    hash_input = timestamp + user_key
    hex_encoded = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    #* Construir el token
    token_parts = [user_nonce, timestamp, hex_encoded]
    Authorization_Token = ":".join(token_parts)


    #* Url de autenticación
    #* Esta URL es la que se utiliza para obtener el token de sesión
    url = "https://10.16.203.10:8443/mt/api/rest/v1/login"
    
    #* === Headers necesarios ===
    headers = {
        "Content-Type": "application/json",
    }

    #* === Body del POST 
    body = {
        "username": "administrator",
        "password": "Sencia.2025",
        "clientName": "PruebaPostman2",
        "authorizationToken": Authorization_Token
    }
    #* === Envío de la solicitud POST ===
    try:
        response = requests.post(url, headers=headers, json=body, verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        logging.info("Respuesta del servidor: %s", data)

        #* Extraer el token de sesión
        session_token = data.get("result", {}).get("session")
        if session_token:
            logging.info("Token de sesión: %s", session_token)
            return session_token
        else:
            logging.critical("No se encontró el campo 'session' en la respuesta.")
            return None

    except requests.exceptions.RequestException as e:
        logging.error("Error al obtener el token de sesión: %s", e)
        return None

#!Funcion del Aforo del parqueadero Norte - SUR_ORIENTAL(4)
def actualizar_aforo_parqueadero(conn, eventos, nombre_evento):
    """
    Procesa los eventos y actualiza el aforo en la BD por evento (histórico acumulado).
    """
    try:
        cursor = conn.cursor()

        # Contar entradas y salidas en este lote
        entradas = sum(1 for e in eventos if "AFORO ENTRADA PARQUEADERO NORTE" in e.get("analyticEventName", "").upper())
        salidas  = sum(1 for e in eventos if "AFORO SALIDA PARQUEADERO NORTE" in e.get("analyticEventName", "").upper())

        if entradas == 0 and salidas == 0:
            return 0  # Nada que registrar

        # ✅ Consultar aforo actual del evento
        cursor.execute("SELECT aforo FROM Aforo_parqueadero WHERE evento = ?", (nombre_evento,))
        row = cursor.fetchone()
        aforo_actual = row[0] if row else 0

        # Calcular nuevo aforo acumulado
        nuevo_aforo = aforo_actual + entradas - salidas
        if nuevo_aforo < 0:
            nuevo_aforo = 0

        if row:  
            # Si el evento ya existe → actualizar
            cursor.execute("""
                UPDATE Aforo_parqueadero
                SET aforo = ?
                WHERE evento = ?
            """, (nuevo_aforo, nombre_evento))
        else:  
            # Si el evento no existe → insertar
            cursor.execute("""
                INSERT INTO Aforo_parqueadero (evento, aforo)
                VALUES (?, ?)
            """, (nombre_evento, nuevo_aforo))

        conn.commit()
        logging.info(f"Aforo actualizado para {nombre_evento}: {nuevo_aforo} (Entradas={entradas}, Salidas={salidas})")
        return 1

    except Exception as e:
        logging.error("Error guardando aforo del evento: %s", e)
        return 0

def actualizar_aforo_parqueadero_Campinsito(conn, eventos, nombre_evento):
    """
    Procesa los eventos y actualiza el aforo en la BD por evento (histórico acumulado).
    """
    try:
        cursor = conn.cursor()

        # Contar entradas y salidas en este lote
        entradas = sum(1 for e in eventos if "ENTRADA VEHICULAR CAMPINSITO" in e.get("analyticEventName", "").upper())
        salidas  = sum(1 for e in eventos if "SALIDA VEHICULAR CAMPINSITO" in e.get("analyticEventName", "").upper())

        if entradas == 0 and salidas == 0:
            return 0  # Nada que registrar

        # ✅ Consultar aforo actual del evento
        cursor.execute("SELECT aforo FROM Aforo_parqueadero_campinsito WHERE evento = ?", (nombre_evento,))
        row = cursor.fetchone()
        aforo_actual = row[0] if row else 0

        # Calcular nuevo aforo acumulado
        nuevo_aforo = aforo_actual + entradas - salidas
        if nuevo_aforo < 0:
            nuevo_aforo = 0

        if row:  
            # Si el evento ya existe → actualizar
            cursor.execute("""
                UPDATE Aforo_parqueadero_campinsito
                SET aforo = ?
                WHERE evento = ?
            """, (nuevo_aforo, nombre_evento))
        else:  
            # Si el evento no existe → insertar
            cursor.execute("""
                INSERT INTO Aforo_parqueadero_campinsito (evento, aforo)
                VALUES (?, ?)
            """, (nombre_evento, nuevo_aforo))

        conn.commit()
        logging.info(f" Aforo actualizado para {nombre_evento}: {nuevo_aforo} (Entradas={entradas}, Salidas={salidas})")
        return 1

    except Exception as e:
        logging.error(" Error guardando aforo del evento: %s", e)
        return 0

def actualizar_aforo_parqueadero_SUR(conn, eventos, nombre_evento):
    """
    Procesa los eventos y actualiza el aforo en la BD por evento (histórico acumulado).
    """
    try:
        cursor = conn.cursor()

        # Contar entradas y salidas en este lote
        entradas = sum(1 for e in eventos if "INGRESO PARQUEADERO SUR" in e.get("analyticEventName", "").upper())
        salidas  = sum(1 for e in eventos if "SALIDA PARQUEADERO SUR" in e.get("analyticEventName", "").upper())

        if entradas == 0 and salidas == 0:
            return 0  # Nada que registrar

        # ✅ Consultar aforo actual del evento
        cursor.execute("SELECT aforo FROM Aforo_parqueadero_SUR WHERE evento = ?", (nombre_evento,))
        row = cursor.fetchone()
        aforo_actual = row[0] if row else 0

        # Calcular nuevo aforo acumulado
        nuevo_aforo = aforo_actual + entradas - salidas
        if nuevo_aforo < 0:
            nuevo_aforo = 0

        if row:  
            # Si el evento ya existe → actualizar
            cursor.execute("""
                UPDATE Aforo_parqueadero_SUR
                SET aforo = ?
                WHERE evento = ?
            """, (nuevo_aforo, nombre_evento))
        else:  
            # Si el evento no existe → insertar
            cursor.execute("""
                INSERT INTO Aforo_parqueadero_SUR (evento, aforo)
                VALUES (?, ?)
            """, (nombre_evento, nuevo_aforo))

        conn.commit()
        logging.info(f" Aforo actualizado ZONA SUR para {nombre_evento}: {nuevo_aforo} (Entradas={entradas}, Salidas={salidas})")
        return 1

    except Exception as e:
        logging.error(" Error guardando aforo del evento: %s", e)
        return 0


#! ==== CONEXIÓN A BASE DE DATOS SQL SERVER ====
def conectar_bd():
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=10.14.15.35;"
            "DATABASE=AVIGILON;"
            "UID=proyectobi3;"
            "PWD=Julio2019**"
        )
        return pyodbc.connect(conn_str, timeout=10)
    except Exception as e:
        logging.error("Error al conectar con la base de datos: %s", e)
        exit(1)

# ==== LEER EVENTO PROGRAMADO DE JSON ====
def leer_evento_programado():
    try:
        with open(EVENTS_JSON, "r", encoding="utf-8") as f:
            eventos = json.load(f)
        hoy = datetime.now(ZoneInfo("America/Bogota")).date().isoformat()
        if hoy in eventos:
            evento = eventos[hoy]
            return evento["nombre"], evento["hora_inicio"], evento["hora_fin"]
        else:
            logging.warning("No hay evento programado para hoy.")
            return None, None, None
    except Exception as e:
        logging.error("Error al leer eventos JSON: %s", e)
        return None, None, None

# ==== CONSULTAR CÁMARAS DESDE ARCHIVO JSON ====
def cargar_ids_camaras(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error("Error cargando cámaras desde archivo: %s", e)
        exit(1)

# ==== CONSULTAR EVENTOS DE UNA CÁMARA ====
def fetch_events(camera_id, start, end, SESSION_TOKEN):

    headers = {
        "session": SESSION_TOKEN,
        "x-avg-session": SESSION_TOKEN,
        "Content-Type": "application/json"
    }
    params = {
        "queryType": "TIME_RANGE",
        "serverId": SERVER_ID,
        "from": start.isoformat().replace("+00:00", "Z"),
        "to": end.isoformat().replace("+00:00", "Z"),
        "eventTopics": "DEVICE_ANALYTICS_STOP",
        "deviceIds": camera_id,
        "limit": 1000
    }

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, verify=False, timeout=30)
        response.raise_for_status()
        return response.json().get("result", {}).get("events", [])
    except requests.RequestException as e:
        logging.error("Error al consultar eventos de la cámara %s: %s", camera_id, e)
        return []

# ==== INSERTAR EVENTOS EN BASE DE DATOS ====
def insertar_eventos(conn, eventos, nombre_evento):
    nuevos = 0
    try:
        cursor = conn.cursor()
        for e in eventos:
            nombre_analitica = e.get("analyticEventName", "").upper()
            if not (
                "PUERTA" in nombre_analitica
                or "AFORO ENTRADA SENCIA" in nombre_analitica
                or nombre_analitica == "INGRESO PERSONAS ENTRADA MARATON"
            ):
                continue
            try:
                timestamp_colombia = datetime.fromisoformat(
                    e.get("timestamp").replace("Z", "+00:00")
                    ).astimezone(ZoneInfo("America/Bogota"))
                cursor.execute("""
                    INSERT INTO eventos_Analisis (
                        analyticEventName, area, activity, cameraId, timestamp, nombre_evento
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    e.get("analyticEventName"),
                    e.get("area"),
                    e.get("activity"),
                    e.get("cameraId"),
                    timestamp_colombia,
                    nombre_evento
                ))
                nuevos += 1
            except Exception as err:
                logging.error("Error insertando evento: %s", err)
        conn.commit()
    except pyodbc.OperationalError as err:
        logging.error("Conexión perdida con la base de datos: %s", err)
        raise err
    return nuevos

# ==== MONITOREO EN TIEMPO REAL ====
def ejecutar_en_tiempo_real(nombre_evento, hora_fin_evento,SESSION_TOKEN):
    conn = conectar_bd()
    camera_ids = cargar_ids_camaras(CAMERA_FILE)
    logging.info(f"Cargando {len(camera_ids)} cámaras permitidas")
    local_tz = ZoneInfo("America/Bogota")
    ultima_fecha_por_camara = {
        cam: datetime.now(local_tz) - timedelta(seconds=INTERVAL_SECONDS)
        for cam in camera_ids
    }
    total_insertados = 0

    logging.info("Iniciando monitoreo...\n")
    try:
        while True:
            ahora = datetime.now(local_tz)
            if ahora.time() > hora_fin_evento:
                logging.info("Fin del evento '%s' a las %s", nombre_evento, hora_fin_evento)
                break

            vuelta_inicio = time.time()
            for cam in camera_ids:
                insertados_camara = 0
                start_local = ultima_fecha_por_camara[cam]
                end_local = start_local + timedelta(seconds=INTERVAL_SECONDS)
                start_utc = start_local.astimezone(ZoneInfo("UTC"))
                end_utc = end_local.astimezone(ZoneInfo("UTC"))

                logging.info("Cámara %s  %s a %s (consulta %s)", cam, start_utc, end_utc, ahora.strftime('%H:%M:%S'))

                while True:
                    eventos = fetch_events(cam, start_utc, end_utc,SESSION_TOKEN)
                    if not eventos:
                        break
#16:04:16)
                    try:
                        nuevos = insertar_eventos(conn, eventos, nombre_evento)
                        actualizar_aforo_parqueadero(conn, eventos, nombre_evento)
                        actualizar_aforo_parqueadero_Campinsito(conn, eventos, nombre_evento)
                        actualizar_aforo_parqueadero_SUR(conn, eventos, nombre_evento)

                    except pyodbc.OperationalError:
                        logging.warning("Reintentando conexión...")
                        conn.close()
                        time.sleep(3)
                        conn = conectar_bd()
                        continue

                    insertados_camara += nuevos
                    total_insertados += nuevos

                    if len(eventos) < 1000:
                        break
                    else:
                        ultimo_ts = eventos[-1]['timestamp']
                        try:
                            start_utc = datetime.fromisoformat(ultimo_ts.replace("Z", "+00:00")) + timedelta(milliseconds=1)
                        except Exception as e:
                            logging.warning("Error de timestamp: %s", e)
                            break

                logging.info("Cámara %s: %d nuevos eventos | Total acumulado: %d", cam, insertados_camara, total_insertados)
                ultima_fecha_por_camara[cam] = end_local

            vuelta_duracion = time.time() - vuelta_inicio
            logging.info("Vuelta completada en %.2f segundos", vuelta_duracion)
            tiempo_espera = INTERVAL_SECONDS - vuelta_duracion
            if tiempo_espera > 0:
                time.sleep(tiempo_espera)

    except KeyboardInterrupt:
        logging.info("Detenido por el usuario.")
    finally:
        conn.close()

# ==== EJECUCIÓN PRINCIPAL ====
if __name__ == "__main__":
    while True:
        nombre_evento, hora_inicio_str, hora_fin_str = leer_evento_programado()

        if not nombre_evento:
            logging.info("No se encontró evento para hoy, reintentando en 30s...")
            time.sleep(30)
            continue

        hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
        hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()
        ahora = datetime.now(ZoneInfo("America/Bogota")).time()

        # Si ya pasó la hora de inicio, arranca
        if ahora >= hora_inicio:
            logging.info("Evento '%s' detectado. Iniciando monitoreo...", nombre_evento)
            break
        
        # Si aún no ha llegado la hora, espera poco tiempo y vuelve a verificar
        logging.info("Esperando inicio del evento '%s' a las %s (ahora son %s)...", 
                     nombre_evento, hora_inicio, ahora)
        time.sleep(30)  # Revisa cada 30s si la hora cambió
        

    # Refrescar datos antes de iniciar (por si los modificaron mientras esperabas)
    nombre_evento, hora_inicio_str, hora_fin_str = leer_evento_programado()
    hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
    hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()

    #! Generación del token de sesión
    user_nonce = "001OK00000Nssnn"
    user_key = "d18324f4d034ee54a77ee92fbf7547b0f4a0c32fb952ca595f6a1810bf6a02ed"
    integration_id = ""
    SESSION_TOKEN = generate_auth_token(user_nonce, user_key, integration_id)

    if not SESSION_TOKEN:
        logging.error("No se pudo generar el token de sesión.")
        exit(1)

    #* Ejecutar el monitoreo en tiempo real
    ejecutar_en_tiempo_real(nombre_evento, hora_fin, SESSION_TOKEN)
