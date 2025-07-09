from flask import Flask, render_template, request, redirect, url_for, flash
from app.models import db, Banner, Galeria, Producto
import os
import logging
from werkzeug.utils import secure_filename
from app.models import Banner

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://aldana_dev:devadmin@localhost/lahoraazul_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Config para subida de archivos
UPLOAD_FOLDER = 'app/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'tu_clave_secreta_aqui'  # necesario para flash()

db.init_app(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Frontend
@app.route('/')
def index():
    banners = Banner.query.order_by(Banner.fecha_creacion).all()
    return render_template('index.html', banners=banners)

@app.route('/nosotras')
def nosotras():
    return render_template('nosotras.html')

@app.route('/tienda')
def tienda():
    return render_template('tienda.html')

@app.route('/producto')
def producto():
    return render_template('producto.html')

@app.route('/marcos')
def marcos():
    return render_template('marcos.html')

@app.route('/galeria')
def galeria():
    return render_template('galeria.html')

@app.route('/carrito')
def carrito():
    return render_template('carrito.html')

@app.route('/login')
def login():
    return render_template('login.html')

# Panel admin
@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route("/admin/banner")
def admin_banner():
    banners = Banner.query.all()
    return render_template("admin_banner.html", banners=banners)


@app.route("/admin/galeria")
def admin_galeria():
    return render_template("admin_galeria.html")

@app.route("/admin/productos")
def admin_productos():
    return render_template("admin_productos.html")

# POST para subir banner
@app.route('/admin/banner/subir', methods=['POST'])
def subir_banner():
    logging.debug("POST /admin/banner/subir iniciada")
    if 'imagen' not in request.files:
        logging.warning("No se encontró el archivo 'imagen' en la petición")
        flash('No se encontró el archivo')
        return redirect(url_for('admin_banner'))
    file = request.files['imagen']
    if file.filename == '':
        logging.warning("Archivo enviado sin nombre")
        flash('No seleccionaste ningún archivo')
        return redirect(url_for('admin_banner'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        logging.info(f"Archivo guardado en {filepath}")

        nuevo_banner = Banner(imagen=filepath)
        db.session.add(nuevo_banner)
        try:
            db.session.commit()
            logging.info(f"Banner agregado a la base de datos: {nuevo_banner}")
            flash('Banner subido correctamente')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error al guardar banner en base: {e}")
            flash('Error al guardar en la base de datos')
        return redirect(url_for('admin_banner'))
    else:
        logging.warning(f"Archivo no permitido: {file.filename}")
        flash('Archivo no permitido')
        return redirect(url_for('admin_banner'))

@app.route('/admin/banner/eliminar/<int:banner_id>', methods=['POST'])
def eliminar_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    try:
        # Primero, borramos el archivo físico (si existe)
        if banner.imagen and os.path.exists(banner.imagen):
            os.remove(banner.imagen)
            logging.info(f"Archivo eliminado: {banner.imagen}")
        
        # Luego, borramos el registro en la base
        db.session.delete(banner)
        db.session.commit()
        flash('Banner eliminado correctamente')
        logging.info(f"Banner eliminado: ID {banner_id}")
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el banner')
        logging.error(f"Error eliminando banner ID {banner_id}: {e}")
    return redirect(url_for('admin_banner'))


# POST para subir imagen a galería
@app.route('/admin/galeria/subir', methods=['POST'])
def subir_galeria():
    logging.debug("POST /admin/galeria/subir iniciada")
    if 'imagen' not in request.files:
        logging.warning("No se encontró el archivo 'imagen' en la petición")
        flash('No se encontró el archivo')
        return redirect(url_for('admin_galeria'))
    file = request.files['imagen']
    if file.filename == '':
        logging.warning("Archivo enviado sin nombre")
        flash('No seleccionaste ningún archivo')
        return redirect(url_for('admin_galeria'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        logging.info(f"Archivo guardado en {filepath}")

        nueva_imagen = Galeria(imagen=filepath)
        db.session.add(nueva_imagen)
        try:
            db.session.commit()
            logging.info(f"Imagen de galería agregada a la base de datos: {nueva_imagen}")
            flash('Imagen de galería subida correctamente')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error al guardar imagen en base: {e}")
            flash('Error al guardar en la base de datos')
        return redirect(url_for('admin_galeria'))
    else:
        logging.warning(f"Archivo no permitido: {file.filename}")
        flash('Archivo no permitido')
        return redirect(url_for('admin_galeria'))

# POST para agregar producto (básico, sin imagen aún)
@app.route('/admin/productos/agregar', methods=['POST'])
def agregar_producto():
    logging.debug("POST /admin/productos/agregar iniciada")
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = request.form.get('precio')
    imagen = request.form.get('imagen')  # ideal subir archivo igual que banners
    categoria_id = request.form.get('categoria_id')

    logging.info(f"Datos recibidos - nombre: {nombre}, precio: {precio}, imagen: {imagen}, categoria_id: {categoria_id}")

    if not (nombre and precio and imagen and categoria_id):
        logging.warning("Faltan campos obligatorios")
        flash('Faltan campos obligatorios')
        return redirect(url_for('admin_productos'))

    try:
        precio_val = float(precio)
    except ValueError:
        logging.warning("Precio inválido recibido")
        flash('Precio inválido')
        return redirect(url_for('admin_productos'))

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio_val,
        imagen=imagen,
        categoria_id=int(categoria_id)
    )
    db.session.add(nuevo_producto)
    try:
        db.session.commit()
        logging.info(f"Producto agregado a la base de datos: {nuevo_producto}")
        flash('Producto agregado correctamente')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al guardar producto en base: {e}")
        flash('Error al guardar en la base de datos')
    return redirect(url_for('admin_productos'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
