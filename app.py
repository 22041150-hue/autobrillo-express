from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from datetime import datetime
from models import db, Usuario, Vehiculo, Servicio, Solicitud, Cotizacion
import os

load_dotenv()

app = Flask(__name__)

db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port + "/" + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    return 'AutoBrillo Express - Servidor funcionando'

@app.route('/solicitud')
def mostrar_formulario():
    servicios = Servicio.query.all()
    return render_template('solicitud.html', servicios=servicios)

@app.route('/solicitud/crear', methods=['POST'])
def crear_solicitud():
    nombre_cliente = request.form['nombre_cliente']
    telefono_cliente = request.form['telefono_cliente']
    marca = request.form['marca']
    modelo = request.form['modelo']
    anio = request.form.get('anio')
    placas = request.form.get('placas')
    servicio_id = request.form['servicio_id']
    descripcion = request.form.get('descripcion')

    nuevo_usuario = Usuario(
        nombre=nombre_cliente,
        email=nombre_cliente.replace(" ", "").lower() + telefono_cliente + "_" + str(int(datetime.now().timestamp())) + "@temporal.com",
        password_hash='sin_login',
        rol='cliente',
        telefono=telefono_cliente
    )
    db.session.add(nuevo_usuario)
    db.session.flush()

    nuevo_vehiculo = Vehiculo(
        usuario_id=nuevo_usuario.id,
        marca=marca,
        modelo=modelo,
        anio=anio if anio else None,
        placas=placas,
        color=None
    )
    db.session.add(nuevo_vehiculo)
    db.session.flush()

    nueva_solicitud = Solicitud(
        usuario_id=nuevo_usuario.id,
        vehiculo_id=nuevo_vehiculo.id,
        servicio_id=servicio_id,
        descripcion=descripcion,
        estado='pendiente'
    )
    db.session.add(nueva_solicitud)
    db.session.commit()

    return redirect(url_for('confirmacion', solicitud_id=nueva_solicitud.id))

@app.route('/confirmacion/<int:solicitud_id>')
def confirmacion(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    return render_template('confirmacion.html', solicitud=solicitud)

@app.route('/solicitudes-pendientes')
def listar_solicitudes_pendientes():
    solicitudes = Solicitud.query.filter(~Solicitud.cotizaciones.any()).all()
    return render_template('solicitudes_pendientes.html', solicitudes=solicitudes)

@app.route('/cotizacion/nueva/<int:solicitud_id>')
def mostrar_form_cotizacion(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    return render_template('form_cotizacion.html', solicitud=solicitud)

@app.route('/cotizacion/crear/<int:solicitud_id>', methods=['POST'])
def crear_cotizacion(solicitud_id):
    monto = request.form['monto']
    detalle = request.form.get('detalle')

    nueva_cotizacion = Cotizacion(
        solicitud_id=solicitud_id,
        monto=monto,
        detalle=detalle,
        estado='pendiente'
    )
    db.session.add(nueva_cotizacion)
    db.session.commit()

    return redirect(url_for('confirmacion_cotizacion', cotizacion_id=nueva_cotizacion.id))

@app.route('/cotizacion/confirmacion/<int:cotizacion_id>')
def confirmacion_cotizacion(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    return render_template('confirmacion_cotizacion.html', cotizacion=cotizacion)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)