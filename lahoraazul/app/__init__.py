from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    toolbar = DebugToolbarExtension(app)

    # ---------------- Configuración ----------------
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://aldana_dev:devadmin@localhost/lahoraazul_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.secret_key = os.getenv('SECRET_KEY')
        
    # ---------------- Configuración Payway ----------------
    app.config['PUBLIC_KEY'] = os.getenv('PUBLIC_KEY')
    app.config['PRIVATE_KEY'] = os.getenv('PRIVATE_KEY')
    app.config['API_KEY'] = os.getenv('API_KEY')
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