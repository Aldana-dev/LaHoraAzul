# ----------------- Importaciones ----------------- #
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from app.models import db, Banner, Galeria, Producto, Categoria, ProductoImagen, Pedido, Usuario
from werkzeug.utils import secure_filename
import os
from functools import wraps
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.DEBUG)

admin_bp = Blueprint('admin', __name__, template_folder='../templates')

# Configuración para subida de archivos
UPLOAD_FOLDER = 'app/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# ----------------- Funciones auxiliares ----------------- #


def allowed_file(filename):
    """Valida que el archivo tenga una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_archivo(file, subcarpeta):
    """
    Guarda un archivo subido en una subcarpeta dentro de la carpeta de uploads si es válido.
    Devuelve la ruta relativa para usar en la app o None si no es válido.
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Usa la ruta absoluta a la carpeta static
        static_folder = current_app.static_folder
        subcarpeta_path = os.path.join(static_folder, 'uploads', subcarpeta)
        os.makedirs(subcarpeta_path, exist_ok=True)

        filepath = os.path.join(subcarpeta_path, filename)
        file.save(filepath)
        logging.debug(f'Archivo guardado en: {filepath}')

        # Devuelve la ruta relativa desde static/
        return os.path.join('uploads', subcarpeta, filename).replace('\\', '/')

    logging.debug('Archivo no válido o no enviado')
    return None


