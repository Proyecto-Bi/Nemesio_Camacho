# Consulta SQL para obtener evento del día actual por Estado (No esta activo)

import pyodbc
from datetime import datetime
conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=10.14.15.35;"
            "DATABASE=AVIGILON;"
            "UID=proyectobi3;"
            "PWD=Julio2019**"
        )
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

hoy = datetime.now().date()

cursor.execute("SELECT nombre, hora_inicio, hora_fin FROM eventos WHERE fecha = ? AND estado_evento = 'Activo'", hoy)
fila = cursor.fetchone()

if fila:
    nombre_evento, hora_inicio, hora_fin = fila
    print(nombre_evento, hora_inicio, hora_fin)
else:
    print("No hay evento programado para hoy.")
