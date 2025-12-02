#Cosnulta eventos, de un rango a otro, de todas la camaras y las inserta en una base de datos SQL Server.

import requests
import json
import urllib3
import pyodbc
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== CONFIGURACIÓN GENERAL ====
SESSION_TOKEN = "AYEAfv8KECQfxZLmdk46pXLneJoeIMgSFgoUFXDN58_T1k7STJ68WQlxyUc6PskaECed7Vemz0srqLVlQ1pUFTYiEAFWznZOdknilSFjBP_wUUkqDlBydWViYVBvc3RtYW4yMiEaEE2erIRywEb_v4iN8kVXy1cqDWFkbWluaXN0cmF0b3I"
SERVER_ID     = "8AMjadEURXKv89qhpPkKKA"
BASE_URL      = "https://10.16.203.10:8443/mt/api/rest/v1/events/search"
CAMERA_FILE   = "ids_camaras_permitidas.json"

# ==== HORARIO A CONSULTAR EN HORA LOCAL ====
local_tz = ZoneInfo("America/Bogota")
hora_inicio_local = datetime(2025, 6, 24, 15, 0, 0, tzinfo=local_tz)
hora_fin_local    = datetime(2025, 6, 24, 23, 59, 59, tzinfo=local_tz)

hora_inicio_utc = hora_inicio_local.astimezone(ZoneInfo("UTC"))
hora_fin_utc    = hora_fin_local.astimezone(ZoneInfo("UTC"))

# ==== CONEXIÓN A SQL SERVER ====
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
        print(f"Error al conectar con la base de datos: {e}")
        exit(1)

# ==== INSERCIÓN EN BASE DE DATOS ====
def insertar_eventos(conn, eventos):
    nuevos = 0
    try:
        cursor = conn.cursor()
        for e in eventos:
            try:
                cursor.execute("""
                    INSERT INTO eventos_Analisis (
                        analyticEventName, area, activity, cameraId, timestamp, nombre_evento
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    e.get("analyticEventName"),
                    e.get("area"),
                    e.get("activity"),
                    e.get("cameraId"),
                    e.get("timestamp"),
                    e.get("nombre_evento", "Santa Fe VS Medellin") 
                ))
                nuevos += 1
            except Exception as err:
                print("Error insertando evento:", err)
        conn.commit()
    except pyodbc.OperationalError as err:
        print("Conexión perdida con la base de datos.")
        raise err
    return nuevos

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

    resp = requests.get(BASE_URL, headers=headers, params=params, verify=False, timeout=30)
    resp.raise_for_status()
    return resp.json().get("result", {}).get("events", [])

# ==== EJECUCIÓN PRINCIPAL ====
if __name__ == "__main__":
    conn = conectar_bd()
    with open(CAMERA_FILE, "r", encoding="utf-8") as f:
        camera_ids = json.load(f)

    bloque = timedelta(minutes=1)
    total_general = 0

    for cam in camera_ids:
        print(f"Consultando cámara {cam}")
        actual = hora_inicio_utc
        total_cam = 0
        eventos_cam = []

        while actual < hora_fin_utc:
            siguiente = min(actual + bloque, hora_fin_utc)
            try:
                eventos = fetch_events(cam, actual, siguiente)
                eventos_cam.extend(eventos)
                print(f"{cam} → De {actual} a {siguiente} → {len(eventos)} eventos")
                total_cam += len(eventos)
            except Exception as e:
                print(f"Error en cámara {cam}: {e}")
            actual = siguiente

        # Guardar eventos si hay
        if eventos_cam:
            insertados = insertar_eventos(conn, eventos_cam)
            print(f"Insertados en base de datos: {insertados}")

        total_general += total_cam
        if eventos_cam:
            print(f"Primer evento: {eventos_cam[0]['timestamp']}")
            print(f"Último evento:  {eventos_cam[-1]['timestamp']}")

    print(f"TOTAL GLOBAL DE EVENTOS INSERTADOS: {total_general}")
    conn.close()
