import sys

# Configuración del AppUserModelID para que Windows muestre el ícono correcto en la barra de tareas
if sys.platform == 'win32':
    import ctypes
    try:
        myappid = 'cei.ingenium.gestion.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication
from ventana_login import VentanaLogin 

def main():
    app = QApplication(sys.argv)
    login = VentanaLogin()
    login.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()