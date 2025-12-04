const express = require("express");
const bodyParser = require("body-parser");
const dotenv = require("dotenv");
const cors = require("cors");

// =========================================
// DEBUG: Cargar SDK
// =========================================

console.log("\n============================================================");
console.log("🧪 DEBUG: Cargando módulo sdk-node-payway");
console.log("============================================================");
console.log("📦 Versión del SDK:", require('sdk-node-payway/package.json').version);

let PaywayModule;
let PaywaySDK;

try {
  // ✅ FORMA CORRECTA según la documentación
  sdk = new PaywaySDK(
    ambient,
    process.env.PUBLIC_KEY,
    process.env.PRIVATE_KEY,
    process.env.COMPANY,
    process.env.USER
  );

  console.log(`\n✅ SDK de Payway inicializado correctamente`);
  console.log("📌 typeof SDK instance:", typeof sdk);
  console.log("📌 SDK es null:", sdk === null);
  console.log("📌 SDK es undefined:", sdk === undefined);
  console.log("📌 SDK value:", sdk);
  
  // 👇 NUEVO: Intenta acceder directamente a los métodos
  console.log("\n🔬 PROBANDO ACCESO A MÉTODOS:");
  console.log("📌 sdk.payment existe:", !!sdk?.payment);
  console.log("📌 typeof sdk.payment:", typeof sdk?.payment);
  console.log("📌 sdk.paymentInfo existe:", !!sdk?.paymentInfo);
  console.log("📌 typeof sdk.paymentInfo:", typeof sdk?.paymentInfo);
  
  if (sdk) {
    console.log("📌 Métodos disponibles:", Object.keys(sdk));
    console.log("📌 Propiedades disponibles:", Object.getOwnPropertyNames(sdk));
    console.log("📌 Prototype:", Object.getPrototypeOf(sdk));
    console.log("📌 Constructor name:", sdk.constructor.name);
  }

  // Validación crítica
  if (!sdk || typeof sdk.payment !== "function") {
    throw new Error("SDK no inicializado correctamente - método payment no disponible");
  }

  console.log("✅ Método payment() detectado correctamente");

} catch (error) {
  console.error(`\n❌ ERROR al inicializar SDK:`);
  console.error(`Mensaje: ${error.message}`);
  console.error(`Stack: ${error.stack}`);
  
  // 👇 NUEVO: Más detalles del error
  console.error(`\n🔍 DEBUG DEL ERROR:`);
  console.error(`Tipo de error:`, typeof error);
  console.error(`Error completo:`, error);
  
  process.exit(1);
}
// =============================================================
// 🔧 EXPRESS CONFIG
// =============================================================

dotenv.config();

const app = express();
app.use(bodyParser.json());
app.use(cors({
  origin: [
    "https://www.horaazul.com",
    "https://www.horaazul.com/carrito",
    "https://www.horaazul.com/modal_compra"
  ],
  credentials: true
}));

const requiredEnvVars = ['PUBLIC_KEY', 'PRIVATE_KEY', 'COMPANY', 'USER'];
const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingVars.length > 0) {
  console.error(`❌ Error: Faltan las siguientes variables de entorno: ${missingVars.join(', ')}`);
  process.exit(1);
}

const ambient = process.env.AMBIENT || "production";

console.log(`\n${'='.repeat(60)}`);
console.log(`🚀 INICIALIZANDO NODE.JS PAYWAY API`);
console.log(`${'='.repeat(60)}`);
console.log(`📋 Configuración:`);
console.log(`   Ambiente: ${ambient}`);
console.log(`   Company: ${process.env.COMPANY}`);
console.log(`   User: ${process.env.USER}`);
console.log(`   Public Key: ${process.env.PUBLIC_KEY.substring(0, 15)}...`);
console.log(`   Private Key: ${process.env.PRIVATE_KEY.substring(0, 15)}...`);
console.log(`   API Key: ${process.env.API_KEY.substring(0, 10)}...`);
console.log(`${'='.repeat(60)}\n`);

