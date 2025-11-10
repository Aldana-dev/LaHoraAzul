// ==============================
// Cotización de envíos
// ==============================
function mostrarCotizacionGlobal(tipo, precio, minDias, maxDias) {
  const labelPrincipal = document.querySelector(`.tarjeta-envio[data-tipo="${tipo}"]`);
  if (labelPrincipal) actualizarLabel(labelPrincipal, precio, minDias, maxDias);

  const labelModal = document.querySelector(`#modal-tarjetas-envio label[data-tipo="${tipo}"]`);
  if (labelModal) actualizarLabel(labelModal, precio, minDias, maxDias);
}

function actualizarLabel(label, precio, minDias, maxDias) {
  if (!label) return;
  const spanPrecio = label.querySelector(".precio-opcion, .precio-opcion-modal");
  const spanTiempo = label.querySelector(".texto-envio");

  if (precio != null) {
    if (spanPrecio) spanPrecio.textContent = `$${precio.toFixed(2)}`;
    label.dataset.precio = precio;
    if (spanTiempo) spanTiempo.textContent = `${minDias} a ${maxDias} días hábiles`;
    const input = label.querySelector("input");
    if (input) input.disabled = false;
  } else {
    if (spanPrecio) spanPrecio.textContent = "No disponible";
    if (spanTiempo) spanTiempo.textContent = "";
    label.dataset.precio = 0;
    const input = label.querySelector("input");
    if (input) input.disabled = true;
  }
}

async function cotizarEnvio(cpDestino, tipo) {
  if (!cpDestino || cpDestino.trim() === '') {
    mostrarErrorAPI("Por favor ingrese un Código Postal válido.");
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

    if (!resp.ok) throw new Error(`Error en la cotización: ${resp.status}`);
    const data = await resp.json();
    if (data.rates && data.rates.length > 0) {
      const tarifa = data.rates.find(r => r.deliveredType === datosCotizacion.deliveredType);
      mostrarCotizacionGlobal(tipo, tarifa?.price ?? null, tarifa?.deliveryTimeMin, tarifa?.deliveryTimeMax);
      ocultarErrorAPI();
    } else {
      mostrarCotizacionGlobal(tipo, null);
      mostrarErrorAPI("No se encontraron tarifas para este destino.");
    }
  } catch (error) {
    mostrarCotizacionGlobal(tipo, null);
    mostrarErrorAPI("Error al cotizar el envío. Verifica los datos e intenta de nuevo.");
  }
}

async function cotizarEnvioModal(cpDestino) {
  if (!cpDestino) {
    mostrarErrorAPI("Por favor ingrese un Código Postal de destino.");
    return;
  }
  try {
    await cotizarEnvio(cpDestino, "domicilio");
    await cotizarEnvio(cpDestino, "sucursal");
  } catch (error) {
    mostrarErrorAPI("Error al cotizar en el modal.");
  }
}

function calcularCotizaciones(cpDestino) {
  if (!cpDestino) {
    mostrarErrorAPI("Por favor ingrese un Código Postal de destino.");
    return;
  }
  cotizarEnvio(cpDestino, "domicilio");
  cotizarEnvio(cpDestino, "sucursal");
}

// ==============================
// Resumen de costos
// ==============================
function parseCurrency(str) {
  return parseFloat(str.replace(/[^0-9.-]+/g, "")) || 0;
}

function actualizarResumen() {
  const seleccionado = document.querySelector('input[name="tipo_envio"]:checked, input[name="opcion-envio"]:checked');
  if (!seleccionado) return;
  const label = seleccionado.closest("label");
  if (!label) return;
  const precioEnvio = parseFloat(label.dataset.precio || 0);
  const subtotalElement = document.getElementById("subtotal");
  if (!subtotalElement) return;
  const subtotal = parseCurrency(subtotalElement.textContent);
  const costoEnvioElement = document.getElementById("costo-envio");
  if (costoEnvioElement) costoEnvioElement.textContent = `$${precioEnvio.toFixed(2)}`;
  const totalCompraElement = document.getElementById("total-compra");
  if (totalCompraElement) totalCompraElement.textContent = `$${(subtotal + precioEnvio).toFixed(2)}`;
}

