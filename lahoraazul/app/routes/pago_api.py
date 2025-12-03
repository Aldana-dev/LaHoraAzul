from flask import Blueprint, request, jsonify, current_app
import requests
import uuid
import hashlib
from datetime import datetime


pago_bp = Blueprint("pago", __name__, url_prefix="/pago")


def get_node_api_url():
    return current_app.config.get("NODE_API_URL")


def get_api_key():
    return current_app.config.get("API_KEY")


@pago_bp.route("/crear", methods=["POST"])
def crear_pago():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "error": "No se recibieron datos"
            }), 400

        required_fields = ["amount", "token", "user_id", "bin", "description"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "error": "Faltan campos obligatorios",
                "missing_fields": missing_fields
            }), 400

        if not isinstance(data["amount"], (int, float)) or data["amount"] <= 0:
            return jsonify({
                "status": "error",
                "error": "El monto debe ser un número positivo"
            }), 400

        if not isinstance(data["bin"], str) or len(data["bin"]) != 6:
            return jsonify({
                "status": "error",
                "error": "El BIN debe ser una cadena de 6 dígitos"
            }), 400

        nombre = data.get("nombre", "cliente")
        apellido = data.get("apellido", "")
        
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        nombre_clean = ''.join(c if c.isalnum() else '' for c in nombre.lower())[:10]
        site_transaction_id = f"txn_{nombre_clean}_{timestamp}"

        payload = {
            "amount": int(data["amount"]),
            "token": str(data["token"]),
            "user_id": str(data["user_id"]),
            "bin": str(data["bin"]),
            "description": str(data["description"]),
            "site_transaction_id": site_transaction_id
        }

        node_api_url = get_node_api_url()
        api_key = get_api_key()
        
        if not api_key:
            return jsonify({
                "status": "error",
                "error": "Configuración del servidor incorrecta"
            }), 500

        print(f"[DEBUG] NODE_API_URL: {node_api_url}")
        print(f"[DEBUG] API_KEY: {api_key[:20]}..." if api_key else "[DEBUG] API_KEY: None")
        print(f"[DEBUG] Site Transaction ID: {site_transaction_id}")
        print(f"[DEBUG] Payload enviado a Node.js: {payload}")

        response = requests.post(
            f"{node_api_url}/create-payment-intent",
            json=payload,
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json"
            },
            timeout=30
        )

        print(f"[DEBUG] Respuesta de Node.js - Status: {response.status_code}")
        print(f"[DEBUG] Respuesta de Node.js - Content: {response.text}")

        response.raise_for_status()
        result = response.json()

        payment_status = result.get("status", "").lower()

        if payment_status == "approved":
            return jsonify({
                "status": "approved",
                "message": "Pago aprobado exitosamente",
                "payment_id": result.get("payment_id"),
                "ticket": result.get("ticket"),
                "authorization_code": result.get("authorization_code"),
                "amount": result.get("amount"),
                "currency": result.get("currency"),
                "card_brand": result.get("card_brand"),
                "installments": result.get("installments")
            }), 200

        elif payment_status == "rejected":
            return jsonify({
                "status": "rejected",
                "message": result.get("message", "Pago rechazado"),
                "error_code": result.get("error_code"),
                "error_reason": result.get("error_reason")
            }), 400

        elif payment_status == "pending" or payment_status == "pre_approved":
            return jsonify({
                "status": "pending",
                "message": "Pago pendiente de aprobación",
                "payment_id": result.get("payment_id")
            }), 202

        else:
            return jsonify({
                "status": "error",
                "message": "Estado de pago desconocido",
                "details": result
            }), 500

    except requests.exceptions.Timeout:
        print("[ERROR] Timeout en comunicación con Node.js")
        return jsonify({
            "status": "error",
            "error": "Timeout al procesar el pago",
            "message": "La solicitud tardó demasiado tiempo. Intente nuevamente."
        }), 504

    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Error de conexión con Node.js: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Error de conexión",
            "message": "No se pudo conectar con el servidor de pagos"
        }), 503

    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP Error: {str(e)}")
        try:
            error_data = e.response.json()
        except:
            error_data = {"error": str(e)}
        
        return jsonify({
            "status": "error",
            "error": "Error en el procesamiento del pago",
            "details": error_data
        }), e.response.status_code if e.response else 500

    except Exception as e:
        print(f"[ERROR] Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": "Error interno del servidor",
            "message": str(e)
        }), 500

@pago_bp.route("/devolucion", methods=["POST"])
def devolucion_pago():
    try:
        data = request.get_json()
        
        if not data or "payment_id" not in data:
            return jsonify({
                "status": "error",
                "error": "Falta el campo 'payment_id'"
            }), 400

        payment_id = data["payment_id"]
        node_api_url = get_node_api_url()
        api_key = get_api_key()

        response = requests.post(
            f"{node_api_url}/refund",
            json={"payment_id": payment_id},
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json"
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()
        
        return jsonify({
            "status": "success",
            "message": "Devolución procesada exitosamente",
            "data": result
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "error": "Error al procesar la devolución",
            "details": str(e)
        }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "Error interno del servidor"
        }), 500


@pago_bp.route("/test", methods=["GET"])
def test_conexion():
    try:
        node_api_url = get_node_api_url()
        api_key = get_api_key()

        if not api_key:
            return jsonify({
                "status": "error",
                "message": "API_KEY no configurada"
            }), 500

        response = requests.get(
            f"{node_api_url}/health",
            timeout=5
        )

        response.raise_for_status()
        result = response.json()

        return jsonify({
            "status": "ok",
            "message": "Conexión con Node.js exitosa",
            "node_status": result
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "No se pudo conectar con el servidor Node.js",
            "details": str(e)
        }), 500