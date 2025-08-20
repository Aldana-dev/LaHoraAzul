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
    url = f"{BASE_URL}/token"
    try:
        response = requests.post(url, auth=(MICORREO_USER, MICORREO_PASSWORD))
        response.raise_for_status()
        data = response.json()
        auth_token = data.get("token")
        return auth_token
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo token: {e}")
        return None

@correo_bp.route("/cotizar_envio", methods=["POST"])
def cotizar_envio():
    """Recibe datos del envío, consulta la API MiCorreo y devuelve la cotización."""
    global auth_token
    datos = request.json

    if not auth_token:
        auth_token = get_auth_token()
        if not auth_token:
            return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/rates"

    try:
        response = requests.post(url, json=datos, headers=headers)

        # Si el token expiró, lo renovamos y reintentamos
        if response.status_code == 401:
            auth_token = get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.post(url, json=datos, headers=headers)

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@correo_bp.route("/sucursales", methods=["GET"])
def consultar_sucursales():
    """Devuelve la lista de sucursales de MiCorreo."""
    global auth_token
    if not auth_token:
        auth_token = get_auth_token()
        if not auth_token:
            return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{BASE_URL}/branches"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            auth_token = get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.get(url, headers=headers)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@correo_bp.route("/importar_envio", methods=["POST"])
def importar_envio():
    """Recibe los datos del envío y lo registra en MiCorreo."""
    global auth_token
    datos = request.json

    if not auth_token:
        auth_token = get_auth_token()
        if not auth_token:
            return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/shipments"

    try:
        response = requests.post(url, json=datos, headers=headers)
        if response.status_code == 401:
            auth_token = get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.post(url, json=datos, headers=headers)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@correo_bp.route("/seguimiento/<tracking_number>", methods=["GET"])
def obtener_seguimiento(tracking_number):
    """Devuelve el estado de un envío por su número de tracking."""
    global auth_token
    if not auth_token:
        auth_token = get_auth_token()
        if not auth_token:
            return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{BASE_URL}/tracking/{tracking_number}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            auth_token = get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.get(url, headers=headers)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
