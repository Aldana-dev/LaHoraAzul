import express from "express";
import sdkModulo from "sdk-node-payway";
import bodyParser from "body-parser";
import dotenv from "dotenv";
import cors from "cors";

dotenv.config();

const app = express();
app.use(bodyParser.json());
app.use(cors({ 
  origin: ["http://localhost:5000", "http://127.0.0.1:5000"],
  credentials: true 
}));

const requiredEnvVars = ['PUBLIC_KEY', 'PRIVATE_KEY', 'COMPANY', 'USER', 'API_KEY'];
const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingVars.length > 0) {
  console.error(`❌ Error: Faltan las siguientes variables de entorno: ${missingVars.join(', ')}`);
  console.error('Por favor, configura tu archivo .env correctamente.');
  process.exit(1);
}

const ambient = process.env.AMBIENT || "developer";
const sdk = new sdkModulo.sdk(
  ambient,
  process.env.PUBLIC_KEY,
  process.env.PRIVATE_KEY,
  process.env.COMPANY,
  process.env.USER
);

console.log(`✅ SDK de Payway inicializado en ambiente: ${ambient}`);

const authenticate = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey) {
    return res.status(401).json({ 
      error: "Unauthorized", 
      message: "Falta el header 'x-api-key'" 
    });
  }
  
  if (apiKey !== process.env.API_KEY) {
    return res.status(401).json({ 
      error: "Unauthorized", 
      message: "API Key inválida" 
    });
  }
  
  next();
};

app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

app.post("/create-payment-intent", authenticate, async (req, res) => {
  const { amount, token, user_id, bin, description, site_transaction_id } = req.body;

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
    return res.status(400).json({ 
      error: "Validación fallida", 
      details: errors 
    });
  }

  try {
    console.log(`\n🔄 Procesando pago...`);
    console.log(`  Transaction ID: ${site_transaction_id}`);
    console.log(`  User ID: ${user_id}`);
    console.log(`  Amount: ${amount} (${(amount / 100).toFixed(2)} ARS)`);
    console.log(`  Token: ${token.substring(0, 10)}...`);
    console.log(`  BIN: ${bin}`);

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
        send_to_cs: false,
        channel: "Web",
        dispatch_method: "Store Pick Up"
      }
    };

    sdk.payment(paymentArgs, (result, err) => {
      if (err) {
        console.error(`\n❌ Error en pago:`, err);
        
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
        console.error(`\n❌ No se recibió respuesta del SDK`);
        return res.status(500).json({ 
          status: "error",
          error: "No se recibió respuesta del gateway de pago"
        });
      }

      console.log(`\n✅ Respuesta del SDK:`, JSON.stringify(result, null, 2));

      const paymentStatus = result.status?.toLowerCase();
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
        
        console.log(`\n🎉 PAGO APROBADO`);
        console.log(`  Payment ID: ${result.id}`);
        console.log(`  Ticket: ${result.status_details?.ticket}`);
        console.log(`  Authorization: ${result.status_details?.card_authorization_code}`);
      } else if (isRejected) {
        response.error_code = result.status_details?.error?.code;
        response.error_reason = result.status_details?.error?.reason;
        response.message = result.status_details?.error?.description || "Pago rechazado";
        
        console.log(`\n⚠️ PAGO RECHAZADO`);
        console.log(`  Razón: ${response.error_reason}`);
        console.log(`  Código: ${response.error_code}`);
      } else if (isPending) {
        response.message = "Pago pendiente de aprobación";
        
        console.log(`\n⏳ PAGO PENDIENTE`);
      }

      response.raw_response = result;
      res.json(response);
    });

  } catch (error) {
    console.error(`\n❌ Error inesperado:`, error);
    res.status(500).json({ 
      status: "error",
      error: "Error interno del servidor",
      details: error.message 
    });
  }
});

app.post("/payment-status", authenticate, async (req, res) => {
  const { payment_id } = req.body;

  if (!payment_id) {
    return res.status(400).json({ 
      error: "Missing payment_id",
      message: "El campo 'payment_id' es requerido" 
    });
  }

  console.log(`\n🔍 Consultando estado del pago: ${payment_id}`);

  try {
    sdk.paymentInfo(payment_id, (result, err) => {
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

      console.log(`\n✅ Estado del pago:`, result.status);
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
  const { payment_id } = req.body;

  if (!payment_id) {
    return res.status(400).json({ 
      error: "Missing payment_id",
      message: "El campo 'payment_id' es requerido" 
    });
  }

  console.log(`\n🔄 Procesando devolución del pago: ${payment_id}`);

  try {
    sdk.refund(payment_id, (result, err) => {
      if (err) {
        console.error(`\n❌ Error en devolución:`, err);
        return res.status(500).json({ 
          error: "Error al procesar la devolución",
          details: err 
        });
      }

      console.log(`\n✅ Devolución exitosa:`, result);
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
  res.json({ 
    status: "ok", 
    message: "Node Payway API is running",
    ambient,
    timestamp: new Date().toISOString()
  });
});

app.use((req, res) => {
  res.status(404).json({ 
    error: "Not found",
    message: `Ruta ${req.method} ${req.path} no encontrada` 
  });
});

app.use((err, req, res, next) => {
  console.error('Error no manejado:', err);
  res.status(500).json({ 
    error: "Internal server error",
    message: err.message 
  });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`\n🚀 Node.js Payway API corriendo en puerto ${PORT}`);
  console.log(`📍 Ambiente: ${ambient}`);
  console.log(`🔑 Company: ${process.env.COMPANY}`);
  console.log(`👤 User: ${process.env.USER}`);
  console.log(`\n✨ Listo para recibir requests desde Flask\n`);
});