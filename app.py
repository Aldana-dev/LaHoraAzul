# ----------------- Importaciones ----------------- #
from flask import Flask, render_template, request, redirect, url_for, flash, session
from app.models import db, Banner, Galeria, Producto, Categoria, ProductoImagen, Usuario, Pedido, PedidoItem
import os
import logging
from flask import session
from werkzeug.utils import secure_filename
from functools import wraps
import json


# ----------------- Configuración básica ----------------- #
logging.basicConfig(level=logging.DEBUG)  # Nivel de logging para debug

app = Flask(__name__, template_folder='app/templates',
            static_folder='app/static')

# Configuración base de datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://aldana_dev:devadmin@localhost/lahoraazul_db'
# Para evitar overhead innecesario
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración para subida de archivos
UPLOAD_FOLDER = 'app/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Clave secreta para manejo de sesiones y flash messages
app.secret_key = 'tu_clave_secreta_aqui'

# Inicialización de la base de datos con la app
db.init_app(app)

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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # Crea carpeta si no existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
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
            return redirect(url_for('admin_login'))
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


# ----------------- Sitio Público ----------------- #
@app.route('/')  # Ruta principal del sitio (página de inicio)
def index():
    # Obtiene todos los banners ordenados por fecha de creación (ascendente)
    banners = Banner.query.order_by(Banner.fecha_creacion).all()

    # Obtiene todas las imágenes de la galería ordenadas por fecha de creación (más recientes primero)
    imagenes_galeria = Galeria.query.order_by(
        Galeria.fecha_creacion.desc()).all()

    # Renderiza la plantilla 'index.html' pasando los banners y las imágenes de galería como contexto
    return render_template('index.html', banners=banners, imagenes_galeria=imagenes_galeria)


@app.route('/nosotras')  # Ruta para la página "Nosotras"
def nosotras():
    # Renderiza la plantilla 'nosotras.html'
    return render_template('nosotras.html')

# Ruta para inicializar manualmente las categorías del catálogo
@app.route('/init_categorias')
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
@app.route('/tienda')
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
@app.route('/producto/<int:producto_id>')
def producto(producto_id):
    # Obtiene el producto desde la base de datos o lanza un error 404 si no existe
    producto = Producto.query.get_or_404(producto_id)

    # Obtiene las imágenes adicionales del producto, ordenadas por su campo 'orden'
    imagenes = ProductoImagen.query.filter_by(
        producto_id=producto_id).order_by(ProductoImagen.orden).all()

    # Renderiza la plantilla 'producto.html' pasando el producto y sus imágenes
    return render_template('producto.html', producto=producto, imagenes=imagenes)


@app.route('/marcos')  # Ruta para la página informativa "Marcos"
def marcos():
    # Renderiza la plantilla estática 'marcos.html'
    return render_template('marcos.html')


@app.route('/galeria')  # Ruta para la galería de imágenes públicas
def galeria():
    # Obtiene todas las imágenes de la galería ordenadas por fecha (más recientes primero)
    imagenes = Galeria.query.order_by(Galeria.fecha_creacion.desc()).all()

    # Renderiza la plantilla 'galeria.html' pasando las imágenes como contexto
    return render_template('galeria.html', imagenes=imagenes)


# ----------------- Carrito ----------------- #
@app.route('/carrito')  # Ruta para visualizar el carrito de compras
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
@app.route('/carrito/agregar/<int:producto_id>', methods=['POST'])
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
    return redirect(url_for('producto', producto_id=producto_id))


# Ruta para quitar un producto del carrito
@app.route('/carrito/quitar/<int:producto_id>', methods=['POST'])
def quitar_del_carrito(producto_id):
    # Obtiene el carrito actual desde la sesión
    carrito = session.get('carrito', [])

    # Si el producto está en el carrito, lo elimina
    if producto_id in carrito:
        carrito.remove(producto_id)
        session['carrito'] = carrito  # Actualiza el carrito en la sesión
        flash('Producto eliminado del carrito')  # Mensaje de confirmación

    # Redirige a la página del carrito
    return redirect(url_for('carrito'))


