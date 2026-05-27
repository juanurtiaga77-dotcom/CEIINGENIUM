from datetime import datetime
from mysql.connector import Error
from backend.conexion import obtener_conexion

def registrar_historial(conexion, cursor_principal, lu_usuario, tipo_edicion):
    """
    Busca los datos del administrador y registra el movimiento 
    exactamente con las columnas que exige la tabla 'historial_edicion'.
    """
    # 1. Buscar el nombre y apellido del usuario que está haciendo el cambio
    cursor_aux = conexion.cursor()
    cursor_aux.execute("SELECT nombres, apellidos FROM beneficiarios WHERE lu = %s", (lu_usuario,))
    usuario = cursor_aux.fetchone()
    cursor_aux.close()
    
    nombres = usuario[0] if usuario else "Desconocido"
    apellidos = usuario[1] if usuario else "Desconocido"
    
    # 2. Separar fecha y hora
    ahora = datetime.now()
    fecha = ahora.strftime('%Y-%m-%d')
    hora = ahora.strftime('%H:%M:%S')
    
    # 3. Insertar en tu tabla historial_edicion con tus nombres de columnas exactos
    cursor_principal.execute('''
        INSERT INTO historial_edicion 
        (nombre_tabla, tipo_edicion, apellido_usuario, nombre_usuario, lu_usuario, fecha, hora)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', ("objetos_prestamos", tipo_edicion, apellidos, nombres, lu_usuario, fecha, hora))


def obtener_todos_objetos():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM objetos_prestamos ORDER BY nombre_objeto ASC")
            return cursor.fetchall()
    except Error as e: 
        print(f"Error al obtener objetos: {e}")
        return []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()

def agregar_objeto(nombre_objeto, cantidad_total, cantidad_disponibles, en_prestamo, veces_prestado, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute('''
                INSERT INTO objetos_prestamos (nombre_objeto, cantidad_total, cantidad_disponibles, en_prestamo, veces_prestado)
                VALUES (%s, %s, %s, %s, %s)
            ''', (nombre_objeto, cantidad_total, cantidad_disponibles, en_prestamo, veces_prestado))
            
            # Registramos en el historial usando la nueva función adaptada
            registrar_historial(conexion, cursor, lu_usuario, "AGREGAR OBJETO")
            
            conexion.commit()
            return True, "Objeto agregado correctamente."
    except Error as e: 
        return False, f"Error al agregar (¿El objeto ya existe?): {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()

def editar_objeto(id_objeto, nombre_objeto, cantidad_total, cantidad_disponibles, en_prestamo, veces_prestado, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute('''
                UPDATE objetos_prestamos 
                SET nombre_objeto=%s, cantidad_total=%s, cantidad_disponibles=%s, en_prestamo=%s, veces_prestado=%s
                WHERE id=%s
            ''', (nombre_objeto, cantidad_total, cantidad_disponibles, en_prestamo, veces_prestado, id_objeto))
            
            registrar_historial(conexion, cursor, lu_usuario, "EDITAR OBJETO")
            
            conexion.commit()
            return True, "Objeto editado correctamente."
    except Error as e: 
        return False, f"Error al editar: {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()

def eliminar_objeto(id_objeto, nombre_objeto, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM objetos_prestamos WHERE id=%s", (id_objeto,))
            
            registrar_historial(conexion, cursor, lu_usuario, "ELIMINAR OBJETO")
            
            conexion.commit()
            return True, "Objeto eliminado permanentemente."
    except Error as e: 
        return False, f"Error al eliminar: {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()

def procesar_excel_masivo(lista_datos, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            consulta = '''
                INSERT INTO objetos_prestamos (nombre_objeto, cantidad_total, cantidad_disponibles, en_prestamo, veces_prestado)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                cantidad_total=VALUES(cantidad_total), cantidad_disponibles=VALUES(cantidad_disponibles), 
                en_prestamo=VALUES(en_prestamo), veces_prestado=VALUES(veces_prestado)
            '''
            cursor.executemany(consulta, lista_datos)
            
            registrar_historial(conexion, cursor, lu_usuario, "IMPORTAR EXCEL MASIVO")
            
            conexion.commit()
            return True, cursor.rowcount
    except Error as e: 
        return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()