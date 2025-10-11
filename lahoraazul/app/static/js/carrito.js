// ===============================
// 🚚 Cotización de envíos
// ===============================
function mostrarCotizacionGlobal(tipo, precio, minDias, maxDias) {
  // Actualizar sección principal
  const labelPrincipal = document.querySelector(`.tarjeta-envio[data-tipo="${tipo}"]`);
  if (labelPrincipal) actualizarLabel(labelPrincipal, precio, minDias, maxDias);

  // Actualizar sección modal
  const labelModal = document.querySelector(`#modal-tarjetas-envio label[data-tipo="${tipo}"]`);
  if (labelModal) actualizarLabel(labelModal, precio, minDias, maxDias);
}

// Función helper para actualizar cualquier label de envío
function actualizarLabel(label, precio, minDias, maxDias) {
  const spanPrecio = label.querySelector(".precio-opcion, .precio-opcion-modal");
  const spanTiempo = label.querySelector(".texto-envio");

  if (precio != null) {
    // Precio SOLO en el span de precio
    spanPrecio.textContent = `$${precio.toFixed(2)}`;
    label.dataset.precio = precio;

    // Tiempo SOLO en el span de tiempo
    if (spanTiempo) spanTiempo.textContent = `${minDias} a ${maxDias} días hábiles`;

    // Habilitar input
    const input = label.querySelector("input");
    if (input) input.disabled = false;
  } else {
    spanPrecio.textContent = "No disponible";
    if (spanTiempo) spanTiempo.textContent = "";

    label.dataset.precio = 0;

    // Deshabilitar input
    const input = label.querySelector("input");
    if (input) input.disabled = true;
  }
}


// Cotizar envío (D = domicilio, S = sucursal)
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
    mostrarCotizacionGlobal(tipo, tarifa?.price ?? null, tarifa?.deliveryTimeMin, tarifa?.deliveryTimeMax);
  } catch (error) {
    console.error("Error:", error);
    mostrarCotizacionGlobal(tipo, null);
  }
}

function calcularCotizaciones(cpDestino) {
  if (!cpDestino) {
    alert("Por favor ingrese un Código Postal de destino.");
    return;
  }
  cotizarEnvio(cpDestino, "domicilio");
  cotizarEnvio(cpDestino, "sucursal");
}

// ===============================
// 💰 Resumen de costos
// ===============================
function parseCurrency(str) {
  return parseFloat(str.replace(/[^0-9.-]+/g, "")) || 0;
}

function actualizarResumen() {
  const seleccionado = document.querySelector('input[name="tipo_envio"]:checked, input[name="opcion-envio"]:checked');
  if (!seleccionado) return;

  const label = seleccionado.closest("label");
  const precioEnvio = parseFloat(label.dataset.precio || 0);

  const subtotal = parseCurrency(document.getElementById("subtotal").textContent);
  document.getElementById("costo-envio").textContent = `$${precioEnvio.toFixed(2)}`;
  document.getElementById("total-compra").textContent = `$${(subtotal + precioEnvio).toFixed(2)}`;
}

// ===============================
// 🚀 Inicialización
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  // Cotización inicial
  calcularCotizaciones("8300");
  document.getElementById("btn-cotizar-envio").addEventListener("click", () => {
    calcularCotizaciones(document.getElementById("cp_destino").value.trim());
  });

  // Escuchar todos los radios de envío (modal + principal)
  document.querySelectorAll('input[name="tipo_envio"], input[name="opcion-envio"]').forEach(radio => {
    radio.addEventListener("change", actualizarResumen);
  });

  actualizarResumen(); // inicializar
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