// =============================================================
// 🧪 TEST DEL SDK ANTES DE INICIAR SERVIDOR
// =============================================================

console.log("\n============================================================");
console.log("🧪 TESTEANDO SDK ANTES DE INICIAR SERVIDOR");
console.log("============================================================");

// Test 1: Verificar que sdk existe
console.log("Test 1: SDK existe:", !!sdk);

// Test 2: Verificar tipo
console.log("Test 2: typeof sdk:", typeof sdk);

// Test 3: Verificar métodos críticos
const metodosRequeridos = ['payment', 'paymentInfo', 'refund', 'cardTokens', 'healthcheck'];
console.log("\nTest 3: Verificando métodos requeridos:");
metodosRequeridos.forEach(metodo => {
  const existe = sdk && typeof sdk[metodo] === 'function';
  console.log(`  - ${metodo}: ${existe ? '✅' : '❌'}`);
});

// Test 4: Intentar llamar a healthcheck (no requiere parámetros sensibles)
if (sdk && typeof sdk.healthcheck === 'function') {
  console.log("\nTest 4: Probando healthcheck()...");
  try {
    sdk.healthcheck((result, err) => {
      if (err) {
        console.error("❌ Error en healthcheck:", err);
      } else {
        console.log("✅ Healthcheck exitoso:", result);
      }
    });
  } catch (error) {
    console.error("❌ Excepción al llamar healthcheck:", error.message);
  }
}

console.log("============================================================\n");
// =============================================================
// 🔌 INICIALIZAR SDK
// =============================================================

console.log("🔌 Creando instancia del SDK...");

let sdk = null;

try {
  // ✅ FORMA CORRECTA según la documentación
  sdk = new PaywaySDK(
    ambient,                    // "production" o "developer"
    process.env.PUBLIC_KEY,     // public key
    process.env.PRIVATE_KEY,    // private key
    process.env.COMPANY,        // company name
    process.env.USER            // user
  );

  console.log(`\n✅ SDK de Payway inicializado correctamente`);
  console.log("📌 typeof SDK instance:", typeof sdk);
  console.log("📌 Métodos disponibles:", sdk ? Object.keys(sdk) : "(sdk es null)");

  // Validación crítica
  if (!sdk || typeof sdk.payment !== "function") {
    throw new Error("SDK no inicializado correctamente - método payment no disponible");
  }

  console.log("✅ Método payment() detectado correctamente");

} catch (error) {
  console.error(`\n❌ ERROR al inicializar SDK:`);
  console.error(`Mensaje: ${error.message}`);
  console.error(`Stack: ${error.stack}`);
  process.exit(1);
}

// Hacemos disponible el SDK globalmente
global.sdk = sdk;

console.log("\n============================================================");
console.log("🔍 VALIDACIÓN FINAL DEL SDK");
console.log("============================================================");
console.log("📌 Tipo de sdk:", typeof sdk);
console.log("📌 Métodos:", Object.keys(sdk));
console.log("📌 Tiene método payment:", typeof sdk.payment);
console.log("📌 Tiene método paymentInfo:", typeof sdk.paymentInfo);
console.log("📌 Tiene método refund:", typeof sdk.refund);
console.log("============================================================\n");

// =============================================================
// 🔐 AUTH
// =============================================================

const authenticate = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];

  if (!apiKey) {
    console.warn(`\n⚠️ [${new Date().toISOString()}] Intento sin API Key`);
    return res.status(401).json({
      error: "Unauthorized",
      message: "Falta el header 'x-api-key'"
    });
  }

  if (apiKey !== process.env.API_KEY) {
    console.warn(`\n⚠️ [${new Date().toISOString()}] API Key inválida`);
    return res.status(401).json({
      error: "Unauthorized",
      message: "API Key inválida"
    });
  }

  console.log(`✅ [${new Date().toISOString()}] Autenticación exitosa`);
  next();
};

