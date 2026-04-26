import mysql.connector
from database import bd_teacheasy  # Asegúrate de que conectar_db esté correctamente definido
from flask import session
import random
import requests
from bs4 import BeautifulSoup
import PyPDF2
import random
import io
from reportlab.pdfgen import canvas
import os
from reportlab.lib.pagesizes import letter
from PIL import Image
import pytesseract

import requests
def iniciar_sesion(correo_electronico, contrasena):
    conexion = bd_teacheasy()

    if conexion:
        cursor = conexion.cursor()

        try:
            # Ejecutar procedimiento
            cursor.callproc(
                'inicio_abcc',
                [4, None, None, correo_electronico, None, None, None, 0, "", 0, "", "", ""]
            )

            # Obtener resultado del SELECT del procedimiento
            data = None
            for res in cursor.stored_results():
                data = res.fetchone()

            if not data:
                return False, None, None, "Usuario no encontrado"

            # Datos del usuario
            p_id_usuario, nombre_usuario, p_rol, password_bd = data

            # Validar contraseña
            if password_bd == contrasena:

                # Consultar si requiere cambio
                cursor.execute("""
                    SELECT requiere_cambio_password
                    FROM usuarios
                    WHERE id_usuario = %s
                """, (p_id_usuario,))

                resultado_cambio = cursor.fetchone()
                requiere_cambio = resultado_cambio[0] if resultado_cambio else 0

                # Guardar sesión
                session['id_usuario'] = p_id_usuario
                session['nombre_usuario'] = nombre_usuario
                session['rol'] = p_rol

                return True, p_rol, requiere_cambio, "Inicio de sesión exitoso"

            else:
                return False, None, None, "Contraseña incorrecta"

        except Exception as e:
            print(f"Error al iniciar sesión: {e}")
            return False, None, None, "Error al procesar la solicitud."

        finally:
            cursor.close()
            conexion.close()

    return False, None, None, "No se pudo conectar a la base de datos."

def registrar_usuario(nombre, correo, contrasena, rol, requiere_cambio):
    conexion = bd_teacheasy()

    if conexion:
        cursor = conexion.cursor()

        try:
            # Asegurar que sea 0 o 1 entero
            requiere_cambio = int(requiere_cambio)

            resultado = cursor.callproc('inicio_abcc', [
                1,                  # p_opcion
                None,               # p_id_usuario
                nombre,             # p_nombre
                correo,             # p_correo
                contrasena,         # p_contrasena
                rol,                # p_rol
                requiere_cambio,    # 👈 YA CORRECTO (1 o 0)

                0,                  # OUT p_valido
                '',                 # OUT p_mensaje
                0,                  # OUT p_id_out
                '',                 # OUT p_nombre_out
                '',                 # OUT p_rol_out
                ''                  # OUT p_password_out
            ])

            p_valido = resultado[7]
            p_mensaje = resultado[8]
            p_id_out = resultado[9]

            if p_valido == 1:
                conexion.commit()
                return True, f"Usuario registrado con éxito. ID: {p_id_out}"
            else:
                return False, p_mensaje

        except Exception as e:
            print(f"Error al registrar usuario: {e}")
            return False, "Error en la base de datos."

        finally:
            cursor.close()
            conexion.close()

    else:
        return False, "No se pudo conectar a la base de datos."
    
def buscar_usuario_por_correo(correo):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()

        if resultado:
            return True
        else:
            return False
def actualizar_contrasena(correo, nueva_contrasena):
    # Conectar a la base de datos
    conexion = bd_teacheasy()  # tu función para obtener conexión
    if conexion:
        cursor = conexion.cursor()
        try:
            # Llamar al procedimiento almacenado con p_opcion = 3
            resultado = cursor.callproc('inicio_abcc', [
                3,           # p_opcion = 3 → actualizar contraseña
                None,        # p_id_usuario (no se usa)
                None,        # p_nombre (no se cambia)
                correo,      # p_correo → identificador
                nueva_contrasena,  # p_contrasena → nueva contraseña
                None,        # p_rol (no se cambia)
                None,
                0,           # p_valido OUT (inicializado)
                '',          # p_mensaje OUT (inicializado)
                0,           # p_id_out OUT (inicializado)
                '',          # p_nombre_out OUT (inicializado)
                '',          # p_rol_out OUT (inicializado)
                ''           # p_password_out OUT (inicializado)
            ])

            # Obtener los valores de salida
            p_valido = resultado[7]
            p_mensaje = resultado[8]
            p_id_out = resultado[9]
            p_nombre_out = resultado[10]
            p_rol_out = resultado[11]
            p_password_out = resultado[12]

            if p_valido == 1:
                conexion.commit()
                return True, f"Contraseña actualizada correctamente para ID usuario: {p_id_out}"
            else:
                return False, p_mensaje

        except Exception as e:
            print(f"Error al actualizar contraseña: {e}")
            return False, "Error en la base de datos."
        finally:
            cursor.close()
            conexion.close()
    else:
        return False, "No se pudo conectar a la base de datos."
    

