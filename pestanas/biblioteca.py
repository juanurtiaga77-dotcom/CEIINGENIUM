import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QMessageBox, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

import backend.db_biblioteca as backend
import backend.db_prestamos as back_alumno 
from backend.utils_vistas import procesar_avatar_circular

class PestañaBiblioteca(QWidget):
    def __init__(self, lu_admin):
        super().__init__()
        self.lu_admin = lu_admin
        self.beneficiario_actual = None
        
        self.cola_devoluciones = {}
        self.cargar_cola_local()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.procesar_cola)
        self.timer.start(1000)
        
        self.inicializar_ui()

    def cargar_cola_local(self):
        archivo = "cola_biblio.json"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                ahora = datetime.now()
                
                for id_str, data in datos.items():
                    id_p = int(id_str)
                    inicio = datetime.strptime(data['inicio'], '%Y-%m-%d %H:%M:%S')
                    segundos_pasados = (ahora - inicio).total_seconds()
                    
                    if segundos_pasados >= 300:
                        backend.consolidar_devolucion_biblio(id_p, self.lu_admin, data['danado'], inicio)
                    else:
                        self.cola_devoluciones[id_p] = {
                            'inicio': inicio,
                            'danado': data['danado'],
                            'btn': None
                        }
                os.remove(archivo)
            except Exception as e:
                print(f"Error cargando cola local biblio: {e}")

    def forzar_cierre_seguro(self):
        datos = {}
        for id_p, data in self.cola_devoluciones.items():
            datos[str(id_p)] = {
                'inicio': data['inicio'].strftime('%Y-%m-%d %H:%M:%S'),
                'danado': data['danado']
            }
        if datos:
            try:
                with open("cola_biblio.json", "w", encoding="utf-8") as f:
                    json.dump(datos, f)
            except Exception:
                pass

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # --- ZONA SUPERIOR: BÚSQUEDA Y ASIGNACIÓN ---
        layout_superior = QHBoxLayout()
        
        # 1. Buscador y Tarjeta de Beneficiario
        frame_beneficiario = QFrame()
        frame_beneficiario.setStyleSheet("background-color: white; border-radius: 10px;")
        layout_bene_main = QHBoxLayout(frame_beneficiario)
        
        self.lbl_foto_bene = QLabel("👤")
        self.lbl_foto_bene.setFixedSize(60, 60)
        self.lbl_foto_bene.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto_bene.setStyleSheet("font-size: 30px; background-color: #f1faff; border-radius: 30px;")
        
        layout_bene_text = QVBoxLayout()
        self.input_bene = QLineEdit()
        self.input_bene.setPlaceholderText("🔍 Ingrese LU o DNI y presione ENTER...")
        self.input_bene.setStyleSheet("padding: 8px; border: 1px solid #ccc;")
        self.input_bene.returnPressed.connect(self.buscar_alumno)
        
        self.lbl_info_bene = QLabel("Busque un beneficiario para comenzar.")
        self.lbl_info_bene.setStyleSheet("color: #666; font-size: 13px;")
        self.lbl_info_bene.setWordWrap(True)
        
        layout_bene_text.addWidget(self.input_bene)
        layout_bene_text.addWidget(self.lbl_info_bene)
        
        layout_bene_main.addWidget(self.lbl_foto_bene)
        layout_bene_main.addLayout(layout_bene_text)
        
        layout_superior.addWidget(frame_beneficiario, stretch=1)

        # 2. Selección de Objeto (Libro)
        frame_objeto = QFrame()
        frame_objeto.setStyleSheet("background-color: white; border-radius: 10px;")
        layout_obj = QVBoxLayout(frame_objeto)
        
        layout_obj.addWidget(QLabel("Seleccionar libro/apunte a prestar:"))
        self.combo_objetos = QComboBox()
        self.combo_objetos.setStyleSheet("padding: 8px; border: 1px solid #ccc;")
        layout_obj.addWidget(self.combo_objetos)
        
        self.btn_prestar = QPushButton("✅ Asignar Préstamo (8 Días)")
        self.btn_prestar.setStyleSheet("background-color: #00b4d8; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_prestar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prestar.clicked.connect(self.ejecutar_prestamo)
        self.btn_prestar.setEnabled(False) 
        layout_obj.addWidget(self.btn_prestar)
        
        layout_superior.addWidget(frame_objeto, stretch=1)
        layout_principal.addLayout(layout_superior)

        # --- ZONA INFERIOR: HISTORIAL ---
        layout_filtro = QHBoxLayout()
        layout_filtro.addWidget(QLabel("<b>Historial de Movimientos de Biblioteca</b>"))
        layout_filtro.addStretch()
        self.input_filtro = QLineEdit()
        self.input_filtro.setPlaceholderText("🔍 Filtrar por LU o Nombre...")
        
        # --- CAMBIO 1: Conectamos la barra al filtro visual rápido ---
        self.input_filtro.textChanged.connect(self.filtrar_tabla)
        
        layout_filtro.addWidget(self.input_filtro)
        layout_principal.addLayout(layout_filtro)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "LU", "Alumno", "Libro / Apunte", "Fecha Préstamo", "Hora", "Devolución", "Estado", "Acciones"
        ])
        self.tabla.setColumnHidden(0, True)
        
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(8, 230)
        
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: transparent; border: none; }")
        
        layout_principal.addWidget(self.tabla)
        
        self.cargar_combo_objetos()
        self.actualizar_tabla()

    def buscar_alumno(self):
        criterio = self.input_bene.text().strip()
        if not criterio: return
        
        b = back_alumno.buscar_beneficiario(criterio)
        if not b:
            self.lbl_foto_bene.clear()
            self.lbl_foto_bene.setText("❌")
            self.lbl_info_bene.setText("No se encuentra registrado en el sistema. (No tiene carnet).")
            self.lbl_info_bene.setStyleSheet("color: #f44336; font-size: 14px; font-weight: bold;")
            self.beneficiario_actual = None
            self.btn_prestar.setEnabled(False)
            return
            
        self.beneficiario_actual = b
        
        pixmap = procesar_avatar_circular(b['ruta_foto'], 60)
        if pixmap:
            self.lbl_foto_bene.setPixmap(pixmap)
        else:
            self.lbl_foto_bene.setText("👤")

        texto_html = f"<b>{b['apellidos']}, {b['nombres']}</b>"
        
        if b['penalizado']:
            texto_html += f"<br><span style='color:#f44336; font-weight:bold;'>⛔ PENALIZADO: No está habilitado para retirar libros.</span>"
            self.btn_prestar.setEnabled(False)
        else:
            texto_html += "<br><span style='color:#4CAF50; font-weight:bold;'>✅ Habilitado para utilizar la biblioteca.</span>"
            self.btn_prestar.setEnabled(True)

        self.lbl_info_bene.setStyleSheet("color: #333; font-size: 13px;")
        self.lbl_info_bene.setText(texto_html)

    def cargar_combo_objetos(self):
        self.combo_objetos.clear()
        for lib in backend.buscar_libros_disponibles():
            self.combo_objetos.addItem(f"{lib['nombre']} (Disp: {lib['disponible']})", lib['id'])

    def ejecutar_prestamo(self):
        if not self.beneficiario_actual or self.combo_objetos.currentIndex() == -1: return
        
        id_libro = self.combo_objetos.currentData()
        nombre_libro = self.combo_objetos.currentText().split(" (")[0]
        lu_bene = self.beneficiario_actual['lu']

        exito, msj = backend.prestar_libro(lu_bene, id_libro, nombre_libro, self.lu_admin)
        
        if exito:
            self.input_bene.clear()
            self.lbl_foto_bene.setText("✅")
            self.lbl_info_bene.setText("<span style='color:#4CAF50; font-weight:bold; font-size:16px;'>¡Préstamo registrado exitosamente!</span>")
            self.beneficiario_actual = None
            self.btn_prestar.setEnabled(False)
            self.cargar_combo_objetos()
            self.actualizar_tabla()
        else:
            QMessageBox.warning(self, "Operación Denegada", msj)

    def actualizar_tabla(self):
        # --- CAMBIO 2: Se pide TODO el historial al backend sin usar el filtro de texto ---
        historial = backend.obtener_historial_biblio("")
        self.tabla.setRowCount(0)

        for f_idx, h in enumerate(historial):
            self.tabla.insertRow(f_idx)
            self.tabla.setRowHeight(f_idx, 45)
            
            id_p = h['id']
            
            self.tabla.setItem(f_idx, 0, QTableWidgetItem(str(id_p)))
            self.tabla.setItem(f_idx, 1, QTableWidgetItem(str(h['lu_beneficiario'])))
            self.tabla.setItem(f_idx, 2, QTableWidgetItem(f"{h['apellidos_beneficiario']}, {h['nombres_beneficiario']}"))
            self.tabla.setItem(f_idx, 3, QTableWidgetItem(str(h['nombre_libro'])))
            
            fecha_str = h['fecha_prestamo'].strftime('%d/%m/%Y') if hasattr(h['fecha_prestamo'], 'strftime') else str(h['fecha_prestamo'])
            hora_str = str(h['hora_prestamo'])
            self.tabla.setItem(f_idx, 4, QTableWidgetItem(fecha_str))
            self.tabla.setItem(f_idx, 5, QTableWidgetItem(hora_str))

            if h['devuelto']:
                self.tabla.setItem(f_idx, 6, QTableWidgetItem(f"{h['fecha_devolucion']} {h['hora_devolucion']}"))
                item_est = QTableWidgetItem("🟢 Devuelto")
                item_est.setForeground(QColor("#4CAF50"))
                self.tabla.setItem(f_idx, 7, item_est)
                self.tabla.setCellWidget(f_idx, 8, QLabel("")) 
            else:
                self.tabla.setItem(f_idx, 6, QTableWidgetItem("-"))
                
                if id_p in self.cola_devoluciones:
                    item_est = QTableWidgetItem("⏳ Procesando...")
                    item_est.setForeground(QColor("#FF9800"))
                    self.tabla.setItem(f_idx, 7, item_est)
                    
                    widget_btn = QWidget()
                    layout_b = QHBoxLayout(widget_btn)
                    layout_b.setContentsMargins(2, 2, 2, 2)
                    layout_b.setSpacing(5)
                    
                    btn_deshacer = QPushButton("↩️ Deshacer")
                    btn_deshacer.setStyleSheet("background-color: #9e9e9e; color: white; padding: 5px; font-weight: bold; min-width: 90px;")
                    btn_deshacer.setProperty("id_p", id_p)
                    btn_deshacer.clicked.connect(self.cancelar_devolucion)
                    
                    btn_danado = QPushButton("⚠️ Dañado")
                    if self.cola_devoluciones[id_p]['danado']:
                        btn_danado.setStyleSheet("background-color: #f44336; color: white; border: 2px solid black; padding: 5px; font-weight: bold; min-width: 90px;")
                        btn_danado.setText("Marcado")
                        btn_danado.setEnabled(False)
                    else:
                        btn_danado.setStyleSheet("background-color: #FF9800; color: white; padding: 5px; font-weight: bold; min-width: 90px;")
                        btn_danado.setProperty("id_p", id_p)
                        btn_danado.clicked.connect(self.marcar_danado)
                        
                    layout_b.addWidget(btn_deshacer)
                    layout_b.addWidget(btn_danado)
                    self.tabla.setCellWidget(f_idx, 8, widget_btn)
                    
                    self.cola_devoluciones[id_p]['btn'] = btn_deshacer 

                else:
                    item_est = QTableWidgetItem("🔴 Prestado")
                    item_est.setForeground(QColor("#f44336"))
                    self.tabla.setItem(f_idx, 7, item_est)
                    
                    btn_dev = QPushButton("Devolver Libro")
                    btn_dev.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
                    btn_dev.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_dev.setProperty("id_p", id_p)
                    btn_dev.clicked.connect(self.iniciar_devolucion)
                    self.tabla.setCellWidget(f_idx, 8, btn_dev)

        # --- CAMBIO 3: Ejecutamos el filtro visual justo después de cargar todos los datos ---
        self.filtrar_tabla(self.input_filtro.text())

    def iniciar_devolucion(self):
        id_p = self.sender().property("id_p")
        self.cola_devoluciones[id_p] = {
            'inicio': datetime.now(), 
            'danado': False,
            'btn': None
        }
        self.actualizar_tabla()

    def cancelar_devolucion(self):
        id_p = self.sender().property("id_p")
        if id_p in self.cola_devoluciones:
            del self.cola_devoluciones[id_p]
            self.actualizar_tabla()

    def marcar_danado(self):
        id_p = self.sender().property("id_p")
        if id_p in self.cola_devoluciones:
            confirmar = QMessageBox.question(self, "ALERTA CRÍTICA", "¿Seguro que el libro o apunte está dañado? Esto penalizará al alumno por 1 AÑO (8760 horas).", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirmar == QMessageBox.StandardButton.Yes:
                self.cola_devoluciones[id_p]['danado'] = True
                self.actualizar_tabla()

    def procesar_cola(self):
        ahora = datetime.now()
        ids_para_borrar = []

        for id_p, data in self.cola_devoluciones.items():
            segundos_pasados = (ahora - data['inicio']).total_seconds()
            segundos_restantes = 300 - segundos_pasados 
            
            if segundos_restantes <= 0:
                backend.consolidar_devolucion_biblio(id_p, self.lu_admin, data['danado'], data['inicio'])
                ids_para_borrar.append(id_p)
            elif data['btn']:
                mins = int(segundos_restantes // 60)
                secs = int(segundos_restantes % 60)
                data['btn'].setText(f"↩️ {mins}:{secs:02d}")

        if ids_para_borrar:
            for i in ids_para_borrar: del self.cola_devoluciones[i]
            self.actualizar_tabla()
            self.cargar_combo_objetos()

    # --- CAMBIO 4: La nueva función de filtro instantáneo ---
    def filtrar_tabla(self, texto):
        """Oculta las filas que no coinciden con la búsqueda (Instantáneo e Inteligente)"""
        t = texto.strip().lower()
        
        # --- TRUCO MÁGICO PARA DNI ---
        # Si escriben 7 o más números (un DNI completo), traducimos ese DNI a LU internamente
        lu_traducido = None
        if t.isdigit() and len(t) >= 7:
            b = back_alumno.buscar_beneficiario(t) # ¡Aquí usamos back_alumno!
            if b:
                lu_traducido = str(b['lu']).lower()

        for fila in range(self.tabla.rowCount()):
            item_lu = self.tabla.item(fila, 1)      
            item_nombre = self.tabla.item(fila, 2)  
            
            coincide = False
            if item_lu and t in item_lu.text().lower(): coincide = True
            if item_nombre and t in item_nombre.text().lower(): coincide = True
            if lu_traducido and item_lu and lu_traducido == item_lu.text().lower(): coincide = True
            
            self.tabla.setRowHidden(fila, not coincide)