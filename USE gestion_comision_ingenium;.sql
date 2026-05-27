USE gestion_comision_ingenium;

CREATE TABLE IF NOT EXISTS libros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150),
    descripcion TEXT,
    tipo VARCHAR(50), 
    cantidad INT DEFAULT 0,
    disponible INT DEFAULT 0,
    veces_prestado INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS historial_biblioteca (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_usuario_presta VARCHAR(20),
    apellidos_presta VARCHAR(100),
    nombres_presta VARCHAR(100),
    id_libro INT,
    nombre_libro VARCHAR(150),
    apellidos_beneficiario VARCHAR(100),
    nombres_beneficiario VARCHAR(100),
    lu_beneficiario VARCHAR(20),
    fecha_prestamo DATE,
    hora_prestamo TIME,
    lu_usuario_recibe VARCHAR(20) DEFAULT NULL,
    apellidos_recibe VARCHAR(100) DEFAULT NULL,
    nombres_recibe VARCHAR(100) DEFAULT NULL,
    fecha_devolucion DATE DEFAULT NULL,
    hora_devolucion TIME DEFAULT NULL,
    devuelto BOOLEAN DEFAULT NULL,
    objeto_danado BOOLEAN DEFAULT NULL,
    corresponde_falta BOOLEAN DEFAULT NULL
);