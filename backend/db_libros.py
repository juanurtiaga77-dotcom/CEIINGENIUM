from datetime import datetime
from mysql.connector import Error
from backend.conexion import obtener_conexion

def registrar_historial_edicion(conexion, cursor_principal, lu_usuario, tipo_edicion, detalle):
    cursor_aux = conexion.cursor()
    cursor_aux.execute("SELECT nombres, apellidos FROM beneficiarios WHERE lu = %s", (lu_usuario,))
    u = cursor_aux.fetchone()
    nombres, apellidos = (u[0], u[1]) if u else ("Desconocido", "Desconocido")
    ahora = datetime.now()
    cursor_principal.execute('''
        INSERT INTO historial_edicion (nombre_tabla, tipo_edicion, apellido_usuario, nombre_usuario, lu_usuario, fecha, hora)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', ("libros", tipo_edicion, apellidos, nombres, lu_usuario, ahora.strftime('%Y-%m-%d'), ahora.strftime('%H:%M:%S')))

def obtener_todos_libros():
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM libros ORDER BY nombre ASC")
            return cursor.fetchall()
    except Error as e: print(e); return []
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def agregar_libro(nombre, desc, tipo, cantidad, disp, veces, lu_admin):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO libros (nombre, descripcion, tipo, cantidad, disponible, veces_prestado) VALUES (%s, %s, %s, %s, %s, %s)", 
                           (nombre, desc, tipo, cantidad, disp, veces))
            registrar_historial_edicion(conexion, cursor, lu_admin, "AGREGAR LIBRO", nombre)
            conexion.commit()
            return True, "Registrado con éxito."
    except Error as e: return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def editar_libro(id_libro, nombre, desc, tipo, cantidad, disp, veces, lu_admin):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("UPDATE libros SET nombre=%s, descripcion=%s, tipo=%s, cantidad=%s, disponible=%s, veces_prestado=%s WHERE id=%s", 
                           (nombre, desc, tipo, cantidad, disp, veces, id_libro))
            registrar_historial_edicion(conexion, cursor, lu_admin, "EDITAR LIBRO", nombre)
            conexion.commit()
            return True, "Actualizado con éxito."
    except Error as e: return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()

def eliminar_libro(id_libro, nombre, lu_admin):
    try:
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM libros WHERE id=%s", (id_libro,))
            registrar_historial_edicion(conexion, cursor, lu_admin, "ELIMINAR LIBRO", nombre)
            conexion.commit()
            return True, "Eliminado permanentemente."
    except Error as e: return False, str(e)
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()
        
def importar_libros_excel(ruta_archivo, lu_admin):
    try:
        # Leemos el archivo Excel
        df = pd.read_excel(ruta_archivo)
        
        # Pasamos las columnas a minúsculas para evitar errores si escribes "Nombre" o "nombre"
        df.columns = df.columns.str.lower()
        
        conexion = obtener_conexion()
        if conexion.is_connected():
            cursor = conexion.cursor()
            agregados = 0
            
            for index, row in df.iterrows():
                nombre = str(row.get('nombre', '')).strip()
                if not nombre or nombre == 'nan': continue # Si no hay nombre, salta la fila

                desc = str(row.get('descripcion', '')).strip()
                if desc == 'nan': desc = ""
                
                tipo = str(row.get('tipo', 'Libro')).strip()
                if tipo == 'nan': tipo = "Libro"
                
                cant = int(row.get('cantidad', 1))
                disp = int(row.get('disponible', cant))
                veces = int(row.get('veces_prestado', 0))

                cursor.execute(
                    "INSERT INTO libros (nombre, descripcion, tipo, cantidad, disponible, veces_prestado) VALUES (%s, %s, %s, %s, %s, %s)", 
                    (nombre, desc, tipo, cant, disp, veces)
                )
                agregados += 1
                
            registrar_historial_edicion(conexion, cursor, lu_admin, "IMPORTAR EXCEL LIBROS", f"{agregados} libros agregados")
            conexion.commit()
            return True, f"Se importaron {agregados} libros con éxito."
            
    except Exception as e: 
        return False, f"Error al procesar el Excel: {str(e)}"
    finally:
        if 'conexion' in locals() and conexion.is_connected(): conexion.close()