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
    ''', ("objetos_guardados", tipo_edicion, apellidos, nombres, lu_usuario, ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S')))

def obtener_todos_guardados():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            # Trae los datos uniendo la tabla con beneficiarios para sacar Nombre y Apellido
            query = '''
                SELECT g.*, b.apellidos, b.nombres 
                FROM objetos_guardados g
                LEFT JOIN beneficiarios b ON g.lu_beneficiario = b.lu
                ORDER BY g.fecha_entrega IS NULL DESC, g.fecha_registro DESC, g.hora_registro DESC
            '''
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e: print(f"Error al obtener elementos guardados: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): cursor.close(); conexion.close()
    return []

def registrar_elemento_guardado(lu_beneficiario, tipo_item, descripcion, lugar, lu_admin):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            ahora = datetime.now()
            
            cursor.execute('''
                INSERT INTO objetos_guardados 
                (lu_beneficiario, lu_usuario_registra, tipo_item, descripcion, lugar_guardado, fecha_registro, hora_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (lu_beneficiario, lu_admin, tipo_item, descripcion, lugar, ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S')))
            
            registrar_historial_edicion(conexion, cursor, lu_admin, "REGISTRO DEPOSITO", f"{tipo_item}: {descripcion[:30]}")
            conexion.commit()
            return True, "Elemento guardado en el sistema con éxito."
    except Error as e: return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): cursor.close(); conexion.close()

def consolidar_entrega_db(id_guardado, lu_admin):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            ahora = datetime.now()
            
            cursor.execute('''
                UPDATE objetos_guardados 
                SET lu_usuario_entrega = %s, fecha_entrega = %s, hora_entrega = %s
                WHERE id = %s
            ''', (lu_admin, ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S'), id_guardado))
            
            registrar_historial_edicion(conexion, cursor, lu_admin, "ENTREGA DEPOSITO", f"ID Registro: {id_guardado}")
            conexion.commit()
            return True
    except Error as e: print(f"Error al consolidar entrega: {e}"); return False
    finally:
        if 'conexion' in locals() and conexion.is_connected(): cursor.close(); conexion.close()

def deshacer_entrega_db(id_guardado, lu_admin):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            # Devolvemos el estado a activo (NULL)
            cursor.execute('''
                UPDATE objetos_guardados 
                SET lu_usuario_entrega = NULL, fecha_entrega = NULL, hora_entrega = NULL
                WHERE id = %s
            ''', (id_guardado,))
            
            registrar_historial_edicion(conexion, cursor, lu_admin, "DESHACER ENTREGA DEPOSITO", f"ID Registro: {id_guardado}")
            conexion.commit()
            return True
    except Error as e: print(f"Error al deshacer entrega: {e}"); return False
    finally:
        if 'conexion' in locals() and conexion.is_connected(): cursor.close(); conexion.close()