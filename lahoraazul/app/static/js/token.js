class PaywayIntegration {
    constructor(publicKey) {
        const urlSandbox = "https://developers.decidir.com/api/v2";
        this.decidir = new Decidir(urlSandbox, true);
        this.decidir.setPublishableKey(publicKey);
        this.decidir.setTimeout(5000);

        this.form = null;
        this.isProcessing = false;
    }

    initForm(formId) {
        this.form = document.querySelector(formId);
        if (!this.form) {
            console.error(`Formulario ${formId} no encontrado`);
            return;
        }
        this.setupFieldFormatting();
    }

    setupFieldFormatting() {
        const numeroTarjeta = document.querySelector('#numero_tarjeta');
        const mesVencimiento = document.querySelector('#mes_vencimiento');
        const anioVencimiento = document.querySelector('#anio_vencimiento');
        const cvv = document.querySelector('#cvv');
        const dni = document.querySelector('#dni');

        if (numeroTarjeta) {
            numeroTarjeta.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\s/g, '');
                value = value.replace(/\D/g, '');
                value = value.substring(0, 16);
                e.target.value = value.replace(/(\d{4})/g, '$1 ').trim();
            });
        }

        if (mesVencimiento) {
            mesVencimiento.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length >= 1) {
                    const num = parseInt(value);
                    if (num > 12) value = '12';
                    if (num === 0) value = '01';
                }
                e.target.value = value.substring(0, 2);
            });
        }

        if (anioVencimiento) {
            anioVencimiento.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 2);
            });
        }

        if (cvv) {
            cvv.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 4);
            });
        }

        if (dni) {
            dni.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 10);
            });
        }
    }

    validateCardFields() {
        const errors = [];

        const numeroTarjeta = document.querySelector('#numero_tarjeta').value.replace(/\s/g, '');
        if (!numeroTarjeta || numeroTarjeta.length < 15) {
            errors.push({ field: 'numero_tarjeta', message: 'Número de tarjeta inválido' });
        }

        const mes = document.querySelector('#mes_vencimiento').value;
        const mesNum = parseInt(mes);
        if (!mes || mesNum < 1 || mesNum > 12) {
            errors.push({ field: 'mes_vencimiento', message: 'Mes de vencimiento inválido' });
        }

        const anio = document.querySelector('#anio_vencimiento').value;
        const anioActual = new Date().getFullYear() % 100;
        const anioNum = parseInt(anio);
        if (!anio || anioNum < anioActual) {
            errors.push({ field: 'anio_vencimiento', message: 'Año de vencimiento inválido' });
        }

        const cvv = document.querySelector('#cvv').value;
        if (!cvv || cvv.length < 3) {
            errors.push({ field: 'cvv', message: 'CVV inválido' });
        }

        const titular = document.querySelector('#titular').value.trim();
        if (!titular || titular.length < 3) {
            errors.push({ field: 'titular', message: 'Nombre del titular inválido' });
        }

        const dni = document.querySelector('#dni').value;
        if (!dni || dni.length < 7) {
            errors.push({ field: 'dni', message: 'Número de documento inválido' });
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    async generatePaymentToken() {
        if (this.isProcessing) {
            return { success: false, error: 'Procesamiento en curso' };
        }

        const validation = this.validateCardFields();
        if (!validation.isValid) {
            return {
                success: false,
                error: 'Errores de validación',
                details: validation.errors
            };
        }

        this.isProcessing = true;

        return new Promise((resolve) => {
            try {
                const sdkCallback = (status, response) => {
                    this.isProcessing = false;

                    if (status === 200 || status === 201) {
                        const token = response.token || response.id;
                        resolve({
                            success: true,
                            token: token,
                            status: status,
                            rawResponse: response
                        });
                    } else {
                        const errorMessage = this.parseSDKError(response);
                        resolve({
                            success: false,
                            error: errorMessage,
                            status: status,
                            details: response
                        });
                    }
                };

                this.decidir.createToken(this.form, sdkCallback);

            } catch (error) {
                this.isProcessing = false;
                resolve({
                    success: false,
                    error: 'Error inesperado al generar el token',
                    details: error.message
                });
            }
        });
    }

    parseSDKError(response) {
        if (!response || !response.error) {
            return 'Error desconocido al generar el token';
        }

        if (Array.isArray(response.error)) {
            const messages = response.error.map(err => {
                if (err.error && err.error.message) {
                    return err.error.message;
                }
                return 'Error de validación';
            });
            return messages.join(', ');
        }

        if (response.error.message) {
            return response.error.message;
        }

        return 'Error al procesar los datos de la tarjeta';
    }

    clearCardFields() {
        const fields = [
            '#numero_tarjeta',
            '#mes_vencimiento',
            '#anio_vencimiento',
            '#cvv',
            '#titular',
            '#dni'
        ];

        fields.forEach(selector => {
            const field = document.querySelector(selector);
            if (field) field.value = '';
        });
    }

    getCardBin() {
        const numeroTarjeta = document.querySelector('#numero_tarjeta').value.replace(/\s/g, '');
        return numeroTarjeta.substring(0, 6);
    }

    getLastFourDigits() {
        const numeroTarjeta = document.querySelector('#numero_tarjeta').value.replace(/\s/g, '');
        return numeroTarjeta.substring(numeroTarjeta.length - 4);
    }
}

let paywayIntegration = null;

function initPaywayIntegration(publicKey) {
    paywayIntegration = new PaywayIntegration(publicKey);
    paywayIntegration.initForm('#form-datos-usuario');
}

async function procesarPagoConPayway() {
    if (!paywayIntegration) {
        console.error('Payway no está inicializado');
        return { success: false, error: 'SDK no inicializado' };
    }

    try {
        mostrarLoading(true);
        const tokenResult = await paywayIntegration.generatePaymentToken();

        if (!tokenResult.success) {
            mostrarErrorAPI(tokenResult.error || "Error al generar token de pago");
            mostrarLoading(false);
            return { success: false, error: tokenResult.error };
        }

        const token = tokenResult.token;
        const bin = paywayIntegration.getCardBin();

        const totalElement = document.getElementById("total-compra");
        let amount = 0;

        if (totalElement) {
            const totalText = totalElement.textContent.replace(/[^0-9.]/g, "");
            amount = Math.round(parseFloat(totalText) * 100);
        }

        if (amount <= 0) {
            mostrarErrorAPI("Error: El monto del carrito es inválido");
            mostrarLoading(false);
            return { success: false, error: "Monto inválido" };
        }

        const nombre = document.querySelector("#nombre")?.value || "Cliente";
        const apellido = document.querySelector("#apellido")?.value || "";
        const email = document.querySelector("#email")?.value || `guest_${Date.now()}@temp.com`;

        const userId = email;

        const paymentData = {
            amount: amount,
            token: token,
            user_id: userId,
            bin: bin,
            description: `Compra en La Hora Azul - ${nombre} ${apellido}`
        };

        const response = await fetch("/pago/crear", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(paymentData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Error del servidor: ${response.status}`);
        }

        const resultado = await response.json();

        if (resultado.status === "approved") {
            mostrarLoading(false);
            ocultarErrorAPI();

            return {
                success: true,
                payment_id: resultado.payment_id,
                ticket: resultado.ticket,
                authorization_code: resultado.authorization_code,
                amount: resultado.amount,
                currency: resultado.currency,
                card_brand: resultado.card_brand,
                token: token
            };

        } else if (resultado.status === "rejected") {
            const errorMsg = `Pago rechazado: ${resultado.message || resultado.error_reason || "Motivo desconocido"}`;
            mostrarErrorAPI(errorMsg);
            mostrarLoading(false);

            return {
                success: false,
                error: errorMsg,
                status: "rejected"
            };

        } else {
            mostrarErrorAPI("Error desconocido al procesar el pago");
            mostrarLoading(false);

            return {
                success: false,
                error: "Estado desconocido",
                status: resultado.status
            };
        }

    } catch (error) {
        console.error("Error:", error);
        mostrarErrorAPI(`Error al procesar el pago: ${error.message}`);
        mostrarLoading(false);

        return {
            success: false,
            error: error.message
        };
    }
}

function mostrarLoading(show) {
    const btnConfirmar = document.querySelector('#btn-confirmar');
    if (btnConfirmar) {
        btnConfirmar.disabled = show;
        btnConfirmar.textContent = show ? 'Procesando...' : 'Confirmar compra';
    }
}

function mostrarErrorAPI(mensaje) {
    const errorDiv = document.querySelector('#api-error');
    if (errorDiv) {
        errorDiv.textContent = mensaje;
        errorDiv.classList.remove('d-none');
        setTimeout(() => {
            errorDiv.classList.add('d-none');
        }, 5000);
    } else {
        alert(mensaje);
    }
}

function ocultarErrorAPI() {
    const errorDiv = document.querySelector('#api-error');
    if (errorDiv) {
        errorDiv.classList.add('d-none');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const btnConfirmar = document.querySelector('#btn-confirmar');
    const form = document.querySelector('#form-datos-usuario');

    let processingPayment = false;

    if (btnConfirmar && form) {
        btnConfirmar.addEventListener('click', async function (e) {
            e.preventDefault();
            if (processingPayment) {
                return;
            }

            processingPayment = true;

            const resultado = await procesarPagoConPayway();

            if (resultado.success) {
                if (typeof datosFormulario !== 'undefined') {
                    datosFormulario.payment_id = resultado.payment_id;
                    datosFormulario.payment_token = resultado.token;
                    datosFormulario.payment_ticket = resultado.ticket;
                    datosFormulario.payment_authorization = resultado.authorization_code;
                    datosFormulario.payment_amount = resultado.amount;
                    datosFormulario.payment_currency = resultado.currency;
                    datosFormulario.payment_card_brand = resultado.card_brand;
                    datosFormulario.metodo_pago = "tarjeta";

                    if (typeof procesarCompraFinal === 'function') {
                        await procesarCompraFinal();
                    } else {
                        console.error('procesarCompraFinal no encontrada');
                    }
                } else {
                    console.error('datosFormulario no encontrada');
                }

            } else {
                console.error('Pago fallido:', resultado.error);
                processingPayment = false;
            }
        });
    }
});
