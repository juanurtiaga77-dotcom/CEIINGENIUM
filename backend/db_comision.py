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

def obtener_todos_beneficiarios():
    """Trae la lista de todos los beneficiarios para mostrar su estado y cargo en configuración."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = '''
                SELECT lu, apellidos, nombres, cargo, penalizado, carrera
                FROM beneficiarios
                ORDER BY apellidos ASC, nombres ASC
            '''
            cursor.execute(consulta)
            return cursor.fetchall()
    except Error as e: 
        print(f"Error al obtener todos los beneficiarios: {e}")
        return []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def buscar_beneficiario_por_lu(lu):
    """Busca un beneficiario específico por LU para edición de cargo."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT lu, apellidos, nombres, cargo, penalizado FROM beneficiarios WHERE lu = %s", (lu,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error al buscar beneficiario por LU: {e}")
        return None
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def actualizar_cargo_beneficiario(lu, nuevo_cargo):
    """Actualiza el cargo de un beneficiario y gestiona su acceso a la comisión si corresponde."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            
            # 1. Actualizar el cargo en beneficiarios
            cursor.execute("UPDATE beneficiarios SET cargo = %s WHERE lu = %s", (nuevo_cargo, lu))
            
            # 2. Gestionar su cuenta en usuarios_comision
            nuevo_cargo_clean = nuevo_cargo.lower().strip()
            cargos_comision_clean = [
                'presidenta del cei', 'presidencia',
                'atención', 'atencion',
                'comisión', 'comision',
                'recursos humanos',
                'informática', 'informatica',
                'asienda', 'hacienda'
            ]
            
            # Verificar si ya existe en usuarios_comision
            cursor.execute("SELECT COUNT(*) FROM usuarios_comision WHERE lu_usuario = %s", (lu,))
            existe = cursor.fetchone()[0]
            
            if nuevo_cargo_clean in cargos_comision_clean:
                if not existe:
                    # Si no existe, lo agregamos con su LU como contraseña por defecto
                    cursor.execute("INSERT INTO usuarios_comision (lu_usuario, contrasena) VALUES (%s, %s)", (lu, lu))
            else:
                # Si el nuevo cargo es Estudiante u otro rol sin acceso, lo removemos de usuarios_comision
                if existe:
                    cursor.execute("DELETE FROM usuarios_comision WHERE lu_usuario = %s", (lu,))
            
            conexion.commit()
            return True, "Cargo actualizado correctamente."
    except Error as e:
        print(f"Error al actualizar cargo: {e}")
        return False, f"Error de base de datos: {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()