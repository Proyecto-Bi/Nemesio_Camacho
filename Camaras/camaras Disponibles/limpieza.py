import json

# 1. Cargar IDs de cámaras permitidas
with open("ids_camaras_permitidas.json", "r", encoding="utf-8") as f:
    camaras_permitidas = set(json.load(f))  # usamos un set para búsqueda rápida

# 2. Cargar eventos originales
with open("eventos_avigilon.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. Palabras clave que indican conteo de vehículos
palabras_vehiculo = ["VEHICULOS", "vehiculo", "carro", "camión", "camion", "auto", "moto"]

# 4. Filtrar eventos
eventos_filtrados = []
for evento in data:
    activity = evento.get("activity", "")
    name = evento.get("analyticEventName", "").lower()
    area = evento.get("area", "").lower()
    camera_id = evento.get("cameraId", "")

    if (
        activity == "OBJECT_COUNTING_ENTER"
        and not any(p in name or p in area for p in palabras_vehiculo)
        and camera_id in camaras_permitidas
    ):
        eventos_filtrados.append({
            "analyticEventName": evento.get("analyticEventName"),
            "area": evento.get("area"),
            "cameraId": camera_id
        })

# 5. Guardar resultado
with open("eventos_personas_filtrados.json", "w", encoding="utf-8") as f:
    json.dump(eventos_filtrados, f, indent=2, ensure_ascii=False)

print(f"✅ Se guardaron {len(eventos_filtrados)} eventos filtrados en 'eventos_personas_filtrados.json'")
