import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QMessageBox, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QDialog, QFormLayout, QTextEdit, QFileDialog, QDateEdit, QTimeEdit)
from PyQt6.QtCore import Qt, QTimer, QDate, QTime
from PyQt6.QtGui import QColor, QFont, QPixmap

import backend.db_perdidos as backend

class DialogoPerdido(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Objeto Perdido")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.input_persona = QLineEdit()
        self.input_persona.setPlaceholderText("Ej: Juan Pérez (Ing. Civil)")
        
        self.date_encuentro = QDateEdit()
        self.date_encuentro.setCalendarPopup(True)
        self.date_encuentro.setDate(QDate.currentDate())
        
        self.time_encuentro = QTimeEdit()
        self.time_encuentro.setTime(QTime.currentTime())
        
        self.input_desc = QTextEdit()
        self.input_desc.setMaximumHeight(60)
        self.input_desc.setPlaceholderText("Descripción detallada del objeto...")
        
        self.input_lugar = QLineEdit()
        self.input_lugar.setPlaceholderText("Ej: Aula 12, Baño Norte...")
        
        self.input_ubicacion = QLineEdit()
        self.input_ubicacion.setPlaceholderText("Ej: Estante 3, Caja Fuerte...")
        
        # Subida de foto
        layout_foto = QHBoxLayout()
        self.lbl_ruta_foto = QLabel("Sin foto")
        self.lbl_ruta_foto.setStyleSheet("color: gray;")
        btn_foto = QPushButton("📷 Buscar Foto")
        btn_foto.clicked.connect(self.seleccionar_foto)
        layout_foto.addWidget(btn_foto); layout_foto.addWidget(self.lbl_ruta_foto, stretch=1)
        self.ruta_archivo_foto = ""

        layout.addRow("Persona que lo encontró:", self.input_persona)
        layout.addRow("Fecha de hallazgo:", self.date_encuentro)
        layout.addRow("Hora de hallazgo:", self.time_encuentro)
        layout.addRow("Lugar exacto del hallazgo:", self.input_lugar)
        layout.addRow("Ubicación actual en CEI:", self.input_ubicacion)
        layout.addRow("Descripción:", self.input_desc)
        layout.addRow("Fotografía:", layout_foto)

        layout_botones = QHBoxLayout()
        btn_guardar = QPushButton("Registrar")
        btn_guardar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        btn_guardar.clicked.connect(self.accept)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #f44336; color: white; padding: 6px;")
        btn_cancelar.clicked.connect(self.reject)
        
        layout_botones.addWidget(btn_guardar); layout_botones.addWidget(btn_cancelar)
        layout.addRow(layout_botones)

    def seleccionar_foto(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto", "", "Imágenes (*.png *.jpg *.jpeg *.webp)")
        if ruta:
            self.ruta_archivo_foto = ruta
            self.lbl_ruta_foto.setText(os.path.basename(ruta))
            self.lbl_ruta_foto.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def obtener_datos(self):
        return {
            "datos_persona": self.input_persona.text().strip(),
            "fecha_enc": self.date_encuentro.date().toString("yyyy-MM-dd"),
            "hora_enc": self.time_encuentro.time().toString("HH:mm:ss"),
            "desc": self.input_desc.toPlainText().strip(),
            "lugar": self.input_lugar.text().strip(),
            "ubicacion": self.input_ubicacion.text().strip(),
            "ruta_foto": self.ruta_archivo_foto
        }


class PestañaPerdidos(QWidget):
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
        archivo = "cola_perdidos.json"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                ahora = datetime.now()
                
                for id_str, data in datos.items():
                    ts = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
                    if (ahora - ts).total_seconds() < 600: # 10 minutos (600 seg)
                        self.cola_devoluciones[int(id_str)] = {
                            'timestamp': ts,
                            'desc': data['desc'],
                            'btn': None
                        }
                    else:
                        # Si expiró con la app cerrada, borrar de DB
                        backend.eliminar_perdido_db(int(id_str), self.lu_admin, data['desc'])
                os.remove(archivo) 
            except Exception as e: print(f"Error cargando cola perdidos: {e}")

    def forzar_cierre_seguro(self):
        datos = {}
        for id_obj, data in self.cola_devoluciones.items():
            datos[str(id_obj)] = {
                'timestamp': data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'desc': data['desc']
            }
        if datos:
            try:
                with open("cola_perdidos.json", "w", encoding="utf-8") as f:
                    json.dump(datos, f)
            except: pass

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        # BARRA SUPERIOR
        layout_herramientas = QHBoxLayout()
        self.btn_agregar = QPushButton("➕ Registrar Objeto Perdido")
        self.btn_agregar.setStyleSheet("background-color: #00b4d8; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.clicked.connect(self.controlador_agregar)
        layout_herramientas.addWidget(self.btn_agregar)

        layout_herramientas.addStretch()

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar objeto por descripción...")
        self.input_busqueda.setMinimumWidth(300)
        self.input_busqueda.textChanged.connect(self.filtrar_tabla)
        self.input_busqueda.setStyleSheet("padding: 8px; border: 1px solid #ccc;")
        layout_herramientas.addWidget(self.input_busqueda)

        layout_principal.addLayout(layout_herramientas)

        # TABLA
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Foto", "Descripción", "Encontrado Por", "Fecha/Hora Hallazgo", "Lugar Hallazgo", "Ubicación CEI", "Registro", "Acciones"
        ])
        self.tabla.setColumnHidden(0, True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(8, 160)
        
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: transparent; border: none; }")
        
        layout_principal.addWidget(self.tabla)
        self.actualizar_tabla_datos()

    def actualizar_tabla_datos(self):
        objetos = backend.obtener_objetos_perdidos()
        self.tabla.setRowCount(0)

        for i, obj in enumerate(objetos):
            self.tabla.insertRow(i)
            self.tabla.setRowHeight(i, 60) # Altura generosa para la foto
            id_obj = obj['id']
            
            self.tabla.setItem(i, 0, QTableWidgetItem(str(id_obj)))
            
            # --- MANEJO DE LA FOTO ---
            lbl_img = QLabel()
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if obj['ruta_foto'] and os.path.exists(obj['ruta_foto']):
                pix = QPixmap(obj['ruta_foto']).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                lbl_img.setPixmap(pix)
            else:
                lbl_img.setText("📷")
                lbl_img.setStyleSheet("font-size: 24px; color: #aaa;")
            self.tabla.setCellWidget(i, 1, lbl_img)
            # -------------------------

            self.tabla.setItem(i, 2, QTableWidgetItem(obj['descripcion_objeto']))
            self.tabla.setItem(i, 3, QTableWidgetItem(obj['datos_persona_encuentra']))
            
            fh_encuentro = f"{obj['fecha_encuentro']} {obj['hora_encuentro']}"
            self.tabla.setItem(i, 4, QTableWidgetItem(fh_encuentro))
            self.tabla.setItem(i, 5, QTableWidgetItem(obj['lugar_encuentro']))
            self.tabla.setItem(i, 6, QTableWidgetItem(obj['ubicacion_en_cei']))
            
            fh_registro = f"{obj['fecha_registro']} {obj['hora_registro']}"
            self.tabla.setItem(i, 7, QTableWidgetItem(fh_registro))
            
            # --- ACCIONES (CON 10 MINS DE DESHACER) ---
            w_btns = QWidget()
            l_btns = QHBoxLayout(w_btns)
            l_btns.setContentsMargins(4,4,4,4)

            if id_obj in self.cola_devoluciones:
                btn_deshacer = QPushButton("↩️ Deshacer (10:00)")
                btn_deshacer.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 6px; border-radius: 4px;")
                btn_deshacer.clicked.connect(lambda ch, id=id_obj: self.cancelar_devolucion(id))
                self.cola_devoluciones[id_obj]['btn'] = btn_deshacer
                l_btns.addWidget(btn_deshacer)
            else:
                btn_dev = QPushButton("🤝 Devolver")
                btn_dev.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px; border-radius: 4px;")
                btn_dev.clicked.connect(lambda ch, id=id_obj, desc=obj['descripcion_objeto']: self.iniciar_devolucion(id, desc))
                l_btns.addWidget(btn_dev)
                
            self.tabla.setCellWidget(i, 8, w_btns)

    def filtrar_tabla(self, texto):
        t = texto.strip().lower()
        for fila in range(self.tabla.rowCount()):
            item = self.tabla.item(fila, 2) # Filtra por descripción
            self.tabla.setRowHidden(fila, item and t not in item.text().lower())

    def controlador_agregar(self):
        dialogo = DialogoPerdido(self)
        if dialogo.exec():
            d = dialogo.obtener_datos()
            if not d['desc'] or not d['lugar']:
                QMessageBox.warning(self, "Error", "La descripción y el lugar son obligatorios.")
                return
            exito, msj = backend.agregar_objeto_perdido(
                d['datos_persona'], d['fecha_enc'], d['hora_enc'], 
                d['desc'], d['lugar'], d['ubicacion'], d['ruta_foto'], self.lu_admin
            )
            if exito: self.actualizar_tabla_datos()
            else: QMessageBox.critical(self, "Error", msj)

    def iniciar_devolucion(self, id_obj, descripcion):
        self.cola_devoluciones[id_obj] = {
            'timestamp': datetime.now(), 
            'desc': descripcion,
            'btn': None
        }
        self.actualizar_tabla_datos()

    def cancelar_devolucion(self, id_obj):
        if id_obj in self.cola_devoluciones:
            del self.cola_devoluciones[id_obj]
            self.actualizar_tabla_datos()

    def procesar_cola(self):
        ahora = datetime.now()
        borrar = []

        for id_obj, data in self.cola_devoluciones.items():
            restante = 600 - (ahora - data['timestamp']).total_seconds() # 600 segundos = 10 minutos
            if restante <= 0:
                backend.eliminar_perdido_db(id_obj, self.lu_admin, data['desc'])
                borrar.append(id_obj)
            elif data['btn']:
                m, s = divmod(int(restante), 60)
                data['btn'].setText(f"↩️ Deshacer ({m}:{s:02d})")

        if borrar:
            for i in borrar: del self.cola_devoluciones[i]
            self.actualizar_tabla_datos()