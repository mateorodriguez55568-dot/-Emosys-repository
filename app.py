from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors
from datetime import datetime
import smtplib
from email.message import EmailMessage

# ============================================================
# IMPORTACIÓN NUEVA: AGREGAR ESTAS DOS LÍNEAS
# ============================================================
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "emosys_secret_key_2026"
# ============================================
# CONEXIÓN A SUPABASE (POSTGRESQL)
# ============================================

def get_db():
    try:
        # Usamos directamente la URI que te dio Supabase (recuerda cambiar la contraseña)
        conexion_url = "postgresql://postgres.ldcaztjxifrhbdabzaeh:Emosys_Sistemadetectordeemociones@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        
        conn = psycopg2.connect(conexion_url)
        return conn

    except Exception as e:
        print(f"[ERROR BD SUPABASE] {e}")
        return None


@app.route("/api/crear_usuario", methods=["POST"])
def crear_usuario():

    datos = request.get_json()

    cedula = datos["cedula"]
    nombres_apellidos = datos["nombres_apellidos"]
    edad = datos["edad"]
    email = datos["email"]
    tipo_usuario = datos["tipo_usuario"]
    password = datos["password"]
    try:
        conexion = get_db()
        cursor = conexion.cursor()
        password_hash = generate_password_hash(password)
        cursor.execute("""
    INSERT INTO usuarios 
    (cedula, nombres_apellidos, edad, email, tipo_usuario, password)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
""", (
    cedula,
    nombres_apellidos,
    edad,
    email,
    tipo_usuario,
    password_hash
))

        usuario_id = cursor.fetchone()[0]

        conexion.commit()

        cursor.close()
        conexion.close()

        return jsonify({
            "exito": True,
            "usuario": {
                "id": usuario_id,
                "cedula": cedula,
                "nombre": nombres_apellidos,
                "email": email
            }
        })

    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "exito": False,
            "error": str(e)
        })
# ============================================
# SERIALIZADOR
# ============================================

def ser(rows):
    datos = []

    for row in rows:
        d = dict(row)

        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()

        datos.append(d)

    return datos

# ============================================
# ENVIO DE CORREOS
# ============================================

def enviar_correo(destino, nombre, reporte):

    try:

        correo_emisor = "emosys.sistema@gmail.com"

        contraseña = "clooebbiuezopcwd"


        mensaje = EmailMessage()

        mensaje["Subject"] = "Resultado de diagnóstico EMOSYS"

        mensaje["From"] = correo_emisor

        mensaje["To"] = destino


        mensaje.set_content(f"""
Hola {nombre}.

Este es el resultado de tu diagnóstico realizado en EMOSYS.

---------------------------------

{reporte}

---------------------------------

Gracias por utilizar Emotion System.

EMOSYS 2026
""")


        servidor = smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        )


        servidor.login(
            correo_emisor,
            contraseña
        )


        servidor.send_message(mensaje)

        servidor.close()


        return True


    except Exception as e:

        print("ERROR SMTP:", e)

        return False
# ============================================
# PÁGINAS
# ============================================
@app.route("/") 
def inicio(): 
    return render_template("Detector.html")

@app.route("/registro")
def registro():
    return render_template("Registro.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")

# ============================================================
# BLOQUE A REEMPLAZAR: API REGISTRO DE USUARIO
# ============================================================

