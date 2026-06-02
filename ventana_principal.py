import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QFrame, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

import backend.auth as backend_auth
# IMPORTAMOS LA PESTAÑA MODULAR
from pestanas.carnets import PestañaCarnets 
from pestanas.objetos import PestañaObjetos 
from pestanas.prestamos import PestañaPrestamos
from pestanas.libreria import PestañaLibreria
from pestanas.ventas import PestañaVentas
from pestanas.pancitos import PestañaPancitos
from pestanas.perdidos import PestañaPerdidos
from pestanas.guardados import PestañaGuardados
from pestanas.libros import PestañaLibros
from pestanas.biblioteca import PestañaBiblioteca
from pestanas.historial_general import PestañaHistorialGeneral
from pestanas.comision import PestañaComision
from pestanas.configuracion import PestañaConfiguracion
from backend.db_backup import chequear_y_ejecutar_backup
# IMPORTAMOS LA UTILIDAD DE VISTAS
from backend.utils_vistas import procesar_avatar_circular

class VentanaPrincipal(QWidget):
    def __init__(self, nombre_usuario, lu_usuario, ruta_foto_perfil, cargo_usuario="Estudiante"):
        super().__init__()
        self.nombre_usuario = nombre_usuario
        self.lu_usuario = lu_usuario          
        self.ruta_foto = ruta_foto_perfil 
        self.cargo_usuario = cargo_usuario
        self.hora_ingreso = datetime.now()    
        
        self.modo_oscuro = False
        self.cargar_config_tema()
        
        self.inicializar_ui()
        # =====================================================================
        # SYSTEM BACKUP AUTOMÁTICO REGLA 19:00 HS
        # =====================================================================
        chequear_y_ejecutar_backup()
        
        self.timer_backup_diario = QTimer(self)
        self.timer_backup_diario.timeout.connect(chequear_y_ejecutar_backup)
        self.timer_backup_diario.start(60000) # 60000 ms = 1 minuto
        # =====================================================================

    def inicializar_ui(self):
        self.setWindowTitle("Sistema CEI - INGENIUM")
        self.setObjectName("main_window")
        import os
        import sys
        ruta_logo = os.path.join(sys._MEIPASS, "logo.png") if hasattr(sys, '_MEIPASS') else "logo.png"
        self.setWindowIcon(QIcon(ruta_logo)) 
        self.showMaximized() 

        # LAYOUT PRINCIPAL VERTICAL (El "Sándwich")
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0) 
        layout_principal.setSpacing(0)

        # =================================================================
        # CAPA 1: ENCABEZADO SUPERIOR (Logo, Perfil y Cerrar Sesión)
        # =================================================================
        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar") 
        layout_top = QHBoxLayout(self.top_bar)
        layout_top.setContentsMargins(20, 10, 20, 5) # Reduje un poco el margen inferior
        layout_top.setSpacing(15) 

        self.label_app_title = QLabel("CEI - INGENIUM")
        self.label_app_title.setObjectName("app_title")
        layout_top.addWidget(self.label_app_title)

        # El resorte mágico que empuja el logo a la izq y el perfil a la der
        layout_top.addStretch() 

        # Avatar Circular
        self.avatar_perfil = QLabel()
        self.avatar_perfil.setFixedSize(45, 45) 
        self.avatar_perfil.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        tamano_perfil = 45 
        pixmap_circular = procesar_avatar_circular(self.ruta_foto, tamano_perfil)
        
        if pixmap_circular:
            self.avatar_perfil.setPixmap(pixmap_circular)
        else:
            self.avatar_perfil.setText("👤")
            self.avatar_perfil.setStyleSheet("font-size: 24px;")
            
        layout_top.addWidget(self.avatar_perfil)

        # Nombre de Usuario
        self.label_user = QLabel(self.nombre_usuario)
        self.label_user.setObjectName("user_info")
        layout_top.addWidget(self.label_user)

        # Tag/Badge visual de Cargo
        self.label_cargo = QLabel(self.cargo_usuario.upper())
        self.label_cargo.setObjectName("user_badge")
        layout_top.addWidget(self.label_cargo)

        # Botón Alternar Tema (Modo Oscuro)
        self.btn_tema_toggle = QPushButton("☀️ Modo Claro" if self.modo_oscuro else "🌙 Modo Oscuro")
        self.btn_tema_toggle.setObjectName("btn_tema_toggle")
        self.btn_tema_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tema_toggle.clicked.connect(self.cambiar_tema)
        layout_top.addWidget(self.btn_tema_toggle)

        # Botón Cerrar Sesión
        self.btn_logout = QPushButton("Cerrar Sesión")
        self.btn_logout.setObjectName("btn_logout_top")
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.clicked.connect(self.close) 
        layout_top.addWidget(self.btn_logout)

        layout_principal.addWidget(self.top_bar)

        # =================================================================
        # CAPA 2: BARRA DE NAVEGACIÓN (Justo debajo del encabezado)
        # =================================================================
        self.nav_bar = QFrame()
        self.nav_bar.setObjectName("nav_bar") 
        layout_nav = QHBoxLayout(self.nav_bar)
        layout_nav.setContentsMargins(20, 0, 20, 10) 
        layout_nav.setSpacing(5) 
        
        # 1. PRIMER RESORTE (Empuja los botones desde la izquierda hacia el centro)
        layout_nav.addStretch() 

        opciones = ["Préstamos", "Ventas", "Pancitos", "Perdidos", "Guardados", "Librería", "Objetos", "Libros", "Biblioteca", "Carnets", "Atención", "Historial"]
        
        # Acceso a Configuración para los primeros 5 roles (Presidencia, Comisión, Recursos Humanos, Informática, Asienda)
        cargo_clean = self.cargo_usuario.lower().strip() if self.cargo_usuario else ""
        cargos_configuracion = [
            "presidencia", "presidenta del cei", 
            "comisión", "comision", 
            "recursos humanos", 
            "informática", "informatica", 
            "asienda", "hacienda"
        ]
        if cargo_clean in cargos_configuracion:
            opciones.append("Configuración")
            
        self.botones_menu = []
        
        for texto in opciones:
            btn = QPushButton(texto)
            btn.setProperty("class", "nav_button") 
            btn.setCheckable(True)
            btn.setAutoExclusive(True) 
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self.cambiar_seccion)
            layout_nav.addWidget(btn)
            self.botones_menu.append(btn)
            
        # 2. SEGUNDO RESORTE (Empuja los botones desde la derecha hacia el centro)
        layout_nav.addStretch()
        
        layout_principal.addWidget(self.nav_bar)
        
        # =================================================================
        # CAPA 3: ÁREA CENTRAL DE TRABAJO (El Stacked Widget)
        # =================================================================
        self.content_card = QFrame()
        self.content_card.setObjectName("content_card") 
        layout_content_card = QVBoxLayout(self.content_card)
        layout_content_card.setContentsMargins(0, 0, 0, 0) 

        self.contenedor_paginas = QStackedWidget()
        self.contenedor_paginas.setObjectName("content_area") 
  
        for texto in opciones:
            if texto == "Carnets":
                pagina = PestañaCarnets(self.lu_usuario)
            elif texto == "Objetos":                    
                pagina = PestañaObjetos(self.lu_usuario) 
            elif texto == "Préstamos":
                pagina = PestañaPrestamos(self.lu_usuario)
            elif texto == "Librería":
                pagina = PestañaLibreria(self.lu_usuario)
            elif texto == "Ventas":
                pagina = PestañaVentas(self.lu_usuario)  
            elif texto == "Pancitos":
                pagina = PestañaPancitos(self.lu_usuario) 
            elif texto == "Perdidos":
                pagina = PestañaPerdidos(self.lu_usuario)
            elif texto == "Guardados":
                pagina = PestañaGuardados(self.lu_usuario)
            elif texto == "Libros":
                pagina = PestañaLibros(self.lu_usuario)
            elif texto == "Biblioteca":
                pagina = PestañaBiblioteca(self.lu_usuario)
            elif texto == "Historial":
                pagina = PestañaHistorialGeneral(self.lu_usuario)
            elif texto == "Atención":
                pagina = PestañaComision(self.lu_usuario)
            elif texto == "Configuración":
                pagina = PestañaConfiguracion(self.lu_usuario)
            else:
                pagina = QFrame()
                layout_pag = QVBoxLayout(pagina)
                layout_pag.setContentsMargins(50, 50, 50, 50)
                titulo = QLabel(texto)
                titulo.setObjectName("section_title")
                titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout_pag.addWidget(titulo)
                layout_pag.addStretch() 
            self.contenedor_paginas.addWidget(pagina)

        layout_content_card.addWidget(self.contenedor_paginas)
        
        # El "1" le dice a la ventana que el área central debe estirarse y ocupar todo el espacio posible hacia abajo
        layout_principal.addWidget(self.content_card, 1) 

        # =================================================================

        if self.botones_menu:
            self.botones_menu[0].setChecked(True) 
            self.contenedor_paginas.setCurrentIndex(0) 

        self.cargar_estilos()

    def closeEvent(self, event):
        for i in range(self.contenedor_paginas.count()):
            pagina = self.contenedor_paginas.widget(i)
            if type(pagina).__name__ == "PestañaPrestamos": 
                pagina.forzar_cierre_seguro()
            elif type(pagina).__name__ == "PestañaVentas": 
                pagina.forzar_cierre_seguro()
            elif type(pagina).__name__ == "PestañaPerdidos": 
                pagina.forzar_cierre_seguro()
            elif type(pagina).__name__ == "PestañaGuardados":
                pagina.forzar_cierre_seguro()
            elif type(pagina).__name__ == "PestañaBiblioteca":
                pagina.forzar_cierre_seguro()

        horas_totales = (datetime.now() - self.hora_ingreso).total_seconds() / 3600.0
        backend_auth.registrar_cierre_sesion(self.lu_usuario, horas_totales)
        
        event.accept()

    def cambiar_seccion(self):
        btn = self.sender()
        try:
            indice = self.botones_menu.index(btn)
            self.contenedor_paginas.setCurrentIndex(indice)
        except ValueError: pass

    def cargar_config_tema(self):
        import json
        archivo = f"config_tema_{self.lu_usuario}.json"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.modo_oscuro = data.get("modo_oscuro", False)
            except:
                pass

    def guardar_config_tema(self):
        import json
        archivo = f"config_tema_{self.lu_usuario}.json"
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump({"modo_oscuro": self.modo_oscuro}, f)
        except:
            pass

    def cambiar_tema(self):
        self.modo_oscuro = not self.modo_oscuro
        self.guardar_config_tema()
        self.cargar_estilos()
        
        if self.modo_oscuro:
            self.btn_tema_toggle.setText("☀️ Modo Claro")
        else:
            self.btn_tema_toggle.setText("🌙 Modo Oscuro")

    def aplicar_tema_recursivo(self, widget, is_dark):
        if hasattr(widget, "styleSheet") and widget.styleSheet():
            ss = widget.styleSheet()
            if is_dark:
                # Reemplazo de colores claros inline por colores oscuros compatibles
                ss = ss.replace("background-color: white;", "background-color: #1e1e2a;")
                ss = ss.replace("background-color: white", "background-color: #1e1e2a")
                ss = ss.replace("background-color: #f1faff;", "background-color: #151522;")
                ss = ss.replace("background-color: #f1faff", "background-color: #151522")
                ss = ss.replace("background-color: #f8f9fa;", "background-color: #151522;")
                ss = ss.replace("background-color: #f8f9fa", "background-color: #151522")
                ss = ss.replace("color: #333;", "color: #e0e0e9;")
                ss = ss.replace("color: #333", "color: #e0e0e9")
                ss = ss.replace("color: #555;", "color: #a0a0bf;")
                ss = ss.replace("color: #555", "color: #a0a0bf")
                ss = ss.replace("color: #666;", "color: #a0a0bf;")
                ss = ss.replace("color: #666", "color: #a0a0bf")
                ss = ss.replace("border: 1px solid #ccc;", "border: 1px solid #2d2d3f;")
                ss = ss.replace("border: 1px solid #ccc", "border: 1px solid #2d2d3f")
                ss = ss.replace("border: 1px solid #ddd;", "border: 1px solid #2d2d3f;")
                ss = ss.replace("border: 1px solid #ddd", "border: 1px solid #2d2d3f")
            else:
                # Reemplazo inverso de colores oscuros inline por colores claros
                ss = ss.replace("background-color: #1e1e2a;", "background-color: white;")
                ss = ss.replace("background-color: #1e1e2a", "background-color: white")
                ss = ss.replace("background-color: #151522;", "background-color: #f1faff;")
                ss = ss.replace("background-color: #151522", "background-color: #f1faff")
                ss = ss.replace("color: #e0e0e9;", "color: #333;")
                ss = ss.replace("color: #e0e0e9", "color: #333")
                ss = ss.replace("color: #a0a0bf;", "color: #666;")
                ss = ss.replace("color: #a0a0bf", "color: #666")
                ss = ss.replace("border: 1px solid #2d2d3f;", "border: 1px solid #ccc;")
                ss = ss.replace("border: 1px solid #2d2d3f", "border: 1px solid #ccc")
            widget.setStyleSheet(ss)
        
        # Propagar a todos los componentes hijos
        for child in widget.findChildren(QWidget):
            self.aplicar_tema_recursivo(child, is_dark)

    def cargar_estilos(self):
        try:
            import os
            import sys
            archivo_qss = "estilos_oscuros.qss" if self.modo_oscuro else "estilos.qss"
            ruta_qss = os.path.join(sys._MEIPASS, archivo_qss) if hasattr(sys, '_MEIPASS') else archivo_qss
            with open(ruta_qss, "r", encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            
            # Aplicamos recursivamente los estilos para sobreescribir estilos inline
            self.aplicar_tema_recursivo(self, self.modo_oscuro)
        except Exception as e:
            print(f"Error cargando estilos: {e}")