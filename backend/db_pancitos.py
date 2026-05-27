from datetime import datetime
from mysql.connector import Error
from backend.conexion import obtener_conexion

def obtener_stock_hoy():
    """Calcula matemáticamente cuántos panes quedan de los 100 diarios."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            hoy = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM historial_pancitos WHERE fecha = %s AND entrego_pancito = TRUE", (hoy,))
            entregados = cursor.fetchone()[0]
            # Si se dieron 20, quedan 80. Nunca menos de 0.
            return max(0, 100 - entregados)
    except Error as e: print(f"Error al obtener stock de pan: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return 0

def buscar_beneficiario_pan(criterio):
    """Busca al alumno por LU o DNI."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM beneficiarios WHERE lu = %s OR dni = %s", (criterio, criterio))
            return cursor.fetchone()
    except Error as e: print(f"Error al buscar alumno: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return None

def ya_recibio_hoy(lu_beneficiario):
    """Verifica si el alumno ya retiró su pan en la fecha actual."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            hoy = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT id FROM historial_pancitos WHERE lu_beneficiario = %s AND fecha = %s AND entrego_pancito = TRUE", (lu_beneficiario, hoy))
            return cursor.fetchone() is not None
    except Error as e: print(f"Error al comprobar entrega: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return False

def entregar_pancito(lu_admin, lu_beneficiario, apellido, nombre):
    """Registra la entrega en el historial y le suma 1 al contador del alumno."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            if obtener_stock_hoy() <= 0:
                return False, "Se agotó el stock de 100 pancitos por hoy."
            
            if ya_recibio_hoy(lu_beneficiario):
                return False, "El alumno ya recibió su beneficio hoy."

            cursor = conexion.cursor()
            ahora = datetime.now()
            fecha = ahora.strftime('%Y-%m-%d')
            hora = ahora.strftime('%H:%M:%S')

            # 1. Registrar en el historial de pancitos
            cursor.execute('''
                INSERT INTO historial_pancitos 
                (lu_usuario, lu_beneficiario, apellido_beneficiario, nombre_beneficiario, fecha, hora, entrego_pancito)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            ''', (lu_admin, lu_beneficiario, apellido, nombre, fecha, hora))

            # 2. Sumarle el pan al contador global del alumno
            cursor.execute("UPDATE beneficiarios SET pan = pan + 1 WHERE lu = %s", (lu_beneficiario,))

            conexion.commit()
            return True, "Pan entregado correctamente."
    except Error as e: 
        return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def obtener_historial_hoy():
    """Trae solo los movimientos de la fecha actual."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            hoy = datetime.now().strftime('%Y-%m-%d')
            # Ordenamos por hora descendente (el más reciente arriba)
            cursor.execute("SELECT * FROM historial_pancitos WHERE fecha = %s ORDER BY hora DESC", (hoy,))
            return cursor.fetchall()
    except Error as e: print(f"Error historial pancitos: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return []