# Ruta para confirmar el pedido desde el carrito
@app.route('/carrito/confirmar', methods=['POST'])
def confirmar_pedido():
    # Obtiene los IDs de productos en el carrito
    carrito_ids = session.get('carrito', [])

    if not carrito_ids:
        # Muestra mensaje si el carrito está vacío
        flash('Tu carrito está vacío')
        return redirect(url_for('carrito'))

    # Obtiene el email de contacto del formulario
    email_contacto = request.form.get('email_contacto')
    if not email_contacto:
        # Valida que se haya ingresado el email
        flash('Debés ingresar un email')
        return redirect(url_for('carrito'))

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

    return redirect(url_for('index'))  # Redirige al inicio

# ----------------- Autenticación de Administrador ----------------- #

# Ruta para crear un usuario admin inicial (solo para desarrollo)
@app.route('/init_admin')
def init_admin():
    if Usuario.query.filter_by(email='admin@site.com').first():
        return 'El admin ya existe'  # Si ya existe, no lo crea de nuevo

    # Crea un nuevo usuario administrador con credenciales por defecto, ⚠️ debe cambiarse
    admin = Usuario(
        nombre='Admin',
        email='admin@site.com',
        es_admin=True
    )
    admin.set_password('123')  # ⚠️ Clave débil, debe cambiarse
    db.session.add(admin)
    db.session.commit()
    return 'Admin creado correctamente'


# Ruta para iniciar sesión como administrador
@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('username')
        clave = request.form.get('password')

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.es_admin and usuario.check_password(clave):
            session['admin'] = True  # Marca al usuario como admin en la sesión
            flash('Sesión iniciada correctamente')
            # Redirige al panel de administración
            return redirect(url_for('admin'))
        else:
            flash('Credenciales incorrectas')  # Si falla la autenticación

    return render_template('login.html')  # Muestra el formulario de login


@app.route('/logout')  # Ruta para cerrar sesión de administrador
def admin_logout():
    session.pop('admin', None)  # Elimina la sesión admin
    flash('Sesión cerrada')
    return redirect(url_for('index'))  # Redirige a la página principal

# ----------------- Panel de Administración ----------------- #


@app.route('/admin')  # Ruta principal del panel de administración
@admin_required
def admin():
    # Muestra el panel con accesos a secciones admin
    return render_template('admin.html')

# ----------------- Administración de Banners ----------------- #


@app.route("/admin/banner")  # Ruta para administrar los banners del sitio
@admin_required
def admin_banner():
    banners = Banner.query.all()  # Obtiene todos los banners existentes
    return render_template("admin_banner.html", banners=banners)


# Sube un nuevo banner desde el panel de administración
@app.route('/admin/banner/subir', methods=['POST'])
@admin_required
def subir_banner():
    # Obtiene el archivo subido desde el formulario
    file = request.files.get('imagen')
    if not file or file.filename == '':
        flash('No seleccionaste ningún archivo')
        return redirect(url_for('admin_banner'))

    # Guarda el archivo en el sistema de archivos y devuelve la ruta relativa
    filepath = guardar_archivo(file)
    if not filepath:
        # Puede fallar si el archivo no tiene una extensión válida
        flash('Archivo no permitido')
        return redirect(url_for('admin_banner'))

    # Crea una nueva instancia de banner con la ruta de la imagen
    nuevo_banner = Banner(imagen=filepath)
    db.session.add(nuevo_banner)
    try:
        db.session.commit()  # Guarda el nuevo banner en la base de datos
        flash('Banner subido correctamente')
    except Exception:
        db.session.rollback()  # Si hay error, se revierte la operación
        flash('Error al guardar en la base de datos')

    return redirect(url_for('admin_banner'))


# Elimina un banner desde el panel admin
@app.route('/admin/banner/eliminar/<int:banner_id>', methods=['POST'])
@admin_required
def eliminar_banner(banner_id):
    # Busca el banner por ID o lanza error 404 si no existe
    banner = Banner.query.get_or_404(banner_id)
    try:
        # Construye la ruta física completa del archivo en el sistema
        ruta_fisica = os.path.join(app.static_folder, banner.imagen)
        # Si el archivo existe en el sistema, lo elimina
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        # Elimina el registro del banner de la base de datos
        db.session.delete(banner)
        db.session.commit()
        flash('Banner eliminado correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al eliminar el banner')

    return redirect(url_for('admin_banner'))


# ----------------- Administración de Galería ----------------- #


@app.route("/admin/galeria")  # Ruta para administrar la galería de imágenes
@admin_required
def admin_galeria():
    imagenes = Galeria.query.order_by(
        Galeria.fecha_creacion).all()  # Imágenes ordenadas por fecha
    return render_template("admin_galeria.html", imagenes=imagenes)


