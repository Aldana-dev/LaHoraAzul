from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from app.models import db, Banner, Galeria, Producto, Categoria, ProductoImagen, Pedido, Usuario
from werkzeug.utils import secure_filename
import os
from functools import wraps
from datetime import datetime


admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates')

UPLOAD_FOLDER = 'app/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def guardar_archivo(file, subcarpeta):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        static_folder = current_app.static_folder
        subcarpeta_path = os.path.join(static_folder, 'uploads', subcarpeta)
        os.makedirs(subcarpeta_path, exist_ok=True)

        filepath = os.path.join(subcarpeta_path, filename)
        file.save(filepath)

        return os.path.join('uploads', subcarpeta, filename).replace('\\', '/')
    return None

def admin_required(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Necesitás iniciar sesión como admin')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorada

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('username')
        clave = request.form.get('password')

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.es_admin and usuario.check_password(clave):
            session.permanent = True
            session['admin_id'] = usuario.id
            print(f"DEBUG: Login exitoso - admin_id {usuario.id} guardado en sesión")
            flash('Sesión iniciada correctamente')
            return redirect(url_for('admin.dashboard'))

        print(f"DEBUG: Login fallido - usuario: {usuario}, es_admin: {usuario.es_admin if usuario else 'N/A'}")
        flash('Credenciales incorrectas')

    return render_template('login.html')

@admin_bp.route('/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Sesión cerrada')
    return redirect(url_for('main.index'))
@admin_bp.route('/')
@admin_required
def dashboard():
    return render_template('admin.html')

@admin_bp.route("/banner")
@admin_required
def admin_banner():
    banners = Banner.query.all()
    return render_template("admin_banner.html", banners=banners)

@admin_bp.route('/banner/subir', methods=['POST'])
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

@admin_bp.route('/banner/eliminar/<int:banner_id>', methods=['POST'])
@admin_required
def eliminar_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    try:
        ruta_fisica = os.path.join(current_app.static_folder, banner.imagen)
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        db.session.delete(banner)
        db.session.commit()
        flash('Banner eliminado correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al eliminar el banner')

    return redirect(url_for('admin.admin_banner'))

@admin_bp.route("/galeria")
@admin_required
def admin_galeria():
    imagenes = Galeria.query.order_by(Galeria.fecha_creacion).all()
    return render_template("admin_galeria.html", imagenes=imagenes)

@admin_bp.route('/galeria/subir', methods=['POST'])
@admin_required
def subir_galeria():
    archivos = request.files.getlist('imagenes')
    if not archivos:
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

@admin_bp.route('/galeria/eliminar/<int:imagen_id>', methods=['POST'])
@admin_required
def eliminar_galeria(imagen_id):
    imagen = Galeria.query.get_or_404(imagen_id)
    try:
        ruta_fisica = os.path.join(current_app.static_folder, imagen.imagen)
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        db.session.delete(imagen)
        db.session.commit()
        flash('Imagen eliminada correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al eliminar la imagen')

    return redirect(url_for('admin.admin_galeria'))

@admin_bp.route("/productos")
@admin_required
def admin_productos():
    categorias = Categoria.query.all()
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("admin_productos.html", categorias=categorias, productos=productos)

@admin_bp.route('/productos/agregar', methods=['POST'])
@admin_required
def agregar_producto():
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
    except Exception:
        db.session.rollback()
        flash('Error al agregar producto')

    return redirect(url_for('admin.admin_productos'))

@admin_bp.route('/productos/editar/<int:producto_id>', methods=['POST'])
@admin_required
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = request.form.get('precio')
    categoria_id = request.form.get('categoria_id')
    imagen_file = request.files.get('imagen')
    imagenes_adicionales_files = request.files.getlist('imagenes_adicionales')

    if not (nombre and precio and categoria_id):
        flash('Faltan campos obligatorios')
        return redirect(url_for('admin.admin_productos'))

    try:
        precio_val = float(precio)
    except ValueError:
        flash('Precio inválido')
        return redirect(url_for('admin.admin_productos'))

    try:
        producto.nombre = nombre
        producto.descripcion = descripcion or ''
        producto.precio = precio_val
        producto.categoria_id = int(categoria_id)

        if imagen_file and imagen_file.filename != '':
            filename = secure_filename(imagen_file.filename)
            carpeta_relativa = 'uploads/productos/principal'
            carpeta_absoluta = os.path.join(current_app.root_path, 'static', carpeta_relativa)
            os.makedirs(carpeta_absoluta, exist_ok=True)
            ruta_guardado = os.path.join(carpeta_absoluta, filename)
            imagen_file.save(ruta_guardado)
            producto.imagen = f'{carpeta_relativa}/{filename}'

        for img_file in imagenes_adicionales_files:
            if img_file and img_file.filename != '':
                filename = secure_filename(img_file.filename)
                carpeta_relativa = 'uploads/productos/galeria'
                carpeta_absoluta = os.path.join(current_app.root_path, 'static', carpeta_relativa)
                os.makedirs(carpeta_absoluta, exist_ok=True)
                ruta_guardado = os.path.join(carpeta_absoluta, filename)
                img_file.save(ruta_guardado)

                nueva_imagen = ProductoImagen(
                    producto_id=producto.id,
                    imagen=f'{carpeta_relativa}/{filename}',
                    orden=len(producto.imagenes) + 1
                )
                db.session.add(nueva_imagen)

        imagenes_a_eliminar = request.form.get('imagenes_a_eliminar', '')
        if imagenes_a_eliminar:
            nombres = [n.strip() for n in imagenes_a_eliminar.split(',') if n.strip()]
            for nombre in nombres:
                img = ProductoImagen.query.filter_by(producto_id=producto.id, imagen=nombre).first()
                if img:
                    ruta_img = os.path.join(current_app.static_folder, img.imagen)
                    if os.path.exists(ruta_img):
                        os.remove(ruta_img)
                    db.session.delete(img)

        db.session.commit()
        flash('Producto actualizado correctamente')

    except Exception:
        db.session.rollback()
        flash('Error al actualizar el producto')

    return redirect(url_for('admin.admin_productos'))

@admin_bp.route('/productos/<int:producto_id>/imagenes/subir', methods=['POST'])
@admin_required
def subir_imagen_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    files = request.files.getlist('imagenes')

    if not files or files[0].filename == '':
        flash('No seleccionaste archivos')
        return redirect(url_for('admin.admin_productos'))

    for file in files:
        filepath = guardar_archivo(file, 'productos/galeria')
        if filepath:
            max_orden = db.session.query(db.func.max(ProductoImagen.orden)).filter_by(producto_id=producto_id).scalar()
            orden = (max_orden or 0) + 1
            nueva_img = ProductoImagen(producto_id=producto_id, imagen=filepath, orden=orden)
            db.session.add(nueva_img)
        else:
            flash(f'Archivo no permitido: {file.filename}')
            return redirect(url_for('admin.admin_productos'))

    try:
        db.session.commit()
        flash('Imágenes subidas correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al guardar las imágenes')

    return redirect(url_for('admin.admin_productos'))

@admin_bp.route('/productos/imagenes/editar/<int:imagen_id>', methods=['POST'])
@admin_required
def editar_imagen_producto(imagen_id):
    imagen = ProductoImagen.query.get_or_404(imagen_id)
    file = request.files.get('imagen_nueva')

    if not file or file.filename == '':
        flash('No seleccionaste archivo para la imagen')
        return redirect(url_for('admin.admin_productos'))

    if allowed_file(file.filename):
        try:
            ruta_anterior = os.path.join(current_app.static_folder, imagen.imagen)
            if os.path.exists(ruta_anterior):
                os.remove(ruta_anterior)

            filename = secure_filename(file.filename)
            carpeta_relativa = 'uploads/productos/galeria'
            carpeta_absoluta = os.path.join(current_app.root_path, 'static', carpeta_relativa)
            os.makedirs(carpeta_absoluta, exist_ok=True)
            ruta_guardado = os.path.join(carpeta_absoluta, filename)

            file.save(ruta_guardado)
            imagen.imagen = f'{carpeta_relativa}/{filename}'

            db.session.commit()
            flash('Imagen actualizada correctamente')
        except Exception:
            db.session.rollback()
            flash('Error al actualizar la imagen')
    else:
        flash('Archivo no permitido')

    return redirect(url_for('admin.admin_productos'))

@admin_bp.route('/productos/eliminar/<int:producto_id>', methods=['POST'])
@admin_required
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    try:
        for img in producto.imagenes:
            ruta_fisica = os.path.join(current_app.static_folder, img.imagen)
            if os.path.exists(ruta_fisica):
                os.remove(ruta_fisica)
            db.session.delete(img)

        if producto.imagen:
            ruta_imagen_principal = os.path.join(current_app.static_folder, producto.imagen)
            if os.path.exists(ruta_imagen_principal):
                os.remove(ruta_imagen_principal)

        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al eliminar el producto')

    return redirect(url_for('admin.admin_productos'))

@admin_bp.route('/productos/imagenes/eliminar/<int:imagen_id>', methods=['POST'])
@admin_required
def eliminar_imagen_producto(imagen_id):
    imagen = ProductoImagen.query.get_or_404(imagen_id)
    try:
        ruta_fisica = os.path.join(current_app.static_folder, imagen.imagen)
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        db.session.delete(imagen)
        db.session.commit()
        flash('Imagen eliminada correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al eliminar la imagen')

    return redirect(url_for('admin.admin_productos'))

@admin_bp.route("/pedidos")
@admin_required
def admin_pedidos():
    filtro = request.args.get('filtro', 'nuevos')

    if filtro == "nuevos":
        pedidos = Pedido.query.filter_by(es_viejo=False).order_by(Pedido.fecha.desc()).all()
    elif filtro == "historial":
        pedidos = Pedido.query.filter_by(es_viejo=True).order_by(Pedido.fecha.desc()).all()
    else:
        pedidos = Pedido.query.order_by(Pedido.fecha.desc()).all()

    return render_template("admin_pedidos.html", pedidos=pedidos, filtro=filtro, current_time=datetime.now())

@admin_bp.route('/pedidos/toggle_estado/<int:pedido_id>', methods=['POST'])
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
        flash(f"Estado del pedido #{pedido.id} actualizado a {pedido.estado}.", "success")
    except Exception:
        db.session.rollback()
        flash("Error al actualizar estado del pedido.", "danger")

    return redirect(url_for('admin.admin_pedidos', filtro='nuevos'))

@admin_bp.route('/pedidos/marcar_como_historial', methods=['POST'])
@admin_required
def marcar_como_historial():
    ids = request.form.getlist('pedido_ids')
    if not ids:
        flash("No seleccionaste pedidos para marcar como historial.", "warning")
        return redirect(url_for('admin.admin_pedidos', filtro='nuevos'))

    pedidos = Pedido.query.filter(Pedido.id.in_(ids), Pedido.es_viejo == False).all()
    for pedido in pedidos:
        pedido.es_viejo = True

    try:
        db.session.commit()
        flash(f"Se marcaron {len(pedidos)} pedidos como historial.", "success")
    except Exception:
        db.session.rollback()
        flash("Error al marcar pedidos como historial.", "danger")

    return redirect(url_for('admin.admin_pedidos', filtro='nuevos'))
