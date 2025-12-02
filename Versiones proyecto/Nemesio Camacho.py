#Codigo, funcional, para tomar eventos de un Json, ejecutar el archivo en tiempo real,
#  hasta acabar el evento y guarda en una BD


import requests
import json
import urllib3
import pyodbc
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== CONFIGURACIÓN GENERAL ====
SESSION_TOKEN = "AYEAfv8KECQfxZLmdk46pXLneJoeIMgSFgoU-kwtxAMUYaH60afg6rydeMMEmBUaEFubcGdOXkLog7lzCWug_AYiEAFWznZOdknilSFjBP_wUUkqDlBydWViYVBvc3RtYW4yMiEaEE2erIRywEb_v4iN8kVXy1cqDWFkbWluaXN0cmF0b3I"
SERVER_ID     = "8AMjadEURXKv89qhpPkKKA"
BASE_URL = "https://10.16.203.10:8443/mt/api/rest/v1/events/search"
CAMERA_FILE = "ids_camaras_permitidas.json"
EVENTS_JSON = "eventos_programados.json"
INTERVAL_SECONDS = 60

# ==== CONEXIÓN A BASE DE DATOS SQL SERVER ====
def conectar_bd():
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=190.60.210.149;"
            "DATABASE=AVIGILON;"
            "UID=proyectobi3;"
            "PWD=Julio2019**"
        )
        return pyodbc.connect(conn_str, timeout=10)
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
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
            print("📭 No hay evento programado para hoy.")
            return None, None, None
    except Exception as e:
        print(f"❌ Error al leer eventos JSON: {e}")
        return None, None, None

# ==== CONSULTAR CÁMARAS DESDE ARCHIVO JSON ====
def cargar_ids_camaras(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando cámaras desde archivo: {e}")
        exit(1)

# ==== CONSULTAR EVENTOS DE UNA CÁMARA ====
def fetch_events(camera_id, start, end):
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
        print(f"❌ Error al consultar eventos de la cámara {camera_id}: {e}")
        return []

# ==== INSERTAR EVENTOS EN BASE DE DATOS ====
def insertar_eventos(conn, eventos, nombre_evento):
    nuevos = 0
    try:
        cursor = conn.cursor()
        for e in eventos:
            nombre_analitica = e.get("analyticEventName", "").upper()
            if "PUERTA" not in nombre_analitica:
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
                print("❌ Error insertando evento:", err)
        conn.commit()
    except pyodbc.OperationalError as err:
        print("🔌 ❗ Conexión perdida con la base de datos.")
        raise err
    return nuevos

# ==== MONITOREO EN TIEMPO REAL ====
def ejecutar_en_tiempo_real(nombre_evento, hora_fin_evento):
    conn = conectar_bd()
    camera_ids = cargar_ids_camaras(CAMERA_FILE)
    print(f"📸 Cargando {len(camera_ids)} cámaras permitidas")
    local_tz = ZoneInfo("America/Bogota")
    ultima_fecha_por_camara = {
        cam: datetime.now(local_tz) - timedelta(seconds=INTERVAL_SECONDS)
        for cam in camera_ids
    }
    total_insertados = 0

    print("🚀 Iniciando monitoreo...\n")
    try:
        while True:
            ahora = datetime.now(local_tz)
            if ahora.time() > hora_fin_evento:
                print(f"⏹️ Fin del evento '{nombre_evento}' a las {hora_fin_evento}")
                break

            vuelta_inicio = time.time()
            for cam in camera_ids:
                insertados_camara = 0
                start_local = ultima_fecha_por_camara[cam]
                end_local = start_local + timedelta(seconds=INTERVAL_SECONDS)
                start_utc = start_local.astimezone(ZoneInfo("UTC"))
                end_utc = end_local.astimezone(ZoneInfo("UTC"))

                print(f"⏱️ Cámara {cam} → {start_utc} a {end_utc} (consulta {ahora.strftime('%H:%M:%S')})")

                while True:
                    eventos = fetch_events(cam, start_utc, end_utc)
                    if not eventos:
                        break

                    try:
                        nuevos = insertar_eventos(conn, eventos, nombre_evento)
                    except pyodbc.OperationalError:
                        print("🔁 Reintentando conexión...")
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
                            print(f"⚠️ Error de timestamp: {e}")
                            break

                print(f"📊 Cámara {cam}: {insertados_camara} nuevos eventos | Total acumulado: {total_insertados}")
                ultima_fecha_por_camara[cam] = end_local

            vuelta_duracion = time.time() - vuelta_inicio
            print(f"🔁 Vuelta completada en {vuelta_duracion:.2f} segundos")
            tiempo_espera = INTERVAL_SECONDS - vuelta_duracion
            if tiempo_espera > 0:
                time.sleep(tiempo_espera)

    except KeyboardInterrupt:
        print("🛑 Detenido por el usuario.")
    finally:
        conn.close()

# ==== EJECUCIÓN PRINCIPAL ====
if __name__ == "__main__":
    nombre_evento, hora_inicio_str, hora_fin_str = leer_evento_programado()

    if not nombre_evento:
        print("🛑 No se encontró evento para hoy.")
        exit(0)

    hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
    hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()

    ahora = datetime.now(ZoneInfo("America/Bogota")).time()

    if ahora < hora_inicio:
        segundos_espera = (datetime.combine(datetime.today(), hora_inicio) - datetime.now()).total_seconds()
        print(f"⏳ Esperando {segundos_espera:.0f} segundos hasta el inicio del evento '{nombre_evento}'...")
        time.sleep(segundos_espera)
    ejecutar_en_tiempo_real(nombre_evento, hora_fin)
