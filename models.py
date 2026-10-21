from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    telefono = db.Column(db.String(20))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    vehiculos = db.relationship('Vehiculo', backref='propietario', lazy=True)

class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    anio = db.Column(db.Integer)
    placas = db.Column(db.String(20))
    color = db.Column(db.String(30))

class Servicio(db.Model):
    __tablename__ = 'servicios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)
    duracion_estimada = db.Column(db.Integer)

class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    vehiculo_id = db.Column(db.Integer, db.ForeignKey('vehiculos.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(30), default='pendiente')
    a_domicilio = db.Column(db.Boolean, default=False)
    urgente = db.Column(db.Boolean, default=False)

    usuario = db.relationship('Usuario', backref='solicitudes', lazy=True)
    vehiculo = db.relationship('Vehiculo', backref='solicitudes', lazy=True)
    servicio = db.relationship('Servicio', backref='solicitudes', lazy=True)

class Cotizacion(db.Model):
    __tablename__ = 'cotizaciones'
    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes.id'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    detalle = db.Column(db.Text)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='pendiente')
    descuento = db.Column(db.Numeric(5, 2), default=0)
    vigencia = db.Column(db.Date)

    solicitud = db.relationship('Solicitud', backref='cotizaciones', lazy=True)

class Cita(db.Model):
    __tablename__ = 'citas'
    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes.id'), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_hora = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(30), default='agendada')
    bahia = db.Column(db.String(30))
    duracion_min = db.Column(db.Integer)
    recordatorio_correo = db.Column(db.Boolean, default=False)
    recordatorio_sms = db.Column(db.Boolean, default=False)
    notas = db.Column(db.Text)
    etapa = db.Column(db.String(30), default='recibido')
    fecha_estimada_entrega = db.Column(db.DateTime)
    fecha_real_entrega = db.Column(db.DateTime)
    estatus_pago = db.Column(db.String(20), default='pendiente')
    monto_pagado = db.Column(db.Numeric(10, 2), default=0)

    solicitud = db.relationship('Solicitud', backref='citas', lazy=True)
    empleado = db.relationship('Usuario', backref='citas_asignadas', lazy=True)

class HistorialReparacion(db.Model):
    __tablename__ = 'historial_reparaciones'
    id = db.Column(db.Integer, primary_key=True)
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=False)
    notas = db.Column(db.Text)
    fecha_finalizacion = db.Column(db.DateTime)
    fotos_evidencia = db.Column(db.String(255))

    cita = db.relationship('Cita', backref='historial', lazy=True)

class Resenha(db.Model):
    __tablename__ = 'resenhas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=False)
    calificacion = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    publicar_nombre = db.Column(db.Boolean, default=False)
    visible = db.Column(db.Boolean, default=True)

    usuario = db.relationship('Usuario', backref='resenhas', lazy=True)
    cita = db.relationship('Cita', backref='resenha', lazy=True)

class Factura(db.Model):
    __tablename__ = 'facturas'
    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey('cotizaciones.id'), nullable=False)
    folio = db.Column(db.String(50), unique=True)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(30))
    estado = db.Column(db.String(20), default='pendiente')
    rfc = db.Column(db.String(20))
    uso_cfdi = db.Column(db.String(50))
    subtotal = db.Column(db.Numeric(10, 2))
    iva = db.Column(db.Numeric(10, 2))

    cotizacion = db.relationship('Cotizacion', backref=db.backref('factura', uselist=False), lazy=True)