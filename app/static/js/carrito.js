// Función para calcular cotización
async function calcularCotizacion(cpDestino) {
    if (!cpDestino) {
        alert("Por favor ingrese un Código Postal de destino.");
        return;
    }

    const datosCotizacion = {
        customerId: "0001079998", // ID proporcionado por MiCorreo
        postalCodeOrigin: "8407", // CP de tu tienda/origen
        postalCodeDestination: cpDestino,
        deliveredType: "D", // "D" a domicilio, "S" a sucursal
        dimensions: {
            weight: 1000, // en gramos
            height: 10, // cm
            width: 20, // cm
            length: 30, // cm
        },
    };

    try {
        const resp = await fetch("/cotizar_envio", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datosCotizacion),
        });

        if (!resp.ok) {
            throw new Error(`Error en la cotización: ${resp.status}`);
        }

        const data = await resp.json();

        if (data.rates && data.rates.length > 0) {
            const tarifaDomicilio = data.rates.find(r => r.deliveredType === "D");
            if (tarifaDomicilio) {
                const precio = tarifaDomicilio.price.toFixed(2);
                document.getElementById("precio-domicilio").textContent = `$${precio}`;
                document.getElementById("costo-envio").textContent = `$${precio}`;

                const subtotalElem = document.getElementById("subtotal");
                const subtotal = subtotalElem ? parseFloat(subtotalElem.textContent.replace('$', '')) : 0;

                document.getElementById("total-compra").textContent = `$${(
                    subtotal + tarifaDomicilio.price
                ).toFixed(2)}`;

            } else {
                alert("No se encontró tarifa para entrega a domicilio.");
            }
        } else {
            alert("No se obtuvieron tarifas para este destino.");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("No se pudo calcular el costo de envío.");
    }
}

// Ejecutar cotización inicial al cargar la página con CP 8300
document.addEventListener("DOMContentLoaded", () => {
    calcularCotizacion("8300");
});

// Asignar el botón para que el usuario pueda recalcular
document.getElementById("btn-cotizar-envio").addEventListener("click", () => {
    const cpDestino = document.getElementById("cp_destino").value.trim();
    calcularCotizacion(cpDestino);
});

document.getElementById("btn-guardar-pedido").addEventListener("click", async () => {
    const form = document.getElementById("form-datos-usuario");
    const formData = new FormData(form);

    // Convertimos FormData a objeto JSON
    const datos = {};
    formData.forEach((value, key) => {
        datos[key] = value;
    });

    // Total del pedido (subtotal + envío)
    const subtotal = parseFloat(document.getElementById("subtotal").textContent.replace("$", "")) || 0;
    const costoEnvio = parseFloat(document.getElementById("costo-envio").textContent.replace("$", "")) || 0;
    datos.total = subtotal + costoEnvio;

    // Aquí opcionalmente agregamos los productos del carrito
    const productos = [];
    document.querySelectorAll(".item-carrito").forEach(item => {
        productos.push({
            nombre: item.querySelector(".nombre-producto").textContent,
            precio: parseFloat(item.querySelector(".precio").textContent.replace("$", ""))
        });
    });
    datos.productos = productos;

    try {
        const resp = await fetch("/carrito/confirmar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos),
        });

        if (!resp.ok) throw new Error("Error guardando pedido");

        const result = await resp.json();
        alert(`Pedido guardado con ID ${result.id}`);
    } catch (error) {
        console.error(error);
        alert("No se pudo guardar el pedido.");
    }
});
// Actualiza el campo oculto costo_envio antes de enviar el formulario
const btnPagar = document.getElementById("btn-pagar");
const inputCostoEnvio = document.getElementById("costo_envio_hidden");
const spanCostoEnvio = document.getElementById("costo-envio"); // desde tu resumen

btnPagar.addEventListener("click", () => {
    // Obtener valor del costo de envío (sin $ y convertir a float)
    let costo = parseFloat(spanCostoEnvio.textContent.replace('$','')) || 0;
    inputCostoEnvio.value = costo;

    // Enviar formulario
    document.getElementById("form-datos-usuario").submit();
});
