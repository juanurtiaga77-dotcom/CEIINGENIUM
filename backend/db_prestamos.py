from datetime import datetime, timedelta
from mysql.connector import Error
from backend.conexion import obtener_conexion

def mantenimiento_penalizaciones(conexion):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT lu, horas_penalizacion FROM beneficiarios WHERE penalizado = TRUE")
    penalizados = cursor.fetchall()

    ahora = datetime.now()
    for p in penalizados:
        lu = p['lu']
        horas_condena = p['horas_penalizacion']
        
        if horas_condena > 0: 
            cursor.execute("SELECT fecha_penalizacion FROM historial_penalizaciones_beneficiarios WHERE lu_beneficiario = %s AND fecha_despenalizacion IS NULL ORDER BY id DESC LIMIT 1", (lu,))
            historial = cursor.fetchone()
            
            if historial and historial['fecha_penalizacion']:
                fecha_fin_condena = historial['fecha_penalizacion'] + timedelta(hours=horas_condena)
                if ahora >= fecha_fin_condena:
                    cursor.execute("UPDATE beneficiarios SET penalizado = FALSE, horas_penalizacion = 0 WHERE lu = %s", (lu,))
                    cursor.execute("UPDATE historial_penalizaciones_beneficiarios SET fecha_despenalizacion = %s, razon = CONCAT(razon, ' | Tiempo cumplido automáticamente') WHERE lu_beneficiario = %s AND fecha_despenalizacion IS NULL", (ahora.strftime('%Y-%m-%d %H:%M:%S'), lu))
    conexion.commit()
    cursor.close()