@app.route("/api/registrar", methods=["POST"])
def registrar_usuario():

    data = request.get_json()

    cedula = data.get("cedula", "").strip()
    nombres = data.get("nombres", "").strip()
    edad = data.get("edad")
    email = data.get("email", "").strip()
    tipo_usuario = data.get("tipo_usuario", "").strip()
    password = data.get("password", "").strip()

    if not cedula or not nombres or not edad or not email or not tipo_usuario or not password:
        return jsonify({
            "error": "Todos los campos son obligatorios."
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "La contraseña debe tener al menos 8 caracteres.",
            "campo": "password"
        }), 400

    try:
        edad = int(edad)

    except:
        return jsonify({
            "error": "La edad debe ser numérica."
        }), 400

    if edad < 1 or edad > 120:
        return jsonify({
            "error": "La edad debe estar entre 1 y 120."
        }), 400

    password_hash = generate_password_hash(password)

    conn = get_db()

    if conn is None:
        return jsonify({
            "error": "No fue posible conectar con PostgreSQL."
        }), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:

        cur.execute("SELECT id FROM usuarios WHERE cedula = %s", (cedula,))
        if cur.fetchone():
            return jsonify({
                "error": "Esta cédula ya está registrada.",
                "campo": "cedula"
            }), 400

        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({
                "error": "Este correo ya está registrado.",
                "campo": "email"
            }), 400

        cur.execute("""
            INSERT INTO usuarios
            (
                cedula,
                nombres_apellidos,
                edad,
                email,
                tipo_usuario,
                password
            )

            VALUES
            (%s,%s,%s,%s,%s,%s)

            RETURNING *
        """,
        (
            cedula,
            nombres,
            edad,
            email,
            tipo_usuario,
            password_hash
        ))

        usuario = cur.fetchone()

        conn.commit()

        return jsonify({

            "exito": True,

            "mensaje": "Usuario registrado correctamente.",

            "usuario": {
                "id": usuario["id"],
                "cedula": usuario["cedula"],
                "nombre": usuario["nombres_apellidos"],
                "edad": usuario["edad"],
                "email": usuario["email"],
                "tipo_usuario": usuario["tipo_usuario"]

            }

        }), 201

    except errors.UniqueViolation:

        conn.rollback()

        return jsonify({
            "error": "La cédula o el correo ya existen."
        }), 400

    except Exception as e:

        conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()

# ============================================================
# BLOQUE NUEVO: API LOGIN
# ============================================================
@app.route("/api/login", methods=["POST"])
def api_login():

    data = request.get_json()

    usuario_input = data.get("usuario", "").strip()
    password = data.get("password", "").strip()

    if not usuario_input or not password:
        return jsonify({
            "error": "Debes completar todos los campos."
        }), 400


    conn = get_db()

    if conn is None:
        return jsonify({
            "error": "No fue posible conectar con PostgreSQL."
        }), 500


    cur = conn.cursor(cursor_factory=RealDictCursor)


    try:

        cur.execute("""
            SELECT *
            FROM usuarios
            WHERE email = %s OR cedula = %s
        """, (usuario_input, usuario_input))


        usuario = cur.fetchone()


        if usuario is None:
            return jsonify({
                "error": "No existe una cuenta con ese correo o cédula."
            }), 401


        if not usuario["password"] or usuario["password"] == "":
            return jsonify({
                "error": "Esta cuenta no tiene contraseña configurada."
            }), 401


        if not check_password_hash(usuario["password"], password):
            return jsonify({
                "error": "Contraseña incorrecta."
            }), 401



        # ===========================
        # REGISTRAR EL LOGIN
        # ===========================
        # ===========================================
        # CERRAR SESIONES ANTERIORES ABIERTAS DE ESTE USUARIO
        # ===========================================
        cur.execute("""
            UPDATE sesiones 
            SET fecha_fin = CURRENT_TIMESTAMP, estado = 'FINALIZADA'
            WHERE usuario_id = %s AND estado = 'ACTIVA'
        """, (usuario["id"],))
        
        cur.execute("""
            INSERT INTO sesiones (
                usuario_id,
                estado
            )
            VALUES (%s,'ACTIVA')
            RETURNING id;
        """, (usuario["id"],))


        sesion = cur.fetchone()


        conn.commit()



        # ===========================
        # RESPUESTA EXITOSA
        # ===========================

        return jsonify({

            "exito": True,

            "mensaje": "Inicio de sesión exitoso.",

            "usuario": {
                "id": usuario["id"],
                "cedula": usuario["cedula"],
                "nombre": usuario["nombres_apellidos"],
                "email": usuario["email"],
                "tipo_usuario": usuario["tipo_usuario"]
            },

            "idSesion": sesion["id"]

        }), 200



    except Exception as e:

        conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500



    finally:

        cur.close()
        conn.close()
