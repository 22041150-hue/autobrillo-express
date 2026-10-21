from flask import Flask, render_template, request, redirect, url_for, Response
from dotenv import load_dotenv
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from sqlalchemy import or_
from models import db, Usuario, Vehiculo, Servicio, Solicitud, Cotizacion, Cita, HistorialReparacion, Resenha, Factura
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import csv
import io
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

BAHIAS = ['Bahia 1', 'Bahia 2', 'Bahia 3']
ETAPAS = ['recibido', 'en lavado', 'en detallado', 'control de calidad', 'terminado', 'entregado']

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


def monto_aceptado(solicitud):
    for c in solicitud.cotizaciones:
        if c.estado == 'aceptada':
            return c.monto
    return 0


def filas_historial(q, desde, hasta):
    consulta = (HistorialReparacion.query
                .join(Cita, HistorialReparacion.cita_id == Cita.id)
                .join(Solicitud, Cita.solicitud_id == Solicitud.id)
                .join(Usuario, Solicitud.usuario_id == Usuario.id)
                .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id))
    if q:
        patron = '%' + q + '%'
        consulta = consulta.filter(or_(
            Usuario.nombre.ilike(patron),
            Vehiculo.placas.ilike(patron),
            Vehiculo.modelo.ilike(patron)
        ))
    if desde:
        consulta = consulta.filter(HistorialReparacion.fecha_finalizacion >= datetime.strptime(desde, '%Y-%m-%d'))
    if hasta:
        consulta = consulta.filter(HistorialReparacion.fecha_finalizacion < datetime.strptime(hasta, '%Y-%m-%d') + timedelta(days=1))
    registros = consulta.order_by(HistorialReparacion.fecha_finalizacion.desc()).all()

    filas = []
    for h in registros:
        sol = h.cita.solicitud
        filas.append({
            'folio': 'H-' + str(h.id),
            'cliente': sol.usuario.nombre,
            'vehiculo': sol.vehiculo.marca + ' ' + sol.vehiculo.modelo + ' (' + (sol.vehiculo.placas or 'sin placas') + ')',
            'servicio': sol.servicio.nombre,
            'fecha': h.fecha_finalizacion.strftime('%d/%m/%Y') if h.fecha_finalizacion else '',
            'total': monto_aceptado(sol),
            'notas': h.notas
        })
    return filas


