from datetime import datetime
from mysql.connector import Error
from backend.conexion import obtener_conexion

def verificar_login(lu, pw):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            
            # 1. Verificar si las credenciales coinciden
            cursor.execute("SELECT * FROM usuarios_comision WHERE lu_usuario = %s AND contrasena = %s", (lu, pw))
            usuario = cursor.fetchone()
            
            if usuario:
                # 2. REGISTRAR EL INICIO DE SESIÓN EN EL HISTORIAL
                ahora = datetime.now()
                fecha_str = ahora.strftime('%Y-%m-%d')
                hora_str = ahora.strftime('%H:%M:%S')
                
                cursor.execute('''
                    INSERT INTO historial_inicio_sesion (lu_usuario, fecha_inicio, hora_inicio) 
                    VALUES (%s, %s, %s)
                ''', (lu, fecha_str, hora_str))
                conexion.commit()

                # 3. Buscar la foto, el NOMBRE COMPLETO y el CARGO en la tabla beneficiarios
                cursor.execute("SELECT ruta_foto, nombres, apellidos, cargo FROM beneficiarios WHERE lu = %s", (lu,))
                b = cursor.fetchone()
                
                ruta_foto = b['ruta_foto'] if b else None
                cargo = b['cargo'] if (b and 'cargo' in b and b['cargo']) else 'Estudiante'
                
                # Armamos el nombre que aparecerá arriba a la derecha
                if b and b['nombres'] and b['apellidos']:
                    nombre_completo = f"{b['nombres']} {b['apellidos']}"
                else:
                    nombre_completo = f"Usuario {lu}"
                
                # Devolvemos True, el nombre real, la foto y el cargo
                return True, nombre_completo, ruta_foto, cargo
            else:
                return False, "LU o contraseña incorrectos", None, 'Estudiante'
    except Error as e:
        return False, f"Error de base de datos: {e}", None, 'Estudiante'
    finally:
        if 'conexion' in locals() and conexion.is_connected(): cursor.close(); conexion.close()

def actualizar_contrasena(lu, nueva_pass):
    """Actualiza la contraseña del usuario en la base de datos."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("UPDATE usuarios_comision SET contrasena = %s WHERE lu_usuario = %s", (nueva_pass, lu))
            conexion.commit()
            return True
    except Error as e:
        print(f"Error al cambiar contraseña: {e}")
        return False
    finally:
        if 'conexion' in locals() and conexion.is_connected(): cursor.close(); conexion.close()

def registrar_cierre_sesion(lu_usuario, horas_totales):
    """Calcula y rellena la salida del historial y actualiza el acumulador del usuario."""
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            ahora = datetime.now()
            
            # Actualiza el registro NULL más reciente de la sesión
            cursor.execute(
                'UPDATE historial_inicio_sesion SET fecha_cierre = %s, hora_cierre = %s, cantidad_horas = %s WHERE lu_usuario = %s AND fecha_cierre IS NULL ORDER BY id DESC LIMIT 1', 
                (ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S'), round(horas_totales, 2), lu_usuario)
            )
            
            # Suma las horas trabajadas en el perfil de la comisión
            cursor.execute(
                'UPDATE usuarios_comision SET horas_logueado = horas_logueado + %s WHERE lu_usuario = %s', 
                (round(horas_totales, 2), lu_usuario)
            )
            conexion.commit()
    except Error as e: 
        print(f"Error al cerrar sesión de auditoría: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()