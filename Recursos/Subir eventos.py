import pandas as pd
import sqlalchemy as sa
import pyodbc
import os

# ==============================
# CONFIGURACIÓN
# ==============================
EXCEL_PATH = r"C:\Users\jcuadros.MELTEC\Desktop\Campin\Recursos\carin leon.xlsx"
NOMBRE_TABLA = "eventos_Analisis"

SERVER = '10.14.15.35'
DATABASE = 'AVIGILON'
USERNAME = 'proyectobi3'
PASSWORD = 'Julio2019**'

# ==============================
# LEER ARCHIVO
# ==============================
if not os.path.exists(EXCEL_PATH):
    raise FileNotFoundError(f"No se encontró el archivo: {EXCEL_PATH}")

df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
print(f"Archivo Excel cargado con {len(df)} registros.")

# ==============================
# LIMPIAR Y CONVERTIR CAMPOS
# ==============================
# Forzamos que todos los campos string sean string y rellenamos NaN
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].fillna('').astype(str)

# ==============================
# CONEXIÓN
# ==============================
connection_string = (
    f"mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
)

# ==============================
# TIPOS EXPLÍCITOS PARA SQL SERVER
# ==============================
from sqlalchemy.types import NVARCHAR, Integer, DateTime

sql_types = {
    "id": Integer(),
    "eventTime": DateTime(),
    "activity": NVARCHAR(100),
    "analyticEventName": NVARCHAR(255),
    "area": NVARCHAR(255),
    "cameraId": NVARCHAR(100),
    "nombre_evento": NVARCHAR(255),
}

# ==============================
# SUBIR DATOS
# ==============================
try:
    engine = sa.create_engine(connection_string, fast_executemany=True)
    with engine.begin() as conn:
        df.to_sql(NOMBRE_TABLA, conn, if_exists='append', index=False, dtype=sql_types, method='multi')
        print(f"Datos insertados en la tabla {NOMBRE_TABLA} correctamente.")
except Exception as e:
    print("Error al subir los datos:", e)
