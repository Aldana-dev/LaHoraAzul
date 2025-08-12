document
    .getElementById("btn-cotizar-envio")
    .addEventListener("click", async () => {
        const cpDestino = document.getElementById("cp_destino").value.trim();
        if (!cpDestino) {
            alert("Por favor ingrese un Código Postal de destino.");
            return;
        }

        // ⚠ Ajusta estos valores según tu negocio
        const datosCotizacion = {
            customerId: "0001656097", // ID proporcionado por MiCorreo
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
                // Tomamos la tarifa de entrega a domicilio
                const tarifaDomicilio = data.rates.find(
                    (r) => r.deliveredType === "D"
                );
                if (tarifaDomicilio) {
                    const precio = tarifaDomicilio.price.toFixed(2);
                    document.getElementById(
                        "precio-domicilio"
                    ).textContent = `$${precio}`;
                    document.getElementById("costo-envio").textContent = `$${precio}`;

                    const subtotal = parseFloat("{{ subtotal }}");
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
    });
