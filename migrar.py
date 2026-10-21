from sqlalchemy import text
from app import app, db

COMANDOS = [
    "ALTER TABLE solicitudes ADD COLUMN IF NOT EXISTS a_domicilio BOOLEAN DEFAULT FALSE",
    "ALTER TABLE solicitudes ADD COLUMN IF NOT EXISTS urgente BOOLEAN DEFAULT FALSE",
    "ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS descuento NUMERIC(5,2) DEFAULT 0",
    "ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS vigencia DATE",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS bahia VARCHAR(30)",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS duracion_min INTEGER",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS recordatorio_correo BOOLEAN DEFAULT FALSE",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS recordatorio_sms BOOLEAN DEFAULT FALSE",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS notas TEXT",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS etapa VARCHAR(30) DEFAULT 'recibido'",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS fecha_estimada_entrega TIMESTAMP",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS fecha_real_entrega TIMESTAMP",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS estatus_pago VARCHAR(20) DEFAULT 'pendiente'",
    "ALTER TABLE citas ADD COLUMN IF NOT EXISTS monto_pagado NUMERIC(10,2) DEFAULT 0",
    "ALTER TABLE resenhas ADD COLUMN IF NOT EXISTS publicar_nombre BOOLEAN DEFAULT FALSE",
    "ALTER TABLE resenhas ADD COLUMN IF NOT EXISTS visible BOOLEAN DEFAULT TRUE",
    "ALTER TABLE facturas ADD COLUMN IF NOT EXISTS rfc VARCHAR(20)",
    "ALTER TABLE facturas ADD COLUMN IF NOT EXISTS uso_cfdi VARCHAR(50)",
    "ALTER TABLE facturas ADD COLUMN IF NOT EXISTS subtotal NUMERIC(10,2)",
    "ALTER TABLE facturas ADD COLUMN IF NOT EXISTS iva NUMERIC(10,2)",
]

with app.app_context():
    for c in COMANDOS:
        db.session.execute(text(c))
    db.session.commit()
    print("Listo: columnas agregadas")
    