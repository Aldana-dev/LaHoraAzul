// Variables globales
let pasoActual = 1;
let datosFormulario = {};

// Muestra el paso actual del modal
function mostrarPaso(paso) {
  const pasos = document.querySelectorAll(".paso");
  const btnAnterior = document.getElementById("btn-anterior");
  const btnSiguiente = document.getElementById("btn-siguiente");
  const btnConfirmar = document.getElementById("btn-confirmar");

  pasos.forEach((p, i) => p.classList.toggle("d-none", i !== paso - 1));

  btnAnterior?.classList.add("d-none");
  btnSiguiente?.classList.add("d-none");
  btnConfirmar?.classList.add("d-none");

  if (paso === 1) {
    btnSiguiente?.classList.remove("d-none");
  } else if (paso === 2) {
    btnAnterior?.classList.remove("d-none");
    btnConfirmar?.classList.remove("d-none");
  }

  pasoActual = paso;
}

// Cotización global (carrito)
function mostrarCotizacionGlobal(tipo, precio, minDias, maxDias) {
  const labelPrincipal = document.querySelector(`.tarjeta-envio[data-tipo="${tipo}"]`);
  if (labelPrincipal) actualizarLabel(labelPrincipal, precio, minDias, maxDias);
}

// Actualiza el label de cotización en carrito
function actualizarLabel(label, precio, minDias, maxDias) {
  if (!label) return;

  const spanPrecio = label.querySelector(".precio-opcion");
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

// Consulta API y cotiza un envío
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

    if (!resp.ok) throw new Error();
    const data = await resp.json();

    if (data.rates?.length > 0) {
      const tarifa = data.rates.find(r => r.deliveredType === datosCotizacion.deliveredType);
      mostrarCotizacionGlobal(tipo, tarifa?.price ?? null, tarifa?.deliveryTimeMin, tarifa?.deliveryTimeMax);
      ocultarErrorAPI();
    } else {
      mostrarCotizacionGlobal(tipo, null);
      mostrarErrorAPI("No se encontraron tarifas para este destino.");
    }
  } catch {
    mostrarCotizacionGlobal(tipo, null);
    mostrarErrorAPI("Error al cotizar el envío.");
  }
}

// Ejecuta cotización domicilio + sucursal
function calcularCotizaciones(cpDestino) {
  if (!cpDestino) {
    mostrarErrorAPI("Por favor ingrese un Código Postal de destino.");
    return;
  }
  cotizarEnvio(cpDestino, "domicilio");
  cotizarEnvio(cpDestino, "sucursal");
}

// Convierte "$1234" en número
function parseCurrency(str) {
  return parseFloat(str.replace(/[^0-9.-]+/g, "")) || 0;
}

// Actualiza resumen (carrito o modal)
function actualizarResumen(contexto = 'carrito') {
  let seleccionado = contexto === 'carrito'
    ? document.querySelector('input[name="opcion-envio"]:checked')
    : document.querySelector('input[name="tipo_envio"]:checked');

  if (!seleccionado) return;

  const label = seleccionado.closest("label");
  if (!label) return;

  const precioEnvio = parseFloat(label.dataset.precio || 0);

  const subtotalElement = contexto === 'carrito'
    ? document.getElementById("subtotal")
    : document.getElementById("subtotal-modal");

  if (!subtotalElement) return;

  const subtotal = parseCurrency(subtotalElement.textContent);

  const costoEnvioElement = contexto === 'carrito'
    ? document.getElementById("costo-envio")
    : document.getElementById("costo-envio-modal");

  if (costoEnvioElement) costoEnvioElement.textContent = `$${precioEnvio.toFixed(2)}`;

  const totalFinal = subtotal + precioEnvio;

  const totalCompraElement = contexto === 'carrito'
    ? document.getElementById("total-compra")
    : document.getElementById("total-compra-modal");

  if (totalCompraElement) totalCompraElement.textContent = `$${totalFinal.toFixed(2)}`;

  // Actualiza campo oculto solo en modal (para el pago)
  if (contexto === 'modal') {
    const totalCarritoInput = document.getElementById("total-carrito");
    if (totalCarritoInput) {
      totalCarritoInput.value = Math.round(totalFinal * 100).toString();
    }
  }
}

// Inicializa subtotal del carrito
function inicializarSubtotal() {
  const subtotalElement = document.getElementById("subtotal");
  if (subtotalElement) actualizarResumen('carrito');
}