def consultar_usuarios():
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor(dictionary=True)  # 👈 IMPORTANTE
        try:
            # Llamamos al procedimiento solo con la opción 4
            cursor.callproc('inicio_abcc', [5, None, None, None, None, None, None, None, None,None,None,None,None])

            usuarios = []

            for result in cursor.stored_results():
                usuarios = result.fetchall()

            return usuarios

        except mysql.connector.Error as e:
            print(f"Error al consultar los usuarios: {e}")
            return []

        finally:
            cursor.close()
            conexion.close()
            
def baja_usuario(Id_usuario):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            resultados = cursor.callproc(
                'inicio_abcc',
                [
                    2,              # p_opcion (Eliminar)
                    Id_usuario,     # p_id_usuario
                    None,           # p_nombre
                    None,           # p_correo
                    None,           # p_contrasena
                    None,           # p_rol
                    None,
                    0,              # p_valido (OUT)
                    "",             # p_mensaje (OUT)
                    0,              # p_id_out (OUT)
                    "",             # p_nombre_out (OUT)
                    "",             # p_rol_out (OUT)
                    ""              # p_password_out (OUT)
                ]
            )
            
  

            p_valido = resultados[7]
            p_mensaje = resultados[8]

            if p_valido == 1:
                conexion.commit()
                return True, p_mensaje
            else:
                return False, p_mensaje

        except Exception as e:
            print("Error al eliminar usuario:", e)
            return False, "Error al eliminar usuario"

        finally:
            cursor.close()
            conexion.close()
def actualizar_usuario(Id_usuario, nombre, correo, rol):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            # Llamada al procedimiento
            resultados = cursor.callproc(
                'inicio_abcc',
                [
                    6,          # p_opcion (Actualizar datos)
                    Id_usuario, # p_id_usuario
                    nombre,     # p_nombre
                    correo,     # p_correo
                    None,       # p_contrasena (no se actualiza aquí)
                    rol,        # p_rol
                    None,
                    0,          # p_valido (OUT)
                    "",         # p_mensaje (OUT)
                    0,          # p_id_out (OUT)
                    "",         # p_nombre_out (OUT)
                    "",         # p_rol_out (OUT)
                    ""          # p_password_out (OUT)
                ]
            )

            # Recuperar los parámetros OUT
            p_valido = resultados[7]
            p_mensaje = resultados[8]
            p_id_out = resultados[9]
            p_nombre_out = resultados[10]
            p_rol_out = resultados[11]

            if p_valido == 1:
                conexion.commit()
                return True, p_mensaje, p_id_out, p_nombre_out, p_rol_out
            else:
                return False, p_mensaje, None, None, None

        except Exception as e:
            print("Error al actualizar usuario:", e)
            return False, "Error al actualizar usuario", None, None, None

        finally:
            cursor.close()
            conexion.close()

            
def buscar_usuario_por_id(id_usuario):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            # Llamamos al procedimiento
            resultados = cursor.callproc(
                'inicio_abcc',
                [
                    7,           # opción buscar por ID
                    id_usuario,  # p_id_usuario
                    None, None, None, None,None,
                    0, "", 0, "", "", ""
                ]
            )

            # Recuperamos los parámetros OUT
            p_valido = resultados[7]
            if p_valido == 0:
                return None

            usuario = {
                "id_usuario": resultados[9],
                "nombre": resultados[10],
                "rol": resultados[11],
                "correo": resultados[12]
            }

            return usuario

        except Exception as e:
            print("Error al buscar usuario:", e)
            return None
        finally:
            cursor.close()
            conexion.close()
            

