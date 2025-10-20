import os
import requests
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

load_dotenv()

correo_bp = Blueprint("correo_api", __name__)

# Configuración
BASE_URL = os.getenv("MICORREO_URL")
MICORREO_USER = os.getenv("MICORREO_USER")
MICORREO_PASSWORD = os.getenv("MICORREO_PASSWORD")

# Cache simple para el token
auth_token = None

def get_auth_token():
    """Obtiene un token JWT de MiCorreo."""
    global auth_token
    print("[DEBUG] Intentando obtener token de autenticación...")
    if not MICORREO_USER or not MICORREO_PASSWORD or not BASE_URL:
        print("[ERROR] Variables de entorno faltantes: MICORREO_URL, MICORREO_USER o MICORREO_PASSWORD")
        return None
    
    url = f"{BASE_URL}/token"
    try:
        print(f"[DEBUG] Enviando POST a {url} con usuario {MICORREO_USER}")
        response = requests.post(url, auth=(MICORREO_USER, MICORREO_PASSWORD))
        response.raise_for_status()
        data = response.json()
        auth_token = data.get("token")
        print(f"[DEBUG] Token obtenido exitosamente: {auth_token[:10]}...")  # Solo primeros 10 chars por seguridad
        return auth_token
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error obteniendo token: {e}")
        return None

def ensure_token():
    """Renueva el token si no existe."""
    global auth_token
    print("[DEBUG] Verificando token...")
    if not auth_token:
        print("[DEBUG] Token no existe, obteniendo nuevo...")
        auth_token = get_auth_token()
        if not auth_token:
            print("[ERROR] No se pudo obtener token")
            return False
    else:
        print("[DEBUG] Token ya existe")
    return True

@correo_bp.route("/cotizar_envio", methods=["POST"])
def cotizar_envio():
    """Recibe datos del envío, consulta la API MiCorreo y devuelve la cotización."""
    print("[DEBUG] Endpoint /cotizar_envio llamado")
    datos = request.json
    print(f"[DEBUG] Datos recibidos del frontend: {datos}")
    
    if not datos:
        print("[ERROR] No se recibieron datos JSON")
        return jsonify({"error": "Datos JSON requeridos"}), 400

    if not ensure_token():
        return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/rates"
    print(f"[DEBUG] Enviando POST a {url} con headers y datos: {datos}")

    try:
        response = requests.post(url, json=datos, headers=headers)
        print(f"[DEBUG] Respuesta de MiCorreo - Status: {response.status_code}, Content: {response.text}")

        if response.status_code == 401:
            print("[DEBUG] Token expirado (401), renovando...")
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.post(url, json=datos, headers=headers)
            print(f"[DEBUG] Reintento - Status: {response.status_code}, Content: {response.text}")

        # Devuelve la respuesta tal cual, incluso si rates está vacío
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error en la solicitud a MiCorreo: {e}")
        return jsonify({"error": str(e)}), 500

@correo_bp.route("/sucursales", methods=["GET"])
def consultar_sucursales():
    """Devuelve la lista de sucursales de MiCorreo."""
    print("[DEBUG] Endpoint /sucursales llamado")
    if not ensure_token():
        return jsonify({"error": "No se pudo obtener token"}), 500

    customer_id = request.args.get("customerId")
    province_code = request.args.get("provinceCode")
    print(f"[DEBUG] Parámetros: customerId={customer_id}, provinceCode={province_code}")

    if not customer_id or not province_code:
        print("[ERROR] Faltan parámetros customerId o provinceCode")
        return jsonify({"error": "Se requiere customerId y provinceCode"}), 400

    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{BASE_URL}/agencies"

    try:
        params = {"customerId": customer_id, "provinceCode": province_code}
        print(f"[DEBUG] Enviando GET a {url} con params: {params}")
        response = requests.get(url, headers=headers, params=params)
        print(f"[DEBUG] Respuesta - Status: {response.status_code}, Content: {response.text}")

        if response.status_code == 401:
            print("[DEBUG] Token expirado, renovando...")
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.get(url, headers=headers, params=params)
            print(f"[DEBUG] Reintento - Status: {response.status_code}, Content: {response.text}")

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error en la solicitud: {e}")
        return jsonify({"error": str(e)}), 500

@correo_bp.route("/importar_envio", methods=["POST"])
def importar_envio():
    """Recibe los datos del envío y lo registra en MiCorreo."""
    print("[DEBUG] Endpoint /importar_envio llamado")
    datos = request.json
    print(f"[DEBUG] Datos recibidos: {datos}")

    if not ensure_token():
        return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/shipping/import"
    print(f"[DEBUG] Enviando POST a {url}")

    try:
        response = requests.post(url, json=datos, headers=headers)
        print(f"[DEBUG] Respuesta - Status: {response.status_code}, Content: {response.text}")

        if response.status_code == 401:
            print("[DEBUG] Token expirado, renovando...")
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.post(url, json=datos, headers=headers)
            print(f"[DEBUG] Reintento - Status: {response.status_code}, Content: {response.text}")

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error en la solicitud: {e}")
        return jsonify({"error": str(e)}), 500

@correo_bp.route("/seguimiento", methods=["GET"])
def obtener_seguimiento():
    """Devuelve el estado de un envío por su número de tracking."""
    print("[DEBUG] Endpoint /seguimiento llamado")
    tracking_number = request.args.get("shippingId")
    print(f"[DEBUG] Parámetro shippingId: {tracking_number}")

    if not tracking_number:
        print("[ERROR] Falta parámetro shippingId")
        return jsonify({"error": "Se requiere shippingId"}), 400

    if not ensure_token():
        return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{BASE_URL}/shipping/tracking"
    payload = {"shippingId": tracking_number}
    print(f"[DEBUG] Enviando GET a {url} con payload: {payload}")

    try:
        response = requests.get(url, headers=headers, json=payload)
        print(f"[DEBUG] Respuesta - Status: {response.status_code}, Content: {response.text}")

        if response.status_code == 401:
            print("[DEBUG] Token expirado, renovando...")
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.get(url, headers=headers, json=payload)
            print(f"[DEBUG] Reintento - Status: {response.status_code}, Content: {response.text}")

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error en la solicitud: {e}")
        return jsonify({"error": str(e)}), 500