// Inicialización general modal + carrito
document.addEventListener("DOMContentLoaded", () => {
  const btnAnterior = document.getElementById("btn-anterior");
  const btnSiguiente = document.getElementById("btn-siguiente");
  const btnConfirmar = document.getElementById("btn-confirmar");
  const modalCompra = document.getElementById("modalCompra");

  if (btnAnterior) {
    btnAnterior.addEventListener("click", () => {
      if (pasoActual > 1) mostrarPaso(pasoActual - 1);
    });
  }

  if (btnSiguiente) {
    btnSiguiente.addEventListener("click", () => {
      if (pasoActual === 1 && validarYGuardarPaso1()) {
        mostrarPaso(2);
      }
    });
  }

  if (btnConfirmar) {
    btnConfirmar.addEventListener("click", () => {
      if (pasoActual === 2) {
        // Pago se procesa en token.js
      }
    });
  }

  if (modalCompra) {
    modalCompra.addEventListener("shown.bs.modal", () => {
      pasoActual = 1;
      mostrarPaso(1);
    });
  }

  inicializarSubtotal();

  const cpDestinoInicial = document.getElementById("cp_destino")?.value.trim();
  if (cpDestinoInicial) calcularCotizaciones(cpDestinoInicial);

  const btnCotizar = document.getElementById("btn-cotizar-envio");
  if (btnCotizar) {
    btnCotizar.addEventListener("click", () => {
      const cpDestino = document.getElementById("cp_destino")?.value.trim();
      if (cpDestino) calcularCotizaciones(cpDestino);
      else mostrarErrorAPI("Por favor ingrese un Código Postal de destino.");
    });
  }

  document.querySelectorAll('input[name="opcion-envio"]').forEach(radio => {
    radio.addEventListener("change", () => actualizarResumen('carrito'));
  });

  if (modalCompra) {
    modalCompra.addEventListener("shown.bs.modal", () => {
      const subtotalPrincipal = document.getElementById("subtotal");
      const subtotalModal = document.getElementById("subtotal-modal");

      if (subtotalPrincipal && subtotalModal) {
        const subtotalValue = parseCurrency(subtotalPrincipal.textContent);
        subtotalModal.textContent = `$${subtotalValue.toFixed(2)}`;
      }

      ['domicilio', 'sucursal'].forEach(tipo => {
        const labelPrincipal = document.querySelector(`.tarjeta-envio[data-tipo="${tipo}"]`);
        const labelModal = document.querySelector(`#modal-tarjetas-envio label[data-tipo="${tipo}"]`);

        if (labelPrincipal && labelModal) {
          const precio = parseFloat(labelPrincipal.dataset.precio || 0);
          labelModal.dataset.precio = precio;

          const spanPrecioModal = labelModal.querySelector('.precio-opcion-modal');
          if (spanPrecioModal) {
            spanPrecioModal.textContent = precio > 0 ? `$${precio.toFixed(2)}` : 'Ingrese CP arriba';
          }
        }
      });

      const envioSeleccionadoPrincipal = document.querySelector('input[name="opcion-envio"]:checked');
      if (envioSeleccionadoPrincipal) {
        const valorEnvio = envioSeleccionadoPrincipal.value;
        const radioModal = document.querySelector(`input[name="tipo_envio"][value="${valorEnvio}"]`);
        if (radioModal) radioModal.checked = true;
      }

      actualizarResumen('modal');
    });
  }
});

// Cotización dentro del modal
async function cotizarEnvioModal(cpDestino) {
  if (!cpDestino) {
    mostrarErrorAPI("Por favor ingrese un Código Postal de destino.");
    return;
  }
  try {
    await cotizarEnvioModalTipo(cpDestino, "domicilio");
    await cotizarEnvioModalTipo(cpDestino, "sucursal");
  } catch {
    mostrarErrorAPI("Error al cotizar en el modal.");
  }
}

// Cotiza un tipo de envío en el modal
async function cotizarEnvioModalTipo(cpDestino, tipo) {
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

    if (!resp.ok) throw new Error();
    const data = await resp.json();

    if (data.rates?.length > 0) {
      const tarifa = data.rates.find(r => r.deliveredType === datosCotizacion.deliveredType);
      actualizarLabelModal(tipo, tarifa?.price ?? null, tarifa?.deliveryTimeMin, tarifa?.deliveryTimeMax);
      ocultarErrorAPI();
    } else {
      actualizarLabelModal(tipo, null);
      mostrarErrorAPI("No se encontraron tarifas para este destino.");
    }
  } catch {
    actualizarLabelModal(tipo, null);
    mostrarErrorAPI("Error al cotizar el envío.");
  }
}

