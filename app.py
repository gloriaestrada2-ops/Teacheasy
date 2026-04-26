from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file,jsonify
from admin import iniciar_sesion,cambiar_password_bd,votar_recurso,obtener_evaluaciones_admin,obtener_docentes,obtener_grupos,obtener_total_preguntas,obtener_grupo_docente,obtener_alumnos_grupo_evaluacion,guardar_resultado,actualizar_alumno_db,consultar_grupos,actualizar_maestro_grupo_db,consultar_alumnos_por_grupo,eliminar_alumno_db,obtener_maestros,eliminar_grupo_db, agregar_alumno_db,crear_grupo_db,registrar_usuario,buscar_usuario_por_correo,obtener_examenes_pdf_por_usuario, agregar_preguntas_evaluacion,actualizar_contrasena,consultar_usuarios,baja_usuario,actualizar_usuario,consultar_recursos_por_tipo,agregar_recurso_y_tema,baja_recurso,obtener_unidades_con_recursos,crear_evaluacion_auto,obtener_temas_por_unidad,obtener_preguntas_evaluacion,generar_pdf_examen,guardar_pdf,info_examen,obtener_resultados,datos_graficas
from datetime import datetime
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import pandas as pd
from io import BytesIO
from database import bd_teacheasy  
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import random
import requests
from bs4 import BeautifulSoup
import PyPDF2
import random
import io
from werkzeug.utils import secure_filename
import json



