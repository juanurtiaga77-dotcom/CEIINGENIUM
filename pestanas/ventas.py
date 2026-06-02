import os
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QMessageBox, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
                             QInputDialog, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

import backend.db_ventas as backend

class PestañaVentas(QWidget):
    def __init__(self, lu_administrador):
        super().__init__()
        self.lu_admin = lu_administrador 
        
        self.carrito = {} 
        self.tiempo_autorizacion = None
        
        self.ventas_recientes = {}   
        self.ventas_deshechas = {}   
        
        self.cargar_cola_local()
        
        self.ultimo_arqueo_hora = None
        
        self.timer_colas = QTimer(self)
        self.timer_colas.timeout.connect(self.procesar_colas_deshacer)
        self.timer_colas.start(1000)

        self.timer_arqueo = QTimer(self)
        self.timer_arqueo.timeout.connect(self.verificar_arqueo)
        self.timer_arqueo.start(60000) 

        # TIMER DE SINCRONIZACIÓN ENTRE TERMINALES
        self.timer_sincronizacion = QTimer(self)
        self.timer_sincronizacion.timeout.connect(self.sincronizar_remoto)
        self.timer_sincronizacion.start(10000) # Cada 10 segundos

        self.inicializar_ui()

    def cargar_cola_local(self):
        import socket
        archivo = f"cola_ventas_{socket.gethostname()}.json"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                ahora = datetime.now()
                
                for id_str, data in datos.get('recientes', {}).items():
                    ts = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
                    if (ahora - ts).total_seconds() < 300:
                        self.ventas_recientes[int(id_str)] = {
                            'timestamp': ts,
                            'carrito_data': data['carrito_data'],
                            'forma': data['forma'],
                            'efe': data['efe'],
                            'trans': data['trans'],
                            'btn': None
                        }
                
                for id_str, info in datos.get('deshechas', {}).items():
                    ts = datetime.strptime(info['timestamp'], '%Y-%m-%d %H:%M:%S')
                    if (ahora - ts).total_seconds() < 120:
                        self.ventas_deshechas[int(id_str)] = {
                            'timestamp': ts,
                            'data': info['data'],
                            'btn': None
                        }
                os.remove(archivo) 
            except Exception as e:
                print(f"Error al cargar cola de ventas: {e}")

    def forzar_cierre_seguro(self):
        datos = {'recientes': {}, 'deshechas': {}}
        
        for id_v, data in self.ventas_recientes.items():
            datos['recientes'][str(id_v)] = {
                'timestamp': data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'carrito_data': data['carrito_data'],
                'forma': data['forma'],
                'efe': float(data['efe']),
                'trans': float(data['trans'])
            }
            
        for id_v, info in self.ventas_deshechas.items():
            datos['deshechas'][str(id_v)] = {
                'timestamp': info['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'data': info['data']
            }
            
        if datos['recientes'] or datos['deshechas']:
            try:
                import socket
                archivo = f"cola_ventas_{socket.gethostname()}.json"
                with open(archivo, "w", encoding="utf-8") as f:
                    json.dump(datos, f)
            except Exception as e:
                print(f"Error al guardar cola de ventas: {e}")

    def inicializar_ui(self):
        layout_principal = QHBoxLayout(self) 
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)

        # ---------- PANEL IZQUIERDO: CARRITO ----------
        panel_izq = QFrame()
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(0,0,0,0)

        layout_izq.addWidget(QLabel("<b>🛒 Punto de Venta</b>"))
        layout_selector = QHBoxLayout()
        self.combo_articulos = QComboBox()
        self.combo_articulos.setObjectName("combo_articulos")
        layout_selector.addWidget(self.combo_articulos, stretch=1)
        
        btn_agregar = QPushButton("Agregar al Carrito")
        btn_agregar.setStyleSheet("background-color: #00b4d8; color: white; font-weight: bold; padding: 8px;")
        btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_agregar.clicked.connect(self.agregar_al_carrito)
        layout_selector.addWidget(btn_agregar)
        layout_izq.addLayout(layout_selector)

        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setColumnCount(5)
        self.tabla_carrito.setHorizontalHeaderLabels(["Artículo", "P.U.", "Cant.", "Subtotal", "Acciones"])
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.tabla_carrito.setColumnWidth(4, 200) 
        self.tabla_carrito.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout_izq.addWidget(self.tabla_carrito)

        layout_totales = QHBoxLayout()
        self.lbl_mensaje_venta = QLabel("")
        self.lbl_mensaje_venta.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout_totales.addWidget(self.lbl_mensaje_venta, stretch=1)

        self.lbl_total = QLabel("Total: $ 0.00")
        self.lbl_total.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout_totales.addWidget(self.lbl_total)
        layout_izq.addLayout(layout_totales)

        layout_pagos = QHBoxLayout()
        btn_efectivo = QPushButton("💵 Pago Efectivo")
        btn_efectivo.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        btn_efectivo.clicked.connect(lambda: self.procesar_pago("Efectivo"))
        
        btn_transf = QPushButton("📱 Pago Transferencia")
        btn_transf.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        btn_transf.clicked.connect(lambda: self.procesar_pago("Transferencia"))
        
        btn_mixto = QPushButton("⚖️ Pago Mixto")
        btn_mixto.setStyleSheet("background-color: #9C27B0; color: white; padding: 10px; font-weight: bold;")
        btn_mixto.clicked.connect(lambda: self.procesar_pago("Mixto"))

        layout_pagos.addWidget(btn_efectivo); layout_pagos.addWidget(btn_transf); layout_pagos.addWidget(btn_mixto)
        layout_izq.addLayout(layout_pagos)

        layout_principal.addWidget(panel_izq, stretch=5)

        # ---------- PANEL DERECHO: CAJA E HISTORIAL ----------
        panel_der = QFrame()
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(0,0,0,0)

        frame_caja = QFrame()
        frame_caja.setObjectName("frame_card_caja")
        layout_caja = QVBoxLayout(frame_caja)
        layout_caja.addWidget(QLabel("<b>💰 Resumen de Caja</b>"))
        
        self.lbl_caja_efe = QLabel("Efectivo: $ 0.00"); self.lbl_caja_efe.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.lbl_caja_trans = QLabel("Transferencia: $ 0.00"); self.lbl_caja_trans.setStyleSheet("color: #2196F3; font-weight: bold;")
        self.lbl_caja_tot = QLabel("TOTAL: $ 0.00"); self.lbl_caja_tot.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        layout_caja.addWidget(self.lbl_caja_efe); layout_caja.addWidget(self.lbl_caja_trans); layout_caja.addWidget(self.lbl_caja_tot)

        layout_btns_caja = QHBoxLayout()
        btn_extraer = QPushButton("📤 Extraer Dinero")
        btn_extraer.setStyleSheet("background-color: #FF9800; color: white;")
        btn_extraer.clicked.connect(self.extraer_dinero)
        
        btn_adicionar = QPushButton("📥 Agregar Dinero")
        btn_adicionar.setStyleSheet("background-color: #607D8B; color: white;")
        btn_adicionar.clicked.connect(self.agregar_dinero)
        
        layout_btns_caja.addWidget(btn_extraer); layout_btns_caja.addWidget(btn_adicionar)
        layout_caja.addLayout(layout_btns_caja)
        layout_der.addWidget(frame_caja)

        layout_der.addWidget(QLabel("<b>🧾 Últimas Ventas (48hs)</b>"))
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(7) 
        self.tabla_historial.setHorizontalHeaderLabels(["ID", "LU Vendedor", "Hora", "Detalle", "Pago", "Total", "Acciones"])
        self.tabla_historial.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 
        
        self.tabla_historial.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla_historial.setColumnWidth(6, 200) 
        
        self.tabla_historial.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout_der.addWidget(self.tabla_historial)

        layout_principal.addWidget(panel_der, stretch=5)
        
        self.cargar_articulos()
        self.actualizar_caja()
        self.actualizar_historial_con_deshechas()

    def cargar_articulos(self):
        self.lista_bd = backend.obtener_articulos_venta()
        self.combo_articulos.clear()
        for a in self.lista_bd:
            precio_float = float(a['precio'])
            self.combo_articulos.addItem(f"{a['articulo']} - $ {precio_float:.2f} (Stock: {a['stock']})", a)

    def agregar_al_carrito(self):
        if self.combo_articulos.currentIndex() == -1: return
        art = self.combo_articulos.currentData()
        
        if art['id'] in self.carrito:
            if self.carrito[art['id']]['cant'] < art['stock']:
                self.carrito[art['id']]['cant'] += 1
            else: QMessageBox.warning(self, "Stock", "No hay más stock disponible.")
        else:
            self.carrito[art['id']] = {
                'id': art['id'], 
                'articulo': art['articulo'], 
                'precio': float(art['precio']), 
                'cant': 1, 
                'stock': art['stock']
            }
        self.dibujar_carrito()

    def modificar_cant(self, id_art, valor):
        if id_art in self.carrito:
            nueva_cant = self.carrito[id_art]['cant'] + valor
            if nueva_cant <= 0: del self.carrito[id_art]
            elif nueva_cant > self.carrito[id_art]['stock']: QMessageBox.warning(self, "Stock", "Stock insuficiente.")
            else: self.carrito[id_art]['cant'] = nueva_cant
        self.dibujar_carrito()

    def eliminar_del_carrito(self, id_art):
        if id_art in self.carrito: del self.carrito[id_art]
        self.dibujar_carrito()

    def dibujar_carrito(self):
        self.tabla_carrito.setRowCount(0)
        total = 0.0
        
        for i, (id_art, item) in enumerate(self.carrito.items()):
            self.tabla_carrito.insertRow(i)
            self.tabla_carrito.setRowHeight(i, 45)
            
            subtotal = item['precio'] * item['cant']
            total += subtotal
            
            self.tabla_carrito.setItem(i, 0, QTableWidgetItem(item['articulo']))
            self.tabla_carrito.setItem(i, 1, QTableWidgetItem(f"$ {item['precio']:.2f}"))
            self.tabla_carrito.setItem(i, 2, QTableWidgetItem(str(item['cant'])))
            self.tabla_carrito.setItem(i, 3, QTableWidgetItem(f"$ {subtotal:.2f}"))
            
            w_btns = QWidget()
            l_btns = QHBoxLayout(w_btns)
            l_btns.setContentsMargins(4,4,4,4)
            l_btns.setSpacing(5)
            
            btn_menos = QPushButton(" - ")
            btn_menos.setStyleSheet("QPushButton { color: black; font-weight: bold; font-size: 16px; background-color: #e0e0e0; border-radius: 4px; padding: 6px; }")
            btn_menos.clicked.connect(lambda ch, id=id_art: self.modificar_cant(id, -1))
            
            btn_mas = QPushButton(" + ")
            btn_mas.setStyleSheet("QPushButton { color: black; font-weight: bold; font-size: 16px; background-color: #e0e0e0; border-radius: 4px; padding: 6px; }")
            btn_mas.clicked.connect(lambda ch, id=id_art: self.modificar_cant(id, 1))
            
            btn_del = QPushButton(" Eliminar ")
            btn_del.setStyleSheet("QPushButton { color: white; font-weight: bold; font-size: 13px; background-color: #f44336; border-radius: 4px; padding: 6px; }")
            btn_del.clicked.connect(lambda ch, id=id_art: self.eliminar_del_carrito(id))
            
            l_btns.addWidget(btn_menos); l_btns.addWidget(btn_mas); l_btns.addWidget(btn_del)
            self.tabla_carrito.setCellWidget(i, 4, w_btns)
            
        self.lbl_total.setText(f"Total: $ {total:.2f}")

    def procesar_pago(self, forma):
        if not self.carrito: return QMessageBox.warning(self, "Vacío", "El carrito está vacío.")
        
        total = sum(i['precio'] * i['cant'] for i in self.carrito.values())
        pago_efe = 0.0
        pago_trans = 0.0
        
        if forma == "Efectivo": pago_efe = total
        elif forma == "Transferencia": pago_trans = total
        elif forma == "Mixto":
            monto_efe, ok = QInputDialog.getDouble(self, "Pago Mixto", f"Total a pagar: ${total:.2f}\nIngrese cantidad en EFECTIVO:", min=0.0, max=total, decimals=2)
            if not ok: return
            pago_efe = monto_efe
            pago_trans = total - monto_efe

        exito, r = backend.registrar_venta(self.lu_admin, self.carrito, forma, total, pago_efe, pago_trans)
        if exito:
            id_venta = r
            self.ventas_recientes[id_venta] = {'timestamp': datetime.now(), 'carrito_data': self.carrito.copy(), 'forma': forma, 'efe': pago_efe, 'trans': pago_trans}
            
            self.carrito.clear()
            self.dibujar_carrito()
            self.cargar_articulos()
            self.actualizar_caja()
            self.actualizar_historial_con_deshechas()
            
            self.lbl_mensaje_venta.setText("<span style='color:#4CAF50; font-weight:bold;'>✅ ¡Venta registrada exitosamente!</span>")
            QTimer.singleShot(3000, lambda: self.lbl_mensaje_venta.setText(""))
            
        else: QMessageBox.critical(self, "Error", r)

    def verificar_pass_hacienda(self):
        ahora = datetime.now()
        if self.tiempo_autorizacion and (ahora - self.tiempo_autorizacion).total_seconds() < 300:
            return True 
        pwd, ok = QInputDialog.getText(self, "Seguridad", "Contraseña de Hacienda:", QLineEdit.EchoMode.Password)
        if ok and pwd == "Ingeniumcei26":
            self.tiempo_autorizacion = datetime.now()
            return True
        elif ok: QMessageBox.warning(self, "Denegado", "Contraseña incorrecta.")
        return False

    def actualizar_caja(self):
        e, t, tot = backend.obtener_estado_caja()
        self.lbl_caja_efe.setText(f"Efectivo: $ {e:.2f}")
        self.lbl_caja_trans.setText(f"Transferencia: $ {t:.2f}")
        self.lbl_caja_tot.setText(f"TOTAL: $ {tot:.2f}")

    def extraer_dinero(self):
        if not self.verificar_pass_hacienda(): return
        c_efe, _, _ = backend.obtener_estado_caja()
        monto, ok = QInputDialog.getDouble(self, "Extraer a Banco", f"Efectivo disponible: ${c_efe:.2f}\nMonto a transferir:", min=0.01, max=c_efe, decimals=2)
        if ok:
            exito, msj = backend.registrar_movimiento_caja(self.lu_admin, 0, monto, monto, 0, "CAJA_VENTAS", "Extracción Efectivo a Transferencia")
            if exito: self.actualizar_caja()
            else: QMessageBox.critical(self, "Error", msj)

    def agregar_dinero(self):
        if not self.verificar_pass_hacienda(): return
        efe, ok1 = QInputDialog.getDouble(self, "Adicionar", "Monto a ingresar en Efectivo:", min=0, max=99999, decimals=2)
        if not ok1: return
        trans, ok2 = QInputDialog.getDouble(self, "Adicionar", "Monto a ingresar en Transferencia:", min=0, max=99999, decimals=2)
        if not ok2: return
        
        if efe > 0 or trans > 0:
            exito, msj = backend.registrar_movimiento_caja(self.lu_admin, efe, trans, 0, 0, "CAJA_VENTAS", "Adición Manual de Dinero")
            if exito: self.actualizar_caja()

    def verificar_arqueo(self):
        ahora = datetime.now()
        if ahora.weekday() <= 4 and 8 <= ahora.hour <= 20 and ahora.hour % 2 == 0:
            if self.ultimo_arqueo_hora != ahora.hour:
                self.ultimo_arqueo_hora = ahora.hour
                c_efe, _, _ = backend.obtener_estado_caja()
                
                ingresado, ok = QInputDialog.getDouble(self, "Arqueo de Caja Obligatorio", 
                    "Por favor, cuente los billetes físicos en la caja e ingrese el total en EFECTIVO:", min=0, max=999999, decimals=2)
                
                if ok:
                    if abs(ingresado - c_efe) > 0.1: 
                        QMessageBox.warning(self, "Diferencia de Caja", f"⚠️ ADVERTENCIA: El sistema indica ${c_efe:.2f} pero usted declaró ${ingresado:.2f}.\n\nSe ha guardado registro de esta discrepancia, pero puede continuar operando.")
                    else:
                        QMessageBox.information(self, "Arqueo Correcto", "¡La caja cuadra perfectamente! Buen trabajo.")

    def actualizar_historial(self):
        v_scroll = self.tabla_historial.verticalScrollBar().value()
        h_scroll = self.tabla_historial.horizontalScrollBar().value()

        ventas = backend.obtener_historial_48h()
        self.tabla_historial.setRowCount(0)
        
        for i, v in enumerate(ventas):
            self.tabla_historial.insertRow(i)
            self.tabla_historial.setRowHeight(i, 45)
            id_v = v['id']
            
            self.tabla_historial.setItem(i, 0, QTableWidgetItem(str(id_v)))
            self.tabla_historial.setItem(i, 1, QTableWidgetItem(str(v['lu_usuario']))) 
            self.tabla_historial.setItem(i, 2, QTableWidgetItem(str(v['hora'])))
            
            item_detalle = QTableWidgetItem(v['articulos_y_cantidades'])
            item_detalle.setToolTip(v['articulos_y_cantidades']) 
            self.tabla_historial.setItem(i, 3, item_detalle)
            
            self.tabla_historial.setItem(i, 4, QTableWidgetItem(v['forma_pago']))
            self.tabla_historial.setItem(i, 5, QTableWidgetItem(f"${v['total']}"))
            
            if id_v in self.ventas_recientes:
                btn = QPushButton("↩️ Deshacer")
                btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 6px; border-radius: 4px; min-width: 140px;")
                btn.clicked.connect(lambda ch, id=id_v: self.deshacer_venta(id))
                
                w_btn = QWidget(); l_btn = QHBoxLayout(w_btn); l_btn.setContentsMargins(4,4,4,4)
                l_btn.addWidget(btn)
                
                self.ventas_recientes[id_v]['btn'] = btn
                self.tabla_historial.setCellWidget(i, 6, w_btn)
            else:
                item_cons = QTableWidgetItem("Consolidada")
                item_cons.setForeground(QColor("#4CAF50"))
                self.tabla_historial.setItem(i, 6, item_cons)

        self.tabla_historial.verticalScrollBar().setValue(v_scroll)
        self.tabla_historial.horizontalScrollBar().setValue(h_scroll)

    def deshacer_venta(self, id_venta):
        if id_venta in self.ventas_recientes:
            data = self.ventas_recientes[id_venta]
            backend.revertir_venta(id_venta, data['carrito_data'], data['efe'], data['trans'], self.lu_admin)
            
            del self.ventas_recientes[id_venta]
            self.ventas_deshechas[id_venta] = {'timestamp': datetime.now(), 'data': data, 'btn': None}
            
            self.actualizar_caja()
            self.cargar_articulos()
            self.actualizar_historial_con_deshechas()

    def actualizar_historial_con_deshechas(self):
        self.actualizar_historial() 
        
        for id_v, info in self.ventas_deshechas.items():
            self.tabla_historial.insertRow(0)
            self.tabla_historial.setRowHeight(0, 45)
            self.tabla_historial.setItem(0, 0, QTableWidgetItem(str(id_v)))
            
            item_nulo = QTableWidgetItem("VENTA ANULADA")
            item_nulo.setForeground(QColor("#f44336"))
            self.tabla_historial.setItem(0, 3, item_nulo)
            
            btn = QPushButton("❌ Cancelar Anulación")
            btn.setStyleSheet("background-color: #9c27b0; color: white; font-weight: bold; padding: 6px; border-radius: 4px; min-width: 160px;")
            btn.clicked.connect(lambda ch, id=id_v: self.cancelar_deshacer(id))
            
            w_btn = QWidget(); l_btn = QHBoxLayout(w_btn); l_btn.setContentsMargins(4,4,4,4)
            l_btn.addWidget(btn)
            
            info['btn'] = btn
            self.tabla_historial.setCellWidget(0, 6, w_btn)

    def cancelar_deshacer(self, id_venta_original):
        if id_venta_original in self.ventas_deshechas:
            d = self.ventas_deshechas[id_venta_original]['data']
            backend.registrar_venta(self.lu_admin, d['carrito_data'], d['forma'], sum(i['precio']*i['cant'] for i in d['carrito_data'].values()), d['efe'], d['trans'])
            del self.ventas_deshechas[id_venta_original]
            self.cargar_articulos()
            self.actualizar_caja()
            self.actualizar_historial_con_deshechas()

    def procesar_colas_deshacer(self):
        ahora = datetime.now()
        cambios = False
        
        borrar_recientes = []
        for id_v, data in self.ventas_recientes.items():
            restante = 300 - (ahora - data['timestamp']).total_seconds()
            if restante <= 0: borrar_recientes.append(id_v)
            elif 'btn' in data and data['btn']:
                m, s = divmod(int(restante), 60)
                data['btn'].setText(f"↩️ Deshacer ({m}:{s:02d})")
                
        for i in borrar_recientes: del self.ventas_recientes[i]; cambios = True

        borrar_deshechas = []
        for id_v, info in self.ventas_deshechas.items():
            restante = 120 - (ahora - info['timestamp']).total_seconds()
            if restante <= 0: borrar_deshechas.append(id_v)
            elif 'btn' in info and info['btn']:
                m, s = divmod(int(restante), 60)
                info['btn'].setText(f"❌ Cancelar Anulación ({m}:{s:02d})")

        for i in borrar_deshechas: del self.ventas_deshechas[i]; cambios = True
        
        if cambios: self.actualizar_historial_con_deshechas()

    # --- FUNCIÓN DE SINCRONIZACIÓN (LA QUE FALTABA) ---
    def sincronizar_remoto(self):
        """Refresca los datos de la pantalla con las acciones de la otra PC."""
        self.actualizar_caja()
        self.actualizar_historial_con_deshechas()
        
        if not self.carrito:
            self.cargar_articulos()