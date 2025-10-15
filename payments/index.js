import express from "express";
import sdkModulo from "sdk-node-payway";
import bodyParser from "body-parser";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(bodyParser.json());

// Configuración SDK
const sdk = new sdkModulo.sdk(
    process.env.AMBIENT,
    process.env.PUBLIC_KEY,
    process.env.PRIVATE_KEY,
    process.env.COMPANY,
    process.env.USER
);

// Crear pago
app.post("/create-payment-intent", async (req, res) => {
    const { amount, token } = req.body;

    try {
        const pago = await sdk.cryptogramPayment({
            amount,
            currency: "ARS",
            token,
            site_transaction_id: "pedido_" + Date.now(),
            installments: 1
        });
        res.json({ status: pago.status, id: pago.id, response: pago });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message });
    }
});

// Consultar estado de pago
app.post("/payment-status", async (req, res) => {
    const { payment_id } = req.body;
    try {
        const estado = await sdk.paymentInfo(payment_id);
        res.json(estado);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(3001, () => console.log("Node Payway escuchando en puerto 3001"));