app = Flask(__name__)
app.secret_key = "clave_secreta"


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear carpeta si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CONFIGURACIÓN DEL CORREO (ejemplo con Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'teacheasy9@gmail.com'   # Tu correo
app.config['MAIL_PASSWORD'] = 'yxrzsyrjnrxrpars'      # Contraseña de aplicación
app.config['MAIL_DEFAULT_SENDER'] = 'teacheasy9@gmail.com'

mail = Mail(app)

# Generador de tokens
serializer = URLSafeTimedSerializer(app.secret_key)


@app.route('/modulo_administracion')
def modulo_administracion():
    lista_usuarios = consultar_usuarios()  # 👈 consulta la base
    return render_template('modulo_administracion.html',usuarios=lista_usuarios )

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/administrador')
def administrador():
    return render_template('administrador.html')



@app.route('/docente')
def docente():
    return render_template('docente.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

    

@app.route('/inicio', methods=['POST'])
def handle_login():

    correo = request.form['correo']
    contrasena = request.form['contrasena']

    exito, rol, requiere_cambio, mensaje = iniciar_sesion(correo, contrasena)

    if exito:

        # ✅ GUARDAR EN SESIÓN
        session['correo'] = correo
        session['rol'] = rol

        # 🔴 si requiere cambio → ir a cambiar password
        if requiere_cambio == 1:
            return redirect(url_for('cambiar_password'))

        # ✅ redirección normal
        if rol == "ADMIN":
            return redirect(url_for('administrador'))

        elif rol == "DOCENTE":
            return redirect(url_for('docente'))

    flash(mensaje, "error")
    return redirect(url_for('login'))

@app.route('/menu')
def menu():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html', usuario=session['usuario'])

# Ruta para registrar usuario
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        confirmar = request.form['confirmar_contrasena']
        rol = request.form['rol']

        if contrasena != confirmar:
            flash("⚠️ Las contraseñas no coinciden.", "error")
            return render_template('registro.html', fecha_actual=fecha_actual)

        # ✅ AQUÍ ESTÁ LA CORRECCIÓN
        exito, mensaje = registrar_usuario(
            nombre,
            correo,
            contrasena,
            rol,
            requiere_cambio=0   # 👈 usuario normal = 0
        )

        if exito:
            flash("🎉 Usuario registrado exitosamente. Ahora puedes iniciar sesión.", "success")
        else:
            flash(f"❌ {mensaje}", "error")

    return render_template('registro.html', fecha_actual=fecha_actual)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        correo = request.form['correo']

        existe = buscar_usuario_por_correo(correo)

        if not existe:
            flash("❌ El correo no está registrado.", "error")
            return redirect(url_for('recuperar'))

        # Si existe → generar token
        token = serializer.dumps(correo, salt='recuperar-clave')
        link = url_for('restablecer', token=token, _external=True)

        msg = Message(
            'Restablecer contraseña - TEACHEASY',
            sender=app.config['MAIL_USERNAME'],
            recipients=[correo]
        )

        msg.body = f'''Hola,

Para restablecer tu contraseña haz clic en el siguiente enlace:

{link}

Este enlace expira en 10 minutos.
        '''

        mail.send(msg)

        flash("📩 Se enviaron instrucciones a tu correo.")
        return redirect(url_for('recuperar'))

    return render_template('recuperar.html')


@app.route('/restablecer/<token>', methods=['GET', 'POST'])
def restablecer(token):
    try:
        correo = serializer.loads(token, salt='recuperar-clave', max_age=600)
    except:
        return "El enlace ha expirado o es inválido"

    if request.method == 'POST':
        nueva_contrasena = request.form['contrasena']
        confirmar = request.form['confirmar']

        if nueva_contrasena != confirmar:
            flash("⚠️ Las contraseñas no coinciden.", "error")
            return render_template('nueva_contrasena.html')
        
        
        # Llamar a la función que actualiza la contraseña
        exito, mensaje = actualizar_contrasena(correo, nueva_contrasena)

       

        flash("🎉 Contraseña actualizada correctamente.", "success")
        return redirect(url_for('login'))

    return render_template('nueva_contrasena.html')



@app.route('/agregar_usuario_admin', methods=['GET', 'POST'])
def agregar_usuario_admin():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        confirmar = request.form['confirmar_contrasena']
        rol = request.form['rol']

        # 👇 tomar directamente el hidden
        requiere_cambio = request.form.get('requiere_cambio')
        requiere_cambio = int(requiere_cambio)  # "1" → 1

        if contrasena != confirmar:
            flash("⚠️ Las contraseñas no coinciden.", "error")
            return render_template('agregar_usuario_admin.html', fecha_actual=fecha_actual)

        exito, mensaje = registrar_usuario(
            nombre,
            correo,
            contrasena,
            rol,
            requiere_cambio
        )

        if exito:
            flash("🎉 Usuario registrado exitosamente.", "success")
        else:
            flash(f"❌ {mensaje}", "error")

    return render_template('agregar_usuario_admin.html', fecha_actual=fecha_actual)

@app.route('/eliminar_usuario/<int:id>')
def eliminar_usuario(id):

    exito, mensaje = baja_usuario(id)

    if exito:
        print("Usuario eliminado correctamente")
    else:
        print("Error:", mensaje)

    return redirect(url_for('modulo_administracion'))

@app.route('/actualizar_usuario', methods=['POST'])
def actualizar_usuario_ruta():
    # Recoger datos del formulario
    id_usuario = request.form.get('id_usuario')
    nombre = request.form.get('nombre')
    correo = request.form.get('correo')
    rol = request.form.get('rol')

    # Llamada a la función que ya contiene la lógica del procedimiento
    exito, mensaje, _, _, _ = actualizar_usuario(id_usuario, nombre, correo, rol)

    if exito:
        flash(mensaje, "Usuario actualizado exitosamente")
    else:
        flash(mensaje, "error")

    # Redirigir al módulo de administración después de actualizar
    return redirect(url_for('editar_usuario', id_usuario=id_usuario))

@app.route('/editar_usuario/<int:id_usuario>', methods=['GET'])
def editar_usuario(id_usuario):
    from admin import buscar_usuario_por_id  # función que llame al procedimiento

    # Llamamos a la función que usa el procedimiento para traer datos del usuario
    usuario = buscar_usuario_por_id(id_usuario)

    if not usuario:
        flash("Usuario no encontrado", "error")
        return redirect(url_for('modulo_administracion'))

    return render_template('editar_usuario.html', usuario=usuario)



@app.route('/gestionar_contenido/<int:id_tipo>')
def gestionar_contenido(id_tipo):
    # Llamamos a la función que trae los recursos filtrados por tipo
    recursos = consultar_recursos_por_tipo(id_tipo)
    
    # Renderizamos la plantilla pasando la lista de recursos y el id_tipo
    return render_template('gestionar_contenido.html', recursos=recursos, id_tipo=id_tipo)

@app.route('/agregar_recurso/<int:id_tipo>', methods=['GET', 'POST'])
def agregar_recurso(id_tipo):
    if request.method == 'POST':
        # Capturar datos del formulario
        id_unidad = request.form.get('id_unidad')
        id_tipo = request.form.get('id_tipo')
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        url = request.form.get('url')
        
        archivo = request.files.get('archivo')

        ruta_final = None
        # 🔹 SI SUBE ARCHIVO
        if archivo and archivo.filename != "":
            nombre_seguro = secure_filename(archivo.filename)
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_seguro)
            archivo.save(ruta_guardado)

            # 👉 convertir a URL
            ruta_final = f"/static/uploads/{nombre_seguro}"

        # 🔹 SI ES URL
        elif url:
            ruta_final = url

        else:
            return render_template(
                'agregar_nuevo_recurso.html',
                error="Debes subir un archivo o ingresar una URL"
            )

        # 🔹 GUARDAR EN BD
        exito, mensaje = agregar_recurso_y_tema(
            id_unidad, id_tipo, titulo, descripcion, ruta_final
        )

        if exito:
            return render_template('agregar_recurso.html', id_tipo=id_tipo,mensaje_exito="Recurso guardado con éxito ✅")
         
        else:
            return render_template('agregar_recurso.html', error=mensaje, id_tipo=id_tipo)

    # GET → mostrar formulario
    # GET → mostrar formulario
    return render_template('agregar_recurso.html', id_tipo=id_tipo)



    
      
    


@app.route('/eliminar_recurso/<int:id>/<int:id_tipo>')
def eliminar_recurso(id, id_tipo):

    exito, mensaje = baja_recurso(id)

    if exito:
        print("Recurso eliminado correctamente")
    else:
        print("Error:", mensaje)
  
    return redirect(url_for('gestionar_contenido', id_tipo=id_tipo))


@app.route('/editar_recurso/<int:id_recurso>', methods=['GET'])
def editar_recurso(id_recurso):

    from admin import buscar_recurso_por_id

    recurso = buscar_recurso_por_id(id_recurso)

    if not recurso:
        flash("Recurso no encontrado", "error")
        return redirect(url_for('gestionar_contenido', id_tipo=recurso["id_tipo"]))
        
    
    return render_template('editar_recurso.html',recurso=recurso,id_tipo=recurso["id_tipo"])
    
@app.route('/actualizar_recurso', methods=['POST'])
def actualizar_recurso():

    from admin import actualizar_recurso_db

    id_recurso = request.form['id_recurso']
   
    titulo = request.form['titulo']
    id_unidad = request.form['id_unidad']
    id_tipo = request.form['id_tipo']
    descripcion = request.form['descripcion']
    url = request.form['url']

    valido, mensaje = actualizar_recurso_db(
        id_recurso, titulo, id_unidad, id_tipo, descripcion, url
    )

    flash("Recurso editado correctamente")
    
    return redirect(url_for('editar_recurso', id_recurso=id_recurso))
  
  
@app.route('/generar_backup_excel')
def generar_backup_excel():

    from admin import bd_teacheasy

    conexion = bd_teacheasy()

    if not conexion:
        return "Error de conexión"

    try:
        # 🔹 Leer tablas
        df_usuarios = pd.read_sql("SELECT * FROM usuarios", conexion)
        df_recursos = pd.read_sql("SELECT * FROM recurso", conexion)

        # 🔹 Crear archivo en memoria
        output = BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_usuarios.to_excel(writer, sheet_name='Usuarios', index=False)
            df_recursos.to_excel(writer, sheet_name='Recursos', index=False)

        output.seek(0)

        # 🔹 Nombre con fecha automática
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_archivo = f"backup_teacheasy_{fecha_actual}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return f"Error al generar respaldo: {e}"

    finally:
        conexion.close()

@app.route('/modulo_didactico')
def modulo_didactico():

    id_usuario = session.get('id_usuario')  # ✅ obtener usuario logueado
    datos = obtener_unidades_con_recursos(id_usuario)

    # verificar el rol del usuario
    if session['rol'] == 'ADMIN':
        panel = 'administrador'
    else:
        panel = 'docente'

    return render_template(
        'modulo_didactico.html',
        datos=datos,
        panel=panel
    )       

@app.route('/modulo_didactico2')
def modulo_didactico2():

    id_usuario = session.get('id_usuario')  # ✅ obtener usuario logueado

    datos = obtener_unidades_con_recursos(id_usuario)

    # verificar el rol del usuario
    if session['rol'] == 'ADMIN':
        panel = 'administrador'
    else:
        panel = 'docente'

    return render_template(
        'modulo_didactico2.html',
        datos=datos,
        panel=panel
    )


@app.route('/agregar_nuevo_recurso', methods=['GET', 'POST'])
def agregar_nuevo_recurso():

    if request.method == 'POST':
        id_unidad = request.form.get('id_unidad')
        id_tipo = request.form.get('id_tipo')
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        url = request.form.get('url')

        archivo = request.files.get('archivo')

        ruta_final = None

        # 🔹 SI SUBE ARCHIVO
        if archivo and archivo.filename != "":
            nombre_seguro = secure_filename(archivo.filename)
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_seguro)
            archivo.save(ruta_guardado)

            # 👉 convertir a URL
            ruta_final = f"/static/uploads/{nombre_seguro}"

        # 🔹 SI ES URL
        elif url:
            ruta_final = url

        else:
            return render_template(
                'agregar_nuevo_recurso.html',
                error="Debes subir un archivo o ingresar una URL"
            )

        # 🔹 GUARDAR EN BD
        exito, mensaje = agregar_recurso_y_tema(
            id_unidad, id_tipo, titulo, descripcion, ruta_final
        )

        if exito:
            return render_template(
                'agregar_nuevo_recurso.html',
                mensaje_exito="Recurso guardado con éxito ✅"
            )
        else:
            return render_template(
                'agregar_nuevo_recurso.html',
                error=mensaje
            )

    return render_template('agregar_nuevo_recurso.html')


