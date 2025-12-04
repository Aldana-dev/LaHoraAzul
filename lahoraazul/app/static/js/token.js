class PaywayIntegration {
    constructor(publicKey) {
        console.log(`\n🔧 ========== INICIALIZANDO PAYWAY ==========`);
        console.log(`   Public Key: ${publicKey.substring(0, 20)}...`);

        const urlProduccion = "https://live.decidir.com/api/v2";
        console.log(`   URL: ${urlProduccion}`);

        this.decidir = new Decidir(urlProduccion);
        console.log(`   ✅ Decidir SDK instanciado`);

        this.decidir.setPublishableKey(publicKey);
        console.log(`   ✅ Public Key configurada`);

        this.decidir.setTimeout(3000);
        console.log(`   ✅ Timeout configurado: 3000ms`);

        this.form = null;
        this.isProcessing = false;
        console.log(`✅ PaywayIntegration constructor completado\n`);
    }

    initForm(formId) {
        console.log(`\n📋 ========== INICIALIZANDO FORMULARIO ==========`);
        console.log(`   Buscando formulario: ${formId}`);

        this.form = document.querySelector(formId);
        if (!this.form) {
            console.error(`❌ Formulario ${formId} NO ENCONTRADO`);
            return;
        }

        console.log(`✅ Formulario encontrado`);
        this.setupFieldFormatting();
    }

    setupFieldFormatting() {
        console.log(`\n🎯 ========== CONFIGURANDO CAMPOS ==========`);

        const numeroTarjeta = document.querySelector('#numero_tarjeta');
        const mesVencimiento = document.querySelector('#mes_vencimiento');
        const anioVencimiento = document.querySelector('#anio_vencimiento');
        const cvv = document.querySelector('#cvv');
        const dni = document.querySelector('#dni');

        if (numeroTarjeta) {
            console.log(`✅ Campo #numero_tarjeta encontrado`);
            numeroTarjeta.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\s/g, '');
                value = value.replace(/\D/g, '');
                value = value.substring(0, 16);
                e.target.value = value.replace(/(\d{4})/g, '$1 ').trim();
            });
        } else {
            console.warn(`⚠️ Campo #numero_tarjeta NO encontrado`);
        }

        if (mesVencimiento) {
            console.log(`✅ Campo #mes_vencimiento encontrado`);
            mesVencimiento.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length >= 1) {
                    const num = parseInt(value);
                    if (num > 12) value = '12';
                    if (num === 0) value = '01';
                }
                e.target.value = value.substring(0, 2);
            });
        } else {
            console.warn(`⚠️ Campo #mes_vencimiento NO encontrado`);
        }

        if (anioVencimiento) {
            console.log(`✅ Campo #anio_vencimiento encontrado`);
            anioVencimiento.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 2);
            });
        } else {
            console.warn(`⚠️ Campo #anio_vencimiento NO encontrado`);
        }

        if (cvv) {
            console.log(`✅ Campo #cvv encontrado`);
            cvv.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 4);
            });
        } else {
            console.warn(`⚠️ Campo #cvv NO encontrado`);
        }

        if (dni) {
            console.log(`✅ Campo #dni encontrado`);
            dni.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 10);
            });
        } else {
            console.warn(`⚠️ Campo #dni NO encontrado`);
        }

        console.log(`✅ Campos configurados\n`);
    }

    validateCardFields() {
        console.log(`\n✔️ ========== VALIDANDO CAMPOS ==========`);

        const errors = [];

        const numeroTarjeta = document.querySelector('#numero_tarjeta').value.replace(/\s/g, '');
        console.log(`   Número tarjeta: ****${numeroTarjeta.slice(-4)} (largo: ${numeroTarjeta.length})`);
        if (!numeroTarjeta || numeroTarjeta.length < 15) {
            errors.push({ field: 'numero_tarjeta', message: 'Número de tarjeta inválido' });
            console.error(`   ❌ Número de tarjeta inválido`);
        } else {
            console.log(`   ✅ Número de tarjeta válido`);
        }

        const mes = document.querySelector('#mes_vencimiento').value;
        const mesNum = parseInt(mes);
        console.log(`   Mes vencimiento: ${mes}`);
        if (!mes || mesNum < 1 || mesNum > 12) {
            errors.push({ field: 'mes_vencimiento', message: 'Mes de vencimiento inválido' });
            console.error(`   ❌ Mes de vencimiento inválido`);
        } else {
            console.log(`   ✅ Mes de vencimiento válido`);
        }

        const anio = document.querySelector('#anio_vencimiento').value;
        const anioActual = new Date().getFullYear() % 100;
        const anioNum = parseInt(anio);
        console.log(`   Año vencimiento: ${anio} (actual: ${anioActual})`);
        if (!anio || anioNum < anioActual) {
            errors.push({ field: 'anio_vencimiento', message: 'Año de vencimiento inválido' });
            console.error(`   ❌ Año de vencimiento inválido`);
        } else {
            console.log(`   ✅ Año de vencimiento válido`);
        }

        const cvv = document.querySelector('#cvv').value;
        console.log(`   CVV: *** (largo: ${cvv.length})`);
        if (!cvv || cvv.length < 3) {
            errors.push({ field: 'cvv', message: 'CVV inválido' });
            console.error(`   ❌ CVV inválido`);
        } else {
            console.log(`   ✅ CVV válido`);
        }

        const titular = document.querySelector('#titular').value.trim();
        console.log(`   Titular: ${titular}`);
        if (!titular || titular.length < 3) {
            errors.push({ field: 'titular', message: 'Nombre del titular inválido' });
            console.error(`   ❌ Titular inválido`);
        } else {
            console.log(`   ✅ Titular válido`);
        }

        const dni = document.querySelector('#dni').value;
        console.log(`   DNI: ${dni} (largo: ${dni.length})`);
        if (!dni || dni.length < 7) {
            errors.push({ field: 'dni', message: 'Número de documento inválido' });
            console.error(`   ❌ DNI inválido`);
        } else {
            console.log(`   ✅ DNI válido`);
        }

        console.log(`\n${errors.length === 0 ? '✅ TODAS LAS VALIDACIONES PASARON' : '❌ ERRORES DE VALIDACIÓN'}\n`);

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    async generatePaymentToken() {
        console.log(`\n🎫 ========== GENERANDO TOKEN DE PAGO ==========`);
        console.log(`   Timestamp: ${new Date().toISOString()}`);

        if (this.isProcessing) {
            console.error(`❌ Ya hay un procesamiento en curso`);
            return { success: false, error: 'Procesamiento en curso' };
        }

        const validation = this.validateCardFields();
        if (!validation.isValid) {
            console.error(`❌ Validación fallida`);
            console.error(`   Errores:`, validation.errors);
            return {
                success: false,
                error: 'Errores de validación',
                details: validation.errors
            };
        }

        this.isProcessing = true;
        console.log(`   🔒 isProcessing = true`);

        return new Promise((resolve) => {
            try {
                console.log(`\n🚀 Llamando a decidir.createToken()...`);
                console.log(`   Formulario:`, this.form);

                const sdkCallback = (status, response) => {
                    console.log(`\n📬 RESPUESTA DEL SDK RECIBIDA`);
                    console.log(`   Timestamp: ${new Date().toISOString()}`);
                    console.log(`   Status: ${status}`);
                    console.log(`   Response:`, JSON.stringify(response, null, 2));

                    this.isProcessing = false;
                    console.log(`   🔓 isProcessing = false`);

                    if (status === 200 || status === 201) {
                        const token = response.token || response.id;
                        console.log(`\n✅ TOKEN GENERADO EXITOSAMENTE`);
                        console.log(`   Token: ${token.substring(0, 30)}...${token.substring(token.length - 10)}`);
                        console.log(`   Status HTTP: ${status}\n`);

                        resolve({
                            success: true,
                            token: token,
                            status: status,
                            rawResponse: response
                        });
                    } else {
                        const errorMessage = this.parseSDKError(response);
                        console.error(`\n❌ ERROR AL GENERAR TOKEN`);
                        console.error(`   Status HTTP: ${status}`);
                        console.error(`   Mensaje: ${errorMessage}`);
                        console.error(`   Respuesta completa:`, response, '\n');

                        resolve({
                            success: false,
                            error: errorMessage,
                            status: status,
                            details: response
                        });
                    }
                };

                this.decidir.createToken(this.form, sdkCallback);
                console.log(`   ✅ createToken() llamado correctamente`);

            } catch (error) {
                this.isProcessing = false;
                console.error(`\n❌ EXCEPCIÓN EN TRY-CATCH`);
                console.error(`   Error: ${error.message}`);
                console.error(`   Stack:`, error.stack, '\n');

                resolve({
                    success: false,
                    error: 'Error inesperado al generar el token',
                    details: error.message
                });
            }
        });
    }

    parseSDKError(response) {
        console.log(`   📋 Parseando error del SDK...`);

        if (!response || !response.error) {
            console.log(`   ⚠️ Response no contiene 'error'`);
            return 'Error desconocido al generar el token';
        }

        if (Array.isArray(response.error)) {
            console.log(`   📦 Error es un array con ${response.error.length} elementos`);
            const messages = response.error.map(err => {
                if (err.error && err.error.message) {
                    return err.error.message;
                }
                return 'Error de validación';
            });
            const errorMsg = messages.join(', ');
            console.log(`   💬 Mensajes: ${errorMsg}`);
            return errorMsg;
        }

        if (response.error.message) {
            console.log(`   💬 Mensaje: ${response.error.message}`);
            return response.error.message;
        }

        console.log(`   ⚠️ No se pudo parsear el error específico`);
        return 'Error al procesar los datos de la tarjeta';
    }

    clearCardFields() {
        console.log(`\n🧹 Limpiando campos del formulario...`);

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
            if (field) {
                field.value = '';
                console.log(`   ✅ Campo ${selector} limpiado`);
            }
        });
    }

    getCardBin() {
        const numeroTarjeta = document.querySelector('#numero_tarjeta').value.replace(/\s/g, '');
        const bin = numeroTarjeta.substring(0, 6);
        console.log(`   📍 BIN extraído: ${bin}`);
        return bin;
    }

    getLastFourDigits() {
        const numeroTarjeta = document.querySelector('#numero_tarjeta').value.replace(/\s/g, '');
        return numeroTarjeta.substring(numeroTarjeta.length - 4);
    }
}

