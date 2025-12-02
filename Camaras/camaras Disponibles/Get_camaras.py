import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === CONFIGURACIÓN ===
SESSION_TOKEN = "AYEAfv8KECQfxZLmdk46pXLneJoeIMgSFgoUd6flvY7vgThvR8PaGOhheSWdVc4aEA0b2xVHBUgUjzzVgshkHtkiEAFWznZOdknilSFjBP_wUUkqDlBydWViYVBvc3RtYW4yMiEaEE2erIRywEb_v4iN8kVXy1cqDWFkbWluaXN0cmF0b3I"
BASE_URL = "https://10.16.203.10:8443/mt/api/rest/v1/cameras"

# === CONSULTA GET ===
headers = {
    "x-avg-session": SESSION_TOKEN
}

response = requests.get(BASE_URL, headers=headers, verify=False, timeout=20)
response.raise_for_status()

# === EXTRAER Y GUARDAR DATOS ===
cameras_data = response.json().get("result", {}).get("cameras", [])

with open("camaras_avigilonV2.json", "w", encoding="utf-8") as f:
    json.dump(cameras_data, f, ensure_ascii=False, indent=4)

print(f"✅ Se guardaron {len(cameras_data)} cámaras en 'camaras_avigilonV2.json'")