// ==============================
// Inicialización
// ==============================
document.addEventListener("DOMContentLoaded", () => {
  const cpDestinoInicial = document.getElementById("cp_destino")?.value.trim();
  if (cpDestinoInicial) calcularCotizaciones(cpDestinoInicial);

  const btnCotizar = document.getElementById("btn-cotizar-envio");
  if (btnCotizar) {
    btnCotizar.addEventListener("click", () => {
      const cpDestino = document.getElementById("cp_destino")?.value.trim();
      if (cpDestino) {
        calcularCotizaciones(cpDestino);
      } else {
        mostrarErrorAPI("Por favor ingrese un Código Postal de destino.");
      }
    });
  }

  document.querySelectorAll('input[name="tipo_envio"], input[name="opcion-envio"]').forEach(radio => {
    radio.addEventListener("change", actualizarResumen);
  });

  actualizarResumen();
});

// ==============================
// Validación y envío del formulario
// ==============================
const formularioEnvioCompra = document.getElementById("form-datos-usuario");
if (formularioEnvioCompra) {
  formularioEnvioCompra.addEventListener("submit", function (e) {
    e.preventDefault();
    const datos = {};
    const formData = new FormData(formularioEnvioCompra);
    for (let [key, value] of formData.entries()) {
      datos[key] = value;
    }

    let isValid = true;
    const errorMessages = [];
    const requiredFields = ["nombre", "apellido", "provincia", "localidad", "ciudad", "cp_usuario", "email", "telefono"];

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
        errorMessages.push(`${field} es requerido.`);
      } else if (errorSpan) {
        errorSpan.textContent = "";
        errorSpan.style.display = "none";
      }
    });

    const validations = {
      email: value => !/\S+@\S+\.\S+/.test(value) && "Correo electrónico no válido.",
      cp_usuario: value => !/^[0-9]{4,8}$/.test(value) && "Código postal no válido (4-8 dígitos numéricos).",
      telefono: value => !/[0-9+ ]{7,15}/.test(value) && "Teléfono no válido.",
      provincia: value => !/^[A-Z]$/.test(value) && "Provincia no válida (selecciona del listado).",
      direccion: value => {
        if (!value || value.trim().length < 5) return "Dirección demasiado corta.";
        const parts = value.trim().split(' ');
        if (parts.length < 2 || !/\d/.test(parts[1])) return "Dirección debe incluir calle y número (ej. Calle 123).";
        return false;
      },
      localidad: value => value.trim().length < 2 && "Localidad demasiado corta.",
      ciudad: value => value.trim().length < 2 && "Ciudad demasiado corta."
    };

    for (const [field, validator] of Object.entries(validations)) {
      const value = datos[field];
      if (value) {
        const error = validator(value);
        if (error) {
          isValid = false;
          const errorSpan = document.getElementById(`error-${field}`);
          if (errorSpan) {
            errorSpan.textContent = error;
            errorSpan.style.display = "block";
          }
          errorMessages.push(error);
        }
      }
    }

    const tipoEnvio = datos.tipo_envio;
    if (!tipoEnvio) {
      isValid = false;
      errorMessages.push("Selecciona un tipo de envío.");
    } else if (tipoEnvio === "sucursal" && (!datos.selector_sucursal || datos.selector_sucursal === "")) {
      isValid = false;
      errorMessages.push("Selecciona una sucursal para retiro.");
    }

    if (isValid) {
      if (typeof enviarDatosAAPI === "function") {
        enviarDatosAAPI(datos);
      }
    } else {
      mostrarErrorAPI("Corrige los errores: " + errorMessages.join(" "));
    }
  });
}

