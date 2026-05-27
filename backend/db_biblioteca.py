from datetime import datetime, timedelta
from mysql.connector import Error
from backend.conexion import obtener_conexion

def buscar_libros_disponibles():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM libros WHERE disponible > 0 ORDER BY veces_prestado DESC")
            return cursor.fetchall()
    except Error as e: print(e); return []
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def prestar_libro(lu_bene, id_libro, nombre_libro, lu_admin):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT prestamos_activos, apellidos, nombres, penalizado FROM beneficiarios WHERE lu = %s", (lu_bene,))
            b = cursor.fetchone()
            if not b: return False, "Beneficiario no encontrado."
            if b['penalizado']: return False, "El alumno está penalizado."
            
            cursor.execute("SELECT apellidos, nombres FROM beneficiarios WHERE lu = %s", (lu_admin,))
            admin = cursor.fetchone()
            ahora = datetime.now()
            
            cursor.execute('''
                INSERT INTO historial_biblioteca 
                (lu_usuario_presta, apellidos_presta, nombres_presta, id_libro, nombre_libro, apellidos_beneficiario, nombres_beneficiario, lu_beneficiario, fecha_prestamo, hora_prestamo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (lu_admin, admin['apellidos'], admin['nombres'], id_libro, nombre_libro, b['apellidos'], b['nombres'], lu_bene, ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S')))

            cursor.execute("UPDATE libros SET disponible = disponible - 1, veces_prestado = veces_prestado + 1 WHERE id = %s", (id_libro,))
            conexion.commit()
            return True, "Libro prestado exitosamente."
    except Error as e: return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def obtener_historial_biblio(filtro=""):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            q = "SELECT * FROM historial_biblioteca WHERE devuelto IS NULL OR fecha_devolucion = %s"
            p = [datetime.now().strftime('%Y-%m-%d')]
            if filtro: q += " AND lu_beneficiario LIKE %s"; p.append(f"%{filtro}%")
            q += " ORDER BY fecha_prestamo DESC, hora_prestamo DESC"
            cursor.execute(q, tuple(p))
            return cursor.fetchall()
    except: return []
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def consolidar_devolucion_biblio(id_p, lu_admin, danado, fecha_real=None):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM historial_biblioteca WHERE id = %s", (id_p,))
            p = cursor.fetchone()
            if not p or p['devuelto']: return False

            ahora = fecha_real if fecha_real else datetime.now()
            dt_prestamo = datetime.combine(p['fecha_prestamo'], (datetime.min + p['hora_prestamo']).time())
            
            # LÓGICA DE 8 DÍAS (192 horas)
            es_tarde = ahora > (dt_prestamo + timedelta(days=8))
            
            cursor.execute("SELECT * FROM beneficiarios WHERE lu = %s", (p['lu_beneficiario'],))
            b = cursor.fetchone()
            faltas = b['faltas']; penalizado = b['penalizado']; cant_p = b['cant_penalizaciones']; horas_p = b['horas_penalizacion']
            razon = ""

            if danado:
                penalizado = True; horas_p = 8760; razon = f"Libro/Apunte dañado: {p['nombre_libro']}."
            elif es_tarde:
                faltas += 1
                if faltas >= 5:
                    faltas = 0; penalizado = True; cant_p += 1
                    horas_p = 168 if cant_p <= 2 else (360 if cant_p <= 5 else 720)
                    razon = "Acumulación de 5 faltas por devoluciones tardías."

            cursor.execute("UPDATE beneficiarios SET faltas=%s, penalizado=%s, cant_penalizaciones=%s, horas_penalizacion=%s WHERE lu=%s", 
                           (faltas, penalizado, cant_p, horas_p, p['lu_beneficiario']))
            
            if penalizado and razon:
                cursor.execute("INSERT INTO historial_penalizaciones_beneficiarios (lu_beneficiario, fecha_penalizacion, razon, lu_usuario_penaliza) VALUES (%s, %s, %s, %s)", 
                               (p['lu_beneficiario'], ahora.strftime('%Y-%m-%d %H:%M:%S'), razon, lu_admin))

            cursor.execute("SELECT apellidos, nombres FROM beneficiarios WHERE lu = %s", (lu_admin,))
            admin = cursor.fetchone()
            
            cursor.execute('''
                UPDATE historial_biblioteca SET lu_usuario_recibe=%s, apellidos_recibe=%s, nombres_recibe=%s, 
                fecha_devolucion=%s, hora_devolucion=%s, devuelto=TRUE, objeto_danado=%s, corresponde_falta=%s WHERE id=%s
            ''', (lu_admin, admin['apellidos'], admin['nombres'], ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S'), danado, es_tarde, id_p))
            
            cursor.execute("UPDATE libros SET disponible = disponible + 1 WHERE id = %s", (p['id_libro'],))
            conexion.commit()
            return True
    except Error as e: print(e); return False
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()