def admin_required(f):
    """Decorador para proteger rutas solo para admins."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get('admin'):
            flash('Necesitás iniciar sesión como admin')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorada


# ----------------- Autenticación de Administrador ----------------- #

# Ruta para crear un usuario admin inicial (solo para desarrollo)
@admin_bp.route('/init_admin')
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
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('username')
        clave = request.form.get('password')

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.es_admin and usuario.check_password(clave):
            session['admin'] = True  # Marca al usuario como admin en la sesión
            flash('Sesión iniciada correctamente')
            # Redirige al panel de administración
            return redirect(url_for('admin.admin'))
        else:
            flash('Credenciales incorrectas')  # Si falla la autenticación

    return render_template('login.html')  # Muestra el formulario de login


@admin_bp.route('/logout')  # Ruta para cerrar sesión de administrador
def admin_logout():
    session.pop('admin', None)  # Elimina la sesión admin
    flash('Sesión cerrada')
    return redirect(url_for('main.index'))  # Redirige a la página principal


# ----------------- Panel de Administración ----------------- #


@admin_bp.route('/admin')  # Ruta principal del panel de administración
@admin_required
def admin():
    # Muestra el panel con accesos a secciones admin
    return render_template('admin.html')

# ----------------- Administración de Banners ----------------- #


@admin_bp.route("/admin/banner")  # Ruta para administrar los banners del sitio
@admin_required
def admin_banner():
    banners = Banner.query.all()  # Obtiene todos los banners existentes
    return render_template("admin_banner.html", banners=banners)


# Sube un nuevo banner desde el panel de administración
@admin_bp.route('/admin/banner/subir', methods=['POST'])
@admin_required
def subir_banner():
    archivos = request.files.getlist('imagenes')
    if not archivos or all(f.filename == '' for f in archivos):
        flash('No seleccionaste ningún archivo')
        return redirect(url_for('admin.admin_banner'))

    cantidad_subidas = 0

    for file in archivos:
        filepath = guardar_archivo(file, 'banner')
        if filepath:
            nuevo_banner = Banner(imagen=filepath)
            db.session.add(nuevo_banner)
            cantidad_subidas += 1

    try:
        db.session.commit()
        flash(f'Se subieron {cantidad_subidas} banner(s) correctamente.')
    except Exception:
        db.session.rollback()
        flash('Error al guardar los banners en la base de datos.')

    return redirect(url_for('admin.admin_banner'))

# Elimina un banner desde el panel admin


@admin_bp.route('/admin/banner/eliminar/<int:banner_id>', methods=['POST'])
@admin_required
def eliminar_banner(banner_id):
    # Busca el banner por ID o lanza error 404 si no existe
    banner = Banner.query.get_or_404(banner_id)
    try:
        # Construye la ruta física completa del archivo en el sistema
        ruta_fisica = os.path.join(current_app.static_folder, banner.imagen)
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

    return redirect(url_for('admin.admin_banner'))


# ----------------- Administración de Galería ----------------- #


# Ruta para administrar la galería de imágenes
@admin_bp.route("/admin/galeria")
@admin_required
def admin_galeria():
    imagenes = Galeria.query.order_by(
        Galeria.fecha_creacion).all()  # Imágenes ordenadas por fecha
    return render_template("admin_galeria.html", imagenes=imagenes)


# Sube una imagen a la galería desde el panel admin
@admin_bp.route('/admin/galeria/subir', methods=['POST'])
@admin_required
def subir_galeria():
    archivos = request.files.getlist('imagenes')
    if not archivos or archivos == []:
        flash('No seleccionaste ningún archivo')
        return redirect(url_for('admin.admin_galeria'))

    exitos = 0
    for file in archivos:
        if file and file.filename != '':
            filepath = guardar_archivo(file, 'galeria')
            if filepath:
                nueva_imagen = Galeria(imagen=filepath)
                db.session.add(nueva_imagen)
                exitos += 1

    if exitos > 0:
        try:
            db.session.commit()
            flash(f'{exitos} imagen(es) subidas correctamente a la galería')
        except Exception:
            db.session.rollback()
            flash('Error al guardar en la base de datos')
    else:
        flash('No se pudieron subir las imágenes (formatos no válidos)')

    return redirect(url_for('admin.admin_galeria'))


# Elimina una imagen de la galería desde el panel admin
@admin_bp.route('/admin/galeria/eliminar/<int:imagen_id>', methods=['POST'])
@admin_required
def eliminar_galeria(imagen_id):
    # Busca la imagen por ID o devuelve 404 si no existe
    imagen = Galeria.query.get_or_404(imagen_id)
    try:
        # Construye la ruta física del archivo en el servidor
        ruta_fisica = os.path.join(current_app.static_folder, imagen.imagen)
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

    return redirect(url_for('admin.admin_galeria'))

# ----------------- Administración de Productos ----------------- #


# Ruta para administrar productos en la tienda
@admin_bp.route("/admin/productos")
@admin_required
def admin_productos():
    categorias = Categoria.query.all()  # Todas las categorías disponibles
    # Productos ordenados del más reciente al más antiguo
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("admin_productos.html", categorias=categorias, productos=productos)

# Agrega un nuevo producto desde el panel admin


@admin_bp.route('/admin/productos/agregar', methods=['POST'])
@admin_required
def agregar_producto():
    # Obtiene los datos del formulario
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = request.form.get('precio')
    categoria_id = request.form.get('categoria_id')
    imagen_principal = request.files.get('imagen_principal')
    imagenes_secundarias = request.files.getlist('imagenes_secundarias')

    if not (nombre and precio and categoria_id and imagen_principal and imagen_principal.filename != ''):
        flash('Faltan campos obligatorios, incluyendo la imagen principal')
        return redirect(url_for('admin.admin_productos'))

    try:
        precio_val = float(precio)
    except ValueError:
        flash('Precio inválido')
        return redirect(url_for('admin.admin_productos'))

    ruta_principal = guardar_archivo(imagen_principal, 'productos/principal')
    if not ruta_principal:
        flash('Imagen principal inválida')
        return redirect(url_for('admin.admin_productos'))

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion or '',
        precio=precio_val,
        imagen=ruta_principal,
        categoria_id=int(categoria_id)
    )
    db.session.add(nuevo_producto)
    db.session.flush()

    # Guardar imágenes secundarias
    for img_file in imagenes_secundarias:
        if img_file and img_file.filename != '':
            ruta_secundaria = guardar_archivo(img_file, 'productos/galeria')
            if ruta_secundaria:
                orden = len(nuevo_producto.imagenes) + 1
                imagen_secundaria = ProductoImagen(
                    producto_id=nuevo_producto.id,
                    imagen=ruta_secundaria,
                    orden=orden
                )
                db.session.add(imagen_secundaria)

    try:
        db.session.commit()
        flash('Producto agregado correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al agregar producto')
        logging.error(f'Error agregando producto: {e}')

    return redirect(url_for('admin.admin_productos'))


# Edita un producto existente y sus imágenes desde el panel admin
@admin_bp.route('/admin/productos/editar/<int:producto_id>', methods=['POST'])
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
        return redirect(url_for('admin.admin_productos'))

    try:
        precio_val = float(precio)
    except ValueError:
        flash('Precio inválido')
        return redirect(url_for('admin.admin_productos'))

    try:
        # Actualiza los campos básicos del producto
        producto.nombre = nombre
        producto.descripcion = descripcion or ''
        producto.precio = precio_val
        producto.categoria_id = int(categoria_id)

        # --- Imagen principal ---
        if imagen_file and imagen_file.filename != '':
            filename = secure_filename(imagen_file.filename)
            carpeta_relativa = 'uploads/productos/principal'
            carpeta_absoluta = os.path.join(
                current_app.root_path, 'static', carpeta_relativa)
            os.makedirs(carpeta_absoluta, exist_ok=True)
            ruta_guardado = os.path.join(carpeta_absoluta, filename)
            imagen_file.save(ruta_guardado)
            producto.imagen = f'{carpeta_relativa}/{filename}'

        # --- Imágenes adicionales ---
        for img_file in imagenes_adicionales_files:
            if img_file and img_file.filename != '':
                filename = secure_filename(img_file.filename)
                carpeta_relativa = 'uploads/productos/galeria'
                carpeta_absoluta = os.path.join(
                    current_app.root_path, 'static', carpeta_relativa)
                os.makedirs(carpeta_absoluta, exist_ok=True)
                ruta_guardado = os.path.join(carpeta_absoluta, filename)
                img_file.save(ruta_guardado)

                nueva_imagen = ProductoImagen(
                    producto_id=producto.id,
                    imagen=f'{carpeta_relativa}/{filename}',
                    orden=producto.imagenes.count() + 1
                )
                db.session.add(nueva_imagen)

        # Eliminar imágenes adicionales marcadas
        imagenes_a_eliminar = request.form.get('imagenes_a_eliminar', '')
        if imagenes_a_eliminar:
            nombres = [n.strip() for n in imagenes_a_eliminar.split(',') if n.strip()]
            for nombre in nombres:
                img = ProductoImagen.query.filter_by(
                    producto_id=producto.id, imagen=nombre).first()
                if img:
                    ruta_img = os.path.join(current_app.static_folder, img.imagen)
                    if os.path.exists(ruta_img):
                        os.remove(ruta_img)
                    db.session.delete(img)

        db.session.commit()
        flash('Producto actualizado correctamente')

    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el producto')
        logging.error(f'Error actualizando producto: {e}')

    return redirect(url_for('admin.admin_productos'))


# Sube imágenes adicionales para un producto específico
@admin_bp.route('/admin/productos/<int:producto_id>/imagenes/subir', methods=['POST'])
@admin_required
def subir_imagen_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    files = request.files.getlist('imagenes')

    if not files or files[0].filename == '':
        flash('No seleccionaste archivos')
        return redirect(url_for('admin.admin_productos'))

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
            return redirect(url_for('admin.admin_productos'))

    try:
        db.session.commit()
        flash('Imágenes subidas correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al guardar las imágenes')
        logging.error(f'Error guardando imágenes: {e}')

    return redirect(url_for('admin.admin_productos'))


# Edita/actualiza una imagen adicional existente de un producto
@admin_bp.route('/admin/productos/imagenes/editar/<int:imagen_id>', methods=['POST'])
@admin_required
def editar_imagen_producto(imagen_id):
    imagen = ProductoImagen.query.get_or_404(imagen_id)
    file = request.files.get('imagen_nueva')

    if not file or file.filename == '':
        flash('No seleccionaste archivo para la imagen')
        return redirect(url_for('admin.admin_productos'))

    if allowed_file(file.filename):
        try:
            # Borra la imagen anterior del sistema de archivos
            ruta_anterior = os.path.join(
                current_app.static_folder, imagen.imagen)
            if os.path.exists(ruta_anterior):
                os.remove(ruta_anterior)

            filename = secure_filename(file.filename)
            carpeta_relativa = 'uploads/productos/galeria'
            carpeta_absoluta = os.path.join(
                current_app.root_path, 'static', carpeta_relativa)
            os.makedirs(carpeta_absoluta, exist_ok=True)
            ruta_guardado = os.path.join(carpeta_absoluta, filename)

            file.save(ruta_guardado)

            # Guarda la ruta relativa en la base de datos
            imagen.imagen = f'{carpeta_relativa}/{filename}'

            db.session.commit()
            flash('Imagen actualizada correctamente')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la imagen')
            logging.error(f'Error actualizando imagen: {e}')
    else:
        flash('Archivo no permitido')

    return redirect(url_for('admin.admin_productos'))


# Elimina un producto y todas sus imágenes (físicas y BD)
@admin_bp.route('/admin/productos/eliminar/<int:producto_id>', methods=['POST'])
@admin_required
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    try:
        # Elimina cada imagen física y su registro de la base de datos
        for img in producto.imagenes:
            ruta_fisica = os.path.join(current_app.static_folder, img.imagen)
            if os.path.exists(ruta_fisica):
                os.remove(ruta_fisica)
            db.session.delete(img)

        # Además elimina la imagen principal si existe y no está vacía
        if producto.imagen:
            ruta_imagen_principal = os.path.join(
                current_app.static_folder, producto.imagen)
            if os.path.exists(ruta_imagen_principal):
                os.remove(ruta_imagen_principal)

        # Elimina el producto de la base de datos
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el producto')
        logging.error(f'Error eliminando producto: {e}')

    return redirect(url_for('admin.admin_productos'))


# Elimina una imagen adicional de producto (física y base de datos)
@admin_bp.route('/admin/productos/imagenes/eliminar/<int:imagen_id>', methods=['POST'])
@admin_required
def eliminar_imagen_producto(imagen_id):
    imagen = ProductoImagen.query.get_or_404(imagen_id)
    try:
        # Construir ruta física completa usando current_app.static_folder + ruta guardada en la BD
        ruta_fisica = os.path.join(current_app.static_folder, imagen.imagen)

        # Verificar que el archivo exista antes de eliminar
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        # Eliminar registro de la base de datos
        db.session.delete(imagen)
        db.session.commit()
        flash('Imagen eliminada correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la imagen')
        logging.error(f'Error eliminando imagen: {e}')

    return redirect(url_for('admin.admin_productos'))


# ----------------- Administración de Pedidos ----------------- #

@admin_bp.route("/admin/pedidos")
@admin_required
def admin_pedidos():
    filtro = request.args.get('filtro', 'nuevos')

    if filtro == "nuevos":
        pedidos = Pedido.query.filter_by(
            es_viejo=False).order_by(Pedido.fecha.desc()).all()
    elif filtro == "historial":
        pedidos = Pedido.query.filter_by(
            es_viejo=True).order_by(Pedido.fecha.desc()).all()
    else:
        pedidos = Pedido.query.order_by(Pedido.fecha.desc()).all()

    return render_template("admin_pedidos.html", pedidos=pedidos, filtro=filtro, current_time=datetime.now())


@admin_bp.route('/admin/pedidos/toggle_estado/<int:pedido_id>', methods=['POST'])
@admin_required
def toggle_estado_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.es_viejo:
        flash("No se puede cambiar el estado de un pedido en historial.", "warning")
        return redirect(url_for('admin.admin_pedidos', filtro='nuevos'))

    if pedido.estado == 'nuevo':
        pedido.estado = 'pendiente'
    elif pedido.estado == 'pendiente':
        pedido.estado = 'nuevo'
    else:
        flash("Estado actual no permite toggle.", "warning")
        return redirect(url_for('admin.admin_pedidos', filtro='nuevos'))

    try:
        db.session.commit()
        flash(
            f"Estado del pedido #{pedido.id} actualizado a {pedido.estado}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar estado del pedido: {str(e)}", "danger")

    return redirect(url_for('admin.admin_pedidos', filtro='nuevos'))


@admin_bp.route('/admin/pedidos/marcar_como_historial', methods=['POST'])
@admin_required
def marcar_como_historial():
    ids = request.form.getlist('pedido_ids')
    if not ids:
        flash("No seleccionaste pedidos para marcar como historial.", "warning")
        return redirect(url_for('admin.admin_pedidos', filtro='nuevos'))

    pedidos = Pedido.query.filter(Pedido.id.in_(
        ids), Pedido.es_viejo == False).all()
    for pedido in pedidos:
        pedido.es_viejo = True

    try:
        db.session.commit()
        flash(f"Se marcaron {len(pedidos)} pedidos como historial.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al marcar pedidos como historial: {str(e)}", "danger")

    return redirect(url_for('admin.admin_pedidos', filtro='nuevos'))
