// ===============================
// 🚚 Cotización de envíos
// ===============================
function mostrarCotizacionGlobal(tipo, precio, minDias, maxDias) {
  console.log(`Actualizando cotización para tipo: ${tipo}, precio: ${precio}`);

  // Actualizar sección principal
  const labelPrincipal = document.querySelector(`.tarjeta-envio[data-tipo="${tipo}"]`);
  if (labelPrincipal) {
    actualizarLabel(labelPrincipal, precio, minDias, maxDias);
  } else {
    console.error(`Label principal para tipo ${tipo} no encontrado`);
  }

  // Actualizar sección modal
  const labelModal = document.querySelector(`#modal-tarjetas-envio label[data-tipo="${tipo}"]`);
  if (labelModal) {
    actualizarLabel(labelModal, precio, minDias, maxDias);
  } else {
    console.error(`Label modal para tipo ${tipo} no encontrado`);
  }
}

// Función helper para actualizar cualquier label de envío
function actualizarLabel(label, precio, minDias, maxDias) {
  if (!label) {
    console.error("Label no proporcionado");
    return;
  }
  const spanPrecio = label.querySelector(".precio-opcion, .precio-opcion-modal");
  const spanTiempo = label.querySelector(".texto-envio");

  if (precio != null) {
    console.log(`Actualizando label con precio: ${precio}`);
    if (spanPrecio) spanPrecio.textContent = `$${precio.toFixed(2)}`;
    label.dataset.precio = precio;
    if (spanTiempo) spanTiempo.textContent = `${minDias} a ${maxDias} días hábiles`;
    const input = label.querySelector("input");
    if (input) input.disabled = false;
  } else {
    console.log("Precio no disponible");
    if (spanPrecio) spanPrecio.textContent = "No disponible";
    if (spanTiempo) spanTiempo.textContent = "";
    label.dataset.precio = 0;
    const input = label.querySelector("input");
    if (input) input.disabled = true;
  }
}

// Cotizar envío (D = domicilio, S = sucursal)
async function cotizarEnvio(cpDestino, tipo) {
  console.log(`Cotizando envío para CP: ${cpDestino}, tipo: ${tipo}`);
  if (!cpDestino || cpDestino.trim() === '') {
    console.error("CP no proporcionado o inválido en cotizarEnvio");
    alert("Por favor ingrese un Código Postal válido.");
    return;
  }

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

    if (!resp.ok) {
      throw new Error(`Error en la cotización: ${resp.status} - ${await resp.text()}`);
    }
    const data = await resp.json();
    console.log("Respuesta completa de la API:", data);
    if (data.rates && data.rates.length > 0) {
      const tarifa = data.rates.find(r => r.deliveredType === datosCotizacion.deliveredType);
      mostrarCotizacionGlobal(tipo, tarifa?.price ?? null, tarifa?.deliveryTimeMin, tarifa?.deliveryTimeMax);
    } else {
      console.error("No se encontraron tarifas en la respuesta");
      mostrarCotizacionGlobal(tipo, null);
    }
  } catch (error) {
    console.error("Error en cotizarEnvio:", error);
    alert("Error al cotizar el envío. Verifica los datos e intenta de nuevo.");
    mostrarCotizacionGlobal(tipo, null);
  }
}

async function cotizarEnvioModal(cpDestino) {
  console.log("Llamando a cotizarEnvioModal con CP:", cpDestino);
  if (!cpDestino) {
    console.error("CP no proporcionado en cotizarEnvioModal");
    alert("Por favor ingrese un Código Postal de destino.");
    return;
  }
  try {
    await cotizarEnvio(cpDestino, "domicilio");
    await cotizarEnvio(cpDestino, "sucursal");
    // actualizarResumenModal();  // Comentado porque no está definida; descomenta si la defines
  } catch (error) {
    console.error("Error en cotizarEnvioModal:", error);
    alert("Error al cotizar en el modal.");
  }
}

function calcularCotizaciones(cpDestino) {
  console.log("Llamando a calcularCotizaciones con CP:", cpDestino);
  if (!cpDestino) {
    console.error("CP no proporcionado en calcularCotizaciones");
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
  console.log("Parseando currency:", str);
  return parseFloat(str.replace(/[^0-9.-]+/g, "")) || 0;
}

function actualizarResumen() {
  console.log("Actualizando resumen");
  const seleccionado = document.querySelector('input[name="tipo_envio"]:checked, input[name="opcion-envio"]:checked');
  if (!seleccionado) {
    console.warn("Ningún tipo de envío seleccionado");
    return;
  }
  const label = seleccionado.closest("label");
  if (!label) {
    console.error("Label no encontrado para el seleccionado");
    return;
  }
  const precioEnvio = parseFloat(label.dataset.precio || 0);
  const subtotalElement = document.getElementById("subtotal");
  if (!subtotalElement) {
    console.error("Elemento subtotal no encontrado");
    return;
  }
  const subtotal = parseCurrency(subtotalElement.textContent);
  const costoEnvioElement = document.getElementById("costo-envio");
  if (costoEnvioElement) costoEnvioElement.textContent = `$${precioEnvio.toFixed(2)}`;
  const totalCompraElement = document.getElementById("total-compra");
  if (totalCompraElement) totalCompraElement.textContent = `$${(subtotal + precioEnvio).toFixed(2)}`;
}

// ===============================
// 🚀 Inicialización
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOMContentLoaded ejecutado");
  const cpDestinoInicial = document.getElementById("cp_destino")?.value.trim();
  if (cpDestinoInicial) {
    console.log("Iniciando cotización con CP inicial:", cpDestinoInicial);
    calcularCotizaciones(cpDestinoInicial);
  } else {
    console.warn("No se encontró CP inicial");
  }

  const btnCotizar = document.getElementById("btn-cotizar-envio");
  if (btnCotizar) {
    btnCotizar.addEventListener("click", () => {
      const cpDestino = document.getElementById("cp_destino")?.value.trim();
      console.log("Botón cotizar presionado con CP:", cpDestino);
      if (cpDestino) {
        calcularCotizaciones(cpDestino);
      } else {
        console.error("CP no proporcionado en el botón");
        alert("Por favor ingrese un Código Postal de destino.");
      }
    });
  } else {
    console.error("Botón btn-cotizar-envio no encontrado");
  }

  document.querySelectorAll('input[name="tipo_envio"], input[name="opcion-envio"]').forEach(radio => {
    radio.addEventListener("change", () => {
      console.log("Tipo de envío cambiado");
      actualizarResumen();
    });
  });

  actualizarResumen();  // Inicializar resumen
});

