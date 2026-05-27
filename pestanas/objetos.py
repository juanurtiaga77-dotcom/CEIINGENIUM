import os
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QMessageBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QFileDialog, QInputDialog, QDialog, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt

import backend.db_objetos as backend

class DialogoObjeto(QDialog):
    def __init__(self, parent=None, datos=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Objeto" if not datos else "Editar Objeto")
        self.setMinimumWidth(350)
        self.datos = datos 
        
        layout = QFormLayout(self)
        
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #ccc;")
        
        self.spin_cantidad = QSpinBox(); self.spin_cantidad.setMaximum(9999); self.spin_cantidad.setStyleSheet("padding: 5px;")
        self.spin_disp = QSpinBox(); self.spin_disp.setMaximum(9999); self.spin_disp.setStyleSheet("padding: 5px;")
        self.spin_prest = QSpinBox(); self.spin_prest.setMaximum(9999); self.spin_prest.setStyleSheet("padding: 5px;")
        self.spin_veces = QSpinBox(); self.spin_veces.setMaximum(99999); self.spin_veces.setStyleSheet("padding: 5px;")

        # Leemos los datos de la base de datos usando los nombres exactos de las columnas
        if datos:
            self.input_nombre.setText(str(datos['nombre_objeto']))
            self.spin_cantidad.setValue(int(datos['cantidad_total']))
            self.spin_disp.setValue(int(datos['cantidad_disponibles']))
            self.spin_prest.setValue(int(datos['en_prestamo']))
            self.spin_veces.setValue(int(datos['veces_prestado']))

        layout.addRow(QLabel("Nombre del Objeto:"), self.input_nombre)
        layout.addRow(QLabel("Cantidad Total:"), self.spin_cantidad)
        layout.addRow(QLabel("Disponibles:"), self.spin_disp)
        layout.addRow(QLabel("En préstamos:"), self.spin_prest)
        layout.addRow(QLabel("Veces prestado:"), self.spin_veces)

        layout_botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        btn_guardar.clicked.connect(self.accept) 
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #f44336; color: white; padding: 8px; border-radius: 5px;")
        btn_cancelar.clicked.connect(self.reject)
        
        layout_botones.addWidget(btn_guardar)
        layout_botones.addWidget(btn_cancelar)
        layout.addRow(layout_botones)

    def obtener_datos(self):
        return {
            "nombre_objeto": self.input_nombre.text().strip(),
            "cantidad_total": self.spin_cantidad.value(),
            "cantidad_disponibles": self.spin_disp.value(),
            "en_prestamo": self.spin_prest.value(),
            "veces_prestado": self.spin_veces.value()
        }


class PestañaObjetos(QWidget):
    def __init__(self, lu_administrador):
        super().__init__()
        self.lu_admin = lu_administrador 
        self.tiempo_autorizacion = None 
        self.inicializar_ui()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        layout_herramientas = QHBoxLayout()
        
        self.btn_agregar = QPushButton("➕ Agregar Objeto")
        self.btn_agregar.setObjectName("btn_herramienta_carnet")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.clicked.connect(self.controlador_agregar)
        layout_herramientas.addWidget(self.btn_agregar)

        self.btn_cargar_excel = QPushButton("📥 Cargar desde Excel")
        self.btn_cargar_excel.setObjectName("btn_herramienta_carnet")
        self.btn_cargar_excel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar_excel.clicked.connect(self.cargar_excel)
        layout_herramientas.addWidget(self.btn_cargar_excel)

        self.btn_exportar = QPushButton("📤 Exportar a Excel")
        self.btn_exportar.setObjectName("btn_herramienta_carnet")
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.clicked.connect(self.exportar_excel)
        layout_herramientas.addWidget(self.btn_exportar)

        layout_herramientas.addStretch()

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar objeto...")
        self.input_busqueda.setMinimumWidth(300)
        self.input_busqueda.textChanged.connect(self.filtrar_tabla)
        layout_herramientas.addWidget(self.input_busqueda)

        layout_principal.addLayout(layout_herramientas)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7) 
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Objeto", "Cantidad", "Disponibles", "En préstamos", "Cantidad de veces prestado", "Acciones"
        ])
        
        self.tabla.setColumnHidden(0, True) 
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: transparent; border: none; } QTableWidget::item { padding: 5px; }")
        
        layout_principal.addWidget(self.tabla)
        self.actualizar_tabla_datos()

    def actualizar_tabla_datos(self):
        objetos = backend.obtener_todos_objetos()
        self.tabla.setRowCount(0)

        for fila_idx, obj in enumerate(objetos):
            self.tabla.insertRow(fila_idx)
            self.tabla.setRowHeight(fila_idx, 50) 
            
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(str(obj['id'])))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(str(obj['nombre_objeto'])))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(str(obj['cantidad_total'])))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(str(obj['cantidad_disponibles'])))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(str(obj['en_prestamo'])))
            self.tabla.setItem(fila_idx, 5, QTableWidgetItem(str(obj['veces_prestado'])))
            
            widget_botones = QWidget()
            layout_btn_celda = QHBoxLayout(widget_botones)
            layout_btn_celda.setContentsMargins(4, 2, 4, 2)
            layout_btn_celda.setSpacing(6)

            btn_editar = QPushButton("✏️ Editar")
            btn_editar.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 5px; border-radius: 4px;")
            btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_editar.setProperty("fila_datos", obj) 
            btn_editar.clicked.connect(self.controlador_editar)
            layout_btn_celda.addWidget(btn_editar)

            btn_eliminar = QPushButton("🗑️ Eliminar")
            btn_eliminar.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 5px; border-radius: 4px;")
            btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_eliminar.setProperty("id_obj", obj['id'])
            btn_eliminar.setProperty("nombre_obj", obj['nombre_objeto'])
            btn_eliminar.clicked.connect(self.controlador_eliminar)
            layout_btn_celda.addWidget(btn_eliminar)

            widget_botones.setLayout(layout_btn_celda)
            self.tabla.setCellWidget(fila_idx, 6, widget_botones)

    def filtrar_tabla(self, texto_busqueda):
        texto_limpio = texto_busqueda.strip().lower()
        for fila in range(self.tabla.rowCount()):
            item = self.tabla.item(fila, 1) 
            if item and texto_limpio in item.text().lower():
                self.tabla.setRowHidden(fila, False)
            else:
                self.tabla.setRowHidden(fila, True)

    def verificar_autorizacion(self, requiere_siempre=False):
        ahora = datetime.now()
        
        if not requiere_siempre and self.tiempo_autorizacion:
            if (ahora - self.tiempo_autorizacion).total_seconds() < 300:
                return True 
                
        password, ok = QInputDialog.getText(self, "Autorización de RRHH", 
                                            "Ingrese contraseña para habilitar edición:", 
                                            QLineEdit.EchoMode.Password)
        if ok and password == "Ingeniumcei26":
            if not requiere_siempre:
                self.tiempo_autorizacion = datetime.now() 
            return True
        elif ok:
            QMessageBox.warning(self, "Acceso Denegado", "Contraseña incorrecta.")
        
        return False

    def controlador_agregar(self):
        if self.verificar_autorizacion(requiere_siempre=False):
            dialogo = DialogoObjeto(self)
            if dialogo.exec(): 
                d = dialogo.obtener_datos()
                if not d['nombre_objeto']:
                    QMessageBox.warning(self, "Error", "El objeto debe tener un nombre.")
                    return
                
                exito, msj = backend.agregar_objeto(d['nombre_objeto'], d['cantidad_total'], d['cantidad_disponibles'], d['en_prestamo'], d['veces_prestado'], self.lu_admin)
                if exito:
                    self.actualizar_tabla_datos()
                else:
                    QMessageBox.critical(self, "Error", msj)

    def controlador_editar(self):
        if self.verificar_autorizacion(requiere_siempre=False):
            btn = self.sender()
            datos_obj = btn.property("fila_datos")
            
            dialogo = DialogoObjeto(self, datos=datos_obj)
            if dialogo.exec():
                d = dialogo.obtener_datos()
                if not d['nombre_objeto']:
                    QMessageBox.warning(self, "Error", "El nombre no puede quedar vacío.")
                    return
                
                exito, msj = backend.editar_objeto(datos_obj['id'], d['nombre_objeto'], d['cantidad_total'], d['cantidad_disponibles'], d['en_prestamo'], d['veces_prestado'], self.lu_admin)
                if exito:
                    self.actualizar_tabla_datos()
                else:
                    QMessageBox.critical(self, "Error", msj)

    def controlador_eliminar(self):
        btn = self.sender()
        id_obj = btn.property("id_obj")
        nombre_obj = btn.property("nombre_obj")

        confirmar = QMessageBox.question(
            self, "⚠️ ALERTA DE ELIMINACIÓN", 
            f"Está a punto de eliminar el objeto '{nombre_obj}' de forma permanente.\n\n¿Desea continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirmar == QMessageBox.StandardButton.Yes:
            if self.verificar_autorizacion(requiere_siempre=True):
                exito, msj = backend.eliminar_objeto(id_obj, nombre_obj, self.lu_admin)
                if exito:
                    QMessageBox.information(self, "Eliminado", "El objeto fue eliminado del sistema.")
                    self.actualizar_tabla_datos()
                else:
                    QMessageBox.critical(self, "Error", msj)

    def cargar_excel(self):
        if not self.verificar_autorizacion(requiere_siempre=False):
            return

        ruta_archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel de Objetos", "", "Archivos de Excel (*.xlsx *.xls)")
        if not ruta_archivo: return

        try:
            df = pd.read_excel(ruta_archivo)
            columnas_requeridas = ['Objeto', 'Cantidad', 'Disponibles', 'En préstamo', 'Cantidad de veces prestado']
            
            for col in columnas_requeridas:
                if col not in df.columns:
                    QMessageBox.critical(self, "Excel Inválido", f"El archivo debe tener exactamente estas columnas. Falta: '{col}'")
                    return

            df = df.fillna(0) 
            datos_para_db = []
            for _, fila in df.iterrows():
                if str(fila['Objeto']).strip(): 
                    datos_para_db.append((
                        str(fila['Objeto']).strip(), 
                        int(fila['Cantidad']), 
                        int(fila['Disponibles']), 
                        int(fila['En préstamo']), 
                        int(fila['Cantidad de veces prestado'])
                    ))

            exito, msj = backend.procesar_excel_masivo(datos_para_db, self.lu_admin)
            if exito:
                QMessageBox.information(self, "Carga Exitosa", f"Se registraron/actualizaron los objetos correctamente.")
                self.actualizar_tabla_datos()
            else:
                QMessageBox.critical(self, "Error de base de datos", msj)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo Excel.\nDetalle: {e}")

    def exportar_excel(self):
        if not self.verificar_autorizacion(requiere_siempre=False):
            return
            
        ruta_archivo, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte", "Reporte_Objetos_CEI.xlsx", "Archivos de Excel (*.xlsx)")
        if not ruta_archivo: return

        try:
            objetos = backend.obtener_todos_objetos()
            if not objetos:
                QMessageBox.information(self, "Vacío", "No hay objetos para exportar.")
                return
            
            df = pd.DataFrame(objetos)
            
            # Formateamos el dataframe usando los nombres de tu DB
            df = df.rename(columns={
                'nombre_objeto': 'Objeto', 
                'cantidad_total': 'Cantidad', 
                'cantidad_disponibles': 'Disponibles', 
                'en_prestamo': 'En préstamo', 
                'veces_prestado': 'Cantidad de veces prestado'
            })
            df = df[['Objeto', 'Cantidad', 'Disponibles', 'En préstamo', 'Cantidad de veces prestado']]
            
            df.to_excel(ruta_archivo, index=False)
            QMessageBox.information(self, "Éxito", "¡Reporte de Inventario guardado exitosamente!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", str(e))