# ============================================================
# FIN DEL BLOQUE NUEVO
# ============================================================
@app.route("/api/verificar_admin/<int:id>")
def verificar_admin(id):

    conn=get_db()

    cur=conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT tipo_usuario
        FROM usuarios
        WHERE id=%s
    """,(id,))

    usuario=cur.fetchone()

    cur.close()
    conn.close()


    if usuario and usuario["tipo_usuario"]=="admin":
        return jsonify({
            "admin":True
        })

    return jsonify({
        "admin":False
    })
# ============================================
# API DIAGNOSTICOS
# ============================================
@app.route("/api/diagnosticos")
def get_diagnosticos():


    conn=get_db()

    cur=conn.cursor(cursor_factory=RealDictCursor)


    try:

        cur.execute("""
        
        SELECT

        d.id,
        u.nombres_apellidos,
        u.email,

        d.temperatura,
        d.pulso,
        d.emocion,
        d.fecha


        FROM diagnosticos d


        INNER JOIN usuarios u

        ON d.usuario_id=u.id


        ORDER BY d.fecha DESC


        """)


        datos=cur.fetchall()


        return jsonify(ser(datos))


    finally:

        cur.close()
        conn.close()
# ============================================
# API USUARIOS
# ============================================

@app.route("/api/usuarios", methods=["GET"])
def get_usuarios():

    conn = get_db()

    if conn is None:
        return jsonify({"error": "Sin conexión a la base de datos"}), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:

        cur.execute("""
            SELECT *
            FROM usuarios
            ORDER BY fecha_registro DESC
        """)

        usuarios = cur.fetchall()

        return jsonify(ser(usuarios))

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()
        
@app.route("/api/sesiones", methods=["GET"])
def get_sesiones():

    conn = get_db()

    if conn is None:
        return jsonify({"error": "Sin conexión a la base de datos"}), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:

        cur.execute("""

            SELECT

            s.id,
            u.nombres_apellidos,
            s.fecha_inicio,
            s.fecha_fin,
            s.estado

            FROM sesiones s

            JOIN usuarios u
            ON s.usuario_id = u.id

            ORDER BY s.fecha_inicio DESC

        """)

        sesiones = cur.fetchall()

        return jsonify(ser(sesiones))

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        cur.close()
        conn.close()
# ============================================
# API ELIMINAR USUARIO
# ============================================

@app.route("/api/eliminar_usuario/<int:id>", methods=["DELETE"])
def eliminar_usuario(id):

    conn = get_db()

    if conn is None:
        return jsonify({
            "error": "No se pudo conectar a la base de datos."
        }), 500

    cur = conn.cursor()

    try:

        # ============================================
        # 1. VERIFICAR QUE EL USUARIO EXISTA
        # ============================================

        cur.execute("""
            SELECT id
            FROM usuarios
            WHERE id = %s
        """, (id,))

        usuario = cur.fetchone()

        if usuario is None:
            return jsonify({
                "error": "El usuario no existe."
            }), 404


        # ============================================
        # 2. ELIMINAR DIAGNÓSTICOS DEL USUARIO
        # ============================================

        cur.execute("""
            DELETE FROM diagnosticos
            WHERE usuario_id = %s
        """, (id,))


        # ============================================
        # 3. ELIMINAR SESIONES DEL USUARIO
        # ============================================

        cur.execute("""
            DELETE FROM sesiones
            WHERE usuario_id = %s
        """, (id,))


        # ============================================
        # 4. ELIMINAR USUARIO
        # ============================================

        cur.execute("""
            DELETE FROM usuarios
            WHERE id = %s
        """, (id,))


        # ============================================
        # 5. GUARDAR CAMBIOS
        # ============================================

        conn.commit()


        return jsonify({
            "exito": True,
            "mensaje": "Usuario y todos sus registros asociados fueron eliminados correctamente."
        }), 200


    except Exception as e:

        conn.rollback()

        print("ERROR AL ELIMINAR USUARIO:", e)

        return jsonify({
            "exito": False,
            "error": str(e)
        }), 500


    finally:

        cur.close()
        conn.close()

# ============================================
# API COMENTARIOS
# ============================================

@app.route("/api/comentar", methods=["POST"])
def crear_comentario():

    data = request.get_json()

    cedula = data.get("cedula", "").strip()
    nombre = data.get("nombre", "").strip()
    comentario = data.get("comentario", "").strip()

    if nombre == "":
        nombre = "Anónimo"

    if comentario == "":
        return jsonify({
            "error": "Debe escribir un comentario."
        }), 400

    conn = get_db()

    if conn is None:
        return jsonify({
            "error": "Sin conexión."
        }), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:

        cur.execute("""
            INSERT INTO comentarios
            (
                cedula_usuario,
                nombre_usuario,
                comentario
            )

            VALUES
            (%s,%s,%s)

            RETURNING *
        """,
        (
            cedula,
            nombre,
            comentario
        ))

        comentario_db = cur.fetchone()

        conn.commit()

        return jsonify({

            "exito": True,
            "mensaje": "Comentario guardado.",

            "comentario": comentario_db

        }), 201

    except Exception as e:

        conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()


@app.route("/api/comentarios", methods=["GET"])
def get_comentarios():

    conn = get_db()

    if conn is None:
        return jsonify({
            "error": "Sin conexión."
        }), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:

        cur.execute("""
            SELECT *
            FROM comentarios
            ORDER BY fecha_comentario DESC
        """)

        comentarios = cur.fetchall()

        return jsonify(ser(comentarios))

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()
# ============================================
# API CERRAR SESION 
# ============================================
@app.route("/api/cerrar_sesion", methods=["POST"])
def cerrar_sesion():

    data = request.get_json()

    id_sesion = data.get("idSesion")

    conn = get_db()

    cur = conn.cursor()

    try:

        cur.execute("""

        UPDATE sesiones

        SET

        fecha_fin = CURRENT_TIMESTAMP,
        estado='FINALIZADA'

        WHERE id=%s

        """,(id_sesion,))


        conn.commit()

        return jsonify({

            "exito":True

        })


    except Exception as e:

        conn.rollback()

        return jsonify({

            "error":str(e)

        }),500


    finally:

        cur.close()
        conn.close()

# ============================================
# LIMPIAR HISTORIAL
# ============================================

@app.route("/api/limpiar", methods=["DELETE"])
def limpiar_todo():

    conn = get_db()

    if conn is None:
        return jsonify({
            "error": "Sin conexión."
        }), 500

    cur = conn.cursor()

    try:

        cur.execute("DELETE FROM comentarios;")
        cur.execute("DELETE FROM usuarios;")

        cur.execute("ALTER SEQUENCE comentarios_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE usuarios_id_seq RESTART WITH 1;")

        conn.commit()

        return jsonify({

            "exito": True,
            "mensaje": "Historial eliminado correctamente."

        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()
# ============================================
# PÁGINAS ADICIONALES
# ============================================

@app.route("/")
def detector():
    return render_template("Detector.html")


@app.route("/Monitor")
def monitor():
    return render_template("Monitor.html")


# ============================================
# FINALIZAR MONITOREO
# ============================================
@app.route("/api/finalizar_monitoreo", methods=["POST"])
def finalizar_monitoreo():

    data = request.get_json()

    usuario_id = data.get("usuario_id")
    temperatura = data.get("temperatura")
    pulso = data.get("pulso")
    emocion = data.get("emocion")

    # =====================================
    # VALIDACIONES
    # =====================================

    if not usuario_id:
        return jsonify({
            "error": "No existe usuario asociado al diagnóstico."
        }), 400

    if temperatura is None or pulso is None or emocion is None:
        return jsonify({
            "error": "Faltan datos del sensor."
        }), 400

    conn = get_db()

    if conn is None:
        return jsonify({
            "error": "No hay conexión con la base de datos."
        }), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:

        # ============================
        # GUARDAR DIAGNÓSTICO
        # ============================

        cur.execute("""
            INSERT INTO diagnosticos
            (
                usuario_id,
                temperatura,
                pulso,
                emocion
            )
            VALUES
            (%s, %s, %s, %s)
            RETURNING *
        """, (
            usuario_id,
            temperatura,
            pulso,
            emocion
        ))

        diagnostico = cur.fetchone()

        # ============================
        # BUSCAR USUARIO
        # ============================

        cur.execute("""
            SELECT *
            FROM usuarios
            WHERE id = %s
        """, (usuario_id,))

        usuario = cur.fetchone()

        if usuario is None:
            return jsonify({
                "error": "Usuario no encontrado."
            }), 404

        conn.commit()

        # ============================
        # CREAR REPORTE
        # ============================

        reporte = f"""