// Renombrado para evitar conflictos
const formularioEnvioCompra = document.getElementById("form-datos-usuario");
if (formularioEnvioCompra) {
  formularioEnvioCompra.addEventListener("submit", function (e) {
    e.preventDefault();
    console.log("Verificando datos del formulario...");
    const datos = {};
    const formData = new FormData(formularioEnvioCompra);  // Actualizado aquí
    for (let [key, value] of formData.entries()) {
      datos[key] = value;
    }

    const requiredFields = ["nombre", "apellido", "provincia", "localidad", "ciudad", "cp_usuario", "email", "telefono"];
    let isValid = true;

    requiredFields.forEach(field => {
      const input = document.getElementById(field);
      const errorSpan = document.getElementById(`error-${field}`);
      const value = datos[field];

      if (!value || value.trim() === "") {
        isValid = false;
        if (errorSpan) {
          errorSpan.textContent = "Este campo es requerido.";
          errorSpan.style.display = "block";
        }
      } else if (errorSpan) {
        errorSpan.textContent = "";
        errorSpan.style.display = "none";
      }

      // Validaciones adicionales en una sola verificación
      const validations = {
        email: value => !/\S+@\S+\.\S+/.test(value) && "Correo electrónico no válido.",
        cp_usuario: value => !/^[0-9]{4,8}$/.test(value) && "Código postal no válido.",
        telefono: value => !/[0-9+ ]{7,15}/.test(value) && "Teléfono no válido."
      };

      if (validations[field] && validations[field](value)) {
        isValid = false;
        if (errorSpan) {
          errorSpan.textContent = validations[field](value);
          errorSpan.style.display = "block";
        }
      }
    });

    if (isValid) {
      console.log("Datos válidos:", datos);
      if (typeof enviarDatosAAPI === "function") {
        enviarDatosAAPI(datos);
      } else {
        console.error("Función enviarDatosAAPI no definida.");
      }
    } else {
      console.error("Hay errores en el formulario.");
    }
  });
}

// ==================================
// 🧭 3. Navegación de pasos en modal
// ==================================
document.addEventListener("DOMContentLoaded", () => {
  let pasoActual = 1;
  const pasos = document.querySelectorAll(".paso");
  const btnAnterior = document.getElementById("btn-anterior");
  const btnSiguiente = document.getElementById("btn-siguiente");
  const btnConfirmar = document.getElementById("btn-confirmar");
  const metodoPago = document.getElementById("metodo_pago");
  const pagoTarjeta = document.getElementById("pago-tarjeta");
  const modalCompra = document.getElementById("modalCompra");

  console.log("Inicializando navegación de modal");

  function mostrarPaso(paso) {
    console.log(`Mostrando paso: ${paso}`);
    if (!pasos || pasos.length === 0) {
      console.error("No se encontraron pasos");
      return;
    }
    pasos.forEach((p, i) => p.classList.toggle("d-none", i !== paso - 1));

    btnAnterior.classList.add("d-none");
    btnSiguiente.classList.add("d-none");
    btnConfirmar.classList.add("d-none");

    if (paso === 1) {
      btnSiguiente.classList.remove("d-none");
    } else if (paso === 2) {
      btnAnterior.classList.remove("d-none");
      btnConfirmar.classList.remove("d-none");
    }

    pasoActual = paso;
  }

  if (btnAnterior) {
    btnAnterior.addEventListener("click", () => {
      console.log("Botón anterior presionado");
      if (pasoActual > 1) mostrarPaso(pasoActual - 1);
    });
  } else {
    console.error("Botón btn-anterior no encontrado");
  }

  if (btnSiguiente) {
    btnSiguiente.addEventListener("click", () => {
      console.log("Botón siguiente presionado");
      if (pasoActual < pasos.length) mostrarPaso(pasoActual + 1);
    });
  } else {
    console.error("Botón btn-siguiente no encontrado");
  }

  if (metodoPago) {
    metodoPago.addEventListener("change", e => {
      console.log("Método de pago cambiado a:", e.target.value);
      if (pagoTarjeta) pagoTarjeta.classList.toggle("d-none", e.target.value !== "tarjeta");
    });
  } else {
    console.error("Elemento metodo_pago no encontrado");
  }

  if (modalCompra) {
    modalCompra.addEventListener("shown.bs.modal", () => {
      console.log("Modal mostrado, reiniciando a paso 1");
      pasoActual = 1;
      mostrarPaso(pasoActual);
    });
  } else {
    console.error("Modal modalCompra no encontrado");
  }

  mostrarPaso(pasoActual);  // Inicializar
});

document.querySelectorAll('input, textarea, select').forEach((element, index) => {
  element.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const nextElement = document.querySelector(`[tabindex="${index + 1}"]`);
      if (nextElement) nextElement.focus();
    }
  });
});