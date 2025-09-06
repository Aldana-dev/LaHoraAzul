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