@app.route('/')
def index():
    resenhas = Resenha.query.filter_by(visible=True).order_by(Resenha.fecha.desc()).limit(5).all()
    return render_template('index.html', resenhas=resenhas)

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
    a_domicilio = 'a_domicilio' in request.form
    urgente = 'urgente' in request.form

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
        estado='pendiente',
        a_domicilio=a_domicilio,
        urgente=urgente
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
    precio = Decimal(request.form['monto'])
    descuento = Decimal(request.form.get('descuento') or 0)
    total = (precio * (Decimal(100) - descuento) / Decimal(100)).quantize(Decimal('0.01'))
    detalle = request.form.get('detalle')
    vigencia = request.form.get('vigencia')

    nueva_cotizacion = Cotizacion(
        solicitud_id=solicitud_id,
        monto=total,
        detalle=detalle,
        estado='pendiente',
        descuento=descuento,
        vigencia=datetime.strptime(vigencia, '%Y-%m-%d').date() if vigencia else None
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
    return render_template('form_cita.html', cotizacion=cotizacion, empleados=empleados, bahias=BAHIAS)

@app.route('/cita/crear/<int:cotizacion_id>', methods=['POST'])
def crear_cita(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    fecha_hora = datetime.strptime(request.form['fecha_hora'], '%Y-%m-%dT%H:%M')
    empleado_id = request.form.get('empleado_id')
    bahia = request.form.get('bahia')
    duracion = request.form.get('duracion_min')
    notas = request.form.get('notas')
    recordatorio_correo = 'recordatorio_correo' in request.form
    recordatorio_sms = 'recordatorio_sms' in request.form

    if bahia:
        ocupada = Cita.query.filter(
            Cita.bahia == bahia,
            Cita.fecha_hora == fecha_hora,
            Cita.estado != 'cancelada'
        ).first()
        if ocupada:
            return 'Esa bahia ya esta ocupada a esa hora. <a href="javascript:history.back()">Volver</a>'

    duracion_min = int(duracion) if duracion else None

    nueva_cita = Cita(
        solicitud_id=cotizacion.solicitud_id,
        empleado_id=empleado_id if empleado_id else None,
        fecha_hora=fecha_hora,
        estado='agendada',
        bahia=bahia if bahia else None,
        duracion_min=duracion_min,
        recordatorio_correo=recordatorio_correo,
        recordatorio_sms=recordatorio_sms,
        notas=notas,
        etapa='recibido',
        fecha_estimada_entrega=fecha_hora + timedelta(minutes=duracion_min) if duracion_min else None
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

@app.route('/cita/estatus/<int:cita_id>', methods=['GET', 'POST'])
@login_required
@rol_requerido('admin', 'empleado')
def estatus_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    if request.method == 'POST':
        cita.etapa = request.form['etapa']
        entrega = request.form.get('fecha_estimada_entrega')
        cita.fecha_estimada_entrega = datetime.strptime(entrega, '%Y-%m-%dT%H:%M') if entrega else None
        cita.estatus_pago = request.form['estatus_pago']
        cita.monto_pagado = request.form.get('monto_pagado') or 0
        if cita.etapa == 'entregado' and not cita.fecha_real_entrega:
            cita.fecha_real_entrega = datetime.now()
        db.session.commit()
        return redirect(url_for('listar_citas'))
    return render_template('estatus_cita.html', cita=cita, etapas=ETAPAS)

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

@app.route('/historial')
@login_required
@rol_requerido('admin', 'empleado')
def listar_historial():
    q = request.args.get('q', '')
    desde = request.args.get('desde', '')
    hasta = request.args.get('hasta', '')
    filas = filas_historial(q, desde, hasta)
    return render_template('historial.html', filas=filas, q=q, desde=desde, hasta=hasta)

@app.route('/historial/exportar')
@login_required
@rol_requerido('admin', 'empleado')
def exportar_historial():
    q = request.args.get('q', '')
    desde = request.args.get('desde', '')
    hasta = request.args.get('hasta', '')
    filas = filas_historial(q, desde, hasta)

    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(['Folio', 'Cliente', 'Vehiculo', 'Servicio', 'Fecha', 'Total'])
    for f in filas:
        escritor.writerow([f['folio'], f['cliente'], f['vehiculo'], f['servicio'], f['fecha'], f['total']])

    return Response(
        '\ufeff' + salida.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=historial.csv'}
    )

@app.route('/factura/crear/<int:cita_id>', methods=['POST'])
def crear_factura(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    cotizacion = Cotizacion.query.filter_by(
        solicitud_id=cita.solicitud_id, estado='aceptada'
    ).first_or_404()

    if cotizacion.factura:
        return redirect(url_for('confirmacion_factura', factura_id=cotizacion.factura.id))

    folio = 'AB-' + datetime.now().strftime('%Y%m%d%H%M%S')

    subtotal = cotizacion.monto
    iva = (subtotal * Decimal('0.16')).quantize(Decimal('0.01'))

    nueva_factura = Factura(
        cotizacion_id=cotizacion.id,
        folio=folio,
        subtotal=subtotal,
        iva=iva,
        total=subtotal + iva,
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

    factura.estado = 'pagada'
    factura.metodo_pago = request.form.get('metodo_pago')
    factura.rfc = request.form.get('rfc') or None
    factura.uso_cfdi = request.form.get('uso_cfdi') or None

    for cita in factura.cotizacion.solicitud.citas:
        cita.estatus_pago = 'pagado'
        cita.monto_pagado = factura.total

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
        comentario=comentario,
        publicar_nombre='publicar_nombre' in request.form,
        visible=True
    )
    db.session.add(nueva_resenha)
    db.session.commit()

    return redirect(url_for('listar_citas'))

@app.route('/resenhas')
@login_required
@rol_requerido('admin')
def moderar_resenhas():
    resenhas = Resenha.query.order_by(Resenha.fecha.desc()).all()
    return render_template('resenhas_admin.html', resenhas=resenhas)

@app.route('/resenha/visibilidad/<int:resenha_id>', methods=['POST'])
@login_required
@rol_requerido('admin')
def cambiar_visibilidad_resenha(resenha_id):
    resenha = Resenha.query.get_or_404(resenha_id)
    resenha.visible = not resenha.visible
    db.session.commit()
    return redirect(url_for('moderar_resenhas'))

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