// Actualiza label del modal
function actualizarLabelModal(tipo, precio, minDias, maxDias) {
  const labelModal = document.querySelector(`#modal-tarjetas-envio label[data-tipo="${tipo}"]`);
  if (!labelModal) return;

  const spanPrecio = labelModal.querySelector('.precio-opcion-modal');
  const spanTiempo = labelModal.querySelector('.texto-envio');

  if (precio != null) {
    if (spanPrecio) spanPrecio.textContent = `$${precio.toFixed(2)}`;
    labelModal.dataset.precio = precio;
    if (spanTiempo) spanTiempo.textContent = `${minDias} a ${maxDias} días hábiles`;
    const input = labelModal.querySelector('input');
    if (input) input.disabled = false;
  } else {
    if (spanPrecio) spanPrecio.textContent = "No disponible";
    if (spanTiempo) spanTiempo.textContent = "";
    labelModal.dataset.precio = 0;
    const input = labelModal.querySelector('input');
    if (input) input.disabled = true;
  }

  const radioInput = labelModal.querySelector('input[name="tipo_envio"]');
  if (radioInput && radioInput.checked) actualizarResumen('modal');
}
document.addEventListener("DOMContentLoaded", () => {

  // Actualizar resumen cuando cambie el tipo de envío
  document.querySelectorAll('input[name="tipo_envio"]').forEach(radio => {
    radio.addEventListener("change", () => {
      actualizarResumen('modal');
    });
  });

  // Mostrar u ocultar el campo de sucursal
  document.querySelectorAll('input[name="tipo_envio"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      const campo = document.getElementById('campo-sucursal');

      if (e.target.value === 'sucursal') {
        if (campo) campo.classList.remove('d-none');

        const provinceCode = document.getElementById('provincia').value;
        if (provinceCode) {
          cargarSucursales(provinceCode);
        } else {
          mostrarErrorAPI("Selecciona una provincia primero.");
        }
      } else {
        if (campo) campo.classList.add('d-none');
      }
    });
  });

  // Cargar sucursales al cambiar provincia
  const provinciaSelect = document.getElementById('provincia');
  if (provinciaSelect) {
    provinciaSelect.addEventListener('change', () => {
      const tipoEnvio = document.querySelector('input[name="tipo_envio"]:checked');
      if (tipoEnvio && tipoEnvio.value === 'sucursal') {
        const provinceCode = provinciaSelect.value;
        if (provinceCode) cargarSucursales(provinceCode);
        else mostrarErrorAPI("Selecciona una provincia válida.");
      }
    });
  }
});


// Cargar sucursales dinámicamente
async function cargarSucursales(provinceCode) {
  const selector = document.getElementById('selector-sucursal');
  const horariosSmall = document.getElementById('horarios-sucursal');

  if (!selector) return;

  selector.innerHTML = '<option value="">Cargando sucursales...</option>';
  if (horariosSmall) horariosSmall.textContent = '';

  try {
    const customerId = "0001079998";
    const response = await fetch(`/sucursales?customerId=${customerId}&provinceCode=${provinceCode}`);
    if (!response.ok) throw new Error();

    const data = await response.json();
    const sucursales = Array.isArray(data) ? data : data.agencies || [];

    selector.innerHTML = '<option value="">Seleccione una sucursal</option>';
    sucursales.forEach(sucursal => {
      const option = document.createElement('option');
      option.value = sucursal.id;
      option.textContent = sucursal.name || sucursal.nombre;
      selector.appendChild(option);
    });

    if (sucursales.length === 0) {
      selector.innerHTML = '<option value="">No hay sucursales disponibles</option>';
      if (horariosSmall) horariosSmall.textContent = 'No se encontraron sucursales.';
    } else {
      selector.addEventListener('change', () => {
        const selectedId = selector.value;
        const selectedSucursal = sucursales.find(s => s.id == selectedId);
        if (selectedSucursal && (selectedSucursal.schedule || selectedSucursal.horario)) {
          if (horariosSmall) horariosSmall.textContent =
            `Horarios: ${selectedSucursal.schedule || selectedSucursal.horario}`;
        } else if (horariosSmall) {
          horariosSmall.textContent = '';
        }
      });
    }

  } catch (error) {
    selector.innerHTML = '<option value="">Error al cargar sucursales</option>';
    mostrarErrorAPI('Error al cargar sucursales. Intenta de nuevo.');
  }
}


