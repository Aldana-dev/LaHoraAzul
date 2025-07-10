from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, Banner, Galeria, Producto, Categoria, ProductoImagen
import os
import logging
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Configuración base de datos (cambiar por tus datos reales)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://aldana_dev:devadmin@localhost/lahoraazul_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Carpeta para subir archivos (imágenes)
UPLOAD_FOLDER = 'app/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Clave secreta para sesiones y flash messages
app.secret_key = 'tu_clave_secreta_aqui'

# Inicializar la base de datos con la app
db.init_app(app)

def allowed_file(filename):
    """Valida que el archivo tenga una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def guardar_archivo(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        logging.debug(f'Archivo guardado en: {filepath}')
        return filename  # solo nombre
    logging.debug('Archivo no válido o no enviado')
    return None

# ----------------- Rutas ----------------- #

@app.route('/')
def index():
    banners = Banner.query.order_by(Banner.fecha_creacion).all()
    imagenes_galeria = Galeria.query.order_by(Galeria.fecha_creacion.desc()).all()
    return render_template('index.html', banners=banners, imagenes_galeria=imagenes_galeria)


@app.route('/nosotras')
def nosotras():
    return render_template('nosotras.html')


@app.route('/init_categorias')
def init_categorias():
    nombres = ["Cuadros", "Cerámica", "Cuadernos", "Totebags"]

    Categoria.query.delete()
    db.session.commit()

    for nombre in nombres:
        db.session.add(Categoria(nombre=nombre))
    db.session.commit()

    return "Categorías inicializadas correctamente."


@app.route('/tienda')
def tienda():
    categoria_id = request.args.get('categoria_id', type=int)
    categorias = Categoria.query.order_by(Categoria.id).all()

    if categoria_id:
        productos = Producto.query.filter_by(categoria_id=categoria_id).order_by(Producto.id.desc()).all()
    else:
        productos = Producto.query.order_by(Producto.id.desc()).all()

    productos_data = []
    for p in productos:
        # Usar directamente p.imagen, que debería estar guardado bien en la DB
        img_path = p.imagen if p.imagen else 'img/placeholder.png'

        productos_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'imagen': img_path
        })

    return render_template('tienda.html', categorias=categorias, productos=productos_data, categoria_id=categoria_id)


@app.route('/producto/<int:producto_id>')
def producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    imagenes = ProductoImagen.query.filter_by(producto_id=producto_id).order_by(ProductoImagen.orden).all()
    return render_template('producto.html', producto=producto, imagenes=imagenes)

@app.route('/marcos')
def marcos():
    return render_template('marcos.html')


@app.route('/galeria')
def galeria():
    imagenes = Galeria.query.order_by(Galeria.fecha_creacion.desc()).all()
    return render_template('galeria.html', imagenes=imagenes)


@app.route('/carrito')
def carrito():
    return render_template('carrito.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route("/admin/banner")
def admin_banner():
    banners = Banner.query.all()
    return render_template("admin_banner.html", banners=banners)


@app.route("/admin/galeria")
def admin_galeria():
    imagenes = Galeria.query.order_by(Galeria.fecha_creacion).all()
    return render_template("admin_galeria.html", imagenes=imagenes)


@app.route("/admin/productos")
def admin_productos():
    categorias = Categoria.query.all()
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("admin_productos.html", categorias=categorias, productos=productos)
@app.route('/admin/productos/agregar', methods=['POST'])
def agregar_producto():
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = request.form.get('precio')
    categoria_id = request.form.get('categoria_id')
    imagen_file = request.files.get('imagen')

    if not (nombre and precio and categoria_id and imagen_file and imagen_file.filename != ''):
        flash('Faltan campos obligatorios, incluyendo la imagen')
        return redirect(url_for('admin_productos'))

    try:
        precio_val = float(precio)
    except ValueError:
        flash('Precio inválido')
        return redirect(url_for('admin_productos'))

    filename = secure_filename(imagen_file.filename)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Ruta absoluta donde está app.py
    uploads_path = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    os.makedirs(uploads_path, exist_ok=True)
    ruta_guardado = os.path.join(uploads_path, filename)
    imagen_file.save(ruta_guardado)
    logging.info(f"Imagen guardada en ruta física: {ruta_guardado}")

    ruta_relativa = os.path.join('uploads', filename).replace('\\', '/')

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
@app.route('/admin/productos/editar/<int:producto_id>', methods=['POST'])
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = request.form.get('precio')
    categoria_id = request.form.get('categoria_id')
    imagen_file = request.files.get('imagen')  # Imagen principal nueva (opcional)
    imagenes_adicionales_files = request.files.getlist('imagenes_adicionales')  # Nuevas imágenes adicionales

    if not (nombre and precio and categoria_id):
        flash('Faltan campos obligatorios')
        return redirect(url_for('admin_productos'))

    try:
        precio_val = float(precio)
    except ValueError:
        flash('Precio inválido')
        return redirect(url_for('admin_productos'))

    try:
        # Actualizar campos básicos
        producto.nombre = nombre
        producto.descripcion = descripcion or ''
        producto.precio = precio_val
        producto.categoria_id = int(categoria_id)

        # Actualizar imagen principal si hay nueva
        if imagen_file and imagen_file.filename != '':
            filename = secure_filename(imagen_file.filename)
            ruta_guardado = os.path.join(app.root_path, 'static', 'uploads', filename)
            os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
            imagen_file.save(ruta_guardado)
            producto.imagen = filename

        # Guardar nuevas imágenes adicionales si hay
        for img_file in imagenes_adicionales_files:
            if img_file and img_file.filename != '':
                filename = secure_filename(img_file.filename)
                ruta_guardado = os.path.join(app.root_path, 'static', 'uploads', filename)
                os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
                img_file.save(ruta_guardado)
                nueva_imagen = ProductoImagen(
                    producto_id=producto.id,
                    imagen=filename,
                    orden=producto.imagenes.count() + 1
                )
                db.session.add(nueva_imagen)

        db.session.commit()
        flash('Producto actualizado correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el producto')
        logging.error(f'Error actualizando producto: {e}')

    return redirect(url_for('admin_productos'))

@app.route('/admin/productos/<int:producto_id>/imagenes/subir', methods=['POST'])
def subir_imagen_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    files = request.files.getlist('imagenes')

    if not files or files[0].filename == '':
        flash('No seleccionaste archivos')
        return redirect(url_for('admin_productos'))

    for file in files:
        filepath = guardar_archivo(file)
        if filepath:
            max_orden = db.session.query(db.func.max(ProductoImagen.orden)).filter_by(producto_id=producto_id).scalar()
            orden = (max_orden or 0) + 1
            nueva_img = ProductoImagen(producto_id=producto_id, imagen=filepath, orden=orden)
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


@app.route('/admin/productos/imagenes/editar/<int:imagen_id>', methods=['POST'])
def editar_imagen_producto(imagen_id):
    imagen = ProductoImagen.query.get_or_404(imagen_id)
    file = request.files.get('imagen_nueva')

    if not file or file.filename == '':
        flash('No seleccionaste archivo para la imagen')
        return redirect(url_for('admin_productos'))

    if allowed_file(file.filename):
        try:
            ruta_anterior = os.path.join(app.static_folder, imagen.imagen)
            if os.path.exists(ruta_anterior):
                os.remove(ruta_anterior)

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

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

@app.route('/admin/productos/eliminar/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    try:
        # Eliminar imágenes físicas y de BD
        for img in producto.imagenes:
            ruta_fisica = os.path.join(app.static_folder, img.imagen)
            if os.path.exists(ruta_fisica):
                os.remove(ruta_fisica)
            db.session.delete(img)

        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el producto')
        logging.error(f'Error eliminando producto: {e}')

    return redirect(url_for('admin_productos'))


@app.route('/admin/productos/imagenes/eliminar/<int:imagen_id>', methods=['POST'])
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


@app.route('/admin/banner/subir', methods=['POST'])
def subir_banner():
    file = request.files.get('imagen')
    if not file or file.filename == '':
        flash('No seleccionaste ningún archivo')
        return redirect(url_for('admin_banner'))

    filepath = guardar_archivo(file)
    if not filepath:
        flash('Archivo no permitido')
        return redirect(url_for('admin_banner'))

    nuevo_banner = Banner(imagen=filepath)
    db.session.add(nuevo_banner)
    try:
        db.session.commit()
        flash('Banner subido correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al guardar en la base de datos')
    return redirect(url_for('admin_banner'))


@app.route('/admin/banner/eliminar/<int:banner_id>', methods=['POST'])
def eliminar_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    try:
        ruta_fisica = os.path.join(app.static_folder, banner.imagen)
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        db.session.delete(banner)
        db.session.commit()
        flash('Banner eliminado correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al eliminar el banner')
    return redirect(url_for('admin_banner'))


@app.route('/admin/galeria/subir', methods=['POST'])
def subir_galeria():
    file = request.files.get('imagen')
    if not file or file.filename == '':
        flash('No seleccionaste ningún archivo')
        return redirect(url_for('admin_galeria'))

    filepath = guardar_archivo(file)
    if not filepath:
        flash('Archivo no permitido')
        return redirect(url_for('admin_galeria'))

    nueva_imagen = Galeria(imagen=filepath)
    db.session.add(nueva_imagen)
    try:
        db.session.commit()
        flash('Imagen de galería subida correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al guardar en la base de datos')
    return redirect(url_for('admin_galeria'))


@app.route('/admin/galeria/eliminar/<int:imagen_id>', methods=['POST'])
def eliminar_galeria(imagen_id):
    imagen = Galeria.query.get_or_404(imagen_id)
    try:
        ruta_fisica = os.path.join(app.static_folder, imagen.imagen)
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)

        db.session.delete(imagen)
        db.session.commit()
        flash('Imagen eliminada correctamente')
    except Exception:
        db.session.rollback()
        flash('Error al eliminar la imagen')
    return redirect(url_for('admin_galeria'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear tablas si no existen
    app.run(debug=True, port=5000)