def buscar_beneficiario(criterio):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            mantenimiento_penalizaciones(conexion) 
            
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM beneficiarios WHERE lu = %s OR dni = %s", (criterio, criterio))
            b = cursor.fetchone()
            
            if b and b['penalizado']:
                cursor.execute("SELECT fecha_penalizacion FROM historial_penalizaciones_beneficiarios WHERE lu_beneficiario = %s AND fecha_despenalizacion IS NULL ORDER BY id DESC LIMIT 1", (b['lu'],))
                hist = cursor.fetchone()
                if hist and hist['fecha_penalizacion']:
                    if b['horas_penalizacion'] > 0:
                        fin = hist['fecha_penalizacion'] + timedelta(hours=b['horas_penalizacion'])
                        faltan = fin - datetime.now()
                        dias, horas = faltan.days, faltan.seconds // 3600
                        b['tiempo_restante_str'] = f"{dias} días y {horas} horas"
                    else:
                        b['tiempo_restante_str'] = "Indefinido (Penalización Manual)"
            return b
    except Error as e: print(f"Error buscar beneficiario: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return None

def obtener_objetos_populares():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM objetos_prestamos WHERE cantidad_disponibles > 0 ORDER BY veces_prestado DESC")
            return cursor.fetchall()
    except Error as e: print(f"Error obtener objetos: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return []

def validar_y_prestar(lu_beneficiario, id_objeto, nombre_objeto, lu_admin):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            
            cursor.execute("SELECT prestamos_activos, apellidos, nombres, penalizado FROM beneficiarios WHERE lu = %s", (lu_beneficiario,))
            b = cursor.fetchone()
            
            if b['penalizado']: return False, "El alumno está penalizado."
            if b['prestamos_activos'] >= 5: return False, "Límite de 5 préstamos alcanzado."
            
            cursor.execute("SELECT id FROM historial_prestamos WHERE lu_beneficiario = %s AND id_objeto = %s AND devuelto IS NULL", (lu_beneficiario, id_objeto))
            if cursor.fetchone(): return False, "Ya tiene este objeto en préstamo."

            cursor.execute("SELECT cantidad_disponibles FROM objetos_prestamos WHERE id = %s", (id_objeto,))
            obj = cursor.fetchone()
            if obj['cantidad_disponibles'] <= 0: return False, "Objeto agotado."

            # --- BUSCAR DATOS DEL ADMINISTRADOR QUE PRESTA ---
            cursor.execute("SELECT apellidos, nombres FROM beneficiarios WHERE lu = %s", (lu_admin,))
            admin = cursor.fetchone()
            apellidos_admin = admin['apellidos'] if admin else ""
            nombres_admin = admin['nombres'] if admin else ""

            ahora = datetime.now()
            fecha = ahora.strftime('%Y-%m-%d')
            hora = ahora.strftime('%H:%M:%S')

            # --- INSERTAR INCLUYENDO LOS NOMBRES DEL ADMINISTRADOR ---
            cursor.execute('''
                INSERT INTO historial_prestamos 
                (lu_usuario_presta, apellidos_presta, nombres_presta, id_objeto, nombre_objeto, apellidos_beneficiario, nombres_beneficiario, lu_beneficiario, fecha_prestamo, hora_prestamo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (lu_admin, apellidos_admin, nombres_admin, id_objeto, nombre_objeto, b['apellidos'], b['nombres'], lu_beneficiario, fecha, hora))

            cursor.execute("UPDATE objetos_prestamos SET cantidad_disponibles = cantidad_disponibles - 1, en_prestamo = en_prestamo + 1, veces_prestado = veces_prestado + 1 WHERE id = %s", (id_objeto,))
            cursor.execute("UPDATE beneficiarios SET prestamos_activos = prestamos_activos + 1 WHERE lu = %s", (lu_beneficiario,))
            cursor.execute("UPDATE usuarios_comision SET num_prestamos = num_prestamos + 1 WHERE lu_usuario = %s", (lu_admin,))
            
            conexion.commit()
            return True, "Préstamo registrado exitosamente."
    except Error as e: return False, f"Error: {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def obtener_historial_activo(filtro_lu=""):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            hoy = datetime.now().strftime('%Y-%m-%d')
            query = "SELECT * FROM historial_prestamos WHERE devuelto IS NULL OR fecha_devolucion = %s"
            params = [hoy]
            if filtro_lu:
                query += " AND lu_beneficiario LIKE %s"
                params.append(f"%{filtro_lu}%")
            query += " ORDER BY fecha_prestamo DESC, hora_prestamo DESC"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e: print(f"Error historial: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
    return []

def consolidar_devolucion_db(id_prestamo, lu_admin, objeto_danado, fecha_real_devolucion=None):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM historial_prestamos WHERE id = %s AND devuelto IS NOT NULL", (id_prestamo,))
            if cursor.fetchone(): return False

            cursor.execute("SELECT * FROM historial_prestamos WHERE id = %s", (id_prestamo,))
            prestamo = cursor.fetchone()
            
            ahora = fecha_real_devolucion if fecha_real_devolucion else datetime.now()
            fecha_dev = ahora.strftime('%Y-%m-%d')
            hora_dev = ahora.strftime('%H:%M:%S')

            dt_prestamo = datetime.combine(prestamo['fecha_prestamo'], (datetime.min + prestamo['hora_prestamo']).time())
            horas_limite = 84 if dt_prestamo.weekday() == 4 else 36
            fecha_limite = dt_prestamo + timedelta(hours=horas_limite)
            
            es_tarde = ahora > fecha_limite
            
            cursor.execute("SELECT * FROM beneficiarios WHERE lu = %s", (prestamo['lu_beneficiario'],))
            b = cursor.fetchone()
            
            nuevas_faltas = b['faltas']
            nuevo_penalizado = b['penalizado']
            nuevas_cant_penal = b['cant_penalizaciones']
            nuevas_horas_penal = b['horas_penalizacion']
            razon_penalidad = ""

            if objeto_danado:
                nuevo_penalizado = True
                nuevas_horas_penal = 8760
                razon_penalidad = f"Objeto dañado: {prestamo['nombre_objeto']}."
            elif es_tarde:
                nuevas_faltas += 1
                if nuevas_faltas >= 5:
                    nuevas_faltas = 0
                    nuevo_penalizado = True
                    nuevas_cant_penal += 1
                    if nuevas_cant_penal <= 2: nuevas_horas_penal = 168
                    elif nuevas_cant_penal <= 5: nuevas_horas_penal = 360
                    else: nuevas_horas_penal = 720
                    razon_penalidad = f"Acumulación de 5 faltas por devoluciones tardías."

            cursor.execute('''
                UPDATE beneficiarios 
                SET prestamos_activos = prestamos_activos - 1, faltas = %s, penalizado = %s, 
                    cant_penalizaciones = %s, horas_penalizacion = %s
                WHERE lu = %s
            ''', (nuevas_faltas, nuevo_penalizado, nuevas_cant_penal, nuevas_horas_penal, prestamo['lu_beneficiario']))

            if nuevo_penalizado and razon_penalidad:
                cursor.execute("INSERT INTO historial_penalizaciones_beneficiarios (lu_beneficiario, fecha_penalizacion, razon, lu_usuario_penaliza) VALUES (%s, %s, %s, %s)", 
                               (prestamo['lu_beneficiario'], ahora.strftime('%Y-%m-%d %H:%M:%S'), razon_penalidad, lu_admin))

            # --- BUSCAR DATOS DEL ADMINISTRADOR QUE RECIBE ---
            cursor.execute("SELECT apellidos, nombres FROM beneficiarios WHERE lu = %s", (lu_admin,))
            admin = cursor.fetchone()
            apellidos_admin = admin['apellidos'] if admin else ""
            nombres_admin = admin['nombres'] if admin else ""

            # --- ACTUALIZAR INCLUYENDO LOS NOMBRES DEL ADMINISTRADOR ---
            cursor.execute('''
                UPDATE historial_prestamos 
                SET lu_usuario_recibe = %s, apellidos_recibe = %s, nombres_recibe = %s, 
                    fecha_devolucion = %s, hora_devolucion = %s, 
                    devuelto = TRUE, objeto_danado = %s, corresponde_falta = %s
                WHERE id = %s
            ''', (lu_admin, apellidos_admin, nombres_admin, fecha_dev, hora_dev, objeto_danado, es_tarde, id_prestamo))

            cursor.execute("UPDATE objetos_prestamos SET cantidad_disponibles = cantidad_disponibles + 1, en_prestamo = en_prestamo - 1 WHERE id = %s", (prestamo['id_objeto'],))
            cursor.execute("UPDATE usuarios_comision SET num_recibidos = num_recibidos + 1 WHERE lu_usuario = %s", (lu_admin,))

            conexion.commit()
            return True
    except Error as e: print(f"Error consolidar devolución: {e}"); return False
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()