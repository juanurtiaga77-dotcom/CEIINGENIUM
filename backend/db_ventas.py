from datetime import datetime, timedelta
from mysql.connector import Error
from backend.conexion import obtener_conexion

# --- FUNCIONES DE AUDITORÍA Y CAJA ---
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
    ''', (detalle, tipo_edicion, apellidos, nombres, lu_usuario, ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S')))

def obtener_estado_caja(conexion=None):
    """Devuelve los valores actuales de la caja."""
    cerrar_aqui = False
    if not conexion:
        conexion = obtener_conexion()
        cerrar_aqui = True
        
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT caja_efectivo, caja_transferencia, caja_total FROM historial_caja_ventas ORDER BY id DESC LIMIT 1")
        ultima = cursor.fetchone()
        if ultima:
            return float(ultima['caja_efectivo']), float(ultima['caja_transferencia']), float(ultima['caja_total'])
        return 0.0, 0.0, 0.0
    finally:
        if cerrar_aqui and conexion.is_connected(): conexion.close()

def registrar_movimiento_caja(lu_usuario, e_efe, e_trans, s_efe, s_trans, tipo_edicion, detalle):
    """Registra entradas o salidas manuales de caja (Extraer/Agregar)."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            c_efe, c_trans, c_tot = obtener_estado_caja(conexion)
            
            n_efe = c_efe + e_efe - s_efe
            n_trans = c_trans + e_trans - s_trans
            n_tot = n_efe + n_trans
            
            ahora = datetime.now()
            cursor = conexion.cursor()
            cursor.execute('''
                INSERT INTO historial_caja_ventas 
                (lu_usuario, fecha_cierre, entrada_efectivo, entrada_transferencia, salida_efectivo, salida_transferencia, caja_efectivo, caja_transferencia, caja_total)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (lu_usuario, ahora.strftime('%Y-%m-%d'), e_efe, e_trans, s_efe, s_trans, n_efe, n_trans, n_tot))
            
            registrar_historial_edicion(conexion, cursor, lu_usuario, tipo_edicion, detalle)
            conexion.commit()
            return True, ""
    except Error as e: return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

# --- FUNCIONES DE VENTAS ---
def obtener_articulos_venta():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM objetos_ventas WHERE stock > 0 ORDER BY veces_vendido DESC")
            return cursor.fetchall()
    except Error as e: print(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return []

def registrar_venta(lu_usuario, carrito, forma_pago, total, pago_efectivo, pago_transf):
    """Guarda la venta, descuenta stock y suma a la caja."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            ahora = datetime.now()
            fecha = ahora.strftime('%Y-%m-%d')
            hora = ahora.strftime('%H:%M:%S')
            
            # 1. Armar texto de artículos y descontar stock
            texto_articulos = []
            for item in carrito.values():
                texto_articulos.append(f"{item['articulo']} x{item['cant']}")
                cursor.execute("UPDATE objetos_ventas SET stock = stock - %s, veces_vendido = veces_vendido + %s WHERE id = %s", 
                               (item['cant'], item['cant'], item['id']))
                
            str_articulos = ", ".join(texto_articulos)
            
            # 2. Registrar en historial_ventas
            cursor.execute('''
                INSERT INTO historial_ventas (lu_usuario, fecha, hora, articulos_y_cantidades, forma_pago, total)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (lu_usuario, fecha, hora, str_articulos, forma_pago, total))
            id_venta = cursor.lastrowid
            
            # 3. Registrar en Caja
            c_efe, c_trans, _ = obtener_estado_caja(conexion)
            n_efe = c_efe + pago_efectivo
            n_trans = c_trans + pago_transf
            cursor.execute('''
                INSERT INTO historial_caja_ventas 
                (lu_usuario, fecha_cierre, entrada_efectivo, entrada_transferencia, salida_efectivo, salida_transferencia, caja_efectivo, caja_transferencia, caja_total)
                VALUES (%s, %s, %s, %s, 0, 0, %s, %s, %s)
            ''', (lu_usuario, fecha, pago_efectivo, pago_transf, n_efe, n_trans, n_efe + n_trans))
            
            conexion.commit()
            return True, id_venta
    except Error as e: return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def revertir_venta(id_venta, carrito, pago_efectivo, pago_transf, lu_usuario):
    """Anula una venta (Deshacer): Devuelve stock, saca plata de caja y borra el registro."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            
            # 1. Devolver Stock
            for item in carrito.values():
                cursor.execute("UPDATE objetos_ventas SET stock = stock + %s, veces_vendido = veces_vendido - %s WHERE id = %s", 
                               (item['cant'], item['cant'], item['id']))
            
            # 2. Borrar del historial
            cursor.execute("DELETE FROM historial_ventas WHERE id = %s", (id_venta,))
            
            # 3. Restar de la caja (Salida)
            c_efe, c_trans, _ = obtener_estado_caja(conexion)
            n_efe = c_efe - pago_efectivo
            n_trans = c_trans - pago_transf
            ahora = datetime.now()
            cursor.execute('''
                INSERT INTO historial_caja_ventas 
                (lu_usuario, fecha_cierre, entrada_efectivo, entrada_transferencia, salida_efectivo, salida_transferencia, caja_efectivo, caja_transferencia, caja_total)
                VALUES (%s, %s, 0, 0, %s, %s, %s, %s, %s)
            ''', (lu_usuario, ahora.strftime('%Y-%m-%d'), pago_efectivo, pago_transf, n_efe, n_trans, n_efe + n_trans))
            
            conexion.commit()
            return True
    except Error as e: print(f"Error al revertir: {e}"); return False
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def obtener_historial_48h():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            # Solo muestra las de las últimas 48 horas
            query = "SELECT * FROM historial_ventas WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 2 DAY) ORDER BY id DESC"
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e: print(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return []