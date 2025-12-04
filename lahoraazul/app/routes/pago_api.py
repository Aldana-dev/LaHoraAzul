from flask import Blueprint, request, jsonify, current_app
import requests
import uuid
import hashlib
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

pago_bp = Blueprint("pago", __name__, url_prefix="/pago")


def get_node_api_url():
    url = current_app.config.get("NODE_API_URL")
    logger.info(f"🌐 NODE_API_URL obtenida: {url}")
    return url


def get_api_key():
    key = current_app.config.get("API_KEY")
    logger.info(f"🔑 API_KEY obtenida: {key[:20]}..." if key else "🔑 API_KEY: None")
    return key


@pago_bp.route("/crear", methods=["POST"])
def crear_pago():
    logger.info("\n" + "="*60)
    logger.info("💳 RECIBIDA SOLICITUD DE PAGO")
    logger.info("="*60)
    
    try:
        logger.info(f"📥 Headers recibidos: {dict(request.headers)}")
        
        data = request.get_json()
        logger.info(f"📦 Datos JSON recibidos: {data}")
        
        if not data:
            logger.error("❌ No se recibieron datos JSON")
            return jsonify({
                "status": "error",
                "error": "No se recibieron datos"
            }), 400

        required_fields = ["amount", "token", "user_id", "bin", "description"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.error(f"❌ Faltan campos: {missing_fields}")
            return jsonify({
                "status": "error",
                "error": "Faltan campos obligatorios",
                "missing_fields": missing_fields
            }), 400

        logger.info(f"✅ Campos obligatorios presentes")

        # Validar amount
        if not isinstance(data["amount"], (int, float)) or data["amount"] <= 0:
            logger.error(f"❌ Amount inválido: {data['amount']}")
            return jsonify({
                "status": "error",
                "error": "El monto debe ser un número positivo"
            }), 400

        logger.info(f"✅ Amount válido: {data['amount']}")

        # Validar BIN
        if not isinstance(data["bin"], str) or len(data["bin"]) != 6:
            logger.error(f"❌ BIN inválido: {data['bin']} (largo: {len(data.get('bin', ''))})")
            return jsonify({
                "status": "error",
                "error": "El BIN debe ser una cadena de 6 dígitos"
            }), 400

        logger.info(f"✅ BIN válido: {data['bin']}")

        nombre = data.get("nombre", "cliente")
        apellido = data.get("apellido", "")
        
        logger.info(f"📝 Nombre: {nombre}, Apellido: {apellido}")
        
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        nombre_clean = ''.join(c if c.isalnum() else '' for c in nombre.lower())[:10]
        site_transaction_id = f"txn_{nombre_clean}_{timestamp}"

        logger.info(f"🔑 Site Transaction ID generado: {site_transaction_id}")

        payload = {
            "amount": int(data["amount"]),
            "token": str(data["token"]),
            "user_id": str(data["user_id"]),
            "bin": str(data["bin"]),
            "description": str(data["description"]),
            "site_transaction_id": site_transaction_id
        }

        logger.info(f"\n📋 Payload a enviar a Node.js:")
        logger.info(f"   Amount: {payload['amount']}")
        logger.info(f"   Token: {payload['token'][:30]}...{payload['token'][-10:]}")
        logger.info(f"   User ID: {payload['user_id']}")
        logger.info(f"   BIN: {payload['bin']}")
        logger.info(f"   Description: {payload['description']}")
        logger.info(f"   Site Transaction ID: {payload['site_transaction_id']}")

        node_api_url = get_node_api_url()
        api_key = get_api_key()
        
        if not node_api_url:
            logger.error("❌ NODE_API_URL no configurada en Flask")
            return jsonify({
                "status": "error",
                "error": "Configuración del servidor incorrecta: NODE_API_URL"
            }), 500

        if not api_key:
            logger.error("❌ API_KEY no configurada en Flask")
            return jsonify({
                "status": "error",
                "error": "Configuración del servidor incorrecta: API_KEY"
            }), 500

        logger.info(f"\n🔌 Conectando a Node.js:")
        logger.info(f"   URL: {node_api_url}/create-payment-intent")
        logger.info(f"   API Key: {api_key[:20]}...")
        logger.info(f"   Timestamp: {datetime.utcnow().isoformat()}Z")

        response = requests.post(
            f"{node_api_url}/create-payment-intent",
            json=payload,
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json"
            },
            timeout=30
        )

        logger.info(f"\n📬 Respuesta recibida de Node.js:")
        logger.info(f"   Status Code: {response.status_code}")
        logger.info(f"   Timestamp: {datetime.utcnow().isoformat()}Z")
        logger.info(f"   Content-Type: {response.headers.get('content-type')}")
        logger.info(f"   Response Body: {response.text}")

        response.raise_for_status()
        result = response.json()

        logger.info(f"\n✅ JSON parseado exitosamente:")
        logger.info(f"   {result}")

        payment_status = result.get("status", "").lower()
        logger.info(f"📊 Payment Status: {payment_status}")

        if payment_status == "approved":
            logger.info(f"\n🎉 PAGO APROBADO")
            logger.info(f"   Payment ID: {result.get('payment_id')}")
            logger.info(f"   Ticket: {result.get('ticket')}")
            logger.info(f"   Authorization: {result.get('authorization_code')}")
            
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
            logger.warning(f"\n⚠️ PAGO RECHAZADO")
            logger.warning(f"   Error Code: {result.get('error_code')}")
            logger.warning(f"   Error Reason: {result.get('error_reason')}")
            logger.warning(f"   Message: {result.get('message')}")
            
            return jsonify({
                "status": "rejected",
                "message": result.get("message", "Pago rechazado"),
                "error_code": result.get("error_code"),
                "error_reason": result.get("error_reason")
            }), 400

        elif payment_status == "pending" or payment_status == "pre_approved":
            logger.info(f"\n⏳ PAGO PENDIENTE")
            logger.info(f"   Payment ID: {result.get('payment_id')}")
            logger.info(f"   Status: {payment_status}")
            
            return jsonify({
                "status": "pending",
                "message": "Pago pendiente de aprobación",
                "payment_id": result.get("payment_id")
            }), 202

        else:
            logger.error(f"\n❌ ESTADO DESCONOCIDO: {payment_status}")
            logger.error(f"   Respuesta completa: {result}")
            
            return jsonify({
                "status": "error",
                "message": "Estado de pago desconocido",
                "details": result
            }), 500

    except requests.exceptions.Timeout as e:
        logger.error(f"\n❌ TIMEOUT EN COMUNICACIÓN CON NODE.JS")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"   Timeout después de 30 segundos")
        
        return jsonify({
            "status": "error",
            "error": "Timeout al procesar el pago",
            "message": "La solicitud tardó demasiado tiempo. Intente nuevamente.",
            "details": str(e)
        }), 504

    except requests.exceptions.ConnectionError as e:
        logger.error(f"\n❌ ERROR DE CONEXIÓN CON NODE.JS")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"   No se pudo conectar a: {get_node_api_url()}")
        
        return jsonify({
            "status": "error",
            "error": "Error de conexión",
            "message": "No se pudo conectar con el servidor de pagos",
            "details": str(e)
        }), 503

    except requests.exceptions.HTTPError as e:
        logger.error(f"\n❌ ERROR HTTP DE NODE.JS")
        logger.error(f"   Status Code: {e.response.status_code if e.response else 'Unknown'}")
        logger.error(f"   Error: {str(e)}")
        
        try:
            error_data = e.response.json()
            logger.error(f"   Response JSON: {error_data}")
        except:
            logger.error(f"   Response Text: {e.response.text if e.response else 'No response'}")
            error_data = {"error": str(e)}
        
        return jsonify({
            "status": "error",
            "error": "Error en el procesamiento del pago",
            "details": error_data
        }), e.response.status_code if e.response else 500

    except Exception as e:
        logger.error(f"\n❌ ERROR INESPERADO")
        logger.error(f"   Error Type: {type(e).__name__}")
        logger.error(f"   Error Message: {str(e)}")
        
        import traceback
        logger.error(f"   Traceback:\n{traceback.format_exc()}")
        
        return jsonify({
            "status": "error",
            "error": "Error interno del servidor",
            "message": str(e)
        }), 500


