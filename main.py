import sys
from PyQt6.QtWidgets import QApplication
from ventana_login import VentanaLogin 

def main():
    app = QApplication(sys.argv)
    login = VentanaLogin()
    login.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()