@app.route('/eliminar_recurso_interactivo/<int:id>')
def eliminar_recurso_interactivo(id):

    exito, mensaje = baja_recurso(id)

    if exito:
        print("Recurso eliminado correctamente")
    else:
        print("Error:", mensaje)

    return redirect(url_for('modulo_didactico'))



@app.route('/editar_recurso_interactivo/<int:id_recurso>', methods=['GET'])
def editar_recurso_interactivo(id_recurso):

    from admin import buscar_recurso_por_id

    recurso = buscar_recurso_por_id(id_recurso)

    if not recurso:
        flash("Recurso no encontrado", "error")
        return redirect(url_for('modulo_didactivo'))
        
    
    return render_template('editar_recurso_interactivo.html',recurso=recurso)


    
@app.route('/actualizar_recurso_interactivo', methods=['POST'])
def actualizar_recurso_interactivo():

    from admin import actualizar_recurso_db

    id_recurso = request.form['id_recurso']
   
    titulo = request.form['titulo']
    id_unidad = request.form['id_unidad']
    id_tipo = request.form['id_tipo']
    descripcion = request.form['descripcion']
    url = request.form['url']

    valido, mensaje = actualizar_recurso_db(
        id_recurso, titulo, id_unidad, id_tipo, descripcion, url
    )

    flash("Recurso editado correctamente")
    
    return redirect(url_for('editar_recurso_interactivo', id_recurso=id_recurso))