app.use((req, res, next) => {
  console.log(`\n[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

app.post("/create-payment-intent", authenticate, async (req, res) => {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`💳 PROCESANDO PAGO`);
  console.log(`${'='.repeat(60)}`);

  const { amount, token, user_id, bin, description, site_transaction_id } = req.body;

  console.log(`\n📥 Datos recibidos:`);
  console.log(`   Amount: ${amount}`);
  console.log(`   Token: ${token ? token.substring(0, 20) + '...' : 'NO PROPORCIONADO'}`);
  console.log(`   User ID: ${user_id}`);
  console.log(`   BIN: ${bin}`);
  console.log(`   Description: ${description}`);
  console.log(`   Site Transaction ID: ${site_transaction_id}`);

  const errors = [];

  if (!amount || typeof amount !== 'number' || amount <= 0) {
    errors.push("amount debe ser un número positivo");
  }

  if (!token || typeof token !== 'string') {
    errors.push("token es requerido y debe ser una cadena");
  }

  if (!user_id || typeof user_id !== 'string') {
    errors.push("user_id es requerido y debe ser una cadena");
  }

  if (!bin || typeof bin !== 'string' || bin.length !== 6) {
    errors.push("bin debe ser una cadena de 6 dígitos");
  }

  if (!description || typeof description !== 'string') {
    errors.push("description es requerido");
  }

  if (!site_transaction_id || typeof site_transaction_id !== 'string') {
    errors.push("site_transaction_id es requerido y debe ser una cadena válida");
  }

  if (errors.length > 0) {
    console.error(`\n❌ VALIDACIÓN FALLIDA:`);
    errors.forEach(e => console.error(`   - ${e}`));
    return res.status(400).json({
      error: "Validación fallida",
      details: errors
    });
  }

  console.log(`\n✅ Validación exitosa - todos los campos son correctos`);

  try {
    console.log(`\n🔐 Preparando argumentos para sdk.payment()...`);

    const paymentArgs = {
      site_transaction_id,
      token,
      user_id,
      payment_method_id: 1,
      bin,
      amount,
      currency: "ARS",
      installments: 1,
      description,
      payment_type: "single",
      sub_payments: [],
      fraud_detection: {
        send_to_cs: true,
        channel: "Web",
        dispatch_method: "Store Pick Up"
      }
    };

    console.log(`\n📦 Argumentos de pago:`);
    console.log(JSON.stringify(paymentArgs, null, 2));

    console.log(`\n🚀 Llamando a sdk.payment()...`);
    console.log(`   Timestamp: ${new Date().toISOString()}`);
    console.log(`   Esperando respuesta...`);

    sdk.payment(paymentArgs, (result, err) => {
      console.log(`\n📬 RESPUESTA DEL SDK RECIBIDA`);
      console.log(`   Timestamp: ${new Date().toISOString()}`);

      if (err) {
        console.error(`\n❌ ERROR EN SDK.PAYMENT():`);
        console.error(`   Type: ${typeof err}`);
        console.error(`   Error:`, err);

        if (typeof err === 'object') {
          console.error(`   Error stringified:`);
          console.error(JSON.stringify(err, null, 2));
        }

        let errorMessage = "Error al procesar el pago";
        let errorDetails = err;

        if (typeof err === 'object') {
          errorMessage = err.message || err.error || errorMessage;
          errorDetails = err;
        } else if (typeof err === 'string') {
          errorMessage = err;
        }

        return res.status(500).json({
          status: "error",
          error: errorMessage,
          details: errorDetails
        });
      }

      if (!result) {
        console.error(`\n❌ No se recibió respuesta del SDK (result es null/undefined)`);
        return res.status(500).json({
          status: "error",
          error: "No se recibió respuesta del gateway de pago"
        });
      }

      console.log(`\n✅ Respuesta recibida correctamente`);
      console.log(`\n📊 Respuesta completa del SDK:`);
      console.log(JSON.stringify(result, null, 2));

      const paymentStatus = result.status?.toLowerCase();
      console.log(`\n📈 Status del pago: ${paymentStatus}`);

      const isApproved = paymentStatus === 'approved';
      const isRejected = paymentStatus === 'rejected';
      const isPending = paymentStatus === 'pending' || paymentStatus === 'pre_approved';

      const response = {
        status: paymentStatus,
        payment_id: result.id,
        site_transaction_id: result.site_transaction_id,
        amount: result.amount,
        currency: result.currency,
        installments: result.installments,
        card_brand: result.card_brand,
        date: result.date,
        bin: result.bin
      };

      if (isApproved) {
        response.ticket = result.status_details?.ticket;
        response.authorization_code = result.status_details?.card_authorization_code;
        response.message = "Pago aprobado exitosamente";

        console.log(`\n${'='.repeat(60)}`);
        console.log(`🎉 PAGO APROBADO EXITOSAMENTE`);
        console.log(`${'='.repeat(60)}`);
        console.log(`   Payment ID: ${result.id}`);
        console.log(`   Ticket: ${result.status_details?.ticket}`);
        console.log(`   Authorization Code: ${result.status_details?.card_authorization_code}`);
        console.log(`   Monto: ${result.amount} ${result.currency}`);
        console.log(`   Card Brand: ${result.card_brand}`);
        console.log(`${'='.repeat(60)}\n`);

      } else if (isRejected) {
        response.error_code = result.status_details?.error?.code;
        response.error_reason = result.status_details?.error?.reason;
        response.message = result.status_details?.error?.description || "Pago rechazado";

        console.log(`\n${'='.repeat(60)}`);
        console.log(`⚠️ PAGO RECHAZADO`);
        console.log(`${'='.repeat(60)}`);
        console.log(`   Error Code: ${response.error_code}`);
        console.log(`   Error Reason: ${response.error_reason}`);
        console.log(`   Error Description: ${response.message}`);
        console.log(`${'='.repeat(60)}\n`);

      } else if (isPending) {
        response.message = "Pago pendiente de aprobación";

        console.log(`\n${'='.repeat(60)}`);
        console.log(`⏳ PAGO PENDIENTE DE APROBACIÓN`);
        console.log(`${'='.repeat(60)}`);
        console.log(`   Estado: ${paymentStatus}`);
        console.log(`   El pago está siendo procesado...`);
        console.log(`${'='.repeat(60)}\n`);

      } else {
        console.log(`\n❓ Estado desconocido del pago: ${paymentStatus}`);
      }

      response.raw_response = result;

      console.log(`\n📤 Respondiendo al cliente con:`);
      console.log(JSON.stringify(response, null, 2));

      res.json(response);
    });

  } catch (error) {
    console.error(`\n❌ ERROR INESPERADO EN TRY-CATCH:`);
    console.error(`   Mensaje: ${error.message}`);
    console.error(`   Stack: ${error.stack}`);

    res.status(500).json({
      status: "error",
      error: "Error interno del servidor",
      details: error.message
    });
  }
});

app.post("/payment-status", authenticate, async (req, res) => {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🔍 CONSULTANDO ESTADO DEL PAGO`);
  console.log(`${'='.repeat(60)}`);

  const { payment_id } = req.body;

  console.log(`   Payment ID: ${payment_id}`);

  if (!payment_id) {
    console.error(`❌ Payment ID no proporcionado`);
    return res.status(400).json({
      error: "Missing payment_id",
      message: "El campo 'payment_id' es requerido"
    });
  }

  try {
    console.log(`\n🚀 Llamando a sdk.paymentInfo()...`);
    console.log(`   Timestamp: ${new Date().toISOString()}`);

    sdk.paymentInfo(payment_id, (result, err) => {
      console.log(`\n📬 RESPUESTA RECIBIDA`);
      console.log(`   Timestamp: ${new Date().toISOString()}`);

      if (err) {
        console.error(`\n❌ Error al consultar pago:`, err);

        let errorMessage = "Error al consultar el estado del pago";
        if (typeof err === 'object' && err.message) {
          errorMessage = err.message;
        } else if (typeof err === 'string') {
          errorMessage = err;
        }

        return res.status(500).json({
          error: errorMessage,
          details: err
        });
      }

      if (!result) {
        console.error(`\n❌ No se encontró información del pago`);
        return res.status(404).json({
          error: "Pago no encontrado",
          payment_id
        });
      }

      console.log(`\n✅ Estado del pago:`);
      console.log(JSON.stringify(result, null, 2));

      res.json(result);
    });
  } catch (error) {
    console.error(`\n❌ Error inesperado:`, error);
    res.status(500).json({
      error: "Error interno del servidor",
      details: error.message
    });
  }
});

