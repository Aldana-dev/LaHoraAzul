from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # ---------------- Configuración ----------------
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://aldana_dev:devadmin@localhost/lahoraazul_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.secret_key = 'clave_super_secreta'  # Cambiala por una segura en producción

    # ---------------- Inicializar DB ----------------
    db.init_app(app)

    # ---------------- Registrar Blueprints ----------------
    # Importar y registrar Blueprints
    from app.routes.admin_routes import admin_bp
    from app.routes.main_routes import main_bp
    from app.routes.correo_api import correo_bp


    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(correo_bp)


    # ---------------- Crear tablas (si no existen) ----------------
    with app.app_context():
        from . import models
        db.create_all()

    return app
