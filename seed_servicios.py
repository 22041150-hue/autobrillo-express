from app import app
from models import db, Servicio

servicios_iniciales = [
    Servicio(nombre="Lavado basico", descripcion="Lavado exterior con shampoo automotriz", precio_base=120.00, duracion_estimada=30),
    Servicio(nombre="Lavado + aspirado", descripcion="Lavado exterior mas aspirado de interiores", precio_base=180.00, duracion_estimada=45),
    Servicio(nombre="Encerado", descripcion="Aplicacion de cera protectora para la pintura", precio_base=250.00, duracion_estimada=60),
    Servicio(nombre="Detallado completo", descripcion="Limpieza profunda interior y exterior", precio_base=450.00, duracion_estimada=120),
    Servicio(nombre="Pulido de faros", descripcion="Restauracion de faros opacos o amarillentos", precio_base=150.00, duracion_estimada=40),
]

with app.app_context():
    db.session.add_all(servicios_iniciales)
    db.session.commit()
    print("Servicios de ejemplo insertados correctamente")