// Validar y guardar datos en memoria
function validarYGuardarPaso1() {
  const requiredFields = ["nombre", "apellido", "provincia", "localidad", "ciudad", "email", "telefono"];
  const tipoEnvio = document.querySelector('input[name="tipo_envio"]:checked')?.value;

  if (tipoEnvio !== "local") {
    requiredFields.push("cp_usuario", "direccion");
  }

  let isValid = true;
  const errores = [];

  requiredFields.forEach(field => {
    const input = document.getElementById(field);
    const errorSpan = document.getElementById(`error-${field}`);
    const value = input?.value.trim() || "";

    if (!value) {
      isValid = false;
      if (errorSpan) {
        errorSpan.textContent = "Este campo es requerido.";
        errorSpan.style.display = "block";
      }
      errores.push(`${field} es requerido.`);
    } else if (errorSpan) {
      errorSpan.textContent = "";
      errorSpan.style.display = "none";
    }

    datosFormulario[field] = value;
  });

  const validations = {
    email: value => !/\S+@\S+\.\S+/.test(value) ? "Email no válido" : null,
    telefono: value => !/[0-9+ ]{7,15}/.test(value) ? "Teléfono no válido" : null,
    localidad: value => value.length < 2 ? "Localidad demasiado corta" : null,
    ciudad: value => value.length < 2 ? "Ciudad demasiado corta" : null,
  };

  for (const [field, validator] of Object.entries(validations)) {
    const value = datosFormulario[field] || "";
    const error = validator(value);
    if (error) {
      isValid = false;
      const errorSpan = document.getElementById(`error-${field}`);
      if (errorSpan) {
        errorSpan.textContent = error;
        errorSpan.style.display = "block";
      }
      errores.push(error);
    }
  }

  datosFormulario.tipo_envio = tipoEnvio;
  datosFormulario.selector_sucursal = document.getElementById('selector-sucursal')?.value;
  datosFormulario.mensaje = document.getElementById('mensaje')?.value || '';

  if (!isValid) {
    mostrarErrorAPI(errores.join(" | "));
    return false;
  }

  mostrarErrorAPI("");
  return true;
}


// Guardar paso 1 en BD
async function guardarPaso1EnBD() {
  try {
    const total = (parseInt(document.getElementById('total-carrito')?.value) || 0) / 100;

    const datosPedido = {
      nombre: datosFormulario.nombre,
      apellido: datosFormulario.apellido,
      email: datosFormulario.email,
      telefono: datosFormulario.telefono,
      provincia: datosFormulario.provincia,
      localidad: datosFormulario.localidad,
      ciudad: datosFormulario.ciudad,
      direccion: datosFormulario.direccion || '',
      cp_usuario: datosFormulario.cp_usuario || '',
      tipo_envio: datosFormulario.tipo_envio,
      total: total,
      comentarios: datosFormulario.mensaje
    };

    const response = await fetch('/carrito/confirmar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datosPedido)
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      mostrarErrorAPI(result.error || 'Error al guardar el pedido');
      return null;
    }

    datosFormulario.pedido_id = result.pedido_id;
    return result.pedido_id;

  } catch (error) {
    mostrarErrorAPI('Error de conexión al guardar pedido');
    return null;
  }
}


