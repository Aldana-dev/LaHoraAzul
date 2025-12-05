from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from app.models import db, Banner, Galeria, Producto, Categoria, ProductoImagen, Pedido, PedidoItem
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os

main_bp = Blueprint('main', __name__)

UPLOAD_FOLDER = 'app/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_archivo(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        return os.path.join('uploads', filename).replace('\\', '/')
    return None


def admin_required(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get('admin'):
            flash('Necesitás iniciar sesión como admin')
            return redirect(url_for('main.admin_login'))
        return f(*args, **kwargs)
    return decorada


def obtener_carrito():
    if 'carrito' not in session:
        session['carrito'] = []
    return session['carrito']


@main_bp.route('/')
def index():
    banners = Banner.query.order_by(Banner.fecha_creacion).all()
    imagenes_galeria = Galeria.query.order_by(Galeria.fecha_creacion.desc()).all()
    return render_template('index.html', banners=banners, imagenes_galeria=imagenes_galeria)


@main_bp.route('/nosotras')
def nosotras():
    return render_template('nosotras.html')


@main_bp.route('/init_categorias')
def init_categorias():
    nombres = ["Cuadros", "Cerámica", "Cuadernos", "Totebags"]
    Categoria.query.delete()
    db.session.commit()
    
    for nombre in nombres:
        db.session.add(Categoria(nombre=nombre))
    
    db.session.commit()
    return "Categorías inicializadas correctamente."


@main_bp.route('/tienda')
def tienda():
    categoria_id = request.args.get('categoria_id', type=int)
    categorias = Categoria.query.order_by(Categoria.id).all()
    
    if categoria_id:
        productos = Producto.query.filter_by(
            categoria_id=categoria_id, vendido=False).order_by(Producto.id.desc()).all()
    else:
        productos = Producto.query.filter_by(
            vendido=False).order_by(Producto.id.desc()).all()
    
    productos_data = []
    for p in productos:
        img_path = p.imagen if p.imagen else 'img/placeholder.png'
        productos_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'imagen': img_path
        })
    
    return render_template('tienda.html', categorias=categorias, productos=productos_data, categoria_id=categoria_id)


@main_bp.route('/producto/<int:producto_id>')
def producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    imagenes = ProductoImagen.query.filter_by(
        producto_id=producto_id).order_by(ProductoImagen.orden).all()
    return render_template('producto.html', producto=producto, imagenes=imagenes)


@main_bp.route('/marcos')
def marcos():
    return render_template('marcos.html')


@main_bp.route('/galeria')
def galeria():
    imagenes = Galeria.query.order_by(Galeria.fecha_creacion.desc()).all()
    return render_template('galeria.html', imagenes=imagenes)


@main_bp.route('/carrito')
def carrito():
    carrito_ids = session.get('carrito', [])
    productos = Producto.query.filter(Producto.id.in_(carrito_ids)).all()
    
    carrito_data = []
    subtotal = 0
    for p in productos:
        subtotal += p.precio
        carrito_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'imagen': p.imagen
        })
    
    costo_envio = 0
    total = subtotal + costo_envio
    
    return render_template(
        'carrito.html',
        carrito=carrito_data,
        carrito_ids=carrito_ids,  # <-- NUEVO: pasamos los IDs al template
        subtotal=subtotal,
        costo_envio=costo_envio,
        total=total
    )


@main_bp.route('/carrito/agregar/<int:producto_id>', methods=['POST'])
def agregar_al_carrito(producto_id):
    carrito = obtener_carrito()
    
    if producto_id not in carrito:
        carrito.append(producto_id)
        session['carrito'] = carrito
        session.modified = True  # <-- NUEVO: forzar que Flask guarde la sesión
        flash('Producto agregado al carrito')
    
    return redirect(url_for('main.producto', producto_id=producto_id))


@main_bp.route('/carrito/quitar/<int:producto_id>', methods=['POST'])
def quitar_del_carrito(producto_id):
    carrito = session.get('carrito', [])
    
    if producto_id in carrito:
        carrito.remove(producto_id)
        session['carrito'] = carrito
        session.modified = True  # <-- NUEVO: forzar que Flask guarde la sesión
        flash('Producto eliminado del carrito')
    
    return redirect(url_for('main.carrito'))


# NUEVA RUTA: API para obtener el estado del carrito
@main_bp.route('/api/carrito/estado', methods=['GET'])
def carrito_estado():
    """Devuelve los IDs de productos en el carrito (para sincronizar con frontend)"""
    carrito_ids = session.get('carrito', [])
    return jsonify({
        'productos': carrito_ids,
        'cantidad': len(carrito_ids)
    })

@main_bp.route('/carrito/confirmar', methods=['POST'])
def confirmar_pedido():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Datos incompletos"}), 400

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
        comentarios = data.get("comentarios", "")
        metodo_pago = data.get("metodo_pago", "tarjeta")
        payment_id = data.get("payment_id")
        payment_token = data.get("payment_token")
        payment_ticket = data.get("payment_ticket")
        payment_authorization = data.get("payment_authorization")
        total = data.get("total")

        if not nombre or not apellido:
            return jsonify({"success": False, "error": "Nombre y apellido son obligatorios"}), 400
        
        if not email_contacto:
            return jsonify({"success": False, "error": "Email es obligatorio"}), 400
        
        if not total or total <= 0:
            return jsonify({"success": False, "error": "Total inválido"}), 400

        if metodo_pago == "tarjeta":
            if not payment_id or not payment_ticket:
                return jsonify({
                    "success": False,
                    "error": "El pago no fue confirmado"
                }), 400

        carrito_ids = data.get("carrito_ids") or session.get("carrito", [])
        if not carrito_ids:
            return jsonify({"success": False, "error": "El carrito está vacío"}), 400

        productos = Producto.query.filter(Producto.id.in_(carrito_ids)).all()
        if not productos:
            return jsonify({"success": False, "error": "Productos no encontrados"}), 400

        nuevo_pedido = Pedido(
            nombre=nombre,
            apellido=apellido,
            email_contacto=email_contacto,
            telefono=telefono,
            tipo_envio=tipo_envio,
            comentarios=comentarios,
            total=total,
            fecha=datetime.utcnow(),
            estado='confirmado',
            payment_id=payment_id if metodo_pago == "tarjeta" else None,
            payment_ticket=payment_ticket if metodo_pago == "tarjeta" else None,
            payment_authorization=payment_authorization if metodo_pago == "tarjeta" else None
        )
        
        db.session.add(nuevo_pedido)
        db.session.flush()

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

        session.pop("carrito", None)

        return jsonify({
            "success": True, 
            "pedido_id": nuevo_pedido.id,
            "message": "Pedido confirmado exitosamente"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False, 
            "error": "Ocurrió un error al procesar el pedido", 
            "details": str(e)
        }), 500