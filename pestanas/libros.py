import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QComboBox,
                             QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QSpinBox, QTextEdit,
                             QInputDialog, QFileDialog) # <-- Agregué QFileDialog aquí
from PyQt6.QtCore import Qt

import backend.db_libros as backend

class DialogoLibro(QDialog):
    def __init__(self, parent=None, datos=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Biblioteca" if not datos else "Editar Libro")
        self.setMinimumWidth(350)
        
        layout = QFormLayout(self)
        self.input_nombre = QLineEdit()
        self.input_desc = QTextEdit(); self.input_desc.setMaximumHeight(60)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Libro", "Apunte", "Revista", "Fotocopia"])
        
        self.spin_cant = QSpinBox(); self.spin_cant.setMaximum(999)
        self.spin_disp = QSpinBox(); self.spin_disp.setMaximum(999)
        self.spin_veces = QSpinBox(); self.spin_veces.setMaximum(9999)

        if datos:
            self.input_nombre.setText(datos['nombre'])
            self.input_desc.setText(datos['descripcion'])
            self.combo_tipo.setCurrentText(datos['tipo'])
            self.spin_cant.setValue(datos['cantidad'])
            self.spin_disp.setValue(datos['disponible'])
            self.spin_veces.setValue(datos['veces_prestado'])

        layout.addRow("Nombre:", self.input_nombre)
        layout.addRow("Descripción:", self.input_desc)
        layout.addRow("Tipo:", self.combo_tipo)
        layout.addRow("Cantidad:", self.spin_cant)
        layout.addRow("Disponible:", self.spin_disp)
        layout.addRow("Veces Prestado:", self.spin_veces)

        l_btn = QHBoxLayout()
        btn_g = QPushButton("Guardar"); btn_g.clicked.connect(self.accept)
        btn_c = QPushButton("Cancelar"); btn_c.clicked.connect(self.reject)
        l_btn.addWidget(btn_g); l_btn.addWidget(btn_c)
        layout.addRow(l_btn)

    def obtener_datos(self):
        return {
            "nombre": self.input_nombre.text().strip(), "desc": self.input_desc.toPlainText().strip(),
            "tipo": self.combo_tipo.currentText(), "cant": self.spin_cant.value(),
            "disp": self.spin_disp.value(), "veces": self.spin_veces.value()
        }

class PestañaLibros(QWidget):
    def __init__(self, lu_admin):
        super().__init__()
        self.lu_admin = lu_admin 
        self.tiempo_autorizacion = None
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QVBoxLayout(self)
        
        l_sup = QHBoxLayout()
        
        l_sup = QHBoxLayout()
        
        btn_add = QPushButton("➕ Agregar Libro/Apunte")
        btn_add.setObjectName("btn_herramienta_carnet") # <--- ¡LA MAGIA ESTÁ AQUÍ!
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.agregar)
        l_sup.addWidget(btn_add)
        
        btn_excel = QPushButton("📥 Cargar desde Excel")
        btn_excel.setObjectName("btn_herramienta_carnet") # <--- ¡LA MAGIA ESTÁ AQUÍ!
        btn_excel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_excel.clicked.connect(self.cargar_excel)
        l_sup.addWidget(btn_excel)
        
        l_sup.addStretch()
        
        self.input_buscar = QLineEdit(); self.input_buscar.setPlaceholderText("🔍 Buscar...")
        self.input_buscar.setStyleSheet("padding: 8px; border: 1px solid #ccc;")
        self.input_buscar.textChanged.connect(self.filtrar)
        l_sup.addWidget(self.input_buscar)
        layout.addLayout(l_sup)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Descripción", "Tipo", "Cant", "Disp.", "Prestado", "Acciones"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(7, 160) 
        
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: transparent; border: none; }")
        
        layout.addWidget(self.tabla)
        self.actualizar_tabla()

    def actualizar_tabla(self):
        libros = backend.obtener_todos_libros()
        self.tabla.setRowCount(0)
        for i, lib in enumerate(libros):
            self.tabla.insertRow(i)
            self.tabla.setRowHeight(i, 45) 
            
            self.tabla.setItem(i, 0, QTableWidgetItem(str(lib['id'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(lib['nombre']))
            
            item_desc = QTableWidgetItem(lib['descripcion'])
            item_desc.setToolTip(lib['descripcion'])
            self.tabla.setItem(i, 2, item_desc)
            
            self.tabla.setItem(i, 3, QTableWidgetItem(lib['tipo']))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(lib['cantidad'])))
            self.tabla.setItem(i, 5, QTableWidgetItem(str(lib['disponible'])))
            self.tabla.setItem(i, 6, QTableWidgetItem(str(lib['veces_prestado'])))
            
            w_btn = QWidget(); l_btn = QHBoxLayout(w_btn); l_btn.setContentsMargins(4,4,4,4)
            
            b_edit = QPushButton("Editar")
            b_edit.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 5px; border-radius: 4px;")
            b_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            b_edit.clicked.connect(lambda ch, d=lib: self.editar(d))
            
            b_del = QPushButton("Eliminar")
            b_del.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 5px; border-radius: 4px;")
            b_del.setCursor(Qt.CursorShape.PointingHandCursor)
            b_del.clicked.connect(lambda ch, d=lib: self.eliminar(d['id'], d['nombre']))
            
            l_btn.addWidget(b_edit); l_btn.addWidget(b_del)
            self.tabla.setCellWidget(i, 7, w_btn)

    def filtrar(self, texto):
        t = texto.strip().lower()
        for fila in range(self.tabla.rowCount()):
            item = self.tabla.item(fila, 1)
            self.tabla.setRowHidden(fila, item and t not in item.text().lower())

    def verificar_pass(self, siempre=False):
        ahora = datetime.now()
        if not siempre and self.tiempo_autorizacion and (ahora - self.tiempo_autorizacion).total_seconds() < 600: return True
        pwd, ok = QInputDialog.getText(self, "Seguridad", "Clave de Biblioteca:", QLineEdit.EchoMode.Password)
        if ok and pwd == "Ingeniumcei26":
            if not siempre: self.tiempo_autorizacion = datetime.now()
            return True
        elif ok: QMessageBox.warning(self, "Error", "Clave incorrecta.")
        return False

    def agregar(self):
        if self.verificar_pass(False):
            diag = DialogoLibro(self)
            if diag.exec():
                d = diag.obtener_datos()
                exito, msj = backend.agregar_libro(d['nombre'], d['desc'], d['tipo'], d['cant'], d['disp'], d['veces'], self.lu_admin)
                if exito: self.actualizar_tabla()

    # --- NUEVA FUNCIÓN PARA IMPORTAR ---
    def cargar_excel(self):
        if self.verificar_pass(False):
            ruta_archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo Excel", "", "Archivos Excel (*.xlsx *.xls)")
            
            if ruta_archivo:
                exito, msj = backend.importar_libros_excel(ruta_archivo, self.lu_admin)
                if exito:
                    QMessageBox.information(self, "Importación Exitosa", msj)
                    self.actualizar_tabla()
                else:
                    QMessageBox.critical(self, "Error al importar", msj)

    def editar(self, datos):
        if self.verificar_pass(False):
            diag = DialogoLibro(self, datos=datos)
            if diag.exec():
                d = diag.obtener_datos()
                exito, msj = backend.editar_libro(datos['id'], d['nombre'], d['desc'], d['tipo'], d['cant'], d['disp'], d['veces'], self.lu_admin)
                if exito: self.actualizar_tabla()

    def eliminar(self, id_l, nombre):
        conf = QMessageBox.question(self, "Confirmar", f"¿Eliminar {nombre}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if conf == QMessageBox.StandardButton.Yes and self.verificar_pass(True):
            exito, msj = backend.eliminar_libro(id_l, nombre, self.lu_admin)
            if exito: self.actualizar_tabla()