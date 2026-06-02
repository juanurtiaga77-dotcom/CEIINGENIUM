import os
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QMessageBox, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                             QDialog, QInputDialog) # <--- Asegúrate de tener QInputDialog aquí
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPixmap # <--- Importación de QPixmap añadida

import backend.db_prestamos as backend
import backend.db_carnets as db_carnets # <--- Importado para buscar el motivo de sanción
from backend.utils_vistas import procesar_avatar_circular

class PestañaPrestamos(QWidget):
    def __init__(self, lu_administrador):
        super().__init__()
        self.lu_admin = lu_administrador 
        self.beneficiario_actual = None
        
        self.cola_devoluciones = {}
        self.cargar_cola_local() # Recupera la cola si se cerró la app bruscamente
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.procesar_cola)
        self.timer.start(1000)

        self.timer_sincronizacion = QTimer(self)
        self.timer_sincronizacion.timeout.connect(self.actualizar_tabla)
        self.timer_sincronizacion.start(2000)

        self.inicializar_ui()

    def cargar_cola_local(self):
        """Si el programa se cerró, recupera los temporizadores de un archivo local."""
        import socket
        archivo = f"cola_devoluciones_{socket.gethostname()}.json"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r") as f:
                    datos = json.load(f)
                ahora = datetime.now()
                
                for id_p_str, data in datos.items():
                    id_p = int(id_p_str)
                    inicio = datetime.strptime(data['inicio'], '%Y-%m-%d %H:%M:%S')
                    segundos_pasados = (ahora - inicio).total_seconds()
                    
                    if segundos_pasados >= 300:
                        # Si estuvo apagada más de 5 minutos, consolida en DB
                        backend.consolidar_devolucion_db(id_p, self.lu_admin, data['danado'], inicio)
                    else:
                        # Si todavía tiene tiempo, vuelve a la memoria RAM
                        self.cola_devoluciones[id_p] = {
                            'inicio': inicio,
                            'danado': data['danado'],
                            'btn': None
                        }
                os.remove(archivo) # Limpiamos el archivo residual
            except Exception as e:
                print(f"Error cargando cola local: {e}")

    def forzar_cierre_seguro(self):
        """En vez de mandarlo a DB forzado, lo guarda en JSON para reanudar luego."""
        datos = {}
        for id_p, data in self.cola_devoluciones.items():
            datos[str(id_p)] = {
                'inicio': data['inicio'].strftime('%Y-%m-%d %H:%M:%S'),
                'danado': data['danado']
            }
        if datos:
            try:
                import socket
                archivo = f"cola_devoluciones_{socket.gethostname()}.json"
                with open(archivo, "w") as f:
                    json.dump(datos, f)
            except Exception as e:
                print(f"Error guardando cola local: {e}")

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        layout_superior = QHBoxLayout()
        
        frame_beneficiario = QFrame()
        frame_beneficiario.setObjectName("frame_card_beneficiario")
        layout_bene_main = QHBoxLayout(frame_beneficiario)
        
        self.lbl_foto_bene = QLabel("👤")
        self.lbl_foto_bene.setObjectName("lbl_foto_bene")
        self.lbl_foto_bene.setFixedSize(60, 60)
        self.lbl_foto_bene.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- ACTIVACIÓN DE CLIC EN LA FOTO ---
        self.lbl_foto_bene.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_foto_bene.mousePressEvent = self.mostrar_foto_ampliada
        
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

        frame_objeto = QFrame()
        frame_objeto.setObjectName("frame_card_objeto")
        layout_obj = QVBoxLayout(frame_objeto)
        
        layout_obj.addWidget(QLabel("Seleccionar objeto a prestar:"))
        self.combo_objetos = QComboBox()
        self.combo_objetos.setObjectName("combo_objetos")
        layout_obj.addWidget(self.combo_objetos)
        
        self.btn_prestar = QPushButton("✅ Asignar Préstamo")
        self.btn_prestar.setStyleSheet("background-color: #00b4d8; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_prestar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prestar.clicked.connect(self.ejecutar_prestamo)
        self.btn_prestar.setEnabled(False) 
        layout_obj.addWidget(self.btn_prestar)
        
        layout_superior.addWidget(frame_objeto, stretch=1)
        layout_principal.addLayout(layout_superior)

        layout_filtro = QHBoxLayout()
        layout_filtro.addWidget(QLabel("<b>Historial de Movimientos</b>"))
        layout_filtro.addStretch()
        self.input_filtro = QLineEdit()
        self.input_filtro.setPlaceholderText("🔍 Filtrar por LU o Nombre...")
        self.input_filtro.textChanged.connect(self.filtrar_tabla)
        
        layout_filtro.addWidget(self.input_filtro)
        layout_principal.addLayout(layout_filtro)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "LU", "Alumno", "Objeto", "Fecha Préstamo", "Hora", "Devolución", "Estado", "Acciones"
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
        
        b = backend.buscar_beneficiario(criterio)
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

        texto_html = f"<b>{b['apellidos']}, {b['nombres']}</b><br>Préstamos Activos: <b>{b['prestamos_activos']}/5</b>"
        
        if b['penalizado']:
            # --- NUEVA LÓGICA DE CARTEL ROJO CON MOTIVOS ---
            razon_texto = db_carnets.obtener_motivo_sancion_activa(b['lu'])
            
            if b.get('horas_penalizacion') == -1:
                texto_alerta = f"⛔ PENALIZADO: Tiempo Indefinido<br>Motivo: {razon_texto}"
            else:
                texto_alerta = f"⛔ PENALIZADO: {b.get('tiempo_restante_str', 'Calculando...')}<br>Motivo: {razon_texto}"
            
            texto_html += f"<br><span style='color:#f44336; font-weight:bold;'>{texto_alerta}</span>"
            self.btn_prestar.setEnabled(False)
            
        elif b['prestamos_activos'] >= 5:
            texto_html += "<br><span style='color:#FF9800; font-weight:bold;'>⚠️ LÍMITE: Debe devolver algo primero.</span>"
            self.btn_prestar.setEnabled(False)
        else:
            texto_html += "<br><span style='color:#4CAF50; font-weight:bold;'>✅ Habilitado para retirar.</span>"
            self.btn_prestar.setEnabled(True)

        self.lbl_info_bene.setStyleSheet("color: #333; font-size: 13px;")
        self.lbl_info_bene.setText(texto_html)

    def cargar_combo_objetos(self):
        objetos = backend.obtener_objetos_populares()
        self.combo_objetos.clear()
        for o in objetos:
            self.combo_objetos.addItem(f"{o['nombre_objeto']} (Disponibles: {o['cantidad_disponibles']})", o['id'])

    def ejecutar_prestamo(self):
        if not self.beneficiario_actual: return
        if self.combo_objetos.currentIndex() == -1: return

        id_objeto = self.combo_objetos.currentData()
        nombre_obj_combo = self.combo_objetos.currentText().split(" (")[0]
        lu_bene = self.beneficiario_actual['lu']

        # =======================================================
        # --- 1. FILTRO ANTI-ACAPARAMIENTO (Familia de Objetos) ---
        # =======================================================
        # Tomamos la primera palabra clave (Ej: "Taza" de "Taza c/ cucharita")
        palabra_clave = nombre_obj_combo.split()[0].lower()
        
        historial_completo = backend.obtener_historial_activo("")
        
        for h in historial_completo:
            # Si el préstamo es de este alumno y aún NO lo devolvió...
            if str(h['lu_beneficiario']) == str(lu_bene) and not h['devuelto']:
                # Comparamos si la palabra clave ya existe en lo que tiene prestado
                if palabra_clave in str(h['nombre_objeto']).lower():
                    QMessageBox.warning(self, "Límite de Categoría", 
                                        f"El alumno ya tiene un objeto de esta familia en préstamo: '{h['nombre_objeto']}'.\n\nDebe devolverlo antes de retirar otro similar.")
                    return # Bloqueamos la ejecución
        # =======================================================

        # =======================================================
        # --- 2. LÓGICA INTELIGENTE DE OBJETOS ENUMERADOS ---
        # =======================================================
        objetos_numerados = [
            "delantal", "set de mate", "regla t", "escuadra 45 45", "escuadra 30 60"
        ]
        
        nombre_final = nombre_obj_combo
        
        if any(palabra in nombre_obj_combo.lower() for palabra in objetos_numerados):
            from PyQt6.QtWidgets import QInputDialog 
            
            numero, ok = QInputDialog.getText(self, "Inventario Numerado", f"Ingrese el NÚMERO exacto de: {nombre_obj_combo}")
            
            if not ok: return 
                
            if not numero.strip():
                QMessageBox.warning(self, "Dato Obligatorio", "Debe especificar qué número de objeto está entregando para auditarlo correctamente.")
                return
                
            nombre_final = f"{nombre_obj_combo} N° {numero.strip()}"
        # =======================================================

        # 3. GUARDADO FINAL EN LA BASE DE DATOS
        exito, msj = backend.validar_y_prestar(lu_bene, id_objeto, nombre_final, self.lu_admin)
        
        if exito:
            self.input_bene.clear()
            self.lbl_foto_bene.setText("✅")
            self.lbl_info_bene.setText(f"<span style='color:#4CAF50; font-weight:bold; font-size:16px;'>¡Préstamo registrado exitosamente!</span>")
            self.beneficiario_actual = None
            self.btn_prestar.setEnabled(False)
            self.cargar_combo_objetos()
            self.actualizar_tabla()
        else:
            QMessageBox.warning(self, "Operación Denegada", msj)

    def actualizar_tabla(self):
        v_scroll = self.tabla.verticalScrollBar().value()
        h_scroll = self.tabla.horizontalScrollBar().value()

        historial = backend.obtener_historial_activo("")
        self.tabla.setRowCount(0)

        for f_idx, h in enumerate(historial):
            self.tabla.insertRow(f_idx)
            self.tabla.setRowHeight(f_idx, 45)
            
            id_p = h['id']
            
            self.tabla.setItem(f_idx, 0, QTableWidgetItem(str(id_p)))
            self.tabla.setItem(f_idx, 1, QTableWidgetItem(str(h['lu_beneficiario'])))
            self.tabla.setItem(f_idx, 2, QTableWidgetItem(f"{h['apellidos_beneficiario']}, {h['nombres_beneficiario']}"))
            self.tabla.setItem(f_idx, 3, QTableWidgetItem(str(h['nombre_objeto'])))
            
            fecha_str = h['fecha_prestamo'].strftime('%d/%m/%Y') if hasattr(h['fecha_prestamo'], 'strftime') else str(h['fecha_prestamo'])
            hora_str = str(h['hora_prestamo'])
            self.tabla.setItem(f_idx, 4, QTableWidgetItem(fecha_str))
            self.tabla.setItem(f_idx, 5, QTableWidgetItem(hora_str))

            if h['devuelto'] == 1: # Devuelto definitivamente
                self.tabla.setItem(f_idx, 6, QTableWidgetItem(f"{h['fecha_devolucion']} {h['hora_devolucion']}"))
                item_est = QTableWidgetItem("🟢 Devuelto")
                item_est.setForeground(QColor("#4CAF50"))
                self.tabla.setItem(f_idx, 7, item_est)
                self.tabla.setCellWidget(f_idx, 8, QLabel("")) 
            else: # devuelto IS NULL (activo) o devuelto = 2 (procesando)
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
                elif h['devuelto'] == 2:
                    # Devuelto en proceso en la otra PC
                    item_est = QTableWidgetItem("⏳ En Proceso (Otra PC)")
                    item_est.setForeground(QColor("#FF9800"))
                    self.tabla.setItem(f_idx, 7, item_est)
                    
                    lbl_proc = QLabel("En Devolución...")
                    lbl_proc.setStyleSheet("color: #FF9800; font-weight: bold;")
                    lbl_proc.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabla.setCellWidget(f_idx, 8, lbl_proc)
                else:
                    item_est = QTableWidgetItem("🔴 En Préstamo")
                    item_est.setForeground(QColor("#f44336"))
                    self.tabla.setItem(f_idx, 7, item_est)
                    
                    btn_dev = QPushButton("Devolver Objeto")
                    btn_dev.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
                    btn_dev.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_dev.setProperty("id_p", id_p)
                    btn_dev.clicked.connect(self.iniciar_devolucion)
                    self.tabla.setCellWidget(f_idx, 8, btn_dev)

        self.filtrar_tabla(self.input_filtro.text())

        self.tabla.verticalScrollBar().setValue(v_scroll)
        self.tabla.horizontalScrollBar().setValue(h_scroll)

    def iniciar_devolucion(self):
        id_p = self.sender().property("id_p")
        # 1. Marcar el estado temporal 2 en la Base de Datos para notificar a otras terminales
        if backend.marcar_devolucion_pendiente_db(id_p):
            # 2. Agregar a la cola local en RAM
            self.cola_devoluciones[id_p] = {
                'inicio': datetime.now(), 
                'danado': False,
                'btn': None
            }
            self.actualizar_tabla()

    def cancelar_devolucion(self):
        id_p = self.sender().property("id_p")
        if id_p in self.cola_devoluciones:
            # 1. Revertir a NULL el estado en la base de datos
            backend.revertir_devolucion_pendiente_db(id_p)
            # 2. Quitar de la cola local en RAM
            del self.cola_devoluciones[id_p]
            self.actualizar_tabla()

    def marcar_danado(self):
        id_p = self.sender().property("id_p")
        if id_p in self.cola_devoluciones:
            confirmar = QMessageBox.question(self, "ALERTA CRÍTICA", "¿Seguro que está dañado? Esto penalizará al alumno por 1 AÑO (8760 horas).", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
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
                backend.consolidar_devolucion_db(id_p, self.lu_admin, data['danado'], data['inicio'])
                ids_para_borrar.append(id_p)
            elif data['btn']:
                mins = int(segundos_restantes // 60)
                secs = int(segundos_restantes % 60)
                data['btn'].setText(f"↩️ {mins}:{secs:02d}")

        if ids_para_borrar:
            for i in ids_para_borrar: del self.cola_devoluciones[i]
            self.actualizar_tabla()
            self.cargar_combo_objetos()

    def filtrar_tabla(self, texto):
        t = texto.strip().lower()
        
        lu_traducido = None
        if t.isdigit() and len(t) >= 7:
            b = backend.buscar_beneficiario(t)
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

    # --- NUEVA FUNCIÓN PARA AMPLIAR LA FOTO CON CLIC ---
    def mostrar_foto_ampliada(self, event):
        """Abre una ventana emergente con la foto en mayor tamaño."""
        if not self.beneficiario_actual or not self.beneficiario_actual.get('ruta_foto'):
            return

        ruta_img = self.beneficiario_actual['ruta_foto']

        if not os.path.exists(ruta_img):
            QMessageBox.information(self, "Sin Foto", "El alumno no tiene una foto válida o el archivo fue borrado.")
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle(f"Identidad: {self.beneficiario_actual['apellidos']}, {self.beneficiario_actual['nombres']}")
        dialogo.setFixedSize(450, 450) 
        dialogo.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl_img_grande = QLabel()
        lbl_img_grande.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(ruta_img)
        if not pixmap.isNull():
            pixmap_escalado = pixmap.scaled(430, 430, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_img_grande.setPixmap(pixmap_escalado)
            
            layout.addWidget(lbl_img_grande)
            dialogo.exec() 
        else:
            QMessageBox.warning(self, "Error de Formato", "No se puede previsualizar este formato de imagen.")