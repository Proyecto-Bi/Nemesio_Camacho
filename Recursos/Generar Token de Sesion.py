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



def generate_auth_token(user_nonce, user_key, integration_id=None):

    #* Obtener el timestamp actual en formato Unix
    timestamp = str(int(time.time()))
    hash_input = timestamp + user_key
    hex_encoded = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    #* Construir el token
    token_parts = [user_nonce, timestamp, hex_encoded]
    Authorization_Token = ":".join(token_parts)
    print(f"Authorization Token: {Authorization_Token}")

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

user_nonce = "001OK00000Nssnn"
user_key = "d18324f4d034ee54a77ee92fbf7547b0f4a0c32fb952ca595f6a1810bf6a02ed"
integration_id = ""
SESSION_TOKEN = generate_auth_token(user_nonce, user_key, integration_id)
print(f"Token de sesión generado: {SESSION_TOKEN}")