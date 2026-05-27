from datetime import datetime
from mysql.connector import Error
from backend.conexion import obtener_conexion

def obtener_todos_beneficiarios():
    """Trae la lista completa de beneficiarios ordenada alfabéticamente."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM beneficiarios ORDER BY apellidos ASC")
            return cursor.fetchall()
    except Error as e: 
        print(f"Error al obtener beneficiarios: {e}")
        return []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def insertar_beneficiarios_masivo(lista_beneficiarios):
    """Inserta nuevos alumnos desde Excel o actualiza campos clave si el DNI ya existía."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            consulta = '''
                INSERT INTO beneficiarios (apellidos, nombres, dni, lu, telefono, carrera, correo, pan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                apellidos=VALUES(apellidos), nombres=VALUES(nombres), telefono=VALUES(telefono), 
                carrera=VALUES(carrera), correo=VALUES(correo), pan=VALUES(pan)
            '''
            cursor.executemany(consulta, lista_beneficiarios)
            conexion.commit()
            return True, cursor.rowcount
    except Error as e: 
        return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def asociar_foto_beneficiario(dni, ruta_completa):
    """Cruza y asigna la ruta del archivo de imagen al alumno que coincida con su DNI."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("UPDATE beneficiarios SET ruta_foto = %s WHERE dni = %s", (ruta_completa, dni))
            conexion.commit()
            return cursor.rowcount > 0
    except Error as e: 
        print(f"Error asociando foto por DNI: {e}")
        return False
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def aplicar_penalizacion_db(lu_beneficiario, razon, horas_penalidad, lu_usuario_penaliza):
    """Cambia el estado a penalizado (con horas) e inserta una fila de auditoría."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 1. Bloquear al alumno y setear sus horas (-1 será indefinido)
            cursor.execute('''
                UPDATE beneficiarios 
                SET penalizado = TRUE, cant_penalizaciones = cant_penalizaciones + 1, horas_penalizacion = %s
                WHERE lu = %s
            ''', (horas_penalidad, lu_beneficiario))
            
            # 2. Guardar justificación en tabla histórica
            cursor.execute('''
                INSERT INTO historial_penalizaciones_beneficiarios (lu_beneficiario, fecha_penalizacion, razon, lu_usuario_penaliza)
                VALUES (%s, %s, %s, %s)
            ''', (lu_beneficiario, ahora, razon, lu_usuario_penaliza))
            
            conexion.commit()
            return True
    except Error as e: 
        print(f"Error en transacción de penalización: {e}")
        return False
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def aplicar_despenalizacion_db(lu_beneficiario, razon, lu_usuario_penaliza):
    """Devuelve el permiso de préstamo al alumno y cierra su registro de sanción activo."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Levantar sanción en la tabla maestra
            cursor.execute('UPDATE beneficiarios SET penalizado = FALSE WHERE lu = %s', (lu_beneficiario,))
            
            # Buscar la sanción abierta y estampar la fecha de cierre de sanción
            cursor.execute('''
                UPDATE historial_penalizaciones_beneficiarios 
                SET fecha_despenalizacion = %s, razon = CONCAT(razon, ' | DESPENALIZACIÓN: ', %s)
                WHERE lu_beneficiario = %s AND fecha_despenalizacion IS NULL
                ORDER BY id DESC LIMIT 1
            ''', (ahora, razon, lu_beneficiario))
            
            conexion.commit()
            return True
    except Error as e: 
        print(f"Error en transacción de despenalización: {e}")
        return False
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def crear_usuario_comision(lu_usuario):
    """Registra las credenciales iniciales de un alumno para que pueda iniciar sesión."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute('''
                INSERT INTO usuarios_comision (lu_usuario, contrasena) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE lu_usuario=lu_usuario
            ''', (lu_usuario, lu_usuario))
            conexion.commit()
            return True
    except Error as e: 
        print(f"Error en alta de permisos de comisión: {e}")
        return False
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def obtener_motivo_sancion_activa(lu_beneficiario):
    """Busca la razón de la última penalización que aún no fue perdonada."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute('''
                SELECT razon FROM historial_penalizaciones_beneficiarios 
                WHERE lu_beneficiario = %s AND fecha_despenalizacion IS NULL 
                ORDER BY id DESC LIMIT 1
            ''', (lu_beneficiario,))
            resultado = cursor.fetchone()
            return resultado['razon'] if resultado else "Razón no especificada."
    except Error as e:
        return "Error al leer la razón."
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()