// Importar envío a Correo Argentino
async function importarEnvio() {
  if (datosFormulario.tipo_envio === 'local') return true;

  try {
    const total = (parseInt(document.getElementById('total-carrito')?.value) || 0) / 100;

    let deliveryType = datosFormulario.tipo_envio === 'sucursal' ? 'S' : 'D';
    let streetName = 'Calle Desconocida';
    let streetNumber = '123';

    if (datosFormulario.direccion) {
      const match = datosFormulario.direccion.trim().match(/^(.+)\s+(\d+)$/);
      if (match) {
        streetName = match[1].trim();
        streetNumber = match[2];
      }
    }

    const payload = {
      customerId: '0001079998',
      extOrderId: `order-${Date.now()}`,
      orderNumber: datosFormulario.pedido_id || '102',
      sender: {
        name: 'La Hora Azul',
        phone: '123456789',
        email: 'lahoraazul@example.com',
        originAddress: {
          streetName: 'Calle Origen',
          streetNumber: '123',
          city: 'Ciudad Origen',
          provinceCode: 'B',
          postalCode: '8407'
        }
      },
      recipient: {
        name: `${datosFormulario.nombre} ${datosFormulario.apellido}`,
        phone: datosFormulario.telefono,
        email: datosFormulario.email
      },
      shipping: {
        deliveryType: deliveryType,
        agency: datosFormulario.tipo_envio === 'sucursal' ? datosFormulario.selector_sucursal : null,
        productType: 'CP',
        address: {
          streetName: streetName,
          streetNumber: streetNumber,
          city: datosFormulario.ciudad,
          provinceCode: datosFormulario.provincia,
          postalCode: datosFormulario.cp_usuario
        },
        weight: 1000,
        declaredValue: total,
        height: 10,
        length: 30,
        width: 20
      }
    };

    const response = await fetch('/importar_envio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (!response.ok || !result.createdAt) return false;

    return true;

  } catch {
    return false;
  }
}


// Mostrar resumen final
function mostrarResumenFinal() {
  const resumenUl = document.getElementById('resumen-compra');
  if (resumenUl) {
    const total = (parseInt(document.getElementById('total-carrito')?.value) || 0) / 100;

    let tipoEnvioTexto = 'Retiro en el local';
    if (datosFormulario.tipo_envio === 'domicilio') tipoEnvioTexto = 'Envío a domicilio';
    if (datosFormulario.tipo_envio === 'sucursal') tipoEnvioTexto = 'Envío a sucursal';

    resumenUl.innerHTML = `
      <li><strong>Pedido ID:</strong> ${datosFormulario.pedido_id || 'N/A'}</li>
      <li><strong>Cliente:</strong> ${datosFormulario.nombre} ${datosFormulario.apellido}</li>
      <li><strong>Email:</strong> ${datosFormulario.email}</li>
      <li><strong>Teléfono:</strong> ${datosFormulario.telefono}</li>
      <li><strong>Tipo de Envío:</strong> ${tipoEnvioTexto}</li>
      <li><strong>Dirección:</strong> ${datosFormulario.direccion || 'Retiro en local'}</li>
      <li><strong>Total:</strong> $${total.toFixed(2)}</li>
    `;
  }
}


// Finalizar compra (llamado por token.js)
async function procesarCompraFinal() {
  try {
    const carritoItems = document.querySelectorAll('.item-carrito');
    const carrito_ids = Array.from(carritoItems)
      .map(item => parseInt(item.getAttribute('data-producto-id')))
      .filter(id => id);

    const total = (parseInt(document.getElementById('total-carrito')?.value) || 0) / 100;

    const datosConfirmacion = {
      nombre: datosFormulario.nombre,
      apellido: datosFormulario.apellido,
      email: datosFormulario.email,
      telefono: datosFormulario.telefono,
      provincia: datosFormulario.provincia,
      localidad: datosFormulario.localidad,
      ciudad: datosFormulario.ciudad,
      direccion: datosFormulario.direccion || '',
      cp_usuario: datosFormulario.cp_usuario || '',
      tipo_envio: datosFormulario.tipo_envio,
      total: total,
      comentarios: datosFormulario.mensaje,
      carrito_ids: carrito_ids,
      metodo_pago: datosFormulario.metodo_pago,
      payment_id: datosFormulario.payment_id,
      payment_token: datosFormulario.payment_token,
      payment_ticket: datosFormulario.payment_ticket,
      payment_authorization: datosFormulario.payment_authorization
    };

    const envioImportado = await importarEnvio();
    if (!envioImportado && datosFormulario.tipo_envio !== 'local') {
      mostrarErrorAPI('Pedido confirmado, pero hubo un problema al procesar el envío.');
    }

    const response = await fetch('/carrito/confirmar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datosConfirmacion)
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      mostrarErrorAPI(result.error || 'Error al confirmar pedido');
      return;
    }

    datosFormulario.pedido_id = result.pedido_id;

    mostrarResumenFinal();
    mostrarPaso(3);
    ocultarErrorAPI();

  } catch {
    mostrarErrorAPI('Error al completar la compra');
  }
}


// Manejo global de errores
function mostrarErrorAPI(mensaje) {
  const errorDiv = document.getElementById('api-error');
  if (errorDiv) {
    if (mensaje) {
      errorDiv.textContent = mensaje;
      errorDiv.classList.remove('d-none');
    } else {
      errorDiv.classList.add('d-none');
    }
  }
}

function ocultarErrorAPI() {
  const errorDiv = document.getElementById('api-error');
  if (errorDiv) errorDiv.classList.add('d-none');
}