// ==============================
// Navegación de pasos en modal
// ==============================
document.addEventListener("DOMContentLoaded", () => {
  let pasoActual = 1;
  const pasos = document.querySelectorAll(".paso");
  const btnAnterior = document.getElementById("btn-anterior");
  const btnSiguiente = document.getElementById("btn-siguiente");
  const btnConfirmar = document.getElementById("btn-confirmar");
  const metodoPago = document.getElementById("metodo_pago");
  const pagoTarjeta = document.getElementById("pago-tarjeta");
  const modalCompra = document.getElementById("modalCompra");

  function mostrarPaso(paso) {
    pasos.forEach((p, i) => p.classList.toggle("d-none", i !== paso - 1));
    btnAnterior.classList.add("d-none");
    btnSiguiente.classList.add("d-none");
    btnConfirmar.classList.add("d-none");

    if (paso === 1) btnSiguiente.classList.remove("d-none");
    else if (paso === 2) {
      btnAnterior.classList.remove("d-none");
      btnConfirmar.classList.remove("d-none");
    }
    pasoActual = paso;
  }

  if (btnAnterior) btnAnterior.addEventListener("click", () => { if (pasoActual > 1) mostrarPaso(pasoActual - 1); });
  if (btnSiguiente) btnSiguiente.addEventListener("click", () => { if (pasoActual < pasos.length) mostrarPaso(pasoActual + 1); });
  if (metodoPago) metodoPago.addEventListener("change", e => { if (pagoTarjeta) pagoTarjeta.classList.toggle("d-none", e.target.value !== "tarjeta"); });
  if (modalCompra) modalCompra.addEventListener("shown.bs.modal", () => { pasoActual = 1; mostrarPaso(pasoActual); });

  mostrarPaso(pasoActual);
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

// ==============================
// Funciones de errores y API
// ==============================
function mostrarErrorAPI(mensaje) {
  const errorDiv = document.getElementById('api-error');
  if (errorDiv) {
    errorDiv.textContent = mensaje;
    errorDiv.classList.remove('d-none');
  }
}

function ocultarErrorAPI() {
  const errorDiv = document.getElementById('api-error');
  if (errorDiv) errorDiv.classList.add('d-none');
}

async function enviarDatosAAPI(datos) {
  const direccionParts = datos.direccion.trim().split(' ');
  let streetName = "Calle Desconocida";
  let streetNumber = "123";
  if (direccionParts.length >= 2) {
    streetName = direccionParts.slice(0, -1).join(' ');
    const numeroMatch = direccionParts[direccionParts.length - 1].match(/\d+/);
    if (numeroMatch) streetNumber = numeroMatch[0];
  }

  const payload = {
    customerId: "0001079998",
    extOrderId: `order-${Date.now()}`,
    orderNumber: "102",
    sender: {
      name: "Tu Tienda",
      phone: "123456789",
      email: "tienda@example.com",
      originAddress: {
        streetName: "Calle Origen",
        streetNumber: "123",
        city: "Ciudad Origen",
        provinceCode: "B",
        postalCode: "8407"
      }
    },
    recipient: {
      name: `${datos.nombre} ${datos.apellido}`,
      phone: datos.telefono,
      email: datos.email
    },
    shipping: {
      deliveryType: datos.tipo_envio === "domicilio" ? "D" : "S",
      agency: datos.tipo_envio === "sucursal" ? datos.selector_sucursal : null,
      productType: "CP",
      address: {
        streetName: streetName,
        streetNumber: streetNumber,
        city: datos.ciudad,
        provinceCode: datos.provincia,
        postalCode: datos.cp_usuario
      },
      weight: 1000,
      declaredValue: 500.00,
      height: 10,
      length: 30,
      width: 20
    }
  };

  try {
    const response = await fetch("/importar_envio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (response.ok && result.createdAt) {
      alert("Envío importado exitosamente. ¡Compra confirmada!");
      ocultarErrorAPI();
      const modal = bootstrap.Modal.getInstance(document.getElementById('modalCompra'));
      modal.hide();
    } else {
      mostrarErrorAPI("Error: " + (result.message || "Desconocido"));
    }
  } catch (error) {
    mostrarErrorAPI("Error de conexión al importar envío.");
  }
}

async function cargarSucursales(provinceCode) {
  try {
    const response = await fetch(`/sucursales?customerId=0001079998&provinceCode=${provinceCode}`);
    const data = await response.json();
    const select = document.getElementById('selector-sucursal');
    select.innerHTML = '<option value="">Seleccione una sucursal</option>';
    if (Array.isArray(data)) {
      data.forEach(suc => {
        select.innerHTML += `<option value="${suc.code}">${suc.name}</option>`;
      });
    }
    document.getElementById('campo-sucursal').classList.remove('d-none');
  } catch (error) {
    mostrarErrorAPI("Error al cargar sucursales.");
  }
}

// ==============================
// Eventos para sucursales
// ==============================
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('input[name="tipo_envio"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      if (e.target.value === 'sucursal') {
        const provinceCode = document.getElementById('provincia').value;
        if (provinceCode) cargarSucursales(provinceCode);
        else mostrarErrorAPI("Selecciona una provincia primero.");
      } else {
        document.getElementById('campo-sucursal').classList.add('d-none');
      }
    });
  });

  const provinciaSelect = document.getElementById('provincia');
  if (provinciaSelect) {
    provinciaSelect.addEventListener('change', () => {
      const tipoEnvioSeleccionado = document.querySelector('input[name="tipo_envio"]:checked');
      if (tipoEnvioSeleccionado && tipoEnvioSeleccionado.value === 'sucursal') {
        const provinceCode = provinciaSelect.value;
        if (provinceCode) cargarSucursales(provinceCode);
        else mostrarErrorAPI("Selecciona una provincia válida.");
      }
    });
  }
});
