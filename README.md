# AutoBrillo Express

Aplicacion web de gestion de servicios de lavado y detallado automotriz, desarrollada como proyecto final de la materia Programacion Web / Desarrollo Web (Ingenieria en Sistemas Computacionales, Instituto Tecnologico de Durango).

**Demo en produccion:** https://autobrillo-express.onrender.com

## Descripcion

El sistema cubre el flujo completo de un negocio de lavado y detallado de autos: desde que un cliente solicita un servicio, hasta que se genera y paga la factura correspondiente, pasando por cotizacion, agendado de cita, registro de historial de reparacion y resenas.

## Tecnologias

- Backend: Flask (Python)
- Base de datos: PostgreSQL (hospedada en Aiven)
- ORM: Flask-SQLAlchemy
- Autenticacion: Flask-Login + Flask-Bcrypt (hash de contrasenas)
- Despliegue: Render (Web Service con Gunicorn)
- Frontend: HTML + Jinja2 + CSS

## Modulos funcionales

1. Solicitudes de servicio - formulario publico sin necesidad de cuenta
2. Cotizaciones - el admin cotiza cada solicitud pendiente
3. Agendado de citas - una vez aceptada la cotizacion, se asigna fecha y empleado
4. Estatus de citas - seguimiento del ciclo: agendada, confirmada, completada o cancelada
5. Historial de reparaciones - notas registradas por el empleado al completar una cita
6. Resenas - calificacion y comentario del cliente sobre el servicio
7. Facturacion - generacion de factura con folio unico desde una cotizacion aceptada, con registro de pago
8. Dashboards por rol - vistas diferenciadas para cliente, empleado y administrador

## Modelo de datos

9 tablas principales: usuarios, vehiculos, servicios, solicitudes, cotizaciones, citas, historial_reparaciones, resenhas, facturas. Las relaciones completas estan definidas en models.py.

## Roles de usuario

- cliente: Dashboard con sus propias solicitudes (requiere cuenta registrada)
- empleado: Dashboard con sus citas asignadas
- admin: Dashboard con resumen general y accesos rapidos a todas las vistas

## Instalacion local

Requisitos previos: Python 3.10+, cuenta en Aiven o cualquier PostgreSQL accesible.

Pasos:

git clone https://github.com/22041150-hue/autobrillo-express.git
cd autobrillo-express
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

## Variables de entorno

Crear un archivo .env en la raiz del proyecto con:

DB_HOST=tu_host_de_postgresql
DB_PORT=tu_puerto
DB_NAME=tu_nombre_de_base_de_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_password
SECRET_KEY=una_clave_secreta_para_flask

Este archivo nunca se sube al repositorio (ver .gitignore).

## Ejecutar en desarrollo

flask --app app run --debug

La aplicacion queda disponible en http://127.0.0.1:5000

## Despliegue en Render

Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Variables de entorno configuradas directamente en el panel de Render (las mismas que en .env local).

## Estructura de rutas principales

- /solicitud (GET): formulario de nueva solicitud
- /solicitud/crear (POST): crea la solicitud
- /solicitudes-pendientes (GET): lista de solicitudes sin cotizar
- /cotizacion/crear/<id> (POST): genera cotizacion
- /cotizacion/aceptar/<id> (POST): acepta cotizacion
- /cita/crear/<id> (POST): agenda cita desde cotizacion aceptada
- /citas (GET): lista de citas con acciones por estado
- /factura/crear/<cita_id> (POST): genera factura desde cotizacion aceptada
- /factura/pagar/<id> (POST): marca factura como pagada
- /dashboard (GET): redirige al dashboard segun el rol del usuario autenticado
- /registro, /login, /logout (GET/POST): autenticacion de usuarios

## Autor

Cesar Lozano - Ingenieria en Sistemas Computacionales, ITD
