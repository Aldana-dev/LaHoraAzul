from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv
import os

load_dotenv()

# Primero instanciamos los objetos sin app
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    toolbar = DebugToolbarExtension(app)

    # ---------------- Configuración ----------------
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://aldana_dev:devadmin@localhost/lahoraazul_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.secret_key = os.getenv('SECRET_KEY')
        
    # ---------------- Configuración Payway ----------------
    # Public Key (usada en el frontend - token.js)
    app.config['PUBLIC_KEY'] = os.getenv('PUBLIC_KEY')
    
    # Private Key (solo para backend - NO enviar al frontend)
    app.config['PRIVATE_KEY'] = os.getenv('PRIVATE_KEY')
    
    # API Key para comunicación Flask <-> Node.js
    app.config['API_KEY'] = os.getenv('API_KEY')
    
    # URL del servidor Node.js de pagos
    app.config['NODE_API_URL'] = os.getenv('NODE_API_URL', 'http://localhost:3001')

    # ---------------- Inicializar DB y Migraciones ----------------
    db.init_app(app)
    migrate.init_app(app, db)


    # ---------------- Registrar Blueprints ----------------
    from app.routes.admin_routes import admin_bp
    from app.routes.main_routes import main_bp
    from app.routes.correo_api import correo_bp
    from app.routes.pago_api import pago_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(correo_bp)
    app.register_blueprint(pago_bp)

    return app