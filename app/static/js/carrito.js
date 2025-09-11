// Actualiza todos los spans del mismo tipo de envío
function mostrarCotizacion(tipo, precio, minDias, maxDias) {
  const texto = precio
    ? `$${precio.toFixed(2)} (${minDias} a ${maxDias} días hábiles)`
    : "No disponible";

  document.querySelectorAll(`[data-tipo="${tipo}"] span`).forEach(span => {
    span.textContent = texto;
  });
}

// Cotizar envío (puede ser D = domicilio, S = sucursal)
async function cotizarEnvio(cpDestino, tipo) {
  const datosCotizacion = {
    customerId: "0001079998",
    postalCodeOrigin: "8407",
    postalCodeDestination: cpDestino,
    deliveredType: tipo === "domicilio" ? "D" : "S",
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

    const tarifa = data.rates?.find(r => r.deliveredType === datosCotizacion.deliveredType);
    if (tarifa) {
      mostrarCotizacion(tipo, tarifa.price, tarifa.deliveryTimeMin, tarifa.deliveryTimeMax);
    } else {
      mostrarCotizacion(tipo, null);
    }
  } catch (error) {
    console.error("Error:", error);
    mostrarCotizacion(tipo, null);
  }
}

// Ejecutar ambas cotizaciones
function calcularCotizaciones(cpDestino) {
  if (!cpDestino) {
    alert("Por favor ingrese un Código Postal de destino.");
    return;
  }
  cotizarEnvio(cpDestino, "domicilio");
  cotizarEnvio(cpDestino, "sucursal");
}

document.addEventListener("DOMContentLoaded", () => {
  calcularCotizaciones("8300"); // por defecto
  document.getElementById("btn-cotizar-envio").addEventListener("click", () => {
    calcularCotizaciones(document.getElementById("cp_destino").value.trim());
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
