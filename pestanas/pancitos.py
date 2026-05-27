import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QMessageBox, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

import backend.db_pancitos as backend
from backend.utils_vistas import procesar_avatar_circular

class PestañaPancitos(QWidget):
    def __init__(self, lu_administrador):
        super().__init__()
        self.lu_admin = lu_administrador 
        self.beneficiario_actual = None
        self.inicializar_ui()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)

        # ==================== SECCIÓN SUPERIOR: ENTREGA ====================
        frame_superior = QFrame()
        frame_superior.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #ddd;")
        layout_sup = QHBoxLayout(frame_superior)
        layout_sup.setContentsMargins(15, 15, 15, 15)

        # Izquierda: Buscador y Tarjeta
        layout_izq = QVBoxLayout()
        layout_izq.addWidget(QLabel("<b>🔍 Buscar Beneficiario (LU o DNI)</b>"))
        
        self.input_bene = QLineEdit()
        self.input_bene.setPlaceholderText("Ingrese LU o DNI y presione ENTER...")
        self.input_bene.setStyleSheet("padding: 8px; border: 1px solid #ccc; font-size: 14px;")
        self.input_bene.returnPressed.connect(self.buscar_alumno)
        layout_izq.addWidget(self.input_bene)

        # Tarjeta de Info
        frame_info = QFrame()
        layout_info = QHBoxLayout(frame_info)
        layout_info.setContentsMargins(0, 10, 0, 0)
        
        self.lbl_foto = QLabel("👤")
        self.lbl_foto.setFixedSize(60, 60)
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto.setStyleSheet("font-size: 30px; background-color: #f1faff; border-radius: 30px;")
        
        self.lbl_detalles = QLabel("Presione ENTER para buscar a un alumno.")
        self.lbl_detalles.setWordWrap(True)
        self.lbl_detalles.setStyleSheet("font-size: 13px; color: #555;")
        
        layout_info.addWidget(self.lbl_foto)
        layout_info.addWidget(self.lbl_detalles, stretch=1)
        layout_izq.addWidget(frame_info)
        
        layout_sup.addLayout(layout_izq, stretch=6)

        # Derecha: Botón de Entrega y Stock
        layout_der = QVBoxLayout()
        layout_der.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_stock = QLabel("Pancitos Hoy: --/100")
        self.lbl_stock.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_stock.setStyleSheet("color: #FF9800;")
        self.lbl_stock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_der.addWidget(self.lbl_stock)

        self.btn_entregar = QPushButton("🥖 Entregar Pancito")
        self.btn_entregar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 16px; padding: 15px; border-radius: 8px;")
        self.btn_entregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_entregar.setEnabled(False)
        self.btn_entregar.clicked.connect(self.ejecutar_entrega)
        layout_der.addWidget(self.btn_entregar)
        
        layout_sup.addLayout(layout_der, stretch=4)
        
        layout_principal.addWidget(frame_superior)

        # ==================== SECCIÓN INFERIOR: HISTORIAL DE HOY ====================
        layout_principal.addWidget(QLabel("<b>📜 Historial de Entregas (Solo Hoy)</b>"))
        
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(7)
        self.tabla_historial.setHorizontalHeaderLabels([
            "LU Administrador", "LU Beneficiario", "Apellidos", "Nombres", "Fecha", "Hora", "Estado"
        ])
        self.tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_historial.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_historial.setShowGrid(False)
        self.tabla_historial.setStyleSheet("QTableWidget { gridline-color: transparent; border: none; } QTableWidget::item { padding: 5px; }")
        
        layout_principal.addWidget(self.tabla_historial)

        self.actualizar_pantalla()

    def actualizar_pantalla(self):
        """Actualiza el contador de stock y la tabla del historial."""
        # 1. Actualizar Stock
        stock = backend.obtener_stock_hoy()
        self.lbl_stock.setText(f"Pancitos Hoy: {stock}/100")
        
        if stock <= 0:
            self.lbl_stock.setStyleSheet("color: #f44336;") # Rojo si se acaban
            self.btn_entregar.setEnabled(False)
        else:
            self.lbl_stock.setStyleSheet("color: #FF9800;")

        # 2. Actualizar Tabla
        historial = backend.obtener_historial_hoy()
        self.tabla_historial.setRowCount(0)
        
        for i, h in enumerate(historial):
            self.tabla_historial.insertRow(i)
            self.tabla_historial.setItem(i, 0, QTableWidgetItem(str(h['lu_usuario'])))
            self.tabla_historial.setItem(i, 1, QTableWidgetItem(str(h['lu_beneficiario'])))
            self.tabla_historial.setItem(i, 2, QTableWidgetItem(str(h['apellido_beneficiario'])))
            self.tabla_historial.setItem(i, 3, QTableWidgetItem(str(h['nombre_beneficiario'])))
            
            fecha_str = h['fecha'].strftime('%d/%m/%Y') if hasattr(h['fecha'], 'strftime') else str(h['fecha'])
            self.tabla_historial.setItem(i, 4, QTableWidgetItem(fecha_str))
            self.tabla_historial.setItem(i, 5, QTableWidgetItem(str(h['hora'])))
            
            item_estado = QTableWidgetItem("Entregado")
            item_estado.setForeground(QColor("#4CAF50"))
            item_estado.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.tabla_historial.setItem(i, 6, item_estado)

    def buscar_alumno(self):
        criterio = self.input_bene.text().strip()
        if not criterio: return
        
        b = backend.buscar_beneficiario_pan(criterio)
        if not b:
            self.lbl_foto.clear(); self.lbl_foto.setText("❌")
            self.lbl_detalles.setText("<span style='color: #f44336; font-weight: bold;'>Estudiante no encontrado en el sistema.</span>")
            self.beneficiario_actual = None
            self.btn_entregar.setEnabled(False)
            return
            
        self.beneficiario_actual = b
        
        # Cargar Foto
        pixmap = procesar_avatar_circular(b['ruta_foto'], 60)
        if pixmap: self.lbl_foto.setPixmap(pixmap)
        else: self.lbl_foto.setText("👤")

        # Comprobar restricciones
        ya_tiene = backend.ya_recibio_hoy(b['lu'])
        stock_vacio = backend.obtener_stock_hoy() <= 0
        
        texto_html = f"<b>{b['apellidos']}, {b['nombres']}</b> (LU: {b['lu']})<br>Total pancitos históricos: <b>{b['pan']}</b><br>"
        
        if b['penalizado']:
            texto_html += "<span style='color: #FF9800;'><i>Alumno penalizado (No afecta beneficio de pan)</i></span><br>"

        if stock_vacio:
            texto_html += "<span style='color: #f44336; font-weight: bold;'>❌ No hay stock disponible hoy.</span>"
            self.btn_entregar.setEnabled(False)
        elif ya_tiene:
            texto_html += "<span style='color: #f44336; font-weight: bold;'>❌ Ya retiró su pancito el día de hoy.</span>"
            self.btn_entregar.setEnabled(False)
        else:
            texto_html += "<span style='color: #4CAF50; font-weight: bold;'>✅ Apto para recibir pancito.</span>"
            self.btn_entregar.setEnabled(True)

        self.lbl_detalles.setText(texto_html)

    def ejecutar_entrega(self):
        if not self.beneficiario_actual: return
        
        b = self.beneficiario_actual
        exito, msj = backend.entregar_pancito(self.lu_admin, b['lu'], b['apellidos'], b['nombres'])
        
        if exito:
            self.input_bene.clear()
            self.lbl_foto.setText("✅")
            self.lbl_detalles.setText("<span style='color: #4CAF50; font-weight: bold; font-size: 15px;'>¡Pancito entregado con éxito!</span>")
            self.btn_entregar.setEnabled(False)
            self.beneficiario_actual = None
            self.actualizar_pantalla()
            
            # Limpiar mensaje verde después de 3 segundos
            QTimer.singleShot(3000, self.resetear_info)
        else:
            QMessageBox.critical(self, "Error", msj)
            
    def resetear_info(self):
        if not self.beneficiario_actual:
            self.lbl_foto.setText("👤")
            self.lbl_detalles.setText("Presione ENTER para buscar a un alumno.")