from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from datetime import datetime
from functools import wraps
from models import db, Usuario, Vehiculo, Servicio, Solicitud, Cotizacion, Cita, HistorialReparacion, Resenha, Factura
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
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
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def rol_requerido(*roles_permitidos):
    def decorador(f):
        @wraps(f)
        def funcion_envuelta(*args, **kwargs):
            if current_user.rol not in roles_permitidos:
                return 'No tienes permiso para ver esta pagina.', 403
            return f(*args, **kwargs)
        return funcion_envuelta
    return decorador

@app.route('/')
def index():
    return 'AutoBrillo Express - Servidor funcionando'

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.rol == 'admin':
        return redirect(url_for('dashboard_admin'))
    elif current_user.rol == 'empleado':
        return redirect(url_for('dashboard_empleado'))
    else:
        return redirect(url_for('dashboard_cliente'))

@app.route('/dashboard/admin')
@login_required
@rol_requerido('admin')
def dashboard_admin():
    total_solicitudes_pendientes = Solicitud.query.filter(~Solicitud.cotizaciones.any()).count()
    total_cotizaciones_pendientes = Cotizacion.query.filter_by(estado='pendiente').count()
    total_citas_agendadas = Cita.query.filter(Cita.estado.in_(['agendada', 'confirmada'])).count()
    total_facturas_pendientes = Factura.query.filter_by(estado='pendiente').count()
    return render_template(
        'dashboard_admin.html',
        total_solicitudes_pendientes=total_solicitudes_pendientes,
        total_cotizaciones_pendientes=total_cotizaciones_pendientes,
        total_citas_agendadas=total_citas_agendadas,
        total_facturas_pendientes=total_facturas_pendientes
    )

@app.route('/dashboard/empleado')
@login_required
@rol_requerido('empleado')
def dashboard_empleado():
    citas = Cita.query.filter_by(empleado_id=current_user.id).order_by(Cita.fecha_hora).all()
    return render_template('dashboard_empleado.html', citas=citas)

@app.route('/dashboard/cliente')
@login_required
@rol_requerido('cliente')
def dashboard_cliente():
    solicitudes = Solicitud.query.filter_by(usuario_id=current_user.id).order_by(Solicitud.fecha_solicitud.desc()).all()
    return render_template('dashboard_cliente.html', solicitudes=solicitudes)

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

@app.route('/cotizacion/aceptar/<int:cotizacion_id>', methods=['POST'])
def aceptar_cotizacion(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    cotizacion.estado = 'aceptada'
    db.session.commit()
    return redirect(url_for('confirmacion_cotizacion', cotizacion_id=cotizacion.id))

@app.route('/cotizaciones-aceptadas')
def listar_cotizaciones_aceptadas():
    cotizaciones = Cotizacion.query.filter_by(estado='aceptada').join(Solicitud).filter(~Solicitud.citas.any()).all()
    return render_template('cotizaciones_aceptadas.html', cotizaciones=cotizaciones)

@app.route('/cita/nueva/<int:cotizacion_id>')
def mostrar_form_cita(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    empleados = Usuario.query.filter_by(rol='empleado').all()
    return render_template('form_cita.html', cotizacion=cotizacion, empleados=empleados)

@app.route('/cita/crear/<int:cotizacion_id>', methods=['POST'])
def crear_cita(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    fecha_hora = request.form['fecha_hora']
    empleado_id = request.form.get('empleado_id')

    nueva_cita = Cita(
        solicitud_id=cotizacion.solicitud_id,
        empleado_id=empleado_id if empleado_id else None,
        fecha_hora=fecha_hora,
        estado='agendada'
    )
    db.session.add(nueva_cita)
    db.session.commit()

    return redirect(url_for('confirmacion_cita', cita_id=nueva_cita.id))

@app.route('/cita/confirmacion/<int:cita_id>')
def confirmacion_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    return render_template('confirmacion_cita.html', cita=cita)

@app.route('/citas')
def listar_citas():
    citas = Cita.query.all()
    return render_template('citas.html', citas=citas)

@app.route('/cita/estado/<int:cita_id>/<nuevo_estado>', methods=['POST'])
def actualizar_estado_cita(cita_id, nuevo_estado):
    cita = Cita.query.get_or_404(cita_id)
    cita.estado = nuevo_estado
    db.session.commit()
    return redirect(url_for('listar_citas'))

@app.route('/historial/nuevo/<int:cita_id>')
def mostrar_form_historial(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    return render_template('form_historial.html', cita=cita)

@app.route('/historial/crear/<int:cita_id>', methods=['POST'])
def crear_historial(cita_id):
    notas = request.form['notas']

    nuevo_historial = HistorialReparacion(
        cita_id=cita_id,
        notas=notas,
        fecha_finalizacion=datetime.now()
    )
    db.session.add(nuevo_historial)
    db.session.commit()

    return redirect(url_for('listar_citas'))

@app.route('/factura/crear/<int:cita_id>', methods=['POST'])
def crear_factura(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    cotizacion = Cotizacion.query.filter_by(
        solicitud_id=cita.solicitud_id, estado='aceptada'
    ).first_or_404()

    if cotizacion.factura:
        return redirect(url_for('confirmacion_factura', factura_id=cotizacion.factura.id))

    folio = 'AB-' + datetime.now().strftime('%Y%m%d%H%M%S')

    nueva_factura = Factura(
        cotizacion_id=cotizacion.id,
        folio=folio,
        total=cotizacion.monto,
        estado='pendiente'
    )
    db.session.add(nueva_factura)
    db.session.commit()

    return redirect(url_for('confirmacion_factura', factura_id=nueva_factura.id))

@app.route('/factura/confirmacion/<int:factura_id>')
def confirmacion_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    return render_template('confirmacion_factura.html', factura=factura)

@app.route('/factura/pagar/<int:factura_id>', methods=['POST'])
def pagar_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    metodo_pago = request.form.get('metodo_pago')

    factura.estado = 'pagada'
    factura.metodo_pago = metodo_pago
    db.session.commit()

    return redirect(url_for('confirmacion_factura', factura_id=factura.id))

@app.route('/resenha/nueva/<int:cita_id>')
def mostrar_form_resenha(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    return render_template('form_resenha.html', cita=cita)

@app.route('/resenha/crear/<int:cita_id>', methods=['POST'])
def crear_resenha(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    calificacion = request.form['calificacion']
    comentario = request.form.get('comentario')

    nueva_resenha = Resenha(
        usuario_id=cita.solicitud.usuario_id,
        cita_id=cita_id,
        calificacion=calificacion,
        comentario=comentario
    )
    db.session.add(nueva_resenha)
    db.session.commit()

    return redirect(url_for('listar_citas'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        telefono = request.form.get('telefono')

        existente = Usuario.query.filter_by(email=email).first()
        if existente:
            return 'Ese correo ya esta registrado. <a href="/registro">Volver</a>'

        password_encriptado = bcrypt.generate_password_hash(password).decode('utf-8')

        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            password_hash=password_encriptado,
            rol='cliente',
            telefono=telefono
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        login_user(nuevo_usuario)
        return redirect(url_for('dashboard'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and bcrypt.check_password_hash(usuario.password_hash, password):
            login_user(usuario)
            return redirect(url_for('dashboard'))
        else:
            return 'Correo o contrasena incorrectos. <a href="/login">Volver</a>'

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
