from datetime import datetime
from mysql.connector import Error
from backend.conexion import obtener_conexion

def registrar_historial(conexion, cursor_principal, lu_usuario, tipo_edicion):
    cursor_aux = conexion.cursor()
    cursor_aux.execute("SELECT nombres, apellidos FROM beneficiarios WHERE lu = %s", (lu_usuario,))
    usuario = cursor_aux.fetchone()
    cursor_aux.close()
    
    nombres = usuario[0] if usuario else "Desconocido"
    apellidos = usuario[1] if usuario else "Desconocido"
    
    ahora = datetime.now()
    fecha = ahora.strftime('%Y-%m-%d')
    hora = ahora.strftime('%H:%M:%S')
    
    cursor_principal.execute('''
        INSERT INTO historial_edicion 
        (nombre_tabla, tipo_edicion, apellido_usuario, nombre_usuario, lu_usuario, fecha, hora)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', ("objetos_ventas", tipo_edicion, apellidos, nombres, lu_usuario, fecha, hora))

def obtener_todos_articulos():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM objetos_ventas ORDER BY articulo ASC")
            return cursor.fetchall()
    except Error as e: 
        print(f"Error al obtener artículos: {e}")
        return []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()

def agregar_articulo(articulo, precio, stock, reponer_stock, veces_vendido, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute('''
                INSERT INTO objetos_ventas (articulo, precio, stock, reponer_stock, veces_vendido)
                VALUES (%s, %s, %s, %s, %s)
            ''', (articulo, precio, stock, reponer_stock, veces_vendido))
            
            registrar_historial(conexion, cursor, lu_usuario, "AGREGAR ARTICULO")
            conexion.commit()
            return True, "Artículo registrado correctamente."
    except Error as e: 
        return False, f"Error al agregar (¿El artículo ya existe?): {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()

def editar_articulo(id_articulo, articulo, precio, stock, reponer_stock, veces_vendido, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute('''
                UPDATE objetos_ventas 
                SET articulo=%s, precio=%s, stock=%s, reponer_stock=%s, veces_vendido=%s
                WHERE id=%s
            ''', (articulo, precio, stock, reponer_stock, veces_vendido, id_articulo))
            
            registrar_historial(conexion, cursor, lu_usuario, "EDITAR ARTICULO")
            conexion.commit()
            return True, "Artículo actualizado correctamente."
    except Error as e: 
        return False, f"Error al editar: {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()

def reponer_stock_db(id_articulo, cantidad_a_reponer, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute('''
                UPDATE objetos_ventas 
                SET stock = stock + %s 
                WHERE id = %s
            ''', (cantidad_a_reponer, id_articulo))
            
            registrar_historial(conexion, cursor, lu_usuario, f"REPONER STOCK (+{cantidad_a_reponer})")
            conexion.commit()
            return True, "Stock reabastecido correctamente."
    except Error as e: 
        return False, f"Error al reponer stock: {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()

def eliminar_articulo(id_articulo, nombre_articulo, lu_usuario):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM objetos_ventas WHERE id=%s", (id_articulo,))
            
            registrar_historial(conexion, cursor, lu_usuario, f"ELIMINAR ARTICULO ({nombre_articulo})")
            conexion.commit()
            return True, "Artículo eliminado de los registros."
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
                INSERT INTO objetos_ventas (articulo, precio, stock, reponer_stock, veces_vendido)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                precio=VALUES(precio), stock=VALUES(stock), 
                reponer_stock=VALUES(reponer_stock), veces_vendido=VALUES(veces_vendido)
            '''
            cursor.executemany(consulta, lista_datos)
            registrar_historial(conexion, cursor, lu_usuario, "IMPORTAR EXCEL LIBRERIA")
            conexion.commit()
            return True, cursor.rowcount
    except Error as e: 
        return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close(); conexion.close()