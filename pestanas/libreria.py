import os
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
                             QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QFileDialog, QInputDialog, 
                             QDialog, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt

import backend.db_libreria as backend

class DialogoArticulo(QDialog):
    def __init__(self, parent=None, datos=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Artículo" if not datos else "Editar Artículo")
        self.setMinimumWidth(350)
        
        layout = QFormLayout(self)
        
        self.input_articulo = QLineEdit()
        self.input_articulo.setStyleSheet("padding: 6px; border-radius: 4px; border: 1px solid #ccc;")
        
        self.spin_precio = QDoubleSpinBox(); self.spin_precio.setMaximum(999999.99); self.spin_precio.setPrefix("$ "); self.spin_precio.setStyleSheet("padding: 4px;")
        self.spin_stock = QSpinBox(); self.spin_stock.setMaximum(9999); self.spin_stock.setStyleSheet("padding: 4px;")
        self.spin_reponer = QSpinBox(); self.spin_reponer.setMaximum(9999); self.spin_reponer.setStyleSheet("padding: 4px;")
        self.spin_veces = QSpinBox(); self.spin_veces.setMaximum(999999); self.spin_veces.setStyleSheet("padding: 4px;")

        if datos:
            self.input_articulo.setText(str(datos['articulo']))
            self.spin_precio.setValue(float(datos['precio']))
            self.spin_stock.setValue(int(datos['stock']))
            self.spin_reponer.setValue(int(datos['reponer_stock']))
            self.spin_veces.setValue(int(datos['veces_vendido']))

        layout.addRow(QLabel("Nombre del Artículo:"), self.input_articulo)
        layout.addRow(QLabel("Precio Unitario:"), self.spin_precio)
        layout.addRow(QLabel("Stock Actual:"), self.spin_stock)
        layout.addRow(QLabel("Punto de Reposición:"), self.spin_reponer)
        layout.addRow(QLabel("Veces Vendido:"), self.spin_veces)

        layout_botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_guardar.clicked.connect(self.accept) 
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #f44336; color: white; padding: 6px; border-radius: 4px;")
        btn_cancelar.clicked.connect(self.reject)
        
        layout_botones.addWidget(btn_guardar)
        layout_botones.addWidget(btn_cancelar)
        layout.addRow(layout_botones)

    def obtener_datos(self):
        return {
            "articulo": self.input_articulo.text().strip(),
            "precio": self.spin_precio.value(),
            "stock": self.spin_stock.value(),
            "reponer_stock": self.spin_reponer.value(),
            "veces_vendido": self.spin_veces.value()
        }


class PestañaLibreria(QWidget):
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
        
        self.btn_agregar = QPushButton("➕ Agregar Artículo")
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

        # CORRECCIÓN DE TIPO: addStretch()
        layout_herramientas.addStretch()

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar artículo...")
        self.input_busqueda.setMinimumWidth(300)
        self.input_busqueda.textChanged.connect(self.filtrar_tabla)
        layout_herramientas.addWidget(self.input_busqueda)

        layout_principal.addLayout(layout_herramientas)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7) 
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Artículo", "Precio", "Stock", "Reponer Stock", "Veces vendido", "Acciones"
        ])
        
        self.tabla.setColumnHidden(0, True) 
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(6, 300)
        
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: transparent; border: none; } QTableWidget::item { padding: 5px; }")
        
        layout_principal.addWidget(self.tabla)
        self.actualizar_tabla_datos()

    def actualizar_tabla_datos(self):
        articulos = backend.obtener_todos_articulos()
        self.tabla.setRowCount(0)

        for fila_idx, art in enumerate(articulos):
            self.tabla.insertRow(fila_idx)
            self.tabla.setRowHeight(fila_idx, 50) 
            
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(str(art['id'])))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(str(art['articulo'])))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(f"$ {art['precio']:.2f}"))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(str(art['stock'])))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(str(art['reponer_stock'])))
            self.tabla.setItem(fila_idx, 5, QTableWidgetItem(str(art['veces_vendido'])))
            
            widget_botones = QWidget()
            layout_btn_celda = QHBoxLayout(widget_botones)
            layout_btn_celda.setContentsMargins(2, 2, 2, 2)
            layout_btn_celda.setSpacing(4)

            btn_reponer = QPushButton("📦 Reponer")
            btn_reponer.setStyleSheet("background-color: #00b4d8; color: white; font-weight: bold; padding: 4px; border-radius: 4px; min-width: 80px;")
            btn_reponer.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_reponer.setProperty("id_art", art['id'])
            btn_reponer.clicked.connect(self.controlador_reponer)
            layout_btn_celda.addWidget(btn_reponer)

            btn_editar = QPushButton("✏️ Editar")
            btn_editar.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 4px; border-radius: 4px; min-width: 75px;")
            btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_editar.setProperty("fila_datos", art) 
            btn_editar.clicked.connect(self.controlador_editar)
            layout_btn_celda.addWidget(btn_editar)

            btn_eliminar = QPushButton("🗑️ Eliminar")
            btn_eliminar.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 4px; border-radius: 4px; min-width: 75px;")
            btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_eliminar.setProperty("id_art", art['id'])
            btn_eliminar.setProperty("nombre_art", art['articulo'])
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
                
        password, ok = QInputDialog.getText(self, "Autorización de Hacienda", 
                                            "Ingrese contraseña de supervisión:", 
                                            QLineEdit.EchoMode.Password)
        if ok and password == "Ingeniumcei26":
            if not requiere_siempre:
                self.tiempo_autorizacion = datetime.now() 
            return True
        elif ok:
            QMessageBox.warning(self, "Acceso Denegado", "Contraseña de Hacienda incorrecta.")
        return False

    def controlador_agregar(self):
        if self.verificar_autorizacion(requiere_siempre=False):
            dialogo = DialogoArticulo(self)
            if dialogo.exec(): 
                d = dialogo.obtener_datos()
                if not d['articulo']:
                    QMessageBox.warning(self, "Error", "El artículo debe tener un nombre descriptivo.")
                    return
                exito, msj = backend.agregar_articulo(d['articulo'], d['precio'], d['stock'], d['reponer_stock'], d['veces_vendido'], self.lu_admin)
                if exito: self.actualizar_tabla_datos()
                else: QMessageBox.critical(self, "Error", msj)

    def controlador_editar(self):
        if self.verificar_autorizacion(requiere_siempre=False):
            btn = self.sender()
            datos_art = btn.property("fila_datos")
            dialogo = DialogoArticulo(self, datos=datos_art)
            if dialogo.exec():
                d = dialogo.obtener_datos()
                if not d['articulo']:
                    QMessageBox.warning(self, "Error", "El nombre no puede quedar vacío.")
                    return
                exito, msj = backend.editar_articulo(datos_art['id'], d['articulo'], d['precio'], d['stock'], d['reponer_stock'], d['veces_vendido'], self.lu_admin)
                if exito: self.actualizar_tabla_datos()
                else: QMessageBox.critical(self, "Error", msj)

    def controlador_reponer(self):
        if self.verificar_autorizacion(requiere_siempre=False):
            id_art = self.sender().property("id_art")
            cantidad, ok = QInputDialog.getInt(self, "Reponer Stock", "Cantidad de unidades recibidas:", min=1, max=9999)
            if ok and cantidad > 0:
                exito, msj = backend.reponer_stock_db(id_art, cantidad, self.lu_admin)
                if exito: self.actualizar_tabla_datos()
                else: QMessageBox.critical(self, "Error", msj)

    def controlador_eliminar(self):
        btn = self.sender()
        id_art = btn.property("id_art")
        nombre_art = btn.property("nombre_art")

        confirmar = QMessageBox.question(
            self, "⚠️ CONTROL DE ELIMINACIÓN", 
            f"Está por borrar permanentemente el artículo '{nombre_art}'.\n¿Desea proceder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            if self.verificar_autorizacion(requiere_siempre=True):
                exito, msj = backend.eliminar_articulo(id_art, nombre_art, self.lu_admin)
                if exito:
                    QMessageBox.information(self, "Eliminado", "Artículo removido con éxito.")
                    self.actualizar_tabla_datos()
                else: QMessageBox.critical(self, "Error", msj)

    def cargar_excel(self):
        if not self.verificar_autorizacion(requiere_siempre=False): return
        ruta_archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel de Librería", "", "Archivos de Excel (*.xlsx *.xls)")
        if not ruta_archivo: return
        try:
            df = pd.read_excel(ruta_archivo)
            columnas_requeridas = ['Artículo', 'Precio', 'Stock', 'Reponer Stock', 'Veces vendido']
            for col in columnas_requeridas:
                if col not in df.columns:
                    QMessageBox.critical(self, "Excel Inválido", f"Falta la columna obligatoria: '{col}'")
                    return
            df = df.fillna(0) 
            datos_para_db = []
            for _, fila in df.iterrows():
                if str(fila['Artículo']).strip(): 
                    datos_para_db.append((
                        str(fila['Artículo']).strip(), float(fila['Precio']), 
                        int(fila['Stock']), int(fila['Reponer Stock']), int(fila['Veces vendido'])
                    ))
            exito, msj = backend.procesar_excel_masivo(datos_para_db, self.lu_admin)
            if exito:
                QMessageBox.information(self, "Carga Exitosa", "Artículos sincronizados correctamente.")
                self.actualizar_tabla_datos()
            else: QMessageBox.critical(self, "Error", msj)
        except Exception as e: QMessageBox.critical(self, "Error", f"Falla al leer Excel: {e}")

    def exportar_excel(self):
        if not self.verificar_autorizacion(requiere_siempre=False): return
        ruta_archivo, _ = QFileDialog.getSaveFileName(self, "Guardar Inventario Librería", "Inventario_Libreria_CEI.xlsx", "Archivos de Excel (*.xlsx)")
        if not ruta_archivo: return
        try:
            articulos = backend.obtener_todos_articulos()
            if not articulos:
                QMessageBox.information(self, "Vacío", "No hay registros que exportar.")
                return
            df = pd.DataFrame(articulos)
            df = df.rename(columns={
                'articulo': 'Artículo', 'precio': 'Precio', 'stock': 'Stock', 
                'reponer_stock': 'Reponer Stock', 'veces_vendido': 'Veces vendido'
            })
            df = df[['Artículo', 'Precio', 'Stock', 'Reponer Stock', 'Veces vendido']]
            df.to_excel(ruta_archivo, index=False)
            QMessageBox.information(self, "Éxito", "¡Planilla de Librería exportada exitosamente!")
        except Exception as e: QMessageBox.critical(self, "Error al Exportar", str(e))