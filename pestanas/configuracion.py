import os
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QComboBox,
                             QVBoxLayout, QHBoxLayout, QMessageBox, QFrame, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import backend.db_comision as backend

class PestañaConfiguracion(QWidget):
    def __init__(self, lu_administrador):
        super().__init__()
        self.lu_admin = lu_administrador 
        self.beneficiario_encontrado = None
        self.inicializar_ui()

    def inicializar_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)

        # ================= LADO IZQUIERDO: TABLA DE PERSONAS =================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # Buscador superior para la tabla
        layout_busqueda = QHBoxLayout()
        lbl_buscar_tab = QLabel("👥 Personal / Beneficiarios:")
        lbl_buscar_tab.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.input_filtro_tabla = QLineEdit()
        self.input_filtro_tabla.setPlaceholderText("🔍 Filtrar lista por LU, Nombre o Cargo...")
        self.input_filtro_tabla.setMinimumWidth(250)
        self.input_filtro_tabla.textChanged.connect(self.filtrar_tabla)
        
        layout_busqueda.addWidget(lbl_buscar_tab)
        layout_busqueda.addStretch()
        layout_busqueda.addWidget(self.input_filtro_tabla)
        left_layout.addLayout(layout_busqueda)

        # Tabla de beneficiarios
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["LU", "Estudiante", "Cargo", "Estado", "Carrera"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: transparent; border: none; }")
        
        left_layout.addWidget(self.tabla)
        layout_principal.addWidget(left_widget, stretch=3)

        # ================= LADO DERECHO: PANEL DE EDICIÓN =================
        right_frame = QFrame()
        right_frame.setObjectName("config_info_card")
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        right_frame.setFixedWidth(380)
        
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        # Título
        lbl_title_edit = QLabel("⚙️ Gestionar Cargo")
        lbl_title_edit.setStyleSheet("font-size: 18px; font-weight: bold; color: #00b4d8;")
        lbl_title_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(lbl_title_edit)

        # Buscador por LU
        box_buscar = QFrame()
        box_buscar.setStyleSheet("background-color: rgba(0,0,0,0.03); border-radius: 8px; padding: 10px;")
        box_buscar_layout = QVBoxLayout(box_buscar)
        box_buscar_layout.setSpacing(10)

        lbl_buscar_lu = QLabel("Buscar Beneficiario por LU:")
        lbl_buscar_lu.setStyleSheet("font-weight: bold;")
        self.input_buscar_lu = QLineEdit()
        self.input_buscar_lu.setPlaceholderText("Ej: 316449...")
        self.input_buscar_lu.returnPressed.connect(self.buscar_alumno_lu)
        
        self.btn_buscar = QPushButton("🔍 Buscar Persona")
        self.btn_buscar.setStyleSheet("background-color: #00b4d8; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        self.btn_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_buscar.clicked.connect(self.buscar_alumno_lu)

        box_buscar_layout.addWidget(lbl_buscar_lu)
        box_buscar_layout.addWidget(self.input_buscar_lu)
        box_buscar_layout.addWidget(self.btn_buscar)
        right_layout.addWidget(box_buscar)

        # Detalles del alumno encontrado
        self.card_detalles = QFrame()
        self.card_detalles.setStyleSheet("background-color: rgba(0,0,0,0.02); border-radius: 8px; padding: 12px;")
        self.card_detalles.setVisible(False)
        self.detalles_layout = QGridLayout(self.card_detalles)
        self.detalles_layout.setSpacing(8)

        self.lbl_det_nombre = QLabel()
        self.lbl_det_nombre.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_det_lu = QLabel()
        self.lbl_det_estado = QLabel()
        
        self.combo_cargo = QComboBox()
        self.combo_cargo.addItems([
            "Estudiante", 
            "Atención", 
            "Presidencia", 
            "Comisión", 
            "Recursos Humanos", 
            "Informática", 
            "Asienda"
        ])
        
        self.detalles_layout.addWidget(QLabel("Nombre:"), 0, 0)
        self.detalles_layout.addWidget(self.lbl_det_nombre, 0, 1)
        self.detalles_layout.addWidget(QLabel("LU:"), 1, 0)
        self.detalles_layout.addWidget(self.lbl_det_lu, 1, 1)
        self.detalles_layout.addWidget(QLabel("Estado:"), 2, 0)
        self.detalles_layout.addWidget(self.lbl_det_estado, 2, 1)
        self.detalles_layout.addWidget(QLabel("Cargo:"), 3, 0)
        self.detalles_layout.addWidget(self.combo_cargo, 3, 1)

        right_layout.addWidget(self.card_detalles)

        # Botón guardar
        self.btn_guardar = QPushButton("💾 Guardar Nuevo Cargo")
        self.btn_guardar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.clicked.connect(self.guardar_cambio_cargo)
        right_layout.addWidget(self.btn_guardar)

        right_layout.addStretch()
        layout_principal.addWidget(right_frame, stretch=1)

        # Cargar datos iniciales
        self.actualizar_tabla_datos()

    def actualizar_tabla_datos(self):
        # 1. Guardar scroll
        v_scroll = self.tabla.verticalScrollBar().value()
        h_scroll = self.tabla.horizontalScrollBar().value()

        beneficiarios = backend.obtener_todos_beneficiarios()
        self.tabla.setRowCount(0)

        for i, b in enumerate(beneficiarios):
            self.tabla.insertRow(i)
            self.tabla.setRowHeight(i, 45)

            self.tabla.setItem(i, 0, QTableWidgetItem(str(b['lu'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(f"{b['apellidos']}, {b['nombres']}"))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(b['cargo'])))
            
            # Estado (Penalizado / Activo)
            estado_texto = "🔴 Penalizado" if b['penalizado'] else "🟢 Activo"
            estado_item = QTableWidgetItem(estado_texto)
            if b['penalizado']:
                estado_item.setForeground(QColor("#f44336"))
            else:
                estado_item.setForeground(QColor("#4CAF50"))
            self.tabla.setItem(i, 3, estado_item)

            carrera_str = b['carrera'] if b['carrera'] else "-"
            self.tabla.setItem(i, 4, QTableWidgetItem(carrera_str))

        # Re-aplicar filtro
        self.filtrar_tabla()

        # Restaurar scroll
        self.tabla.verticalScrollBar().setValue(v_scroll)
        self.tabla.horizontalScrollBar().setValue(h_scroll)

    def filtrar_tabla(self, texto=""):
        if not isinstance(texto, str):
            texto = self.input_filtro_tabla.text()
        t = texto.strip().lower()
        for fila in range(self.tabla.rowCount()):
            mostrar_fila = False
            for col in (0, 1, 2, 4): 
                item = self.tabla.item(fila, col)
                if item and t in item.text().lower():
                    mostrar_fila = True
                    break
            self.tabla.setRowHidden(fila, not mostrar_fila)

    def buscar_alumno_lu(self):
        lu = self.input_buscar_lu.text().strip()
        if not lu:
            QMessageBox.warning(self, "Atención", "Por favor, introduzca una LU válida.")
            return

        b = backend.buscar_beneficiario_por_lu(lu)
        if b:
            self.beneficiario_encontrado = b
            self.lbl_det_nombre.setText(f"{b['apellidos']}, {b['nombres']}")
            self.lbl_det_lu.setText(str(b['lu']))
            
            estado_text = "🔴 Penalizado" if b['penalizado'] else "🟢 Activo"
            self.lbl_det_estado.setText(estado_text)
            self.lbl_det_estado.setStyleSheet("font-weight: bold; color: #f44336;" if b['penalizado'] else "font-weight: bold; color: #4CAF50;")
            
            # Seleccionar cargo actual en el combo con normalización
            cargo_actual = b['cargo'] if b['cargo'] else "Estudiante"
            cargo_clean = cargo_actual.lower().strip()
            
            if "president" in cargo_clean:
                cargo_actual = "Presidencia"
            elif "hacienda" in cargo_clean:
                cargo_actual = "Asienda"
            elif cargo_clean == "estudiantes":
                cargo_actual = "Estudiante"
            
            idx = self.combo_cargo.findText(cargo_actual)
            if idx >= 0:
                self.combo_cargo.setCurrentIndex(idx)
            else:
                idx_parcial = -1
                for i in range(self.combo_cargo.count()):
                    if self.combo_cargo.itemText(i).lower() in cargo_clean:
                        idx_parcial = i
                        break
                self.combo_cargo.setCurrentIndex(idx_parcial if idx_parcial >= 0 else 0)
            
            self.card_detalles.setVisible(True)
            self.btn_guardar.setEnabled(True)
        else:
            self.beneficiario_encontrado = None
            self.card_detalles.setVisible(False)
            self.btn_guardar.setEnabled(False)
            QMessageBox.information(self, "No Encontrado", f"No se encontró ningún beneficiario con la LU '{lu}'.")

    def guardar_cambio_cargo(self):
        if not self.beneficiario_encontrado:
            return

        lu = self.beneficiario_encontrado['lu']
        nuevo_cargo = self.combo_cargo.currentText()
        nombre = f"{self.beneficiario_encontrado['apellidos']}, {self.beneficiario_encontrado['nombres']}"

        confirmacion = QMessageBox.question(
            self, "Confirmar Cambio", 
            f"¿Está seguro que desea cambiar el cargo de {nombre} a '{nuevo_cargo}'?\n\n"
            "*Nota: Si se asigna un cargo de comisión, se le creará automáticamente una cuenta de acceso.*",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmacion == QMessageBox.StandardButton.Yes:
            exito, msj = backend.actualizar_cargo_beneficiario(lu, nuevo_cargo)
            if exito:
                QMessageBox.information(self, "Éxito", f"¡El cargo de {nombre} ha sido actualizado a '{nuevo_cargo}'!")
                self.input_buscar_lu.clear()
                self.card_detalles.setVisible(False)
                self.btn_guardar.setEnabled(False)
                self.beneficiario_encontrado = None
                self.actualizar_tabla_datos()
            else:
                QMessageBox.critical(self, "Error", msj)
