# 📘 Monitoreo de Eventos Avigilon – Procesamiento en Tiempo Real (API REST + SQL Server)

Este proyecto implementa un sistema de monitoreo en tiempo real para eventos generados por cámaras Avigilon, procesando aforo, entradas, salidas y analíticas específicas, almacenando los datos en SQL Server para reporting y control operativo.

---

# 🏗️ Arquitectura General

El sistema está compuesto por:

- **API REST Avigilon ACC** – Consulta de eventos por cámara.
- **Python** – Lógica principal de consulta y persistencia.
- **SQL Server** – Base de datos para aforo y eventos históricos.
- **Archivos JSON** – Configuración de cámaras y agenda de eventos.
- **Logging Rotativo** – Archivo persistente de 10 MB con rotación automática.

## 📁 Estructura del proyecto

registro de Personas Nemesio Camacho.py
ids_camaras_permitidas.json
eventos_programados.json
Monitoreo nemesio camacho.log
README.md


---

### 📅 Evento Programado

El sistema lee automáticamente el evento del día desde:

eventos_programados.json


Ejemplo:

```json
{
  "2025-01-20": {
    "nombre": "Evento Prueba",
    "hora_inicio": "16:00",
    "hora_fin": "23:00"
  }
}
```
El script detecta:

Nombre del evento

Hora de inicio

Hora de fin

Y mantiene el monitoreo activo en ese intervalo.

### 🔐 Autenticación Avigilon
Para consultas a la API Avigilon se genera un token de sesión temporal, utilizando:

Nonce

Timestamp

Llave secreta

SHA-256

Ejemplo:

session_token = generate_auth_token(user_nonce, user_key, integration_id)
Si el token no se genera → el monitoreo no inicia.

### 🎥 Carga de Cámaras Permitidas
Las cámaras permitidas se definen en:

ids_camaras_permitidas.json
Ejemplo:

```json
Copiar código
[
  "4xIx1DMwMLSwMDW1TElKTtVLTsw1MBAS-MCsnHlRxLVo_edbC5f85NIAAA",
  "4xIx1DMwMLSwMDW1TElKTdJLTsw1MBAS-MCsnHlRxLVo_edbC5f85NIAAA",
  "4xIx1DMwMLSwMDW1TElOMtVLTsw1MBAS-MCsnHlRxLVo_edbC5f85NIAAA"
]
```
### 🔄 Flujo General del Sistema

1. Leer evento del día (eventos_programados.json)
2. Generar token de sesión Avigilon
3. Cargar cámaras permitidas
4. Bucle en tiempo real hasta hora_fin:
      ├── Consultar eventos (API REST)
      ├── Insertar en tabla eventos_Analisis
      ├── Actualizar aforo PARQUEADERO NORTE
      ├── Actualizar aforo CAMPINSITO
      └── Actualizar aforo ZONA SUR
📡 Consulta de Eventos (API REST)
Cada cámara se consulta en intervalos cortos:

fetch_events(camera_id, start, end, session_token)
Parámetros:

from – Timestamp inicio

to – Timestamp fin

eventTopics = DEVICE_ANALYTICS_STOP

limit = 1000

Si recibe 1000 eventos → continúa paginando.

## 🗄️ Inserción en Base de Datos
Cada evento válido se almacena en:
eventos_Analisis
Campos:
analyticEventName
area
activity
cameraId
timestamp (hora local Colombia)
nombre del evento

Ejemplo SQL:

INSERT INTO eventos_Analisis
(analyticEventName, area, activity, cameraID, timestamp, nombre_evento)
VALUES (...)

🚪 Actualización de Aforos
El sistema maneja tres zonas independientes:

PARQUEADERO NORTE

CAMPINSITO

ZONA SUR

Tablas:

* Aforo_parqueadero
* Aforo_parqueadero_campinsito
* Aforo_parqueadero_SUR

Proceso:

Si existe registro → UPDATE
Si no existe      → INSERT
🪵 Logging
Logging rotativo:


LOG_FILENAME = "Monitoreo nemesio camacho.log"
RotatingFileHandler(maxBytes=10_000_000, backupCount=5)
Registra:

Errores

Procesos completados

Número de eventos consultados

SQL ejecutado

Inicio/fin del monitoreo

▶️ Ejecución

#🛠 Requisitos
```
Python 3.10+

ODBC Driver 17 for SQL Server

Acceso a la API Avigilon

Credenciales de SQL Server

Archivos JSON configurados correctamente
```
