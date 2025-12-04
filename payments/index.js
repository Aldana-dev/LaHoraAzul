const express = require("express");
const bodyParser = require("body-parser");
const dotenv = require("dotenv");
const cors = require("cors");

// =============================================================
// 1️⃣ CARGAR ENV Y CONFIGURACIÓN INICIAL
// =============================================================
dotenv.config();
const ambient = process.env.AMBIENT || "production";

console.log("\n============================================================");
console.log("🚀 PAYWAY SDK - INICIALIZACIÓN");
console.log("============================================================");
console.log(`📍 Ambiente: ${ambient}`);
console.log(`📦 SDK Version: ${require('sdk-node-payway/package.json').version}`);
console.log("============================================================\n");

// =============================================================
// 2️⃣ CARGAR Y VERIFICAR SDK
// =============================================================
let PaywaySDK;
try {
  const PaywayModule = require("sdk-node-payway");
  
  if (typeof PaywayModule.sdk !== "function") {
    throw new Error("SDK module structure is invalid");
  }
  
  PaywaySDK = PaywayModule.sdk;
  console.log("✅ SDK module loaded successfully");
} catch (err) {
  console.error("❌ Failed to load SDK module:", err.message);
  process.exit(1);
}

// =============================================================
// 3️⃣ INICIALIZAR SDK
// =============================================================
let sdk = null;
try {
  sdk = new PaywaySDK(
    ambient,
    process.env.PUBLIC_KEY,
    process.env.PRIVATE_KEY,
    process.env.COMPANY,
    process.env.USER
  );

  if (!sdk || typeof sdk.payment !== "function") {
    throw new Error("SDK initialized but payment method not available");
  }

  console.log("✅ SDK initialized successfully");
  console.log(`📋 Available methods: ${Object.keys(sdk).join(', ')}\n`);
} catch (error) {
  console.error("❌ SDK initialization failed:", error.message);
  console.error("Stack:", error.stack);
  process.exit(1);
}

// =============================================================
// 4️⃣ EXPRESS SETUP
// =============================================================
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

// Verificar variables de entorno requeridas
const requiredEnvVars = ['PUBLIC_KEY', 'PRIVATE_KEY', 'COMPANY', 'USER', 'API_KEY'];
const missingVars = requiredEnvVars.filter(v => !process.env[v]);

if (missingVars.length > 0) {
  console.error(`❌ Missing environment variables: ${missingVars.join(', ')}`);
  process.exit(1);
}

console.log("============================================================");
console.log("⚙️  CONFIGURATION");
console.log("============================================================");
console.log(`Company: ${process.env.COMPANY}`);
console.log(`User: ${process.env.USER}`);
console.log(`Public Key: ${process.env.PUBLIC_KEY.substring(0, 15)}...`);
console.log(`Private Key: ${process.env.PRIVATE_KEY.substring(0, 15)}...`);
console.log("============================================================\n");

// =============================================================
// 5️⃣ AUTHENTICATION MIDDLEWARE
// =============================================================
const authenticate = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey || apiKey !== process.env.API_KEY) {
    console.warn(`⚠️  Unauthorized request from ${req.ip}`);
    return res.status(401).json({ error: "Unauthorized" });
  }
  
  next();
};

// Request logger
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// =============================================================
// 6️⃣ ENDPOINTS
// =============================================================

app.post("/create-payment-intent", authenticate, async (req, res) => {
  const { amount, token, user_id, bin, description, site_transaction_id } = req.body;
  
  console.log(`\n💳 Processing payment: ${site_transaction_id}`);
  console.log(`   Amount: $${amount} | User: ${user_id} | BIN: ${bin}`);

  // Validación
  const errors = [];
  if (!amount || typeof amount !== 'number' || amount <= 0) errors.push("invalid amount");
  if (!token || typeof token !== 'string') errors.push("missing token");
  if (!user_id || typeof user_id !== 'string') errors.push("missing user_id");
  if (!bin || typeof bin !== 'string' || bin.length !== 6) errors.push("invalid bin");
  if (!description) errors.push("missing description");
  if (!site_transaction_id) errors.push("missing site_transaction_id");

  if (errors.length > 0) {
    console.error(`❌ Validation failed: ${errors.join(', ')}`);
    return res.status(400).json({ error: "Validation failed", details: errors });
  }

  try {
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

    console.log("🔄 Calling Payway API...");

    sdk.payment(paymentArgs, (result, err) => {
      if (err) {
        console.error(`❌ Payment error:`, err);
        return res.status(500).json({
          status: "error",
          error: typeof err === 'object' ? (err.message || err.error) : err,
          details: err
        });
      }

      if (!result) {
        console.error("❌ No response from gateway");
        return res.status(500).json({ status: "error", error: "No response from gateway" });
      }

      const status = result.status?.toLowerCase();
      console.log(`✅ Payment ${status}: ID ${result.id}`);

      const response = {
        status,
        payment_id: result.id,
        site_transaction_id: result.site_transaction_id,
        amount: result.amount,
        currency: result.currency,
        card_brand: result.card_brand,
        message: status === 'approved' ? 'Payment approved' : 
                 status === 'rejected' ? result.status_details?.error?.description || 'Payment rejected' :
                 'Payment pending'
      };

      if (status === 'approved') {
        response.ticket = result.status_details?.ticket;
        response.authorization_code = result.status_details?.card_authorization_code;
      } else if (status === 'rejected') {
        response.error_code = result.status_details?.error?.code;
        response.error_reason = result.status_details?.error?.reason;
      }

      res.json(response);
    });

  } catch (error) {
    console.error(`❌ Unexpected error:`, error.message);
    res.status(500).json({ status: "error", error: "Internal server error" });
  }
});

app.post("/payment-status", authenticate, async (req, res) => {
  const { payment_id } = req.body;
  
  if (!payment_id) {
    return res.status(400).json({ error: "Missing payment_id" });
  }

  console.log(`🔍 Checking payment status: ${payment_id}`);

  sdk.paymentInfo(payment_id, (result, err) => {
    if (err) {
      console.error(`❌ Error:`, err);
      return res.status(500).json({ error: "Failed to get payment info" });
    }

    if (!result) {
      return res.status(404).json({ error: "Payment not found" });
    }

    console.log(`✅ Payment found: ${result.status}`);
    res.json(result);
  });
});

app.post("/refund", authenticate, async (req, res) => {
  const { payment_id } = req.body;
  
  if (!payment_id) {
    return res.status(400).json({ error: "Missing payment_id" });
  }

  console.log(`🔄 Processing refund: ${payment_id}`);

  sdk.refund(payment_id, (result, err) => {
    if (err) {
      console.error(`❌ Refund error:`, err);
      return res.status(500).json({ error: "Refund failed" });
    }

    console.log(`✅ Refund successful`);
    res.json(result);
  });
});

app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    ambient,
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: "Not found" });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('❌ Unhandled error:', err);
  res.status(500).json({ error: "Internal server error" });
});

// =============================================================
// 7️⃣ START SERVER
// =============================================================
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log("\n============================================================");
  console.log("✅ SERVER RUNNING");
  console.log("============================================================");
  console.log(`Port: ${PORT} | Environment: ${ambient}`);
  console.log(`Company: ${process.env.COMPANY} | User: ${process.env.USER}`);
  console.log("============================================================\n");
});