from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QPushButton, 
                             QMessageBox, QFileDialog, QLabel, QInputDialog, 
                             QLineEdit, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import backend.db_exportaciones as backend

class PestañaHistorialGeneral(QWidget):
    def __init__(self, lu_admin):
        super().__init__()
        self.inicializar_ui()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        titulo = QLabel("📊 Panel de Control y Exportaciones Generales")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        # Usamos un ScrollArea para que los botones nunca se salgan de la pantalla
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        contenedor = QWidget()
        contenedor.setStyleSheet("background-color: transparent;")
        ly = QVBoxLayout(contenedor)
        ly.setSpacing(15)

        # Usamos una Cuadrícula (Grid) de 2 columnas para las 15 tablas
        grid = QGridLayout()
        grid.setSpacing(10)

        # Lista exacta de las 15 tablas de tu base de datos XAMPP
        botones_db = [
            ("👥 Beneficiarios", "beneficiarios"),
            ("📚 Historial Biblioteca", "historial_biblioteca"),
            ("💰 Historial Caja Ventas", "historial_caja_ventas"),
            ("🕵️‍♂️ Historial Edición", "historial_edicion"),
            ("🔑 Historial Inicio Sesión", "historial_inicio_sesion"),
            ("🥖 Historial Pancitos", "historial_pancitos"),
            ("⛔ Historial Penalizaciones", "historial_penalizaciones_beneficiarios"),
            ("📦 Historial Préstamos Comunes", "historial_prestamos"),
            ("🛒 Historial Ventas", "historial_ventas"),
            ("📖 Libros", "libros"),
            ("🗄️ Objetos Guardados", "objetos_guardados"),
            ("❓ Objetos Perdidos", "objetos_perdidos"),
            ("🛠️ Objetos para Préstamos", "objetos_prestamos"),
            ("🛍️ Objetos para Ventas (Librería)", "objetos_ventas"),
            ("🧑‍💼 Usuarios de Comisión", "usuarios_comision")
        ]

        fila = 0
        col = 0
        for texto, tabla in botones_db:
            btn = QPushButton(texto)
            btn.setStyleSheet("background-color: #607D8B; color: white; padding: 12px; font-size: 13px; border-radius: 5px;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Pasamos la tabla y el nombre para exportar
            btn.clicked.connect(lambda ch, t=tabla, n=texto: self.exportar_simple(t, n))
            
            grid.addWidget(btn, fila, col)
            col += 1
            if col > 1: # Si ya llenó 2 columnas, baja a la siguiente fila
                col = 0
                fila += 1

        ly.addLayout(grid)

        # Divisor visual
        ly.addWidget(QLabel("<hr>"))

        # REPORTES DE VARIACIONES (DEUDORES Y PENALIZADOS)
        btn_deu = QPushButton("🚨 EXPORTAR DEUDORES (> 36 HORAS)")
        btn_deu.setStyleSheet("background-color: #f44336; color: white; padding: 15px; font-weight: bold; font-size: 15px; border-radius: 5px;")
        btn_deu.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_deu.clicked.connect(self.exportar_deudores)
        ly.addWidget(btn_deu)

        btn_pen = QPushButton("⛔ EXPORTAR ALUMNOS PENALIZADOS")
        btn_pen.setStyleSheet("background-color: #9C27B0; color: white; padding: 15px; font-weight: bold; font-size: 15px; border-radius: 5px;")
        btn_pen.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pen.clicked.connect(self.exportar_penalizados)
        ly.addWidget(btn_pen)

        ly.addStretch()
        
        # Metemos todo el contenedor dentro del ScrollArea
        scroll.setWidget(contenedor)
        layout_principal.addWidget(scroll)

    # --- LÓGICA DE CONTRASEÑA ---
    def verificar_pass(self):
        pwd, ok = QInputDialog.getText(self, "Seguridad Requerida", "Ingrese contraseña de Administrador:", QLineEdit.EchoMode.Password)
        if ok and pwd == "Ingeniumcei26":
            return True
        elif ok:
            QMessageBox.warning(self, "Acceso Denegado", "Contraseña incorrecta. No se puede exportar.")
        return False

    def obtener_ruta(self, nombre):
        r, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", f"Reporte_{nombre}.xlsx", "Archivos de Excel (*.xlsx)")
        return r

    # --- FUNCIONES DE EXPORTACIÓN ---
    def exportar_simple(self, tabla, nombre):
        if not self.verificar_pass(): return # Pide contraseña antes de hacer nada
        
        r = self.obtener_ruta(tabla)
        if r:
            if backend.exportar_tabla_simple(tabla, r): 
                QMessageBox.information(self, "Éxito", f"Reporte '{nombre}' guardado correctamente.")
            else: 
                QMessageBox.warning(self, "Aviso", f"La tabla '{nombre}' está vacía o hubo un error al exportar.")

    def exportar_deudores(self):
        if not self.verificar_pass(): return 
        
        r = self.obtener_ruta("Deudores_Mora_Critica")
        if r:
            if backend.exportar_deudores(r): 
                QMessageBox.information(self, "Éxito", "Reporte de deudores guardado correctamente.")
            else: 
                QMessageBox.information(self, "Genial", "¡No hay alumnos que deban objetos por más de 36 horas!")

    def exportar_penalizados(self):
        if not self.verificar_pass(): return
        
        r = self.obtener_ruta("Alumnos_Penalizados")
        if r:
            if backend.exportar_penalizados(r): 
                QMessageBox.information(self, "Éxito", "Reporte de penalizados guardado correctamente.")
            else: 
                QMessageBox.information(self, "Genial", "¡No hay alumnos penalizados actualmente!")