def consultar_recursos_por_tipo(id_tipo):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        try:
            # Llamamos al procedimiento con p_opcion=5 y enviamos id_tipo
            cursor.callproc('gestionar_recurso', [
                5,          # p_opcion = 5 (consultar todos)
                None,       # p_id_recurso
                None,       # p_id_tema
                id_tipo,    # p_id_tipo --> filtrará por tipo
                None,
                None,       # p_titulo
                None,       # p_descripcion
                None,       # p_url
                None,
                0,          # p_valido OUT
                "",         # p_mensaje OUT
                0,          # p_id_out OUT
                "",         # p_titulo_out OUT
                0,          # p_tipo_out OUT
                0           # p_tema_out OUT
            ])

            recursos = []

            # Recuperamos los resultados del SELECT del procedimiento
            for result in cursor.stored_results():
                recursos = result.fetchall()  # Ya vienen filtrados por id_tipo desde SQL

            return recursos

        except mysql.connector.Error as e:
            print(f"Error al consultar los recursos: {e}")
            return []

        finally:
            cursor.close()
            conexion.close()
            
def agregar_recurso_y_tema(id_unidad, id_tipo, titulo, descripcion, url):
    # Conectar a la base de datos
    conexion = bd_teacheasy()  # tu función para obtener conexión
    if conexion:
        cursor = conexion.cursor()
        try:
            # Llamar al procedimiento almacenado
            resultado = cursor.callproc('gestionar_recurso', [
                1,         # p_opcion = 1 → agregar recurso y crear tema
                None,      # p_id_recurso (no se necesita para registro)
                None,      # p_id_tema (se generará automáticamente)
                id_tipo,   # p_id_tipo
                id_unidad, # p_id_unidad
                titulo,    # p_titulo
                descripcion, # p_descripcion
                url,       # p_url
                None,
                0,         # p_valido OUT (inicializado)
                '',        # p_mensaje OUT (inicializado)
                0,         # p_id_out OUT (id del recurso)
                '',        # p_titulo_out OUT
                0,         # p_tipo_out OUT
                0          # p_tema_out OUT (id del tema recién creado)
            ])

            # Obtener los valores de salida
            p_valido = resultado[9]
            p_mensaje = resultado[10]
            p_id_out = resultado[11]        # id del recurso
            p_titulo_out = resultado[12]
            p_tipo_out = resultado[13]
            p_tema_out = resultado[14]      # id del tema recién creado

            if p_valido == 1:
                conexion.commit()
                return True, f"Recurso creado con éxito. ID recurso: {p_id_out}, ID tema: {p_tema_out}"
            else:
                return False, p_mensaje

        except Exception as e:
            print(f"Error al agregar recurso: {e}")
            return False, "Error en la base de datos."
        finally:
            cursor.close()
            conexion.close()
    else:
        return False, "No se pudo conectar a la base de datos."
    
def baja_recurso(id_recurso):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            resultados = cursor.callproc(
                'gestionar_recurso',
                [
                    2,              # p_opcion (Eliminar)
                    id_recurso,     # p_id_recurso
                    None,           # p_id_tema
                    None,           # p_id_tipo
                    None,           # p_id_unidad
                    None,           # p_titulo
                    None,           # p_descripcion
                    None,  
                    None,
                    0,              # p_valido OUT
                    "",             # p_mensaje OUT
                    0,              # p_id_out
                    "",             # p_titulo_out
                    0,              # p_tipo_out
                    0               # p_tema_out
                ]
            )

            p_valido = resultados[9]
            p_mensaje = resultados[10]

            if p_valido == 1:
                conexion.commit()
                return True, p_mensaje
            else:
                return False, p_mensaje

        except Exception as e:
            print("Error al eliminar recurso:", e)
            return False, "Error al eliminar recurso"

        finally:
            cursor.close()
            conexion.close()
            

def buscar_recurso_por_id(id_recurso):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.callproc(
                'gestionar_recurso',
                [
                    6,
                    id_recurso,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    0, "", 0, "", 0, 0
                ]
            )

            for result in cursor.stored_results():
                row = result.fetchone()

                if row:
                    recurso = {
                        "id_recurso": row[0],
                        "titulo": row[1],
                        "id_tipo": row[2],
                        "id_tema": row[3],
                        "id_unidad": row[4],
                        "descripcion": row[5],
                        "url": row[6]
                    }
                    return recurso

            return None

        except Exception as e:
            print("Error al buscar recurso:", e)
            return None
        finally:
            cursor.close()
            conexion.close()

