import hmac
import hashlib

import hashlib
import time

def generate_auth_token(user_nonce, user_key, integration_id=None):

    # Obtener el timestamp actual en formato Unix
    timestamp = str(int(time.time()))
    hash_input = timestamp + user_key
    hex_encoded = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    # Construir el token
    token_parts = [user_nonce, timestamp, hex_encoded]
    if integration_id:
        token_parts.append(integration_id)
    
    return ":".join(token_parts)

# Ejemplo de uso
user_nonce = "001OK00000Nssnn"
user_key = "d18324f4d034ee54a77ee92fbf7547b0f4a0c32fb952ca595f6a1810bf6a02ed"
integration_id = ""

SESSION_TOKEN = generate_auth_token(user_nonce, user_key, integration_id)
print("Token generado:", SESSION_TOKEN)