# Sube una imagen a la galería desde el panel admin
@app.route('/admin/galeria/subir', methods=['POST'])
@admin_required
def subir_galeria():
    # Obtiene el archivo subido desde el formulario
    file = request.files.get('imagen')
    if not file or file.filename == '':
        flash('No seleccionaste ningún archivo')
        return redirect(url_for('admin_galeria'))

    # Guarda el archivo y obtiene la ruta relativa, si es válida
    filepath = guardar_archivo(file)
    if not filepath:
        flash('Archivo no permitido')  # Por ejemplo, extensión no válida
        return redirect(url_for('admin_galeria'))

    # Crea un nuevo registro en la tabla Galería con la ruta de la imagen
    nueva_imagen = Galeria(imagen=filepath)
    db.session.add(nueva_imagen)
    try:
        db.session.commit()  # Guarda en la base de datos
        flash('Imagen de galería subida correctamente')
    except Exception:
        db.session.rollback()  # Revierte si hay error
        flash('Error al guardar en la base de datos')

    return redirect(url_for('admin_galeria'))


# Elimina una imagen de la galería desde el panel admin
@app.route('/admin/galeria/eliminar/<int:imagen_id>', methods=['POST'])
@admin_required
def eliminar_galeria(imagen_id):
    # Busca la imagen por ID o devuelve 404 si no existe
    imagen = Galeria.query.get_or_404(imagen_id)
    try:
        # Construye la ruta física del archivo en el servidor
        ruta_fisica = os.path.join(app.static_folder, imagen.imagen)
        # Si el archivo existe, se elimina del sistema
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        # Elimina el registro de la base de datos
        db.session.delete(imagen)
        db.session.commit()
        flash('Imagen eliminada correctamente')
    except Exception:
        db.session.rollback()  # Revertir cambios si ocurre un error
        flash('Error al eliminar la imagen')

    return redirect(url_for('admin_galeria'))

# ----------------- Administración de Productos ----------------- #


@app.route("/admin/productos")  # Ruta para administrar productos en la tienda
@admin_required
def admin_productos():
    categorias = Categoria.query.all()  # Todas las categorías disponibles
    # Productos ordenados del más reciente al más antiguo
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("admin_productos.html", categorias=categorias, productos=productos)

# Agrega un nuevo producto desde el panel admin
@app.route('/admin/productos/agregar', methods=['POST'])
@admin_required
def agregar_producto():
    # Obtiene los datos del formulario
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = request.form.get('precio')
    categoria_id = request.form.get('categoria_id')
    imagen_file = request.files.get('imagen')

    # Verifica que todos los campos requeridos estén presentes
    if not (nombre and precio and categoria_id and imagen_file and imagen_file.filename != ''):
        flash('Faltan campos obligatorios, incluyendo la imagen')
        return redirect(url_for('admin_productos'))

    # Valida que el precio sea un número
    try:
        precio_val = float(precio)
    except ValueError:
        flash('Precio inválido')
        return redirect(url_for('admin_productos'))

    # Guarda la imagen en la carpeta uploads
    filename = secure_filename(imagen_file.filename)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    uploads_path = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    os.makedirs(uploads_path, exist_ok=True)
    ruta_guardado = os.path.join(uploads_path, filename)
    imagen_file.save(ruta_guardado)
    logging.info(f"Imagen guardada en ruta física: {ruta_guardado}")

    # Ruta que se guardará en la base de datos
    ruta_relativa = os.path.join('uploads', filename).replace('\\', '/')

    # Crea y guarda el nuevo producto en la base de datos
    try:
        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion or '',
            precio=precio_val,
            imagen=ruta_relativa,
            categoria_id=int(categoria_id)
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto agregado correctamente')
        logging.info(f"Producto agregado: {nombre} con imagen {ruta_relativa}")
    except Exception as e:
        db.session.rollback()
        flash('Error al agregar producto')
        logging.error(f'Error agregando producto: {e}')

    return redirect(url_for('admin_productos'))

