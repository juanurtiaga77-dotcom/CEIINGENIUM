from PyQt6.QtWidgets import (QWidget, QLineEdit, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import backend.db_comision as backend

class PestañaComision(QWidget):
    def __init__(self, lu_administrador):
        super().__init__()
        self.lu_admin = lu_administrador 
        self.inicializar_ui()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        layout_herramientas = QHBoxLayout()
        layout_herramientas.addStretch()

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar Apellido, Nombre o LU...")
        self.input_busqueda.setMinimumWidth(300)
        self.input_busqueda.textChanged.connect(self.filtrar_tabla)
        layout_herramientas.addWidget(self.input_busqueda)

        layout_principal.addLayout(layout_herramientas)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "LU", "Apellidos", "Nombres", "Préstamos Realizados", "Objetos Recibidos", "Horas Logueado", "Acciones"
        ])
        
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout_principal.addWidget(self.tabla)
        self.actualizar_tabla_datos()

    def actualizar_tabla_datos(self):
        usuarios_raw = backend.obtener_usuarios_comision()
        
        # --- ORDENAMIENTO INTELIGENTE ---
        # Separamos para mandar a los bloqueados al final
        activos = []
        inactivos = []
        
        for u in usuarios_raw:
            if str(u['contrasena']).startswith("BLOQUEADO_"):
                inactivos.append(u)
            else:
                activos.append(u)
                
        usuarios = activos + inactivos # Primero los limpios, al fondo los castigados
        
        self.tabla.setRowCount(0)

        for fila_idx, u in enumerate(usuarios):
            self.tabla.insertRow(fila_idx)
            self.tabla.setRowHeight(fila_idx, 50) 
            
            es_inactivo = str(u['contrasena']).startswith("BLOQUEADO_")
            color_texto = QColor("#f44336") if es_inactivo else QColor("#000000") # Rojo si está bloqueado
            
            items = [
                QTableWidgetItem(str(u['lu'])),
                QTableWidgetItem(str(u['apellidos'])),
                QTableWidgetItem(str(u['nombres'])),
                QTableWidgetItem(str(u['num_prestamos'])),
                QTableWidgetItem(str(u['num_recibidos'])),
                QTableWidgetItem(f"{float(u['horas_logueado']):.1f} hrs")
            ]
            
            # Pintar la fila completa
            for col_idx, item in enumerate(items):
                item.setForeground(color_texto)
                self.tabla.setItem(fila_idx, col_idx, item)

            # BOTONES DE ACCIÓN
            widget_botones = QWidget()
            layout_btn = QHBoxLayout(widget_botones)
            layout_btn.setContentsMargins(4, 2, 4, 2)
            layout_btn.setSpacing(6)

            btn_reset = QPushButton("Resetear Clave")
            btn_reset.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 5px;")
            btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_reset.setProperty("lu_usuario", u['lu'])
            btn_reset.clicked.connect(self.controlador_resetear)
            layout_btn.addWidget(btn_reset)

            # --- BOTÓN DINÁMICO SEGÚN ESTADO ---
            if es_inactivo:
                btn_accion = QPushButton("Habilitar")
                btn_accion.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
                btn_accion.clicked.connect(self.controlador_habilitar)
            else:
                btn_accion = QPushButton("Deshabilitar")
                btn_accion.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 5px;")
                btn_accion.clicked.connect(self.controlador_deshabilitar)
            
            btn_accion.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_accion.setProperty("lu_usuario", u['lu'])
            layout_btn.addWidget(btn_accion)

            self.tabla.setCellWidget(fila_idx, 6, widget_botones)

    def filtrar_tabla(self, texto_busqueda):
        t = texto_busqueda.strip().lower()
        for fila in range(self.tabla.rowCount()):
            mostrar_fila = False
            for col in (0, 1, 2): 
                item = self.tabla.item(fila, col)
                if item and t in item.text().lower():
                    mostrar_fila = True
                    break
            self.tabla.setRowHidden(fila, not mostrar_fila)

    def verificar_pass_admin(self):
        password, ok = QInputDialog.getText(self, "Seguridad Requerida", "Ingrese la clave de Administrador Master:", QLineEdit.EchoMode.Password)
        if ok and password == "Ingeniumcei26":
            return True
        elif ok:
            QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta.")
        return False

    def controlador_resetear(self):
        if not self.verificar_pass_admin(): return
        lu_usuario = self.sender().property("lu_usuario")

        confirmar = QMessageBox.question(self, "Confirmar Reset", f"¿Seguro que desea resetear la contraseña del LU {lu_usuario}?\nLa nueva contraseña será igual a su LU.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmar == QMessageBox.StandardButton.Yes:
            if backend.resetear_contrasena_comision(lu_usuario):
                QMessageBox.information(self, "Éxito", "Contraseña reseteada exitosamente. El usuario ha sido habilitado si estaba inactivo.")
                self.actualizar_tabla_datos()
            else:
                QMessageBox.warning(self, "Error", "No se pudo realizar la operación.")

    def controlador_deshabilitar(self):
        lu_usuario = self.sender().property("lu_usuario")
        
        # Validación de seguridad
        if str(lu_usuario) == str(self.lu_admin):
            QMessageBox.critical(self, "Bloqueo de Seguridad", "No puedes deshabilitarte a ti mismo mientras tienes tu sesión activa.")
            return

        if not self.verificar_pass_admin(): return

        confirmar = QMessageBox.warning(self, "Deshabilitar Usuario", f"¿Está seguro de deshabilitar al LU {lu_usuario}?\nSe le cambiará la clave por una aleatoria y perderá el acceso.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmar == QMessageBox.StandardButton.Yes:
            if backend.deshabilitar_usuario(lu_usuario):
                QMessageBox.information(self, "Éxito", "Usuario deshabilitado. Ha sido desplazado al fondo de la lista.")
                self.actualizar_tabla_datos()
            else:
                QMessageBox.warning(self, "Error", "No se pudo realizar la operación.")

    def controlador_habilitar(self):
        lu_usuario = self.sender().property("lu_usuario")
        
        if not self.verificar_pass_admin(): return

        confirmar = QMessageBox.question(self, "Habilitar Usuario", f"¿Desea restaurar el acceso al LU {lu_usuario}?\nSu contraseña volverá a ser su número de LU.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmar == QMessageBox.StandardButton.Yes:
            if backend.habilitar_usuario(lu_usuario):
                QMessageBox.information(self, "Éxito", "Usuario habilitado correctamente.")
                self.actualizar_tabla_datos()
            else:
                QMessageBox.warning(self, "Error", "No se pudo realizar la operación.")