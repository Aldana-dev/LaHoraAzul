# app/routes/pago_api.py
from flask import Blueprint, request, jsonify
import requests

pago_bp = Blueprint("pago", __name__)

@pago_bp.route("/crear", methods=["POST"])
def crear_pago():
    """
    Recibe un JSON con 'amount' y envía la solicitud al servicio Node.js
    """
    data = request.get_json()
    if not data or "amount" not in data:
        return jsonify({"error": "Falta el campo 'amount'"}), 400

    try:
        response = requests.post(
            "http://localhost:3001/create-payment-intent",
            json={
                "amount": data["amount"],
                "currency": "usd"
            },
            timeout=5
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Error al comunicarse con el servicio de pagos", "details": str(e)}), 500

    return jsonify(response.json())


@pago_bp.route("/estado", methods=["POST"])
def estado_pago():
    """
    Recibe un JSON con 'payment_id' y consulta el estado en Node.js
    """
    data = request.get_json()
    if not data or "payment_id" not in data:
        return jsonify({"error": "Falta el campo 'payment_id'"}), 400

    try:
        response = requests.post(
            "http://localhost:3001/payment-status",
            json={"payment_id": data["payment_id"]},
            timeout=5
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Error al comunicarse con el servicio de pagos", "details": str(e)}), 500

    return jsonify(response.json())