# Edita un producto existente y sus imágenes desde el panel admin
@app.route('/admin/productos/editar/<int:producto_id>', methods=['POST'])
@admin_required
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = request.form.get('precio')
    categoria_id = request.form.get('categoria_id')
    # Imagen principal nueva (opcional)
    imagen_file = request.files.get('imagen')
    imagenes_adicionales_files = request.files.getlist(
        'imagenes_adicionales')  # Nuevas imágenes adicionales

    if not (nombre and precio and categoria_id):
        flash('Faltan campos obligatorios')
        return redirect(url_for('admin_productos'))

    try:
        precio_val = float(precio)
    except ValueError:
        flash('Precio inválido')
        return redirect(url_for('admin_productos'))

    try:
        # Actualiza los campos básicos del producto
        producto.nombre = nombre
        producto.descripcion = descripcion or ''
        producto.precio = precio_val
        producto.categoria_id = int(categoria_id)

        # Si hay una nueva imagen principal, la guarda y actualiza el campo
        if imagen_file and imagen_file.filename != '':
            filename = secure_filename(imagen_file.filename)
            ruta_guardado = os.path.join(
                app.root_path, 'static', 'uploads', filename)
            os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
            imagen_file.save(ruta_guardado)
            producto.imagen = filename

        # Guarda cada nueva imagen adicional, creando registros relacionados
        for img_file in imagenes_adicionales_files:
            if img_file and img_file.filename != '':
                filename = secure_filename(img_file.filename)
                ruta_guardado = os.path.join(
                    app.root_path, 'static', 'uploads', filename)
                os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
                img_file.save(ruta_guardado)
                nueva_imagen = ProductoImagen(
                    producto_id=producto.id,
                    imagen=filename,
                    orden=producto.imagenes.count() + 1  # Coloca al final el orden
                )
                db.session.add(nueva_imagen)

        db.session.commit()
        flash('Producto actualizado correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el producto')
        logging.error(f'Error actualizando producto: {e}')

    return redirect(url_for('admin_productos'))


# Sube imágenes adicionales para un producto específico
@app.route('/admin/productos/<int:producto_id>/imagenes/subir', methods=['POST'])
@admin_required
def subir_imagen_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    files = request.files.getlist('imagenes')

    if not files or files[0].filename == '':
        flash('No seleccionaste archivos')
        return redirect(url_for('admin_productos'))

    for file in files:
        filepath = guardar_archivo(file)
        if filepath:
            # Obtener el mayor orden actual para este producto para asignar el siguiente orden
            max_orden = db.session.query(db.func.max(ProductoImagen.orden)).filter_by(
                producto_id=producto_id).scalar()
            orden = (max_orden or 0) + 1
            nueva_img = ProductoImagen(
                producto_id=producto_id,
                imagen=filepath,
                orden=orden
            )
            db.session.add(nueva_img)
        else:
            flash(f'Archivo no permitido: {file.filename}')
            return redirect(url_for('admin_productos'))

    try:
        db.session.commit()
        flash('Imágenes subidas correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al guardar las imágenes')
        logging.error(f'Error guardando imágenes: {e}')

    return redirect(url_for('admin_productos'))


# Edita/actualiza una imagen adicional existente de un producto
@app.route('/admin/productos/imagenes/editar/<int:imagen_id>', methods=['POST'])
@admin_required
def editar_imagen_producto(imagen_id):
    imagen = ProductoImagen.query.get_or_404(imagen_id)
    file = request.files.get('imagen_nueva')

    if not file or file.filename == '':
        flash('No seleccionaste archivo para la imagen')
        return redirect(url_for('admin_productos'))

    if allowed_file(file.filename):
        try:
            # Borra la imagen anterior del sistema de archivos
            ruta_anterior = os.path.join(app.static_folder, imagen.imagen)
            if os.path.exists(ruta_anterior):
                os.remove(ruta_anterior)

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Actualiza la ruta en la base de datos (ruta relativa)
            imagen.imagen = filepath.replace('app/static/', '')
            db.session.commit()
            flash('Imagen actualizada correctamente')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la imagen')
            logging.error(f'Error actualizando imagen: {e}')
    else:
        flash('Archivo no permitido')

    return redirect(url_for('admin_productos'))


# Elimina un producto y todas sus imágenes (físicas y BD)
@app.route('/admin/productos/eliminar/<int:producto_id>', methods=['POST'])
@admin_required
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    try:
        # Elimina cada imagen física y su registro de la base de datos
        for img in producto.imagenes:
            ruta_fisica = os.path.join(app.static_folder, img.imagen)
            if os.path.exists(ruta_fisica):
                os.remove(ruta_fisica)
            db.session.delete(img)

        # Elimina el producto de la base de datos
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el producto')
        logging.error(f'Error eliminando producto: {e}')

    return redirect(url_for('admin_productos'))