# ---------------------------------------------------------

@app.route('/evaluaciones') 
def evaluaciones():

    if "id_usuario" not in session:
        return redirect(url_for("login"))

    id_usuario = session.get("id_usuario")
    rol = session.get("rol")

    # 🔹 FILTROS (solo admin)
    
    id_docente = request.args.get("docente") or None
    id_grupo = request.args.get("grupo") or None

    # 🔹 ADMIN
    if rol == 'ADMIN':
        panel = 'administrador'
        template = "modulo_de_evaluaciones_admin.html"

        evaluaciones = obtener_evaluaciones_admin(id_docente, id_grupo)
        docentes = obtener_docentes()
        grupos = obtener_grupos()

        return render_template(
            template,
            evaluaciones=evaluaciones,
            panel=panel,
            docentes=docentes,
            grupos=grupos
        )

    # 🔹 DOCENTE
    else:
        panel = 'docente'
        template = "modulo_de_evaluaciones.html"

        evaluaciones = obtener_examenes_pdf_por_usuario(id_usuario)

        return render_template(
            template,
            evaluaciones=evaluaciones,
            panel=panel
        )
        
from admin import finalizar_examen

@app.route('/finalizar_examen/<int:id_pdf>', methods=['POST'])
def finalizar_examen_route(id_pdf):

    finalizar_examen(id_pdf)

    return {"mensaje":"ok"}