Temperatura:
{temperatura} °C

Pulso:
{pulso} BPM

Emoción:
{emocion}

Fecha:
{diagnostico["fecha"]}
"""

        # ============================
        # ENVIAR CORREO
        # ============================

        print("Enviando correo a:", usuario["email"])

        correo_enviado = enviar_correo(
            usuario["email"],
            usuario["nombres_apellidos"],
            reporte
        )

        if not correo_enviado:

            return jsonify({
                "error": "No se pudo enviar el correo."
            }), 500

        print("Correo enviado correctamente")

        return jsonify({

            "exito": True,
            "mensaje": "Diagnóstico guardado y enviado correctamente.",
            "diagnostico": diagnostico

        })

    except Exception as e:

        conn.rollback()

        print("ERROR EN FINALIZAR_MONITOREO:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()
        # ============================================
# ENVIAR REPORTE DESDE ADMIN
# ============================================

@app.route("/api/enviar_reporte/<int:id>", methods=["POST"])
def enviar_reporte(id):

    conn = get_db()

    if conn is None:
        return jsonify({
            "error":"No hay conexión con la base de datos"
        }),500


    cur = conn.cursor(cursor_factory=RealDictCursor)


    try:

        # Buscar diagnóstico
        cur.execute("""
            SELECT 
                d.id,
                d.temperatura,
                d.pulso,
                d.emocion,
                d.fecha,
                u.nombres_apellidos,
                u.email

            FROM diagnosticos d

            INNER JOIN usuarios u
            ON d.usuario_id = u.id

            WHERE d.id=%s

        """,(id,))


        diagnostico = cur.fetchone()


        if diagnostico is None:

            return jsonify({
                "error":"Diagnóstico no encontrado"
            }),404



        reporte=f"""

