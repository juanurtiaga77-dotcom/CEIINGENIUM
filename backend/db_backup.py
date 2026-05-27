import os
import subprocess
from datetime import datetime

def chequear_y_ejecutar_backup():
    """
    Verifica si corresponde realizar la copia de seguridad diaria.
    Se ejecuta al iniciar la app y también de forma periódica cada 1 minuto.
    """
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    archivo_control = "control_backup.txt"
    
    ya_hecho_hoy = False
    
    # 1. Leer el archivo de control para ver cuándo se hizo por última vez
    if os.path.exists(archivo_control):
        try:
            with open(archivo_control, "r", encoding="utf-8") as f:
                if f.read().strip() == fecha_hoy:
                    ya_hecho_hoy = True
        except Exception as e:
            print(f"Error al leer archivo de control de backup: {e}")
            
    # 2. EVALUACIÓN DE REGLAS:
    # Si ya pasaron las 19:00 horas (ahora.hour >= 19) y todavía NO se ha hecho la copia de hoy,
    # significa que o es la hora exacta, o la PC estuvo apagada a las 19:00 y se encendió más tarde.
    if ahora.hour >= 19 and not ya_hecho_hoy:
        try:
            # Escribimos inmediatamente que hoy ya se procesó para evitar bucles infinitos
            with open(archivo_control, "w", encoding="utf-8") as f:
                f.write(fecha_hoy)
            
            # 3. Ejecución asíncrona (segundo plano) del archivo .bat
            if os.path.exists("backup_cei.bat"):
                # subprocess.Popen inicia el proceso de forma independiente.
                # Tu aplicación PyQt NUNCA se congelará ni se pondrá lenta mientras se hace el backup.
                subprocess.Popen("backup_cei.bat", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[{ahora.strftime('%H:%M:%S')}] Copia de seguridad automática iniciada con éxito.")
            else:
                print("Error: No se encontró el archivo 'backup_cei.bat' en el directorio raíz.")
        except Exception as e:
            print(f"Error crítico al lanzar el backup: {e}")