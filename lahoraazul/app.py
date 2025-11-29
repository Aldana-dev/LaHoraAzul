import os
from app import create_app, db
from app.models import Usuario
from alembic.config import Config
from alembic import command

app = create_app()

with app.app_context():
    # ---------------- Aplicar migraciones ----------------
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✔ Migraciones aplicadas correctamente.")
    except Exception as e:
        print("⚠ Error aplicando migraciones:", e)

    # ---------------- Crear admin temporalmente ----------------
    email_admin = "admin@horaazul.com"
    password_admin = "MiContraseñaSegura123"

    admin = Usuario.query.filter_by(email=email_admin).first()
    if not admin:
        admin = Usuario(nombre="Admin", email=email_admin, es_admin=True)
        admin.set_password(password_admin)
        db.session.add(admin)
        db.session.commit()
        print("✔ Usuario administrador creado.")
    else:
        print("El usuario administrador ya existe.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