def actualizar_recurso_db(id_recurso, titulo, id_unidad, id_tipo, descripcion, url):

    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            id_recurso = int(id_recurso)
            id_unidad = int(id_unidad)
            id_tipo = int(id_tipo)

            cursor.execute(
                "SELECT id_tema FROM recurso WHERE id_recurso = %s",
                (id_recurso,)
            )
            row = cursor.fetchone()

            if not row:
                return 0, "Recurso no encontrado"

            id_tema = row[0]

            resultados = cursor.callproc(
                'gestionar_recurso',
                [
                    3,
                    id_recurso,
                    id_tema,
                    id_tipo,
                    id_unidad,
                    titulo,
                    descripcion,
                    url,
                    None,
                    0, "", 0, "", 0, 0
                ]
            )

            conexion.commit()  # 🔥 MUY IMPORTANTE

            p_valido = resultados[9]
            p_mensaje = resultados[10]

            return p_valido, p_mensaje

        except Exception as e:
            print("Error al actualizar recurso:", e)
            return 0, "Error al actualizar"
        finally:
            cursor.close()
            conexion.close()
            
def obtener_unidades_con_recursos(id_usuario):
    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)

    cursor.callproc('gestionar_recurso', [
        7,              # p_opcion
        None, None, None, None,
        None, None, None,
        id_usuario,     # ✅ IMPORTANTE
        0, "", 0, "", 0, 0
    ])

    filas = []

    for result in cursor.stored_results():
        filas = result.fetchall()

    conexion.close()

    unidades = {}

    for fila in filas:
        id_unidad = fila["id_unidad"]

        if id_unidad not in unidades:
            unidades[id_unidad] = {
                "id_unidad": id_unidad,
                "nombre_unidad": fila["nombre_unidad"],
                "objetivo": fila["objetivo"],
                "recursos": []
            }

        # ✅ agregar recurso correctamente
        if fila["id_recurso"]:
            unidades[id_unidad]["recursos"].append({
                "id_recurso": fila["id_recurso"],
                "titulo": fila["titulo"],
                "descripcion": fila["descripcion"],
                "url": fila["url"],
                "votos_utiles": fila["votos_utiles"],
                "ya_voto": fila["ya_voto"]   # ✅ CLAVE PARA EL HTML
            })

    return list(unidades.values())

def obtener_temas_por_unidad(id_unidad):

    conexion = bd_teacheasy()

    if conexion:
        cursor = conexion.cursor(dictionary=True)

        try:

            cursor.callproc('obtener_temas_por_unidad', [id_unidad])

            temas = []

            for result in cursor.stored_results():
                temas = result.fetchall()

            return temas

        except Exception as e:
            print("Error al obtener temas:", e)
            return []

        finally:
            cursor.close()
            conexion.close()
            
def crear_evaluacion_auto(id_unidad, id_usuario, titulo, fecha_creacion, temas):

    conexion = bd_teacheasy()
    if not conexion:
        return False, None

    cursor = conexion.cursor(dictionary=True)

    try:

        # Llamar procedimiento
        cursor.callproc(
            'crear_evaluacion_auto',
            (
                id_unidad,
                id_usuario,
                titulo,
                fecha_creacion,
                temas
            )
        )

        conexion.commit()

        # 🔥 Obtener resultado del SELECT del procedimiento
        id_evaluacion = None

        for result in cursor.stored_results():
            row = result.fetchone()
            if row:
                id_evaluacion = row["id_evaluacion"]

        return True, id_evaluacion

    except Exception as e:
        print("Error al crear evaluación:", e)
        return False, None

    finally:
        cursor.close()
        conexion.close()
        
def agregar_preguntas_evaluacion(id_evaluacion, tipo_pregunta, cantidad, temas):

    conexion = bd_teacheasy()
    if not conexion:
        return False

    cursor = conexion.cursor()

    try:

        cursor.callproc(
            'agregar_preguntas_evaluacion',
            (
                id_evaluacion,    # p_id_evaluacion
                tipo_pregunta,    # p_tipo
                cantidad,         # p_cantidad
                temas             # p_temas (string "1,2,3")
            )
        )

        conexion.commit()

        return True

    except Exception as e:
        print("Error al agregar preguntas:", e)
        return False

    finally:
        cursor.close()
        conexion.close()
        
