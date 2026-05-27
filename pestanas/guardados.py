import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QComboBox,
                             QVBoxLayout, QHBoxLayout, QMessageBox, QFrame, QTextEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

import backend.db_guardados as backend
import backend.db_prestamos as backend_alumno # Reutilizamos tu buscador de alumnos existente

class DialogoGuardar(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Depósito / Guardado")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.input_lu = QLineEdit()
        self.input_lu.setPlaceholderText("Ingrese LU del alumno beneficiario...")
        self.input_lu.textChanged.connect(self.verificar_alumno_dinamico)
        
        self.lbl_nombre_alumno = QLabel("Introduce una libreta válida.")
        self.lbl_nombre_alumno.setStyleSheet("color: gray; font-style: italic;")
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Objeto", "Comida", "TPs (Trabajos Prácticos)"])
        
        self.input_lugar = QLineEdit()
        self.input_lugar.setPlaceholderText("Ej: Armario A, Heladera, Estante TPs...")
        
        self.input_desc = QTextEdit()
        self.input_desc.setMaximumHeight(70)
        self.input_desc.setPlaceholderText("Detalles o características del elemento...")

        layout.addRow("LU Beneficiario:", self.input_lu)
        layout.addRow("", self.lbl_nombre_alumno)
        layout.addRow("¿Qué deja?:", self.combo_tipo)
        layout.addRow("Lugar donde queda:", self.input_lugar)
        layout.addRow("Descripción:", self.input_desc)

        layout_botones = QHBoxLayout()
        self.btn_guardar = QPushButton("Registrar Ingreso")
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_guardar.clicked.connect(self.accept)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #f44336; color: white; padding: 6px;")
        btn_cancelar.clicked.connect(self.reject)
        
        layout_botones.addWidget(self.btn_guardar); layout_botones.addWidget(btn_cancelar)
        layout.addRow(layout_botones)

    def verificar_alumno_dinamico(self):
        lu = self.input_lu.text().strip()
        if len(lu) >= 3:
            b = backend_alumno.buscar_beneficiario(lu)
            if b:
                self.lbl_nombre_alumno.setText(f"✅ Alumno: {b['apellidos']}, {b['nombres']}")
                self.lbl_nombre_alumno.setStyleSheet("color: #4CAF50; font-weight: bold;")
                self.btn_guardar.setEnabled(True)
                return
        self.lbl_nombre_alumno.setText("Introduce una libreta válida.")
        self.lbl_nombre_alumno.setStyleSheet("color: gray; font-style: italic;")
        self.btn_guardar.setEnabled(False)

    def obtener_datos(self):
        return {
            "lu_beneficiario": self.input_lu.text().strip(),
            "tipo_item": self.combo_tipo.currentText(),
            "lugar": self.input_lugar.text().strip(),
            "desc": self.input_desc.toPlainText().strip()
        }


class PestañaGuardados(QWidget):
    def __init__(self, lu_administrador):
        super().__init__()
        self.lu_admin = lu_administrador 
        self.cola_devoluciones = {} 
        
        self.cargar_cola_local()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.procesar_cola)
        self.timer.start(1000)

        self.inicializar_ui()

    def cargar_cola_local(self):
        archivo = "cola_guardados.json"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                ahora = datetime.now()
                for id_str, data in datos.items():
                    ts = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
                    # 10 minutos son 600 segundos
                    if (ahora - ts).total_seconds() < 600:
                        self.cola_devoluciones[int(id_str)] = {'timestamp': ts, 'btn': None}
                os.remove(archivo)
            except: pass

    def forzar_cierre_seguro(self):
        datos = {}
        for id_g, data in self.cola_devoluciones.items():
            datos[str(id_g)] = {'timestamp': data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        if datos:
            try:
                with open("cola_guardados.json", "w", encoding="utf-8") as f: json.dump(datos, f)
            except: pass

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        layout_herramientas = QHBoxLayout()
        self.btn_agregar = QPushButton("➕ Registrar Elemento Guardado")
        self.btn_agregar.setStyleSheet("background-color: #00b4d8; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.clicked.connect(self.controlador_agregar)
        layout_herramientas.addWidget(self.btn_agregar)
        layout_herramientas.addStretch()
        layout_principal.addLayout(layout_herramientas)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(10)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "LU Alumno", "Estudiante", "¿Qué dejó?", "Descripción", 
            "Lugar Ubicación", "Fecha Ingreso", "Hora Ingreso", "Fecha/Hora Entrega", "Acciones"
        ])
        self.tabla.setColumnHidden(0, True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(9, 170) # Ancho perfecto para evitar el bug de Windows
        
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: transparent; border: none; }")
        
        layout_principal.addWidget(self.tabla)
        self.actualizar_tabla_datos()

    def actualizar_tabla_datos(self):
        elementos = backend.obtener_todos_guardados()
        self.tabla.setRowCount(0)

        for i, el in enumerate(elementos):
            self.tabla.insertRow(i)
            self.tabla.setRowHeight(i, 45)
            id_g = el['id']
            
            self.tabla.setItem(i, 0, QTableWidgetItem(str(id_g)))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(el['lu_beneficiario'])))
            
            alumno_str = f"{el['apellidos']}, {el['nombres']}" if el['apellidos'] else "No registrado"
            self.tabla.setItem(i, 2, QTableWidgetItem(alumno_str))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(el['tipo_item'])))
            
            item_desc = QTableWidgetItem(str(el['descripcion']))
            item_desc.setToolTip(str(el['descripcion']))
            self.tabla.setItem(i, 4, item_desc)
            
            self.tabla.setItem(i, 5, QTableWidgetItem(str(el['lugar_guardado'])))
            
            f_ing = el['fecha_registro'].strftime('%d/%m/%Y') if hasattr(el['fecha_registro'], 'strftime') else str(el['fecha_registro'])
            self.tabla.setItem(i, 6, QTableWidgetItem(f_ing))
            self.tabla.setItem(i, 7, QTableWidgetItem(str(el['hora_registro'])))
            
            # Formateo de Entrega
            if el['fecha_entrega']:
                f_ent = el['fecha_entrega'].strftime('%d/%m/%Y') if hasattr(el['fecha_entrega'], 'strftime') else str(el['fecha_entrega'])
                self.tabla.setItem(i, 8, QTableWidgetItem(f"{f_ent} {el['hora_entrega']}"))
            else:
                self.tabla.setItem(i, 8, QTableWidgetItem("En Depósito"))

            # --- PANEL DE ACCIONES ---
            w_btns = QWidget(); l_btns = QHBoxLayout(w_btns); l_btns.setContentsMargins(2,2,2,2)

            if id_g in self.cola_devoluciones:
                btn_deshacer = QPushButton("↩️ Deshacer (10:00)")
                btn_deshacer.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 5px; padding-left:0px; padding-right:0px; border-radius: 4px;")
                btn_deshacer.clicked.connect(lambda ch, id=id_g: self.cancelar_entrega(id))
                self.cola_devoluciones[id_g]['btn'] = btn_deshacer
                l_btns.addWidget(btn_deshacer)
            elif el['fecha_entrega'] is None:
                btn_entregar = QPushButton("🤝 Entregar Objeto")
                btn_entregar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px; border-radius: 4px;")
                btn_entregar.clicked.connect(lambda ch, id=id_g: self.iniciar_entrega(id))
                l_btns.addWidget(btn_entregar)
            else:
                item_estado = QTableWidgetItem("🟢 Retirado")
                item_estado.setForeground(QColor("#4CAF50"))
                self.tabla.setItem(i, 9, item_estado)
                continue
                
            self.tabla.setCellWidget(i, 9, w_btns)

    def controlador_agregar(self):
        dialogo = DialogoGuardar(self)
        if dialogo.exec():
            d = dialogo.obtener_datos()
            if not d['lugar'] or not d['desc']:
                QMessageBox.warning(self, "Error", "El lugar y la descripción son campos obligatorios.")
                return
            exito, msj = backend.registrar_elemento_guardado(d['lu_beneficiario'], d['tipo_item'], d['desc'], d['lugar'], self.lu_admin)
            if exito: self.actualizar_tabla_datos()
            else: QMessageBox.critical(self, "Error", msj)

    def iniciar_entrega(self, id_g):
        # 1. Hacemos el cambio visual y físico directo en la DB
        if backend.consolidar_entrega_db(id_g, self.lu_admin):
            # 2. Iniciamos cronómetro de gracia en la RAM
            self.cola_devoluciones[id_g] = {'timestamp': datetime.now(), 'btn': None}
            self.actualizar_tabla_datos()

    def cancelar_entrega(self, id_g):
        if id_g in self.cola_devoluciones:
            # Revertimos en la DB el estado del depósito
            if backend.deshacer_entrega_db(id_g, self.lu_admin):
                del self.cola_devoluciones[id_g]
                self.actualizar_tabla_datos()

    def procesar_cola(self):
        ahora = datetime.now()
        completados = []

        for id_g, data in self.cola_devoluciones.items():
            restante = 600 - (ahora - data['timestamp']).total_seconds() # 600 seg = 10 minutos
            if restante <= 0:
                completados.append(id_g)
            elif data['btn']:
                m, s = divmod(int(restante), 60)
                data['btn'].setText(f"↩️ Deshacer ({m}:{s:02d})")

        if completados:
            for i in completados: del self.cola_devoluciones[i]
            self.actualizar_tabla_datos()