#! consulta desde una hora a otra con las 17 camaras

import requests
import json
import urllib3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== CONFIGURACIÓN GENERAL ====
SESSION_TOKEN = "AYEAfv8KECQfxZLmdk46pXLneJoeIMgSFgoUigQtR90-s9lVCibh4fb2quEtnQUaEOmeK5VdNE4xtm_U_EOm2iEiEAFWznZOdknilSFjBP_wUUkqDlBydWViYVBvc3RtYW4yMiEaEE2erIRywEb_v4iN8kVXy1cqDWFkbWluaXN0cmF0b3I"
SERVER_ID     = "8AMjadEURXKv89qhpPkKKA"
BASE_URL      = "https://10.16.203.10:8443/mt/api/rest/v1/events/search"
CAMERA_FILE   = "ids_camaras_permitidas.json"

# ==== DEFINIR RANGO DE FECHAS EN HORA LOCAL ====
local_tz = ZoneInfo("America/Bogota")
hora_inicio_local = datetime(2025, 6, 24, 17, 0, 0, tzinfo=local_tz)
hora_fin_local    = datetime(2025, 6, 24, 23, 59, 59, tzinfo=local_tz)

hora_inicio_utc = hora_inicio_local.astimezone(ZoneInfo("UTC"))
hora_fin_utc    = hora_fin_local.astimezone(ZoneInfo("UTC"))

# ==== FUNCIÓN PARA CONSULTAR EVENTOS DE UNA CÁMARA ====
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

# ==== EJECUCIÓN PARA TODAS LAS CÁMARAS ====
if __name__ == "__main__":
    # Cargar lista de cámaras desde el archivo JSON
    with open(CAMERA_FILE, "r", encoding="utf-8") as f:
        camera_ids = json.load(f)

    bloque = timedelta(minutes=1)
    total_general = 0  # ← contador global de eventos

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

        total_general += total_cam  # ← sumar los eventos de esta cámara

        print(f"🧮 Total eventos para cámara {cam}: {total_cam}")
        if eventos_cam:
            print(f"Primer evento: {eventos_cam[0]['timestamp']}")
            print(f"Último evento:  {eventos_cam[-1]['timestamp']}")

    print(f"TOTAL GLOBAL DE EVENTOS EN TODAS LAS CÁMARAS: {total_general}")

