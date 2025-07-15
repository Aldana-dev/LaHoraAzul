from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

# ----------------- CATEGORÍAS DE PRODUCTOS ----------------- #
class Categoria(db.Model):
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

    productos = db.relationship('Producto', backref='categoria', lazy=True)

# ----------------- PRODUCTOS ----------------- #
class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    imagen = db.Column(db.String(255), nullable=False)  # Imagen principal / thumbnail
    vendido = db.Column(db.Boolean, default=False)

    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)

    # Relación uno a muchos con las imágenes adicionales
    imagenes = db.relationship(
        'ProductoImagen',
        backref='producto',
        lazy=True,
        cascade='all, delete-orphan',
        order_by="ProductoImagen.orden"
    )

# ----------------- IMÁGENES DE PRODUCTOS ----------------- #
class ProductoImagen(db.Model):
    __tablename__ = 'producto_imagenes'

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    imagen = db.Column(db.String(255), nullable=False)  # Ruta relativa a /static/uploads/
    orden = db.Column(db.Integer, default=0)  # Para ordenar imágenes; 0 = principal

# ----------------- PEDIDOS ----------------- #
class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    email_contacto = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(50), default='pendiente')  # pendiente, enviado, entregado...
    total = db.Column(db.Numeric(10, 2), nullable=False)

    items = db.relationship('PedidoItem', backref='pedido', lazy=True)

# ----------------- ITEMS DE CADA PEDIDO ----------------- #
class PedidoItem(db.Model):
    __tablename__ = 'pedido_items'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    producto = db.relationship('Producto')

# ----------------- USUARIOS (SOLO ADMIN) ----------------- #
class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contraseña_hash = db.Column(db.String(255), nullable=False)
    es_admin = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.contraseña_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contraseña_hash, password)

# ----------------- GALERÍA ----------------- #
class Galeria(db.Model):
    __tablename__ = 'galeria'

    id = db.Column(db.Integer, primary_key=True)
    imagen = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------- BANNERS ----------------- #
class Banner(db.Model):
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    imagen = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
