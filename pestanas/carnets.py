import os
import pandas as pd
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QMessageBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QFileDialog, QInputDialog, QDialog) # <--- Agregamos QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap # <--- Agregamos QPixmap

import backend.db_carnets as backend
from backend.utils_vistas import procesar_avatar_circular

class PestañaCarnets(QWidget):
    def __init__(self, lu_administrador):
        super().__init__()
        self.lu_admin = lu_administrador 
        self.cache_avatares = {}
        self.inicializar_ui()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        # BARRA DE HERRAMIENTAS SUPERIOR
        layout_herramientas = QHBoxLayout()
        
        self.btn_cargar_excel = QPushButton("📥 Cargar beneficiarios (Excel)")
        self.btn_cargar_excel.setObjectName("btn_herramienta_carnet")
        self.btn_cargar_excel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar_excel.clicked.connect(self.cargar_excel_beneficiarios)
        layout_herramientas.addWidget(self.btn_cargar_excel)

        self.btn_cargar_fotos = QPushButton("📷 Cargar fotos beneficiarios")
        self.btn_cargar_fotos.setObjectName("btn_herramienta_carnet")
        self.btn_cargar_fotos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar_fotos.clicked.connect(self.cargar_fotos_carpeta)
        layout_herramientas.addWidget(self.btn_cargar_fotos)

        self.btn_agregar_usuario = QPushButton("⭐ Agregar usuarios a Comisión")
        self.btn_agregar_usuario.setObjectName("btn_herramienta_carnet")
        self.btn_agregar_usuario.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar_usuario.clicked.connect(self.convertir_en_usuario_comision)
        layout_herramientas.addWidget(self.btn_agregar_usuario)

        layout_herramientas.addStretch()

        # BUSCADOR EN TIEMPO REAL
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar Apellido, Nombre, DNI o LU...")
        self.input_busqueda.setMinimumWidth(300) 
        self.input_busqueda.textChanged.connect(self.filtrar_tabla)
        layout_herramientas.addWidget(self.input_busqueda)

        layout_principal.addLayout(layout_herramientas)

        # TABLA DE BENEFICIARIOS
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(15)
        self.tabla.setHorizontalHeaderLabels([
            "Apellidos", "Nombres", "DNI", "LU", "Teléfono", "Carrera", 
            "Foto", "Correo", "Contador Pan", "Faltas", 
            "Penalizado", "Horas Penaliz.", "Cant. Penaliz.", "Préstamos Act.", "Acciones"
        ])
        
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout_principal.addWidget(self.tabla)
        self.actualizar_tabla_datos()

    def actualizar_tabla_datos(self):
        beneficiarios = backend.obtener_todos_beneficiarios()
        self.tabla.setRowCount(0)

        for fila_idx, b in enumerate(beneficiarios):
            self.tabla.insertRow(fila_idx)
            self.tabla.setRowHeight(fila_idx, 65) 
            
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(str(b['apellidos'])))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(str(b['nombres'])))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(str(b['dni'])))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(str(b['lu'])))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(str(b['telefono'])))
            self.tabla.setItem(fila_idx, 5, QTableWidgetItem(str(b['carrera'])))
            
            lbl_foto = QLabel()
            lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_foto.setContentsMargins(5, 5, 5, 5) 
            ruta_img = b['ruta_foto']
            
            # --- NUEVO: Habilitar clic en cada foto de la tabla ---
            lbl_foto.setCursor(Qt.CursorShape.PointingHandCursor)
            # Usamos lambda para "guardar" los datos específicos de esta fila en el evento de clic
            lbl_foto.mousePressEvent = lambda event, r=ruta_img, a=b['apellidos'], n=b['nombres']: self.mostrar_foto_ampliada(r, a, n)
            # --------------------------------------------------------

            tamano_tabla = 50 

            # CACHÉ DE IMÁGENES
            if ruta_img not in self.cache_avatares:
                self.cache_avatares[ruta_img] = procesar_avatar_circular(ruta_img, tamano_tabla)
            
            pixmap_circular = self.cache_avatares[ruta_img]
            
            if pixmap_circular:
                lbl_foto.setPixmap(pixmap_circular)
            else:
                if ruta_img and ruta_img.lower().endswith('.heic'):
                    lbl_foto.setText("📸 HEIC")
                    lbl_foto.setStyleSheet("color: #0077b6; font-size: 10px; font-weight: bold;")
                else:
                    lbl_foto.setText("👤")
                    lbl_foto.setStyleSheet("color: #ddd; font-size: 24px; background-color: #f8fdff; border-radius: 25px;")
            
            self.tabla.setCellWidget(fila_idx, 6, lbl_foto)

            self.tabla.setItem(fila_idx, 7, QTableWidgetItem(str(b['correo'])))
            self.tabla.setItem(fila_idx, 8, QTableWidgetItem(str(b['pan'])))
            self.tabla.setItem(fila_idx, 9, QTableWidgetItem(str(b['faltas'])))
            
            estado_penalizado = "SÍ" if b['penalizado'] else "NO"
            item_penalizado = QTableWidgetItem(estado_penalizado)
            if b['penalizado']:
                item_penalizado.setForeground(QColor("#f44336"))
            self.tabla.setItem(fila_idx, 10, item_penalizado)
            
            self.tabla.setItem(fila_idx, 11, QTableWidgetItem(str(b['horas_penalizacion'])))
            self.tabla.setItem(fila_idx, 12, QTableWidgetItem(str(b['cant_penalizaciones'])))
            self.tabla.setItem(fila_idx, 13, QTableWidgetItem(str(b['prestamos_activos'])))

            widget_botones = QWidget()
            layout_btn_celda = QHBoxLayout(widget_botones)
            layout_btn_celda.setContentsMargins(4, 2, 4, 2)
            layout_btn_celda.setSpacing(6)

            btn_penalizar = QPushButton("Penalizar")
            btn_penalizar.setObjectName("btn_tabla_penalizar")
            btn_penalizar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_penalizar.setProperty("lu_alumno", b['lu'])
            btn_penalizar.clicked.connect(self.controlador_penalizar)
            layout_btn_celda.addWidget(btn_penalizar)

            btn_despenalizar = QPushButton("Despenalizar")
            btn_despenalizar.setObjectName("btn_tabla_despenalizar")
            btn_despenalizar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_despenalizar.setProperty("lu_alumno", b['lu'])
            btn_despenalizar.clicked.connect(self.controlador_despenalizar)
            layout_btn_celda.addWidget(btn_despenalizar)

            widget_botones.setLayout(layout_btn_celda)
            self.tabla.setCellWidget(fila_idx, 14, widget_botones)

    def filtrar_tabla(self, texto_busqueda):
        texto_limpio = texto_busqueda.strip().lower()

        for fila in range(self.tabla.rowCount()):
            mostrar_fila = False
            for col in (0, 1, 2, 3):
                item = self.tabla.item(fila, col)
                if item and texto_limpio in item.text().lower():
                    mostrar_fila = True
                    break 
            
            self.tabla.setRowHidden(fila, not mostrar_fila)

    def cargar_excel_beneficiarios(self):
        if not self.verificar_pass_rrhh(): return 

        ruta_archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel de Beneficiarios", "", "Archivos de Excel (*.xlsx *.xls)")
        if not ruta_archivo: return

        try:
            df = pd.read_excel(ruta_archivo, dtype=str)
            df = df.fillna('') 

            columnas_requeridas = ['Apellidos', 'Nombres', 'DNI', 'LU', 'Teléfono', 'Carrera que cursa', 'Correo']
            for col in columnas_requeridas:
                if col not in df.columns:
                    QMessageBox.critical(self, "Excel Inválido", f"Falta la columna obligatoria: '{col}'")
                    return

            datos_para_db = []
            for _, fila in df.iterrows():
                valor_pan = int(fila['Pan']) if 'Pan' in df.columns and fila['Pan'] != '' else 0
                datos_para_db.append((
                    str(fila['Apellidos']).strip(), str(fila['Nombres']).strip(), str(fila['DNI']).strip(), 
                    str(fila['LU']).strip(), str(fila['Teléfono']).strip(), str(fila['Carrera que cursa']).strip(), 
                    str(fila['Correo']).strip(), valor_pan
                ))

            exito, filas = backend.insertar_beneficiarios_masivo(datos_para_db)
            if exito:
                QMessageBox.information(self, "Carga Exitosa", f"Se procesaron los registros correctamente.")
                self.actualizar_tabla_datos()
                self.input_busqueda.clear()
            else:
                QMessageBox.critical(self, "Error al guardar masivo", str(filas))
        except Exception as e:
            QMessageBox.critical(self, "Error de Lectura", f"No se pudo procesar el archivo Excel.\nDetalle: {e}")

    def cargar_fotos_carpeta(self):
        if not self.verificar_pass_rrhh(): return 

        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta con las fotos de beneficiarios")
        if not carpeta: return

        archivos = os.listdir(carpeta)
        formatos_validos = ('_foto.jpg', '_foto.jpeg', '_foto.png', '_foto.heic', '_foto.webp')
        
        for archivo in archivos:
            if archivo.lower().endswith(formatos_validos):
                dni = archivo.split('_')[0]
                ruta_completa_foto = os.path.join(carpeta, archivo).replace("\\", "/")
                backend.asociar_foto_beneficiario(dni, ruta_completa_foto)

        QMessageBox.information(self, "Escaneo Completado", "Se encontraron y emparejaron fotos exitosamente.")
        self.actualizar_tabla_datos()
        self.input_busqueda.clear()

    def verificar_pass_rrhh(self):
        password, ok = QInputDialog.getText(self, "Seguridad Requerida", "Ingrese la contraseña de RRHH:", QLineEdit.EchoMode.Password)
        if ok and password == "Ingeniumcei26":
            return True
        elif ok:
            QMessageBox.warning(self, "Acceso Denegado", "Contraseña de RRHH incorrecta.")
        return False

    def controlador_penalizar(self):
        btn = self.sender()
        lu_alumno = btn.property("lu_alumno")

        if self.verificar_pass_rrhh():
            comentario, ok1 = QInputDialog.getMultiLineText(self, "Justificación", "Escriba obligatoriamente la razón de la penalización:")
            if not (ok1 and comentario.strip()):
                QMessageBox.warning(self, "Campo Obligatorio", "Debe ingresar una razón válida para ejecutar la acción.")
                return

            opciones = ["Por cantidad de días específicos", "Por tiempo indefinido"]
            tipo_tiempo, ok2 = QInputDialog.getItem(self, "Duración de Sanción", "Seleccione el alcance de la penalización:", opciones, 0, False)
            if not ok2: return 

            horas_sancion = -1.0 
            
            if tipo_tiempo == opciones[0]:
                dias, ok3 = QInputDialog.getInt(self, "Días de Penalización", "Ingrese la cantidad de días:", 7, 1, 3650)
                if not ok3: return
                horas_sancion = float(dias * 24)

            if backend.aplicar_penalizacion_db(lu_alumno, comentario.strip(), horas_sancion, self.lu_admin):
                QMessageBox.information(self, "Éxito", "El beneficiario ha sido penalizado correctamente.")
                self.actualizar_tabla_datos()

    def controlador_despenalizar(self):
        btn = self.sender()
        lu_alumno = btn.property("lu_alumno")

        if self.verificar_pass_rrhh():
            comentario, ok = QInputDialog.getMultiLineText(self, "Justificación", "Escriba la razón de la despenalización:")
            if ok and comentario.strip():
                if backend.aplicar_despenalizacion_db(lu_alumno, comentario.strip(), self.lu_admin):
                    QMessageBox.information(self, "Éxito", "El beneficiario ha sido despenalizado correctamente.")
                    self.actualizar_tabla_datos()
            elif ok:
                QMessageBox.warning(self, "Campo Obligatorio", "Debe ingresar una razón válida para ejecutar la acción.")

    def convertir_en_usuario_comision(self):
        fila_seleccionada = self.tabla.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, haga clic sobre la fila del beneficiario que desea ascender a Comisión.")
            return

        lu_alumno = self.tabla.item(fila_seleccionada, 3).text()
        apellido = self.tabla.item(fila_seleccionada, 0).text()
        nombre = self.tabla.item(fila_seleccionada, 1).text()

        if self.verificar_pass_rrhh():
            confirmar = QMessageBox.question(
                self, "Confirmar Ascenso", 
                f"¿Está seguro de otorgarle permisos de administrador a:\n{apellido}, {nombre} (LU: {lu_alumno})?\n\nSu clave inicial será su número de LU.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirmar == QMessageBox.StandardButton.Yes:
                if backend.crear_usuario_comision(lu_alumno):
                    QMessageBox.information(self, "Operación Exitosa", "Usuario añadido a Comisión con éxito.")
                else:
                    QMessageBox.critical(self, "Error", "No se pudo otorgar los permisos.")

    # ========================================================================
    # --- NUEVA FUNCIÓN: MOSTRAR FOTO AMPLIADA ---
    # ========================================================================
    def mostrar_foto_ampliada(self, ruta_img, apellidos, nombres):
        """Abre una ventana emergente con la foto del alumno seleccionado."""
        if not ruta_img or not os.path.exists(ruta_img):
            QMessageBox.information(self, "Sin Foto", "El alumno no tiene una foto válida o el archivo fue borrado.")
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle(f"Identidad: {apellidos}, {nombres}")
        dialogo.setFixedSize(450, 450) 
        dialogo.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl_img_grande = QLabel()
        lbl_img_grande.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(ruta_img)
        if not pixmap.isNull():
            # Escalamos la foto original a 430x430 manteniendo su proporción
            pixmap_escalado = pixmap.scaled(430, 430, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_img_grande.setPixmap(pixmap_escalado)
            
            layout.addWidget(lbl_img_grande)
            dialogo.exec() 
        else:
            QMessageBox.warning(self, "Error de Formato", "No se puede previsualizar este formato de imagen.")