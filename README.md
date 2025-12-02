🎯 Descripción General

Este proyecto permite monitorear en tiempo real los eventos enviados por cámaras Avigilon, procesarlos por intervalos de tiempo y almacenarlos en una base de datos SQL Server.

El sistema:

Lee un evento programado diario desde un archivo JSON.

Obtiene un token de sesión autenticándose contra la API Avigilon.

Consulta múltiples cámaras permitidas.

Procesa eventos de aforo, entradas/salidas y analíticas específicas.

Actualiza tres tablas de aforo según la zona.

Guarda eventos en tabla histórica.

Mantiene logs rotativos (10 MB).

Diseñado para funcionar de forma autónoma hasta el fin del evento.

🧱 Arquitectura del Proceso
eventos_programados.json
          │
          ▼
Lee nombre y horario del evento del día
          │
          ▼
Genera token de sesión Avigilon
          │
          ▼
Carga cámaras permitidas (ids_camaras_permitidas.json)
          │
          ▼
Bucle en tiempo real hasta hora_fin
          │
          ├──► Consulta eventos por cada cámara (API REST)
          │
          ├──► Inserción en tabla eventos_Analisis
          │
          ├──► Actualización aforo PARQUEADERO NORTE
          │
          ├──► Actualización aforo CAMPINSITO
          │
          └──► Actualización aforo ZONA SUR

⚙️ Configuración del Logging

El sistema usa RotatingFileHandler para logs permanentes y consola sincronizada.

LOG_FILENAME = "Monitoreo nemesio camacho.log"
file_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10_000_000, backupCount=5)
console_handler = logging.StreamHandler()
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

📝 Se generan dos tipos de logs:

Consola (INFO)

Archivo rotativo (hasta 5 respaldos de 10 MB)

Incluyen timestamps y niveles de severidad.

🧩 Estructura del Proyecto
📂 monitoreo-aventis-tiempo-real
│
├── monitoreo.py                  # Código principal
├── ids_camaras_permitidas.json  # Lista de cámaras habilitadas
├── eventos_programados.json     # Configuración de evento del día
├── README.md                    # Este archivo
└── Monitoreo nemesio camacho.log (autogenerado)

🛠 Dependencias Principales
requests
pyodbc
urllib3
zoneinfo
logging
hashlib
datetime
json

🔐 Autenticación — Generación de Token

El token Avigilon se forma con:

Nonce

Timestamp

SHA256(nonce + timestamp + key)

session_token = generate_auth_token(user_nonce, user_key, integration_id)


Si falla:
❌ No se permite conexión a la API
❌ No inicia el monitoreo

📡 Lectura del Evento Programado

El sistema carga automáticamente el evento correspondiente a la fecha actual:

{
  "2025-01-20": {
    "nombre": "Concierto A",
    "hora_inicio": "16:00",
    "hora_fin": "23:00"
  }
}


Y lo transforma en:

nombre_evento

hora_inicio

hora_fin

🎥 Carga de Cámaras Permitidas

Define qué cámaras se procesan:

ids_camaras_permitidas.json


Ejemplo:

["CAM123", "CAM998", "CAM441"]

📤 Consulta de Eventos por Cámara

Cada ciclo de monitoreo consulta Avigilon:

fetch_events(camera_id, start, end, session_token)


Parámetros principales:

Rango de tiempo (from, to)

eventTopics: DEVICE_ANALYTICS_STOP

limit: 1000 por lote

Si devuelve 1000 → sigue paginando.

🗄 Inserción de Eventos

Solo se insertan eventos válidos:

"PUERTA"

"AFORO ENTRADA SENCIA"

"INGRESO PERSONAS ENTRADA MARATON"

INSERT INTO eventos_Analisis (...)


Campos incluidos:

analyticEventName

area

activity

cameraId

timestamp (convertido a Bogotá)

nombre_evento

🚗 Actualización de Aforos

El sistema actualiza 3 tablas distintas:

🟦 Parqueadero Norte
🟩 Campinsito
🟥 Zona Sur

Cada una con sus reglas:

UPDATE Aforo_parqueadero
UPDATE Aforo_parqueadero_campinsito
UPDATE Aforo_parqueadero_SUR


Si no existe → INSERT.

🕒 Ejecución en Tiempo Real

El monitoreo inicia en cuanto llega la hora de inicio del evento:

ejecutar_en_tiempo_real(nombre_evento, hora_fin, SESSION_TOKEN)


Operación cíclica:

Procesa todas las cámaras

Inserta eventos

Actualiza aforos

Respeta un intervalo dinámico de 60 segundos (o menos si procesa más rápido)

Finaliza automáticamente al llegar la hora_fin

▶️ Ejecución del Script
python monitoreo.py

🌐 Conexión SQL Server
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=10.14.15.35;
DATABASE=AVIGILON;
UID=proyectobi3;
PWD=********

🪪 Requisitos Previos

Windows Server o Linux

Python 3.10+

ODBC Driver 17 para SQL Server

Red con acceso al servidor Avigilon

Firewall habilitando puerto 8443

📘 Notas Importantes

El script NO se detiene hasta que termina el evento.

Si falla la BD → intenta reconectar automáticamente.

Si una cámara devuelve error → continúa con las demás.

Soporta eventos con alta concurrencia.

El log permite ver paso a paso cada inserción y aforo.