@pago_bp.route("/devolucion", methods=["POST"])
def devolucion_pago():
    logger.info("\n" + "="*60)
    logger.info("🔄 RECIBIDA SOLICITUD DE DEVOLUCIÓN")
    logger.info("="*60)
    
    try:
        data = request.get_json()
        logger.info(f"📥 Datos recibidos: {data}")
        
        if not data or "payment_id" not in data:
            logger.error("❌ Falta payment_id")
            return jsonify({
                "status": "error",
                "error": "Falta el campo 'payment_id'"
            }), 400

        payment_id = data["payment_id"]
        logger.info(f"📍 Payment ID: {payment_id}")
        
        node_api_url = get_node_api_url()
        api_key = get_api_key()

        logger.info(f"🔌 Llamando a Node.js: {node_api_url}/refund")

        response = requests.post(
            f"{node_api_url}/refund",
            json={"payment_id": payment_id},
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json"
            },
            timeout=30
        )

        logger.info(f"📬 Respuesta: Status {response.status_code}")

        response.raise_for_status()
        result = response.json()
        
        logger.info(f"✅ Devolución exitosa: {result}")
        
        return jsonify({
            "status": "success",
            "message": "Devolución procesada exitosamente",
            "data": result
        }), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error en solicitud: {str(e)}")
        
        return jsonify({
            "status": "error",
            "error": "Error al procesar la devolución",
            "details": str(e)
        }), 500

    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        return jsonify({
            "status": "error",
            "error": "Error interno del servidor"
        }), 500


@pago_bp.route("/test", methods=["GET"])
def test_conexion():
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST DE CONEXIÓN CON NODE.JS")
    logger.info("="*60)
    
    try:
        node_api_url = get_node_api_url()
        api_key = get_api_key()

        logger.info(f"🔌 URL a probar: {node_api_url}/health")

        if not api_key:
            logger.error("❌ API_KEY no configurada")
            return jsonify({
                "status": "error",
                "message": "API_KEY no configurada"
            }), 500

        logger.info(f"📤 Enviando GET request...")

        response = requests.get(
            f"{node_api_url}/health",
            timeout=5
        )

        logger.info(f"📬 Respuesta recibida:")
        logger.info(f"   Status: {response.status_code}")
        logger.info(f"   Body: {response.text}")

        response.raise_for_status()
        result = response.json()

        logger.info(f"✅ TEST EXITOSO")
        logger.info(f"   Node.js está funcionando correctamente")

        return jsonify({
            "status": "ok",
            "message": "Conexión con Node.js exitosa",
            "node_status": result
        }), 200

    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ NO SE PUDO CONECTAR CON NODE.JS")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"   Verifica que Node.js esté corriendo en: {get_node_api_url()}")
        
        return jsonify({
            "status": "error",
            "message": "No se pudo conectar con el servidor Node.js",
            "details": str(e),
            "node_url": get_node_api_url()
        }), 500

    except Exception as e:
        logger.error(f"❌ ERROR EN TEST")
        logger.error(f"   Error: {str(e)}")
        
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        return jsonify({
            "status": "error",
            "message": "No se pudo conectar con el servidor Node.js",
            "details": str(e)
        }), 500