Temperatura:
{diagnostico["temperatura"]} °C


Pulso:
{diagnostico["pulso"]} BPM


Emoción:
{diagnostico["emocion"]}


Fecha:
{diagnostico["fecha"]}

"""


        enviado = enviar_correo(
            diagnostico["email"],
            diagnostico["nombres_apellidos"],
            reporte
        )


        if enviado:

            return jsonify({
                "exito":True,
                "mensaje":"Correo enviado correctamente"
            })


        else:

            return jsonify({
                "error":"No se pudo enviar el correo"
            }),500



    except Exception as e:

        return jsonify({
            "error":str(e)
        }),500


    finally:

        cur.close()
        conn.close()
# ============================================
# MANEJO DE ERRORES
# ============================================

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return jsonify({
        "error": "Ruta no encontrada."
    }), 404


@app.errorhandler(500)
def error_servidor(error):
    return jsonify({
        "error": "Error interno del servidor."
    }), 500

# ============================================
# API EDITAR USUARIO (NUEVA)
# ============================================

@app.route("/api/editar_usuario/<int:id>", methods=["PUT"])
def editar_usuario(id):
    
    data = request.get_json()
    
    # Capturamos los datos que envía el HTML desde los prompts
    nuevo_nombre = data.get("nombres_apellidos", "").strip()
    nuevo_email = data.get("email", "").strip()
    
    if not nuevo_nombre or not nuevo_email:
        return jsonify({"error": "El nombre y el email no pueden estar vacíos."}), 400

    conn = get_db()
    if conn is None:
        return jsonify({"error": "No se pudo conectar a la base de datos."}), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Actualizamos solo el nombre y el email según el ID
        cur.execute("""
            UPDATE usuarios
            SET nombres_apellidos = %s, email = %s
            WHERE id = %s
            RETURNING *
        """, (nuevo_nombre, nuevo_email, id))

        usuario_actualizado = cur.fetchone()
        conn.commit()

        if usuario_actualizado:
            return jsonify({
                "exito": True,
                "mensaje": "Usuario actualizado correctamente.",
                "usuario": dict(usuario_actualizado)
            }), 200
        else:
            return jsonify({"error": "No se encontró un usuario con ese ID."}), 404

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()


        
# ============================================
# EJECUTAR
# ============================================

if __name__ == "__main__":

    print("=" * 60)
    print("           EMOSYS iniciado correctamente")
    print("=" * 60)
    print("Detector : http://localhost:5000/")
    print("Registro : http://localhost:5000/registro")
    print("Login    : http://localhost:5000/login")
    print("Monitor  : http://localhost:5000/Monitor")
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

