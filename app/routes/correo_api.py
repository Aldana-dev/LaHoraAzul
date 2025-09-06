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


def ensure_token():
    """Renueva el token si no existe."""
    global auth_token
    if not auth_token:
        auth_token = get_auth_token()
        if not auth_token:
            return False
    return True


@correo_bp.route("/cotizar_envio", methods=["POST"])
def cotizar_envio():
    """Recibe datos del envío, consulta la API MiCorreo y devuelve la cotización."""
    datos = request.json

    if not ensure_token():
        return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/rates"

    try:
        response = requests.post(url, json=datos, headers=headers)

        if response.status_code == 401:
            # Renovar token y reintentar
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.post(url, json=datos, headers=headers)

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@correo_bp.route("/sucursales", methods=["GET"])
def consultar_sucursales():
    """Devuelve la lista de sucursales de MiCorreo."""
    if not ensure_token():
        return jsonify({"error": "No se pudo obtener token"}), 500

    customer_id = request.args.get("customerId")
    province_code = request.args.get("provinceCode")

    if not customer_id or not province_code:
        return jsonify({"error": "Se requiere customerId y provinceCode"}), 400

    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{BASE_URL}/agencies"

    try:
        params = {"customerId": customer_id, "provinceCode": province_code}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 401:
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.get(url, headers=headers, params=params)

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@correo_bp.route("/importar_envio", methods=["POST"])
def importar_envio():
    """Recibe los datos del envío y lo registra en MiCorreo."""
    datos = request.json

    if not ensure_token():
        return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/shipping/import"

    try:
        response = requests.post(url, json=datos, headers=headers)

        if response.status_code == 401:
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.post(url, json=datos, headers=headers)

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@correo_bp.route("/seguimiento", methods=["GET"])
def obtener_seguimiento():
    """Devuelve el estado de un envío por su número de tracking."""
    tracking_number = request.args.get("shippingId")
    if not tracking_number:
        return jsonify({"error": "Se requiere shippingId"}), 400

    if not ensure_token():
        return jsonify({"error": "No se pudo obtener token"}), 500

    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{BASE_URL}/shipping/tracking"
    payload = {"shippingId": tracking_number}

    try:
        response = requests.get(url, headers=headers, json=payload)

        if response.status_code == 401:
            get_auth_token()
            headers["Authorization"] = f"Bearer {auth_token}"
            response = requests.get(url, headers=headers, json=payload)

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