app.post("/refund", authenticate, async (req, res) => {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🔄 PROCESANDO DEVOLUCIÓN`);
  console.log(`${'='.repeat(60)}`);

  const { payment_id } = req.body;

  console.log(`   Payment ID: ${payment_id}`);

  if (!payment_id) {
    console.error(`❌ Payment ID no proporcionado`);
    return res.status(400).json({
      error: "Missing payment_id",
      message: "El campo 'payment_id' es requerido"
    });
  }

  try {
    console.log(`\n🚀 Llamando a sdk.refund()...`);
    console.log(`   Timestamp: ${new Date().toISOString()}`);

    sdk.refund(payment_id, (result, err) => {
      console.log(`\n📬 RESPUESTA RECIBIDA`);
      console.log(`   Timestamp: ${new Date().toISOString()}`);

      if (err) {
        console.error(`\n❌ Error en devolución:`, err);
        return res.status(500).json({
          error: "Error al procesar la devolución",
          details: err
        });
      }

      console.log(`\n✅ Devolución exitosa:`);
      console.log(JSON.stringify(result, null, 2));

      res.json(result);
    });
  } catch (error) {
    console.error(`\n❌ Error inesperado:`, error);
    res.status(500).json({
      error: "Error interno del servidor",
      details: error.message
    });
  }
});

app.get("/health", (req, res) => {
  const healthResponse = {
    status: "ok",
    message: "Node Payway API is running",
    ambient,
    timestamp: new Date().toISOString()
  };

  console.log(`\n✅ Health check - API está funcionando`);
  res.json(healthResponse);
});

app.use((req, res) => {
  console.warn(`\n⚠️ Ruta no encontrada: ${req.method} ${req.path}`);
  res.status(404).json({
    error: "Not found",
    message: `Ruta ${req.method} ${req.path} no encontrada`
  });
});

app.use((err, req, res, next) => {
  console.error('\n❌ Error no manejado:', err);
  res.status(500).json({
    error: "Internal server error",
    message: err.message
  });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`✅ SERVIDOR INICIADO CORRECTAMENTE`);
  console.log(`${'='.repeat(60)}`);
  console.log(`🌐 Puerto: ${PORT}`);
  console.log(`📍 Ambiente: ${ambient}`);
  console.log(`🔑 Company: ${process.env.COMPANY}`);
  console.log(`👤 User: ${process.env.USER}`);
  console.log(`📚 Endpoints disponibles:`);
  console.log(`   - POST /create-payment-intent (Procesar pago)`);
  console.log(`   - POST /payment-status (Consultar estado)`);
  console.log(`   - POST /refund (Procesar devolución)`);
  console.log(`   - GET /health (Health check)`);
  console.log(`${'='.repeat(60)}`);
  console.log(`\n✨ Listo para recibir requests desde Flask\n`);
});