def obtener_preguntas_evaluacion(id_evaluacion):

    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)

    query = """
    SELECT p.id_pregunta, p.pregunta, p.tipo_pregunta
    FROM evaluacion_pregunta ep
    JOIN pregunta p ON ep.id_pregunta = p.id_pregunta
    WHERE ep.id_evaluacion = %s
    """

    cursor.execute(query,(id_evaluacion,))
    preguntas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return preguntas

def obtener_opciones(id_pregunta):

    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)

    query = """
    SELECT opcion, es_correcta
    FROM opcion_respuesta
    WHERE id_pregunta=%s
    """

    cursor.execute(query,(id_pregunta,))
    opciones = cursor.fetchall()

    cursor.close()
    conexion.close()

    return opciones
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
import os
def generar_pdf_examen(titulo, preguntas, id_evaluacion, alumno_nombre="________________"):

    carpeta = "static/examenes"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        
    # evitar espacios en nombre
    nombre = f"{titulo.replace(' ','_')}.pdf"
    
    ruta = os.path.join(carpeta, nombre)
    
     # ruta para guardar en la base de datos
    ruta_bd = ruta.replace("\\", "/")


    c = canvas.Canvas(ruta, pagesize=letter)

    y = 750

    # Logo
    logo = "static/logo.png"

    if os.path.exists(logo):
        c.drawImage(logo, 50, 730, width=50, height=50)

    # Nombre del sistema
    c.setFont("Helvetica-Bold",18)
    c.drawString(110, 750, "TEACHEASY")

    # Encabezado examen
    c.setFont("Helvetica-Bold",16)
    c.drawCentredString(300, 720, "EXAMEN 6° GRADO - INGLÉS")

    y = 690

    c.setFont("Helvetica",12)
    c.drawString(50, y, f"Nombre del Alumno: {alumno_nombre}")
    c.drawString(350, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")

    y -= 40

    numero = 1

    for p in preguntas:

        c.setFont("Helvetica",12)
        c.drawString(50, y, f"{numero}. {p['pregunta']}")

        y -= 20

        if p["tipo_pregunta"] == "multiple":

            opciones = obtener_opciones(p["id_pregunta"])

            for op in opciones:
                c.drawString(70, y, "- " + op["opcion"])
                y -= 15

        elif p["tipo_pregunta"] == "verdadero_falso":

            c.drawString(70, y, "( ) Verdadero")
            y -= 15
            c.drawString(70, y, "( ) Falso")
            y -= 15

        elif p["tipo_pregunta"] == "abierta":

            y -= 20
            c.line(50, y, 500, y)
            y -= 15
            c.line(50, y, 500, y)

        y -= 25
        numero += 1

        if y < 100:
            c.showPage()
            y = 750

    c.save()

    return nombre, ruta_bd
def guardar_pdf(id_evaluacion,nombre,ruta):

    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    query = """
    INSERT INTO examen_pdf(
    id_evaluacion,
    nombre_archivo,
    ruta_archivo
    )
    VALUES(%s,%s,%s)
    """

    cursor.execute(query,(id_evaluacion,nombre,ruta))

    conexion.commit()

    cursor.close()
    conexion.close()
    
def obtener_examenes_pdf_por_usuario(id_usuario):

    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    cursor.callproc('examenpdf_consultar_por_usuario', [id_usuario])

    datos = []

    for result in cursor.stored_results():
        datos = result.fetchall()

    cursor.close()
    return datos
    
def finalizar_examen(id_pdf):

    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    cursor.callproc('examenpdf_cambiar_estado', (id_pdf,))

    conexion.commit()
    cursor.close()

    return True





# =====================================
# 2 REGISTRAR RESULTADO EXAMEN
# =====================================
def registrar_resultado(id_alumno,id_evaluacion,aciertos,total):
    
    conexion = bd_teacheasy()
    cursor = conexion.cursor()
    

    cursor.callproc('resultados_abcc',[
        2,
        id_alumno,
        None,
        None,
        None,
        id_evaluacion,
        aciertos,
        total,
        None,
        None,
        None,
        None
    ])
    
    conexion.commit()
    cursor.close()
    


# =====================================
# 3 GUARDAR RESPUESTA
# =====================================
def guardar_respuesta(id_resultado,id_pregunta,id_opcion,respuesta,correcta):
    
    conexion = bd_teacheasy()
    cursor = conexion.cursor()


    cursor.callproc('resultados_abcc',[
        3,
        None,
        None,
        None,
        id_resultado,
        None,
        None,
        None,
        id_pregunta,
        id_opcion,
        respuesta,
        correcta
    ])
    conexion.commit()
    cursor.close()
    


# =====================================
# 4 CONSULTAR TABLA RESULTADOS
# =====================================
def obtener_resultados(id_evaluacion):


    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.callproc('resultados_abcc',[
        4,
        None,
        None,
        None,
        None,
        id_evaluacion,
        None,
        None,
        None,
        None,
        None,
        None
    ])

    for result in cursor.stored_results():
        datos = result.fetchall()
        
    conexion.commit()
    cursor.close()

 

    return datos


# =====================================
# 5 INFORMACION EXAMEN
# =====================================
def info_examen(id_evaluacion):
    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT e.id_evaluacion, e.titulo, ep.estado
        FROM evaluacion e
        JOIN examen_pdf ep ON e.id_evaluacion = ep.id_evaluacion
        WHERE e.id_evaluacion = %s
    """, (id_evaluacion,))

    info = cursor.fetchone()

    cursor.close()
    conexion.close()

    return info

# =====================================
# 6 DATOS GRAFICAS
# =====================================
def datos_graficas(id_evaluacion):

    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)
   

    cursor.callproc('resultados_abcc',[
        6,
        None,
        None,
        None,
        None,
        id_evaluacion,
        None,
        None,
        None,
        None,
        None,
        None
    ])

    for result in cursor.stored_results():
        datos = result.fetchall()

          
    conexion.commit()
    cursor.close()

    return datos


def consultar_grupos():
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.callproc('gestion_grupos', [
                6,  # opción
                None, None, None, None,
                None, None, None,
                None  # OUT
            ])

            grupos = []

            for result in cursor.stored_results():
                grupos = result.fetchall()

            return grupos

        except Exception as e:
            print("Error al consultar grupos:", e)
            return []

        finally:
            cursor.close()
            conexion.close()
            
def consultar_alumnos_por_grupo(id_grupo):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.callproc('gestion_grupos', [
                7,
                id_grupo,
                None, None, None,
                None, None, None,
                None
            ])

            alumnos = []

            for result in cursor.stored_results():
                alumnos = result.fetchall()

            return alumnos

        except Exception as e:
            print("Error alumnos:", e)
            return []

        finally:
            cursor.close()
            conexion.close()
            
def crear_grupo_db(grado, letra, id_maestro):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.callproc('gestion_grupos', [
                1,
                None,
                grado,
                letra,
                id_maestro,
                None, None, None,
                None
            ])

            conexion.commit()
            return True

        except Exception as e:
            print("Error crear grupo:", e)
            return False

        finally:
            cursor.close()
            conexion.close()
            
def agregar_alumno_db(id_grupo, nombre, curp):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.callproc('gestion_grupos', [
                3,
                id_grupo,
                None, None, None,
                None,
                nombre,
                curp,
                None
            ])

            conexion.commit()
            return True

        except Exception as e:
            print("Error agregar alumno:", e)
            return False

        finally:
            cursor.close()
            conexion.close()
            
def eliminar_grupo_db(id_grupo):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.callproc('gestion_grupos', [
                2,
                id_grupo,
                None, None, None,
                None, None, None,
                None
            ])

            conexion.commit()
            return True

        except Exception as e:
            print("Error eliminar grupo:", e)
            return False

        finally:
            cursor.close()
            conexion.close()
            
def eliminar_alumno_db(id_alumno):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.callproc('gestion_grupos', [
                5,
                None,
                None, None, None,
                id_alumno,
                None, None,
                None
            ])

            conexion.commit()
            return True

        except Exception as e:
            print("Error eliminar alumno:", e)
            return False

        finally:
            cursor.close()
            conexion.close()
            
def obtener_maestros():
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_usuario, nombre FROM usuarios WHERE rol='DOCENTE'")
            return cursor.fetchall()

        except Exception as e:
            print("Error maestros:", e)
            return []

        finally:
            cursor.close()
            conexion.close()
            
def actualizar_maestro_grupo_db(id_grupo, id_maestro):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.callproc('gestion_grupos', [
                8,             # p_opcion (ACTUALIZAR MAESTRO)
                id_grupo,      # p_id_grupo
                None, None,   # grado, letra
                id_maestro,    # p_id_maestro
                None,          # p_id_alumno
                None, None,    # nombre, curp
                None           # p_mensaje (OUT)
            ])

            conexion.commit()
            return True

        except Exception as e:
            print("Error actualizar maestro:", e)
            return False

        finally:
            cursor.close()
            conexion.close()
            
def actualizar_alumno_db(id_alumno, nombre, curp):
    conexion = bd_teacheasy()
    if conexion:
        cursor = conexion.cursor()
        try:
            args = [
                9,             # opción
                None,          # id_grupo
                None, None, None,
                id_alumno,
                nombre,
                curp,
                ""
            ]

            resultado = cursor.callproc('gestion_grupos', args)
            mensaje = resultado[-1]

            conexion.commit()

            return True, mensaje

        except Exception as e:
            print("Error actualizar alumno:", e)
            return False, "Error al actualizar alumno"

        finally:
            cursor.close()
            conexion.close()
            
def obtener_alumnos_grupo_evaluacion(id_evaluacion):
    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)

    cursor.callproc("obtener_alumnos_por_evaluacion", [id_evaluacion])

    alumnos = []
    for result in cursor.stored_results():
        alumnos = result.fetchall()

    cursor.close()
    conexion.close()

    print("ALUMNOS:", alumnos)  # 🔥 DEBUG
    return alumnos


def guardar_resultado(id_alumno, id_evaluacion, aciertos, total, fecha):
    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    cursor.callproc("guardar_resultados_evaluacion", [
        id_alumno,
        id_evaluacion,
        aciertos,
        total,
        fecha
    ])

    conexion.commit()
    cursor.close()
    conexion.close()
    
def obtener_resultados(id_evaluacion):
    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)

    cursor.callproc("obtener_resultados_evaluacion", [id_evaluacion])

    resultados = []
    for result in cursor.stored_results():
        resultados = result.fetchall()

    cursor.close()
    conexion.close()
    return resultados

def obtener_total_preguntas(id_evaluacion):
    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)

    cursor.callproc("obtener_total_preguntas_eval", [id_evaluacion])

    total = 0
    for result in cursor.stored_results():
        data = result.fetchone()
        total = data["total"] if data else 0

    cursor.close()
    conexion.close()
    return total

def obtener_grupo_docente(id_usuario):
    conexion = bd_teacheasy()
    cursor = conexion.cursor(dictionary=True)

    cursor.callproc("obtener_grupo_docente", [id_usuario])

    grupo = None
    for result in cursor.stored_results():
        grupo = result.fetchone()

    cursor.close()
    conexion.close()
    return grupo

def obtener_evaluaciones_admin(id_docente=None, id_grupo=None):

    conexion = bd_teacheasy() # tu conexión
    cursor = conexion.cursor()

    cursor.callproc("obtener_evaluaciones_admin", (id_docente, id_grupo))

    resultados = []

    for result in cursor.stored_results():
        for row in result.fetchall():
            resultados.append({
                "id_pdf": row[0],
                "id_evaluacion": row[1],
                "nombre": row[2],
                "ruta": row[3],
                "fecha": row[4],
                "estado": row[5],
                "docente": row[6],
                "grupo": row[7]
            })

    cursor.close()
    conexion.close()

    return resultados

def obtener_docentes():

    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_usuario, nombre 
        FROM usuarios 
        WHERE rol = 'DOCENTE'
    """)

    datos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return datos

def obtener_grupos():

    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_grupo, CONCAT(grado, ' ', letra) 
        FROM grupos
    """)

    datos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return datos

def votar_recurso(id_usuario, id_recurso):
    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    cursor.callproc("votar_recurso", (id_usuario, id_recurso))

    conexion.commit()

    cursor.close()
    conexion.close()
    
    
def cambiar_password_bd(correo, nueva_password):
    conexion = bd_teacheasy()
    cursor = conexion.cursor()

    try:
        resultado = cursor.callproc('inicio_abcc', [
            3, None, None, correo, nueva_password, None, None,
            0, '', 0, '', '', ''
        ])

        p_valido = resultado[7]
        p_mensaje = resultado[8]

        if p_valido == 1:
            conexion.commit()
            return True, p_mensaje
        else:
            return False, p_mensaje

    except Exception as e:
        print(e)
        return False, "Error en base de datos"

    finally:
        cursor.close()
        conexion.close()