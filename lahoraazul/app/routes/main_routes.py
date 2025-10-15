# ----------------- Importaciones ----------------- #
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from app.models import db, Banner, Galeria, Producto, Categoria, ProductoImagen, Pedido, PedidoItem
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os
import logging
import os

main_bp = Blueprint('main', __name__)

# ----------------- Configuración local ----------------- #
UPLOAD_FOLDER = 'app/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# ----------------- Funciones auxiliares ----------------- #


def allowed_file(filename):
    """Valida que el archivo tenga una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_archivo(file):
    """
    Guarda un archivo subido en la carpeta configurada si es válido.
    Devuelve la ruta relativa para usar en la app o None si no es válido.
    """
    if file and allowed_file(file.filename):
        # Evita problemas con nombres maliciosos
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        # Crea carpeta si no existe
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        logging.debug(f'Archivo guardado en: {filepath}')
        return os.path.join('uploads', filename).replace('\\', '/')
    logging.debug('Archivo no válido o no enviado')
    return None


def admin_required(f):
    """
    Decorador para proteger rutas que solo pueden acceder admins.
    Redirige a login si no hay sesión activa como admin.
    """
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get('admin'):
            flash('Necesitás iniciar sesión como admin')
            return redirect(url_for('main.admin_login'))
        return f(*args, **kwargs)
    return decorada


def obtener_carrito():
    """
    Devuelve la lista de productos en el carrito almacenado en sesión.
    Crea la lista si no existe.
    """
    if 'carrito' not in session:
        session['carrito'] = []
    return session['carrito']


# ----------------- Rutas públicas ----------------- #
@main_bp.route('/')  # Ruta principal del sitio (página de inicio)
def index():
    # Obtiene todos los banners ordenados por fecha de creación (ascendente)
    banners = Banner.query.order_by(Banner.fecha_creacion).all()

    # Obtiene todas las imágenes de la galería ordenadas por fecha de creación (más recientes primero)
    imagenes_galeria = Galeria.query.order_by(
        Galeria.fecha_creacion.desc()).all()

    # Renderiza la plantilla 'index.html' pasando los banners y las imágenes de galería como contexto
    return render_template('index.html', banners=banners, imagenes_galeria=imagenes_galeria)


@main_bp.route('/nosotras')  # Ruta para la página "Nosotras"
def nosotras():
    # Renderiza la plantilla 'nosotras.html'
    return render_template('nosotras.html')

# Ruta para inicializar manualmente las categorías del catálogo


@main_bp.route('/init_categorias')
def init_categorias():
    # Lista de nombres de categorías predeterminadas
    nombres = ["Cuadros", "Cerámica", "Cuadernos", "Totebags"]

    # ⚠️ Elimina todas las categorías existentes en la base de datos
    Categoria.query.delete()
    db.session.commit()

    # Crea una nueva instancia de Categoria por cada nombre y la agrega a la sesión
    for nombre in nombres:
        db.session.add(Categoria(nombre=nombre))

    # Guarda los cambios en la base de datos
    db.session.commit()

    # Devuelve un mensaje de éxito como texto plano
    return "Categorías inicializadas correctamente."

# Ruta para la tienda. Muestra todos los productos o filtra por categoría.


@main_bp.route('/tienda')
def tienda():
    # Obtiene el ID de categoría desde los parámetros de la URL (si se especifica)
    categoria_id = request.args.get('categoria_id', type=int)

    # Obtiene todas las categorías ordenadas por ID (para mostrar los filtros)
    categorias = Categoria.query.order_by(Categoria.id).all()

    # Filtra los productos por categoría si hay un ID; si no, trae todos
    if categoria_id:
        productos = Producto.query.filter_by(
            categoria_id=categoria_id, vendido=False).order_by(Producto.id.desc()).all()
    else:
        productos = Producto.query.filter_by(
            vendido=False).order_by(Producto.id.desc()).all()

    # Prepara los datos de los productos para la plantilla
    productos_data = []
    for p in productos:
        # Usa la imagen guardada en la base de datos, o un placeholder si no hay imagen
        img_path = p.imagen if p.imagen else 'img/placeholder.png'

        productos_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'imagen': img_path
        })

    # Renderiza la plantilla 'tienda.html' con los datos de categorías y productos
    return render_template('tienda.html', categorias=categorias, productos=productos_data, categoria_id=categoria_id)

# Ruta para la página de detalle de un producto individual


@main_bp.route('/producto/<int:producto_id>')
def producto(producto_id):
    # Obtiene el producto desde la base de datos o lanza un error 404 si no existe
    producto = Producto.query.get_or_404(producto_id)

    # Obtiene las imágenes adicionales del producto, ordenadas por su campo 'orden'
    imagenes = ProductoImagen.query.filter_by(
        producto_id=producto_id).order_by(ProductoImagen.orden).all()

    # Renderiza la plantilla 'producto.html' pasando el producto y sus imágenes
    return render_template('producto.html', producto=producto, imagenes=imagenes)


@main_bp.route('/marcos')  # Ruta para la página informativa "Marcos"
def marcos():
    # Renderiza la plantilla estática 'marcos.html'
    return render_template('marcos.html')


@main_bp.route('/galeria')  # Ruta para la galería de imágenes públicas
def galeria():
    # Obtiene todas las imágenes de la galería ordenadas por fecha (más recientes primero)
    imagenes = Galeria.query.order_by(Galeria.fecha_creacion.desc()).all()

    # Renderiza la plantilla 'galeria.html' pasando las imágenes como contexto
    return render_template('galeria.html', imagenes=imagenes)

import logging

# ----------------- Carrito ----------------- #
@main_bp.route('/carrito')  # Ruta para visualizar el carrito de compras
def carrito():
    logging.info("Accediendo a la página del carrito")

    # Obtiene los IDs de productos almacenados en la sesión del usuario
    carrito_ids = session.get('carrito', [])
    logging.info(f"IDs en carrito de sesión: {carrito_ids}")

    # Consulta los productos correspondientes a esos IDs desde la base de datos
    productos = Producto.query.filter(Producto.id.in_(carrito_ids)).all()
    logging.info(f"Productos encontrados en DB: {[p.id for p in productos]}")

    # Construye una lista con los datos necesarios para mostrar en la vista
    carrito_data = []
    subtotal = 0  # Variable para almacenar el subtotal de productos
    for p in productos:
        subtotal += p.precio  # Suma el precio de cada producto al subtotal
        carrito_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'imagen': p.imagen
        })
    logging.info(f"Subtotal calculado: {subtotal}")

    # Define un costo de envío inicial en cero
    costo_envio = 0
    total = subtotal + costo_envio
    logging.info(f"Total calculado (subtotal + envío): {total}")

    # Renderiza la plantilla
    return render_template(
        'carrito.html',
        carrito=carrito_data,
        subtotal=subtotal,
        costo_envio=costo_envio,
        total=total
    )


# Ruta para agregar un producto al carrito
@main_bp.route('/carrito/agregar/<int:producto_id>', methods=['POST'])
def agregar_al_carrito(producto_id):
    carrito = obtener_carrito()
    logging.info(f"Agregando producto {producto_id} al carrito. Carrito previo: {carrito}")

    if producto_id not in carrito:
        carrito.append(producto_id)
        session['carrito'] = carrito
        logging.info(f"Producto {producto_id} agregado. Carrito actualizado: {carrito}")
        flash('Producto agregado al carrito')

    return redirect(url_for('main.producto', producto_id=producto_id))


# Ruta para quitar un producto del carrito
@main_bp.route('/carrito/quitar/<int:producto_id>', methods=['POST'])
def quitar_del_carrito(producto_id):
    carrito = session.get('carrito', [])
    logging.info(f"Intentando quitar producto {producto_id} del carrito. Carrito previo: {carrito}")

    if producto_id in carrito:
        carrito.remove(producto_id)
        session['carrito'] = carrito
        logging.info(f"Producto {producto_id} eliminado. Carrito actualizado: {carrito}")
        flash('Producto eliminado del carrito')

    return redirect(url_for('main.carrito'))


# ----------------- Confirmar pedido con integración de pagos ----------------- #
@main_bp.route('/carrito/confirmar', methods=['POST'])
def confirmar_pedido():
    import requests
    logging.info("Inicio del proceso de confirmación de pedido")

    try:
        # --- Recibir datos JSON desde JS ---
        data = request.get_json()
        if not data:
            logging.warning("No se recibieron datos JSON")
            return jsonify({"error": "Datos incompletos"}), 400

        nombre = data.get("nombre")
        apellido = data.get("apellido")
        email_contacto = data.get("email")
        telefono = data.get("telefono")
        provincia = data.get("provincia")
        localidad = data.get("localidad")
        ciudad = data.get("ciudad")
        cp_usuario = data.get("cp_usuario")
        direccion = data.get("direccion")
        referencias = data.get("referencias")
        tipo_envio = data.get("tipo_envio")
        comentarios = data.get("comentarios")
        metodo_pago = data.get("metodo_pago")
        token_tarjeta = data.get("token")
        total = data.get("total")  # total calculado en frontend

        logging.info(f"Datos recibidos: {data}")

        # Validaciones básicas
        if not email_contacto or not total:
            logging.warning("Email o total faltante")
            return jsonify({"error": "Email y total son obligatorios"}), 400

        carrito_ids = session.get("carrito", [])
        if not carrito_ids:
            logging.warning("Carrito vacío al intentar confirmar pedido")
            return jsonify({"error": "El carrito está vacío"}), 400

        productos = Producto.query.filter(Producto.id.in_(carrito_ids)).all()
        subtotal = sum([p.precio for p in productos])
        logging.info(f"Subtotal calculado: {subtotal}")

        # --- Procesar pago si es tarjeta ---
        if metodo_pago == "tarjeta":
            if not token_tarjeta:
                logging.warning("No se recibió token de tarjeta")
                return jsonify({"error": "Falta token de tarjeta"}), 400

            try:
                resp = requests.post(
                    "http://localhost:3001/create-payment-intent",
                    json={"amount": total, "token": token_tarjeta},
                    timeout=5
                )
                resp.raise_for_status()
                resultado_pago = resp.json()
                if resultado_pago.get("status") != "approved":
                    logging.warning(f"Pago rechazado: {resultado_pago}")
                    return jsonify({"error": "Pago rechazado", "details": resultado_pago}), 402
            except requests.exceptions.RequestException as e:
                logging.error(f"Error al procesar pago: {e}")
                return jsonify({"error": "Error en el servicio de pagos", "details": str(e)}), 500

        # --- Crear pedido ---
        nuevo_pedido = Pedido(
            nombre=nombre,
            apellido=apellido,
            email_contacto=email_contacto,
            telefono=telefono,
            provincia=provincia,
            localidad=localidad,
            ciudad=ciudad,
            cp_usuario=cp_usuario,
            direccion=direccion,
            referencias=referencias,
            tipo_envio=tipo_envio,
            comentarios=comentarios,
            total=total,
            fecha=datetime.utcnow(),
            estado_pago="aprobado" if metodo_pago == "tarjeta" else "pendiente"
        )
        db.session.add(nuevo_pedido)
        db.session.flush()
        logging.info(f"Pedido creado con ID temporal: {nuevo_pedido.id}")

        # --- Crear items del pedido ---
        for p in productos:
            item = PedidoItem(
                pedido_id=nuevo_pedido.id,
                producto_id=p.id,
                precio_unitario=p.precio
            )
            db.session.add(item)
            p.vendido = True
            db.session.add(p)

        db.session.commit()
        logging.info(f"Pedido confirmado y guardado con ID: {nuevo_pedido.id}")

        # Vaciar carrito
        session.pop("carrito", None)
        logging.info("Carrito de sesión vaciado")

        return jsonify({"success": True, "pedido_id": nuevo_pedido.id})

    except Exception as e:
        db.session.rollback()
        logging.exception("Error al confirmar pedido")
        return jsonify({"error": "Ocurrió un error al procesar el pedido", "details": str(e)}), 500

        db.session.rollback()
        logging.exception(f"Error al guardar pedido: {e}")
        flash("Ocurrió un error al confirmar el pedido ❌")
        return redirect(url_for("main.carrito"))