# Elimina una imagen adicional de producto (física y base de datos)
@app.route('/admin/productos/imagenes/eliminar/<int:imagen_id>', methods=['POST'])
@admin_required
def eliminar_imagen_producto(imagen_id):
    imagen = ProductoImagen.query.get_or_404(imagen_id)
    try:
        ruta_fisica = os.path.join(app.static_folder, imagen.imagen)
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        db.session.delete(imagen)
        db.session.commit()
        flash('Imagen eliminada correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la imagen')
        logging.error(f'Error eliminando imagen: {e}')

    return redirect(url_for('admin_productos'))


# ----------------- Administración de Pedidos ----------------- #

# ----------------- Administración de Pedidos ----------------- #

@app.route("/admin/pedidos")
@admin_required
def admin_pedidos():
    filtro = request.args.get('filtro', 'nuevos')

    if filtro == "nuevos":
        pedidos = Pedido.query.filter_by(es_viejo=False).order_by(Pedido.fecha.desc()).all()
    elif filtro == "viejos":
        pedidos = Pedido.query.filter_by(es_viejo=True).order_by(Pedido.fecha.desc()).all()
    else:
        pedidos = Pedido.query.order_by(Pedido.fecha.desc()).all()

    return render_template("admin_pedidos.html", pedidos=pedidos, filtro=filtro)


@app.route('/admin/pedidos/toggle_estado/<int:pedido_id>', methods=['POST'])
@admin_required
def toggle_estado_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.es_viejo:
        flash("No se puede cambiar el estado de un pedido viejo.", "warning")
        return redirect(url_for('admin_pedidos', filtro='nuevos'))

    if pedido.estado == 'nuevo':
        pedido.estado = 'pendiente'
    elif pedido.estado == 'pendiente':
        pedido.estado = 'nuevo'
    else:
        flash("Estado actual no permite toggle.", "warning")
        return redirect(url_for('admin_pedidos', filtro='nuevos'))

    try:
        db.session.commit()
        flash(f"Estado del pedido #{pedido.id} actualizado a {pedido.estado}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar estado del pedido: {str(e)}", "danger")

    return redirect(url_for('admin_pedidos', filtro='nuevos'))


@app.route('/admin/pedidos/marcar_como_viejos', methods=['POST'])
@admin_required
def marcar_como_viejos():
    ids = request.form.getlist('pedido_ids')
    if not ids:
        flash("No seleccionaste pedidos para marcar como viejos.", "warning")
        return redirect(url_for('admin_pedidos', filtro='nuevos'))

    pedidos = Pedido.query.filter(Pedido.id.in_(ids), Pedido.es_viejo == False).all()
    for pedido in pedidos:
        pedido.es_viejo = True

    try:
        db.session.commit()
        flash(f"Se marcaron {len(pedidos)} pedidos como viejos.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al marcar pedidos como viejos: {str(e)}", "danger")

    return redirect(url_for('admin_pedidos', filtro='nuevos'))


@app.route('/admin/pedidos/eliminar_viejos', methods=['POST'])
@admin_required
def eliminar_pedidos_viejos():
    ids_json = request.form.get('pedido_ids')
    if not ids_json:
        flash("No seleccionaste pedidos para eliminar.", "warning")
        return redirect(url_for('admin_pedidos', filtro='viejos'))

    try:
        ids = json.loads(ids_json)
    except Exception as e:
        flash(f"Error procesando pedidos seleccionados: {str(e)}", "danger")
        return redirect(url_for('admin_pedidos', filtro='viejos'))

    pedidos = Pedido.query.filter(Pedido.id.in_(ids), Pedido.es_viejo == True).all()
    if not pedidos:
        flash("No se encontraron pedidos viejos para eliminar.", "warning")
        return redirect(url_for('admin_pedidos', filtro='viejos'))

    try:
        for pedido in pedidos:
            db.session.delete(pedido)
        db.session.commit()
        flash(f"Se eliminaron {len(pedidos)} pedidos viejos.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar pedidos viejos: {str(e)}", "danger")

    return redirect(url_for('admin_pedidos', filtro='viejos'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear tablas si no existen
    app.run(debug=True, port=5000)
