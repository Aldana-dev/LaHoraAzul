# ----------------- Importaciones ----------------- #
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, Banner, Galeria, Producto, Categoria, ProductoImagen, Pedido, PedidoItem
from werkzeug.utils import secure_filename
from functools import wraps
import os
import logging
from flask import current_app

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
            categoria_id=categoria_id).order_by(Producto.id.desc()).all()
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


# ----------------- Carrito ----------------- #
@main_bp.route('/carrito')  # Ruta para visualizar el carrito de compras
def carrito():
    # Obtiene los IDs de productos almacenados en la sesión del usuario
    carrito_ids = session.get('carrito', [])

    # Consulta los productos correspondientes a esos IDs
    productos = Producto.query.filter(Producto.id.in_(carrito_ids)).all()

    # Arma la lista de productos con los datos necesarios para la vista
    carrito_data = []
    total = 0
    for p in productos:
        total += p.precio  # Suma el precio de cada producto al total general
        carrito_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'imagen': p.imagen
        })

    # Define un costo fijo de envío
    costo_envio = 150

    # Si hay productos en el carrito, suma el envío al total final
    total_final = total + costo_envio if carrito_data else 0

    # Renderiza la plantilla 'carrito.html' con los datos del carrito
    return render_template('carrito.html', carrito=carrito_data, costo_envio=costo_envio, total=total_final)


# Ruta para agregar un producto al carrito
@main_bp.route('/carrito/agregar/<int:producto_id>', methods=['POST'])
def agregar_al_carrito(producto_id):
    # Obtiene la lista actual del carrito desde la sesión
    carrito = obtener_carrito()

    # Si el producto no está ya en el carrito, lo agrega
    if producto_id not in carrito:
        carrito.append(producto_id)
        # Guarda el carrito actualizado en la sesión
        session['carrito'] = carrito
        flash('Producto agregado al carrito')  # Muestra un mensaje temporal

    # Redirige de vuelta a la página del producto
    return redirect(url_for('main.producto', producto_id=producto_id))


# Ruta para quitar un producto del carrito
@main_bp.route('/carrito/quitar/<int:producto_id>', methods=['POST'])
def quitar_del_carrito(producto_id):
    # Obtiene el carrito actual desde la sesión
    carrito = session.get('carrito', [])

    # Si el producto está en el carrito, lo elimina
    if producto_id in carrito:
        carrito.remove(producto_id)
        session['carrito'] = carrito  # Actualiza el carrito en la sesión
        flash('Producto eliminado del carrito')  # Mensaje de confirmación

    # Redirige a la página del carrito
    return redirect(url_for('main.carrito'))


# Ruta para confirmar el pedido desde el carrito
@main_bp.route('/carrito/confirmar', methods=['POST'])
def confirmar_pedido():
    # Obtiene los IDs de productos en el carrito
    carrito_ids = session.get('carrito', [])

    if not carrito_ids:
        # Muestra mensaje si el carrito está vacío
        flash('Tu carrito está vacío')
        return redirect(url_for('main.carrito'))

    # Obtiene el email de contacto del formulario
    email_contacto = request.form.get('email_contacto')
    if not email_contacto:
        # Valida que se haya ingresado el email
        flash('Debés ingresar un email')
        return redirect(url_for('main.carrito'))

    productos = Producto.query.filter(Producto.id.in_(
        carrito_ids)).all()  # Obtiene los productos del carrito

    total = sum([p.precio for p in productos])  # Calcula el total del pedido
    nuevo_pedido = Pedido(email_contacto=email_contacto,
                          total=total)  # Crea el nuevo pedido

    db.session.add(nuevo_pedido)
    db.session.flush()  # Obtiene el ID del pedido antes del commit

    # Crea un PedidoItem por cada producto en el carrito
    for p in productos:
        item = PedidoItem(
            pedido_id=nuevo_pedido.id,
            producto_id=p.id,
            precio_unitario=p.precio
        )
        db.session.add(item)

        # Marca el producto como vendido
        p.vendido = True
        db.session.add(p)

    # Intenta guardar todo en la base de datos
    try:
        db.session.commit()
        session.pop('carrito', None)  # Vacía el carrito
        flash('Pedido realizado con éxito')  # Mensaje de éxito
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al guardar pedido: {e}")  # Loguea el error
        flash('Ocurrió un error al confirmar el pedido')  # Mensaje de error

    return redirect(url_for('main.index'))  # Redirige al inicio

