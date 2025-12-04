import os
from app import create_app, db
from app.models import Usuario
from alembic.config import Config
from alembic import command
import logging

# Configurar logging para ver todos los errores
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = create_app()
# También en Flask
app.logger.setLevel(logging.DEBUG)

with app.app_context():
    # ---------------- Aplicar migraciones ----------------
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Migraciones aplicadas correctamente.")
    except Exception as e:
        print("Error aplicando migraciones:", e)

    # ---------------- Crear admin temporalmente ----------------
    email_admin = os.getenv("ADMIN_EMAIL")
    password_admin = os.getenv("ADMIN_PASSWORD")

    if email_admin and password_admin:
        admin = Usuario.query.filter_by(email=email_admin).first()
        if not admin:
            admin = Usuario(nombre="Admin", email=email_admin, es_admin=True)
            admin.set_password(password_admin)
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado.")
        else:
            print("El usuario administrador ya existe.")
    else:
        print("ADMIN_EMAIL o ADMIN_PASSWORD no están definidos en el entorno")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