let paywayIntegration = null;

function initPaywayIntegration(publicKey) {
    console.log(`\n🔌 ========== INICIALIZANDO INTEGRACIÓN PAYWAY ==========`);
    console.log(`   Public Key recibida: ${publicKey.substring(0, 20)}...`);

    paywayIntegration = new PaywayIntegration(publicKey);
    paywayIntegration.initForm('#form-datos-usuario');

    console.log(`✅ Integración Payway lista\n`);
}

async function procesarPagoConPayway() {
    console.log(`\n💳 ========== PROCESANDO PAGO ==========`);
    console.log(`   Timestamp: ${new Date().toISOString()}`);

    if (!paywayIntegration) {
        console.error('❌ Payway no está inicializado');
        return { success: false, error: 'SDK no inicializado' };
    }

    try {
        console.log(`\n1️⃣ Mostrando loading...`);
        mostrarLoading(true);

        console.log(`\n2️⃣ Generando token de pago...`);
        const tokenResult = await paywayIntegration.generatePaymentToken();

        console.log(`\n3️⃣ Resultado del token:`, tokenResult);

        if (!tokenResult.success) {
            console.error(`❌ Error en generación de token:`, tokenResult.error);
            mostrarErrorAPI(tokenResult.error || "Error al generar token de pago");
            mostrarLoading(false);
            return { success: false, error: tokenResult.error };
        }

        const token = tokenResult.token;
        console.log(`✅ Token obtenido: ${token.substring(0, 30)}...`);

        console.log(`\n4️⃣ Extrayendo BIN...`);
        const bin = paywayIntegration.getCardBin();

        console.log(`\n5️⃣ Obteniendo monto total...`);
        const totalElement = document.getElementById("total-compra");
        let amount = 0;

        if (totalElement) {
            const totalText = totalElement.textContent.replace(/[^0-9.]/g, "");
            amount = Math.round(parseFloat(totalText) * 100);
            console.log(`   Monto en ARS: ${(amount / 100).toFixed(2)}`);
            console.log(`   Monto en centavos: ${amount}`);
        } else {
            console.warn(`⚠️ Elemento #total-compra no encontrado`);
        }

        if (amount <= 0) {
            console.error(`❌ Monto inválido: ${amount}`);
            mostrarErrorAPI("Error: El monto del carrito es inválido");
            mostrarLoading(false);
            return { success: false, error: "Monto inválido" };
        }

        console.log(`\n6️⃣ Obteniendo datos del cliente...`);
        const nombre = document.querySelector("#nombre")?.value || "Cliente";
        const apellido = document.querySelector("#apellido")?.value || "";
        const email = document.querySelector("#email")?.value || `guest_${Date.now()}@temp.com`;
        const userId = email;

        console.log(`   Nombre: ${nombre}`);
        console.log(`   Apellido: ${apellido}`);
        console.log(`   Email: ${email}`);
        console.log(`   User ID: ${userId}`);

        const paymentData = {
            amount: amount,
            token: token,
            user_id: userId,
            bin: bin,
            description: `Compra en La Hora Azul - ${nombre} ${apellido}`,
            site_transaction_id: `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        };

        console.log(`\n7️⃣ Datos de pago preparados:`, JSON.stringify(paymentData, null, 2));

        console.log(`\n8️⃣ Enviando POST a /pago/crear...`);
        console.log(`   URL: ${window.location.origin}/pago/crear`);
        console.log(`   Timestamp: ${new Date().toISOString()}`);

        const response = await fetch("/pago/crear", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(paymentData),
            credentials: 'same-origin'  // Importante para cookies si las usas
        });

        console.log(`   Payload enviado:`, JSON.stringify(paymentData, null, 2));
        console.log(`   Response status: ${response.status}`);
        console.log(`   Response headers:`, response.headers);

        console.log(`\n9️⃣ Respuesta recibida`);
        console.log(`   Status HTTP: ${response.status}`);
        console.log(`   OK: ${response.ok}`);
        console.log(`   Timestamp: ${new Date().toISOString()}`);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error(`❌ Error HTTP:`, errorData);
            throw new Error(errorData.error || `Error del servidor: ${response.status}`);
        }

        const resultado = await response.json();
        console.log(`\n🔟 Resultado del pago:`, JSON.stringify(resultado, null, 2));

        if (resultado.status === "approved") {
            console.log(`\n✅ PAGO APROBADO`);
            console.log(`   Payment ID: ${resultado.payment_id}`);
            console.log(`   Ticket: ${resultado.ticket}`);

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
            console.error(`\n❌ PAGO RECHAZADO`);
            console.error(`   Razón: ${resultado.error_reason}`);
            console.error(`   Código: ${resultado.error_code}`);

            const errorMsg = `Pago rechazado: ${resultado.message || resultado.error_reason || "Motivo desconocido"}`;
            mostrarErrorAPI(errorMsg);
            mostrarLoading(false);

            return {
                success: false,
                error: errorMsg,
                status: "rejected"
            };

        } else {
            console.error(`\n⚠️ ESTADO DESCONOCIDO: ${resultado.status}`);
            mostrarErrorAPI("Error desconocido al procesar el pago");
            mostrarLoading(false);

            return {
                success: false,
                error: "Estado desconocido",
                status: resultado.status
            };
        }

    } catch (error) {
        console.error(`\n❌ EXCEPCIÓN EN PROCESAR PAGO`);
        console.error(`   Mensaje: ${error.message}`);
        console.error(`   Stack:`, error.stack);

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
    console.log(`\n📄 ========== DOM CONTENT LOADED ==========`);
    console.log(`   Timestamp: ${new Date().toISOString()}`);

    const btnConfirmar = document.querySelector('#btn-confirmar');
    const form = document.querySelector('#form-datos-usuario');

    if (!btnConfirmar) console.error(`❌ #btn-confirmar NO encontrado`);
    if (!form) console.error(`❌ #form-datos-usuario NO encontrado`);

    let processingPayment = false;

    if (btnConfirmar && form) {
        console.log(`✅ Botón y formulario encontrados, agregando listener...`);

        btnConfirmar.addEventListener('click', async function (e) {
            console.log(`\n🖱️ CLICK EN CONFIRMAR COMPRA`);
            console.log(`   Timestamp: ${new Date().toISOString()}`);

            e.preventDefault();

            if (processingPayment) {
                console.warn(`⚠️ Ya hay un pago en procesamiento`);
                return;
            }

            processingPayment = true;

            const resultado = await procesarPagoConPayway();

            if (resultado.success) {
                console.log(`\n✅ PAGO EXITOSO - Guardando datos...`);

                if (typeof datosFormulario !== 'undefined') {
                    datosFormulario.payment_id = resultado.payment_id;
                    datosFormulario.payment_token = resultado.token;
                    datosFormulario.payment_ticket = resultado.ticket;
                    datosFormulario.payment_authorization = resultado.authorization_code;
                    datosFormulario.payment_amount = resultado.amount;
                    datosFormulario.payment_currency = resultado.currency;
                    datosFormulario.payment_card_brand = resultado.card_brand;
                    datosFormulario.metodo_pago = "tarjeta";

                    console.log(`   📦 Datos guardados en datosFormulario`);

                    if (typeof procesarCompraFinal === 'function') {
                        console.log(`   🎬 Llamando a procesarCompraFinal()...`);
                        await procesarCompraFinal();
                    } else {
                        console.error('❌ procesarCompraFinal no encontrada');
                    }
                } else {
                    console.error('❌ datosFormulario no encontrada');
                }

            } else {
                console.error('❌ Pago fallido:', resultado.error);
                processingPayment = false;
            }
        });
    }
});