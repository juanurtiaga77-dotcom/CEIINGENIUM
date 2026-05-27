@echo off
echo Iniciando copia de seguridad automatica de la base de datos...

:: Variables de conexion XAMPP
set DB_NAME=gestion_comision_ingenium
set DB_USER=root

:: Obtener fecha y hora exacta
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set FECHA=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%

set ARCHIVO_NOMBRE=Backup_CEI_%FECHA%.sql
set RUTA_LOCAL=C:\backups

:: Crear la carpeta si no existe en el disco C
if not exist "%RUTA_LOCAL%" mkdir "%RUTA_LOCAL%"

:: Extraer base de datos
C:\xampp\mysql\bin\mysqldump.exe -u %DB_USER% %DB_NAME% > "%RUTA_LOCAL%\%ARCHIVO_NOMBRE%"

exit