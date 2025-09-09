// ==========================
// 📦 1. Cotización de envío
// ==========================
async function calcularCotizacion(cpDestino) {
  if (!cpDestino) {
    alert("Por favor ingrese un Código Postal de destino.");
    return;
  }

  const datosCotizacion = {
    customerId: "0001079998", // ID proporcionado por MiCorreo
    postalCodeOrigin: "8407",
    postalCodeDestination: cpDestino,
    deliveredType: "D",
    dimensions: { weight: 1000, height: 10, width: 20, length: 30 },
  };

  try {
    const resp = await fetch("/cotizar_envio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datosCotizacion),
    });

    if (!resp.ok) throw new Error(`Error en la cotización: ${resp.status}`);

    const data = await resp.json();
    const tarifaDomicilio = data.rates?.find(r => r.deliveredType === "D");

    if (tarifaDomicilio) {
      const precio = tarifaDomicilio.price.toFixed(2);
      document.getElementById("precio-domicilio").textContent = `$${precio}`;
      document.getElementById("costo-envio").textContent = `$${precio}`;

      const subtotal = parseFloat(document.getElementById("subtotal").textContent.replace('$', '')) || 0;
      document.getElementById("total-compra").textContent = `$${(subtotal + tarifaDomicilio.price).toFixed(2)}`;
    } else {
      alert("No se encontró tarifa para entrega a domicilio.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("No se pudo calcular el costo de envío.");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  calcularCotizacion("8300"); // cotiza por defecto
  document.getElementById("btn-cotizar-envio").addEventListener("click", () => {
    calcularCotizacion(document.getElementById("cp_destino").value.trim());
  });
});

// ==================================
// 💳 2. Configuración de Payway
// ==================================
const publicApiKey = "TU_API_KEY_PUBLICA"; // sandbox
const urlSandbox = "https://developers.decidir.com/api/v2";
const decidir = new Decidir(urlSandbox);
decidir.setPublishableKey(publicApiKey);
decidir.setTimeout(5000);

// Formulario del modal
const form = document.querySelector("#form-datos-usuario");

form.addEventListener("submit", function (event) {
  const metodo = document.getElementById("metodo_pago").value;

  if (metodo === "tarjeta") {
    event.preventDefault();
    decidir.createToken(form, sdkResponseHandler);
  }
});

function sdkResponseHandler(status, response) {
  if (status !== 200 && status !== 201) {
    console.error("Error al generar token:", response);
    alert("Hubo un problema con la tarjeta. Revisá los datos.");
  } else {
    console.log("Token generado:", response.token);

    fetch("/confirmar_pedido", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: response.token,
        nombre: document.getElementById("nombre").value,
        apellido: document.getElementById("apellido").value,
        email: document.getElementById("email").value,
        telefono: document.getElementById("telefono").value,
      }),
    })
      .then(res => res.json())
      .then(data => {
        alert("Compra realizada con éxito 🎉");
        console.log("Respuesta backend:", data);
      })
      .catch(err => {
        console.error("Error en el backend:", err);
        alert("No se pudo procesar el pago.");
      });
  }
}

// ==================================
// 🧭 3. Navegación de pasos en modal
// ==================================
let pasoActual = 1;
const pasos = document.querySelectorAll(".paso");
const btnAnterior = document.getElementById("btn-anterior");
const btnSiguiente = document.getElementById("btn-siguiente");
const btnConfirmar = document.getElementById("btn-confirmar");
const metodoPago = document.getElementById("metodo_pago");
const pagoTarjeta = document.getElementById("pago-tarjeta");

function mostrarPaso(paso) {
  pasos.forEach((p, i) => p.classList.toggle("d-none", i !== paso - 1));
  btnAnterior.disabled = paso === 1;
  btnSiguiente.classList.toggle("d-none", paso === pasos.length);
  btnConfirmar.classList.toggle("d-none", paso !== pasos.length);
}

btnAnterior.addEventListener("click", () => {
  if (pasoActual > 1) mostrarPaso(--pasoActual);
});

btnSiguiente.addEventListener("click", () => {
  if (pasoActual < pasos.length) mostrarPaso(++pasoActual);
});

metodoPago.addEventListener("change", e => {
  pagoTarjeta.classList.toggle("d-none", e.target.value !== "tarjeta");
});

mostrarPaso(pasoActual);
