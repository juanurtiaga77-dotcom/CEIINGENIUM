from datetime import datetime
from mysql.connector import Error
from backend.conexion import obtener_conexion

def registrar_historial_edicion(conexion, cursor_principal, lu_usuario, tipo_edicion, detalle):
    cursor_aux = conexion.cursor()
    cursor_aux.execute("SELECT nombres, apellidos FROM beneficiarios WHERE lu = %s", (lu_usuario,))
    u = cursor_aux.fetchone()
    cursor_aux.close()
    
    nombres = u[0] if u else "Desconocido"
    apellidos = u[1] if u else "Desconocido"
    ahora = datetime.now()
    
    cursor_principal.execute('''
        INSERT INTO historial_edicion 
        (nombre_tabla, tipo_edicion, apellido_usuario, nombre_usuario, lu_usuario, fecha, hora)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', ("objetos_perdidos", tipo_edicion, apellidos, nombres, lu_usuario, ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S')))

def obtener_objetos_perdidos():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM objetos_perdidos ORDER BY fecha_registro DESC, hora_registro DESC")
            return cursor.fetchall()
    except Error as e: print(f"Error obtener perdidos: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return []

def agregar_objeto_perdido(datos_persona, fecha_enc, hora_enc, desc, lugar_enc, ubicacion_cei, ruta_foto, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            ahora = datetime.now()
            fecha_reg = ahora.strftime('%Y-%m-%d')
            hora_reg = ahora.strftime('%H:%M:%S')
            
            # SE AÑADIÓ lu_usuario A LA CONSULTA SQL
            cursor.execute('''
                INSERT INTO objetos_perdidos 
                (lu_usuario, datos_persona_encuentra, fecha_encuentro, hora_encuentro, descripcion_objeto, 
                 lugar_encuentro, ubicacion_en_cei, fecha_registro, hora_registro, ruta_foto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (lu_usuario, datos_persona, fecha_enc, hora_enc, desc, lugar_enc, ubicacion_cei, fecha_reg, hora_reg, ruta_foto))
            
            registrar_historial_edicion(conexion, cursor, lu_usuario, "REGISTRO OBJETO PERDIDO", desc[:40])
            conexion.commit()
            return True, "Objeto registrado."
    except Error as e: return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def eliminar_perdido_db(id_objeto, lu_usuario, descripcion):
    """Elimina el objeto permanentemente de la tabla (fue devuelto a su dueño)."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM objetos_perdidos WHERE id = %s", (id_objeto,))
            registrar_historial_edicion(conexion, cursor, lu_usuario, "DEVOLUCION OBJETO PERDIDO", descripcion[:40])
            conexion.commit()
            return True
    except Error as e: print(f"Error al eliminar perdido: {e}"); return False
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()