from flask import request, jsonify

@app.route("/cambiar_estado_examen/<int:id>", methods=["POST"])
def cambiar_estado_examen(id):

    data = request.get_json()
    estado = data["estado"]

    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE examen_pdf
        SET estado=%s
        WHERE id_evaluacion=%s
    """, (estado, id))

    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"estado": estado})

# ---------------------------------------------------------
@app.route('/crear_evaluacion', methods=["GET", "POST"])
def crear_evaluacion():

    if request.method == "POST":

        try:
            # 1️⃣ Datos básicos
            titulo = request.form.get("titulo")
            fecha = request.form.get("fecha")
            unidad = int(request.form.get("unidad"))

            # 🔥 Configuración de tipos
            config_json = request.form.get("configuracion_tipos")

            if not config_json:
                return "Debes seleccionar al menos un tipo de evaluación"

            configuracion = json.loads(config_json)

            # 2️⃣ Temas
            temas_lista = request.form.getlist("tema")

            if not temas_lista:
                return "Debes seleccionar al menos un tema"

            temas = ",".join(temas_lista)  # 🔥 IMPORTANTE (string para MySQL)

            # 👤 Usuario
            id_usuario = session.get("id_usuario")

            if not id_usuario:
                return "Sesión no válida. Inicia sesión nuevamente."

            # 3️⃣ CREAR EVALUACIÓN
            exito, id_evaluacion = crear_evaluacion_auto(
                unidad,
                id_usuario,
                titulo,
                fecha,
                temas
            )

            if not exito:
                return "Error al crear la evaluación"

            # 4️⃣ AGREGAR PREGUNTAS POR TIPO 🔥
            for tipo in configuracion:

                tipo_pregunta = tipo["tipo"]
                cantidad = int(tipo["preguntas"])

                agregar_preguntas_evaluacion(
                    id_evaluacion,
                    tipo_pregunta,
                    cantidad,
                    temas   # 👈 aquí va STRING, no lista
                )

            # 5️⃣ Obtener preguntas
            preguntas = obtener_preguntas_evaluacion(id_evaluacion)

            if not preguntas:
                return "No se generaron preguntas"

            # 6️⃣ Generar PDF
            nombre_pdf, ruta_pdf = generar_pdf_examen(
                titulo,
                preguntas,
                id_evaluacion
            )

            # 7️⃣ Guardar PDF
            guardar_pdf(
                id_evaluacion,
                nombre_pdf,
                ruta_pdf
            )

            return send_file(
                ruta_pdf,
                as_attachment=True,
                download_name=nombre_pdf
            )

        except Exception as e:
            print("Error:", e)
            return "Ocurrió un error al generar la evaluación"

    return render_template("crear_evaluacion.html")
# ---------------------------------------------------------
@app.route("/temas_por_unidad/<int:id_unidad>")
def temas_por_unidad(id_unidad):
    temas = obtener_temas_por_unidad(id_unidad)
    return jsonify(temas)

@app.route("/resultados/<int:id_evaluacion>")
def resultados(id_evaluacion):

    id_usuario = session["id_usuario"]

    # 🔹 Info de la evaluación
    info = info_examen(id_evaluacion)

    # 🔹 Datos del docente
    
    grupo = obtener_grupo_docente(id_usuario)

    # 🔹 Alumnos del grupo
    alumnos = obtener_alumnos_grupo_evaluacion(id_evaluacion)
    

    # 🔹 Total de preguntas de la evaluación
    total_preguntas = obtener_total_preguntas(id_evaluacion)

    # 🔹 Resultados ya guardados (si existen)
    lista = obtener_resultados(id_evaluacion) or []

    # 🔹 Datos para gráficas (si ya hay resultados)
    graficas = datos_graficas(id_evaluacion) or []

    # 🔹 Cálculo de porcentaje (solo si hay datos)
    total_aciertos = 0
    total_preguntas_acum = 0

    for alumno in graficas:
        total_aciertos += alumno.get("aciertos", 0)
        total_preguntas_acum += alumno.get("total_preguntas", 0)

    porcentaje = round((total_aciertos / total_preguntas_acum) * 100) if total_preguntas_acum > 0 else 0

    # 🔹 Estado
    resultados_finales = lista if info and info.get("estado") == "FINALIZADO" else []

    return render_template(
        "resultados.html",

        # info general
        info=info,

        # NUEVO (clave)
        grupo=grupo,
        alumnos=alumnos,
        total_preguntas=total_preguntas,

        # resultados existentes
        lista=lista,
        graficas=graficas,
        resultados=resultados_finales,
        porcentaje=porcentaje
    )
    
    

   
@app.route("/guardar_resultados", methods=["POST"])
def guardarResultados():
    try:
        data = request.get_json()

        id_evaluacion = int(data.get("id_evaluacion"))
        alumnos = data.get("alumnos")
        total_preguntas = int(data.get("total_preguntas"))
        fecha = data.get("fecha")

        conexion = bd_teacheasy()
        cursor = conexion.cursor()

        # ✅ SOLO borrar resultados (NO alumnos)
        cursor.execute(
            "DELETE FROM resultado_evaluacion WHERE id_evaluacion=%s",
            (id_evaluacion,)
        )

        # ✅ Guardar resultados (SIN crear alumnos nuevos)
        for alumno in alumnos:
            id_alumno = alumno.get("id_alumno")
            aciertos = int(alumno.get("aciertos", 0))

            cursor.execute("""
                INSERT INTO resultado_evaluacion(
                    id_alumno,
                    id_evaluacion,
                    aciertos,
                    total_preguntas,
                    fecha
                ) VALUES(%s,%s,%s,%s,%s)
            """, (id_alumno, id_evaluacion, aciertos, total_preguntas, fecha))

        # ✅ Cambiar estado
        cursor.execute(
            "UPDATE examen_pdf SET estado='FINALIZADO' WHERE id_evaluacion=%s",
            (id_evaluacion,)
        )

        conexion.commit()
        cursor.close()
        conexion.close()

        return jsonify({
            "mensaje": "Resultados guardados correctamente",
            "estado": "FINALIZADO"
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)})

@app.route("/gestionar_grupos")
def gestionar_grupos():

    grupos = consultar_grupos()

    # 🔥 agregar alumnos a cada grupo
    for grupo in grupos:
        grupo["alumnos"] = consultar_alumnos_por_grupo(grupo["id_grupo"])

    maestros = obtener_maestros()

    return render_template(
        "grupos.html",
        grupos=grupos,
        maestros=maestros
    )
@app.route("/crear_grupo", methods=["POST"])
def crear_grupo():

    grado = request.form.get("grado")
    letra = request.form.get("letra")
    id_maestro = request.form.get("id_maestro")

    crear_grupo_db(grado, letra, id_maestro)

    return redirect(url_for("gestionar_grupos"))

@app.route("/agregar_alumno", methods=["POST"])
def agregar_alumno():

    id_grupo = request.form.get("id_grupo")
    nombre = request.form.get("nombre")
    curp = request.form.get("curp")

    agregar_alumno_db(id_grupo, nombre, curp)

    return redirect(url_for("gestionar_grupos"))

@app.route("/eliminar_grupo/<int:id_grupo>")
def eliminar_grupo(id_grupo):

    eliminar_grupo_db(id_grupo)

    return redirect(url_for("gestionar_grupos"))


@app.route('/eliminar_alumno/<int:id_alumno>')
def eliminar_alumno(id_alumno):

    eliminar_alumno_db(id_alumno)

    return redirect(url_for('gestionar_grupos'))



@app.route("/actualizar_maestro", methods=["POST"])
def actualizar_maestro():
    id_grupo = request.form["id_grupo"]
    id_maestro = request.form["id_maestro"]

    exito = actualizar_maestro_grupo_db(id_grupo, id_maestro)

    if exito:
        print("✔ Maestro actualizado")
    else:
        print("❌ Error")

    return redirect(url_for("gestionar_grupos"))
    
    


@app.route("/actualizar_alumno", methods=["POST"])
def actualizar_alumno():

    id_alumno = request.form["id_alumno"]
    nombre = request.form["nombre"]
    curp = request.form["curp"]

    exito, mensaje = actualizar_alumno_db(id_alumno, nombre, curp)

    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "error")

    return redirect(url_for("gestionar_grupos"))


@app.route('/votar_recurso/<int:id_recurso>', methods=['POST'])
def votar_recurso_route(id_recurso):

    id_usuario = session.get('id_usuario')

    votar_recurso(id_usuario, id_recurso)

    return redirect(request.referrer)

@app.route('/cambiar_password', methods=['GET', 'POST'])
def cambiar_password():

    if request.method == 'POST':
        nueva = request.form['nueva']
        confirmar = request.form['confirmar']

        if nueva != confirmar:
            flash("Las contraseñas no coinciden", "error")
            return render_template('cambiar_password.html')

        correo = session.get('correo')
        rol = session.get('rol')  # ✅ AGREGADO

        if not correo:
            flash("Sesión inválida", "error")
            return redirect(url_for('login'))

        exito, mensaje = cambiar_password_bd(correo, nueva)

        if exito:
            # 🔴 quitar bloqueo
            conexion = bd_teacheasy()
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE usuarios 
                SET requiere_cambio_password = FALSE 
                WHERE correo = %s
            """, (correo,))
            conexion.commit()
            cursor.close()
            conexion.close()

            flash(mensaje, "success")

            # ✅ LIMPIAR SESIÓN (opcional pero recomendado)
            session.pop('correo', None)

            # 🚀 REDIRECCIÓN SEGÚN ROL
            if rol == "ADMIN":
                return redirect(url_for('administrador'))
            elif rol == "DOCENTE":
                return redirect(url_for('docente'))
            else:
                return redirect(url_for('login'))

        else:
            flash(mensaje, "error")

    return render_template('cambiar_password.html')

if __name__ == '__main__':
    app.run(debug=True)