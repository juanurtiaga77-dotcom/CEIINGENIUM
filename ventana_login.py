from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QFormLayout, QFrame, QMessageBox, 
                             QGraphicsDropShadowEffect, QApplication, QInputDialog) # <--- AQUÍ ESTÁ AGREGADO
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor

from backend.auth import verificar_login, actualizar_contrasena
from ventana_principal import VentanaPrincipal 

class VentanaLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.inicializar_ui()

    def inicializar_ui(self):
        self.setWindowTitle("CEI Programa - Acceso")
        self.setObjectName("login_window") 
        import os
        import sys
        ruta_logo = os.path.join(sys._MEIPASS, "logo.png") if hasattr(sys, '_MEIPASS') else "logo.png"
        self.setWindowIcon(QIcon(ruta_logo))
        
        width, height = 420, 520
        self.setFixedSize(width, height)
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.addStretch() 

        self.login_card = QFrame()
        self.login_card.setObjectName("login_card") 
        self.sombra = QGraphicsDropShadowEffect(self)
        self.sombra.setBlurRadius(25)
        self.sombra.setOffset(0, 4)
        self.sombra.setColor(QColor(0, 0, 0, 40)) 
        self.login_card.setGraphicsEffect(self.sombra)

        layout_card = QVBoxLayout(self.login_card)
        layout_card.setContentsMargins(40, 40, 40, 40)
        
        self.label_titulo = QLabel("BIENVENIDO/A")
        self.label_titulo.setObjectName("login_title")
        self.label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_card.addWidget(self.label_titulo)

        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.form_layout.setVerticalSpacing(8)

        self.label_lu = QLabel("Nº Libreta Universitaria")
        self.label_lu.setObjectName("login_label")
        self.input_lu = QLineEdit()
        self.input_lu.setPlaceholderText("Ej: 321321")
        self.input_lu.setMaxLength(20)
        self.form_layout.addRow(self.label_lu, self.input_lu)

        self.label_pass = QLabel("Contraseña")
        self.label_pass.setObjectName("login_label")
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password) 
        self.input_pass.setPlaceholderText("••••••••")
        self.form_layout.addRow(self.label_pass, self.input_pass)

        # ---------------------------------------------------------
        # AQUÍ ESTÁ LA MAGIA DEL TECLADO (ENTER)
        self.input_lu.returnPressed.connect(self.input_pass.setFocus)
        self.input_pass.returnPressed.connect(self.procesar_login)
        # ---------------------------------------------------------

        layout_card.addLayout(self.form_layout)
        layout_card.addSpacing(25)

        self.layout_botones = QHBoxLayout()
        self.layout_botones.setSpacing(10)

        self.btn_ingresar = QPushButton("Ingresar")
        self.btn_ingresar.setObjectName("btn_ingresar")
        self.btn_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ingresar.clicked.connect(self.procesar_login)
        self.layout_botones.addWidget(self.btn_ingresar)

        self.btn_salir = QPushButton("Salir")
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salir.clicked.connect(self.close)
        self.layout_botones.addWidget(self.btn_salir)

        layout_card.addLayout(self.layout_botones)
        layout_principal.addWidget(self.login_card, 0, Qt.AlignmentFlag.AlignCenter)
        layout_principal.addStretch() 
        self.cargar_estilos()

    def cargar_estilos(self):
        try:
            import os
            import sys
            ruta_qss = os.path.join(sys._MEIPASS, "estilos.qss") if hasattr(sys, '_MEIPASS') else "estilos.qss"
            with open(ruta_qss, "r", encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except: pass

    def procesar_login(self):
        lu = self.input_lu.text().strip()
        pw = self.input_pass.text().strip()
        
        if not lu or not pw:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor ingrese LU y contraseña.")
            return

        exito, resultado, ruta_foto, cargo = verificar_login(lu, pw)
        
        if exito:
            # --- COMPROBACIÓN DE PRIMER INGRESO ---
            if lu == pw:
                while True: # Bucle para insistir hasta que ponga una contraseña válida
                    nueva_pw, ok = QInputDialog.getText(
                        self, 
                        "Primer Ingreso - Seguridad", 
                        "Por seguridad, es obligatorio cambiar su contraseña por defecto.\nIngrese su nueva contraseña:", 
                        QLineEdit.EchoMode.Password
                    )
                    
                    if not ok:
                        QMessageBox.warning(self, "Acceso Denegado", "Debe cambiar la contraseña obligatoriamente para poder ingresar.")
                        return # Cancela el login si cierra la ventana
                    
                    nueva_pw = nueva_pw.strip()
                    
                    if not nueva_pw:
                        QMessageBox.warning(self, "Error", "La contraseña no puede estar vacía.")
                        continue # Vuelve a mostrar el cuadro de diálogo
                        
                    if nueva_pw == lu:
                        QMessageBox.warning(self, "Error de Seguridad", "La nueva contraseña NO puede ser igual a su LU. Por favor, elija otra distinta.")
                        continue # Vuelve a mostrar el cuadro de diálogo
                    
                    # Si pasó todas las validaciones (no está vacía y es distinta al LU)
                    actualizar_contrasena(lu, nueva_pw)
                    QMessageBox.information(self, "Éxito", "Contraseña actualizada correctamente. ¡Bienvenido!")
                    break # Rompe el bucle para continuar con el login
            
            # Si todo está bien, abre el sistema (resultado ahora contiene el NOMBRE, pasamos cargo)
            self.nueva_ventana = VentanaPrincipal(resultado, lu, ruta_foto, cargo)
            self.nueva_ventana.show()
            self.close() 
        else:
            QMessageBox.warning(self, "Error", resultado)