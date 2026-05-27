import os
import io # Importación nueva y necesaria
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QImage
from PyQt6.QtCore import Qt
from PIL import Image, ImageOps # Importación de la librería que instalamos

def procesar_avatar_circular(ruta_imagen, tamano):
    """Carga una imagen con Pillow, la endereza infaliblemente usando EXIF, y la hace circular."""
    if not ruta_imagen or not os.path.exists(ruta_imagen):
        return None

    try:
        # 1. ABRIR Y ENDEREZAR CON PILLOW (La solución real)
        with Image.open(ruta_imagen) as img:
            # Esta función de Pillow es magia pura: lee EXIF y rota los píxeles reales
            img_corregida = ImageOps.exif_transpose(img)
            
            # Convertimos a RGB para asegurar compatibilidad si es WebP o tiene transparencia
            if img_corregida.mode in ('RGBA', 'LA', 'P'):
                img_corregida = img_corregida.convert('RGB')

            # 2. CONVERTIR PILLOW A PYQT6
            # Guardamos la imagen corregida en memoria como bytes
            byte_arr = io.BytesIO()
            img_corregida.save(byte_arr, format='JPEG')
            byte_data = byte_arr.getvalue()
            
            # Cargamos esos bytes en un QImage de PyQt
            qimage = QImage.fromData(byte_data)
            pixmap_original = QPixmap.fromImage(qimage)

        # 3. LÓGICA DE RECORTE Y CÍRCULO (Igual que antes)
        if pixmap_original.isNull():
            return None

        lado_menor = min(pixmap_original.width(), pixmap_original.height())
        rectangulo_cuadrado = pixmap_original.copy(
            (pixmap_original.width() - lado_menor) // 2,
            (pixmap_original.height() - lado_menor) // 2,
            lado_menor,
            lado_menor
        )

        pixmap_escalado = rectangulo_cuadrado.scaled(
            tamano, tamano, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )

        pixmap_circular = QPixmap(tamano, tamano)
        pixmap_circular.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap_circular)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(0, 0, tamano, tamano)
        
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap_escalado)
        painter.end()

        return pixmap_circular

    except Exception as e:
        print(f"Error crítico procesando avatar con Pillow: {e}")
        return None