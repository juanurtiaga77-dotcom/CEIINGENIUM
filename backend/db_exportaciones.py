import pandas as pd
from mysql.connector import Error
from backend.conexion import obtener_conexion
from datetime import datetime

def exportar_tabla_simple(nombre_tabla, ruta_archivo):
    try:
        con = obtener_conexion()
        if con.is_connected():
            df = pd.read_sql(f"SELECT * FROM {nombre_tabla}", con)
            
            # ==========================================
            # --- SOLUCIÓN INTELIGENTE PARA LAS HORAS ---
            # ==========================================
            # Busca automáticamente cualquier columna que se llame 'hora', 'hora_prestamo', etc.
            for col in df.columns:
                if 'hora' in col.lower():
                    # Convierte a texto y toma solo la parte del reloj (14:02:45)
                    df[col] = df[col].astype(str).apply(
                        lambda x: str(x).split()[-1] if pd.notnull(x) and str(x) not in ['NaT', 'None', 'nan'] else ""
                    )
            # ==========================================
            
            df.to_excel(ruta_archivo, index=False)
            return True
    except Error as e: 
        print(f"Error al exportar tabla {nombre_tabla}: {e}")
        return False
    finally:
        if 'con' in locals() and con.is_connected(): con.close()

def exportar_deudores(ruta_archivo):
    """Filtra alumnos que deben préstamos por MÁS de 36 horas."""
    try:
        con = obtener_conexion()
        if con.is_connected():
            cursor = con.cursor(dictionary=True)
            # Trae todos los no devueltos cruzados con datos del alumno
            query = """
                SELECT hp.id, hp.nombre_objeto, hp.fecha_prestamo, hp.hora_prestamo, 
                       b.apellidos, b.nombres, b.dni, b.lu, b.telefono, b.correo 
                FROM historial_prestamos hp 
                JOIN beneficiarios b ON hp.lu_beneficiario = b.lu 
                WHERE hp.devuelto IS NULL
            """
            cursor.execute(query)
            pendientes = cursor.fetchall()
            
            deudores_reales = []
            ahora = datetime.now()
            for p in pendientes:
                dt_pres = datetime.combine(p['fecha_prestamo'], (datetime.min + p['hora_prestamo']).time())
                # Solo si pasaron más de 36 horas
                if (ahora - dt_pres).total_seconds() > (36 * 3600):
                    deudores_reales.append(p)
            
            if not deudores_reales: return False # No hay deudores
            df = pd.DataFrame(deudores_reales)
            
            # --- Aplicamos la misma corrección de hora aquí por si acaso ---
            if 'hora_prestamo' in df.columns:
                df['hora_prestamo'] = df['hora_prestamo'].astype(str).apply(
                    lambda x: str(x).split()[-1] if pd.notnull(x) and str(x) not in ['NaT', 'None', 'nan'] else ""
                )
            
            df.to_excel(ruta_archivo, index=False)
            return True
    except Exception as e: 
        print(f"Error exportando deudores: {e}")
        return False
    finally:
        if 'con' in locals() and con.is_connected(): con.close()

def exportar_penalizados(ruta_archivo):
    try:
        con = obtener_conexion()
        if con.is_connected():
            query = "SELECT apellidos, nombres, dni, lu, telefono, carrera, faltas, horas_penalizacion FROM beneficiarios WHERE penalizado = TRUE"
            df = pd.read_sql(query, con)
            if df.empty: return False
            df.to_excel(ruta_archivo, index=False)
            return True
    except Exception as e:
        print(f"Error exportando penalizados: {e}") 
        return False
    finally:
        if 'con' in locals() and con.is_connected(): con.close()