import random
import string
from mysql.connector import Error
from backend.conexion import obtener_conexion

def obtener_usuarios_comision():
    """Trae la lista de usuarios. Ahora también lee la contraseña para saber si están bloqueados."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = '''
                SELECT c.lu_usuario as lu, c.contrasena, b.apellidos, b.nombres, 
                       c.num_prestamos, c.num_recibidos, c.horas_logueado
                FROM usuarios_comision c
                INNER JOIN beneficiarios b ON c.lu_usuario = b.lu
                ORDER BY b.apellidos ASC
            '''
            cursor.execute(consulta)
            return cursor.fetchall()
    except Error as e: 
        print(f"Error al obtener usuarios de comisión: {e}")
        return []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def deshabilitar_usuario(lu_usuario):
    """Bloquea el acceso cambiando la clave por algo aleatorio con el prefijo BLOQUEADO_"""
    try:
        # Generamos 8 caracteres aleatorios
        letras_random = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        clave_bloqueo = f"BLOQUEADO_{letras_random}"
        
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("UPDATE usuarios_comision SET contrasena = %s WHERE lu_usuario = %s", (clave_bloqueo, lu_usuario))
            conexion.commit()
            return cursor.rowcount > 0
    except Error as e: 
        return False
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def habilitar_usuario(lu_usuario):
    """Restaura el acceso volviendo a poner su LU como contraseña."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("UPDATE usuarios_comision SET contrasena = %s WHERE lu_usuario = %s", (lu_usuario, lu_usuario))
            conexion.commit()
            return cursor.rowcount > 0
    except Error as e: 
        return False
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def resetear_contrasena_comision(lu_usuario):
    """Esta función ahora hace exactamente lo mismo que habilitar_usuario"""
    return habilitar_usuario(lu_usuario)