-- 1. Crear la base de datos
CREATE DATABASE IF NOT EXISTS gestion_comision_INGENIUM;

-- 2. Seleccionar la base de datos para usarla
USE gestion_comision_INGENIUM;

-- 3. Crear las tablas 

-- Tabla de beneficiarios 
CREATE TABLE IF NOT EXISTS beneficiarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apellidos VARCHAR(100),
    nombres VARCHAR(100),
    dni VARCHAR(20) UNIQUE,      
    lu VARCHAR(20) UNIQUE,       
    telefono VARCHAR(20) UNIQUE, 
    carrera VARCHAR(100),
    ruta_foto VARCHAR(255),
    correo VARCHAR(100) UNIQUE,  
    pan INT,
    faltas INT DEFAULT 0,
    penalizado BOOLEAN DEFAULT FALSE,
    horas_penalizacion FLOAT DEFAULT 0,
    cant_penalizaciones INT DEFAULT 0,
    prestamos_activos INT DEFAULT 0
);

-- Tabla de usuarios de la comision (Depende de beneficiarios)
CREATE TABLE IF NOT EXISTS usuarios_comision (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_usuario VARCHAR(20) UNIQUE, 
    contrasena VARCHAR(100),
    num_prestamos INT DEFAULT 0,
    num_recibidos INT DEFAULT 0,
    horas_logueado FLOAT DEFAULT 0,
    
    FOREIGN KEY (lu_usuario) REFERENCES beneficiarios(lu) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Tabla Historial de inicio de sesión (Depende de usuarios_comision)
CREATE TABLE IF NOT EXISTS historial_inicio_sesion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_usuario VARCHAR(20),
    fecha_inicio DATE,
    hora_inicio TIME,
    fecha_cierre DATE,
    hora_cierre TIME,
    cantidad_horas FLOAT,
    
    FOREIGN KEY (lu_usuario) REFERENCES usuarios_comision(lu_usuario) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Tabla historial de penalizaciones de los beneficiarios
CREATE TABLE IF NOT EXISTS historial_penalizaciones_beneficiarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_beneficiario VARCHAR(20),
    fecha_penalizacion DATETIME,
    fecha_despenalizacion DATETIME,
    razon TEXT,
    lu_usuario_penaliza VARCHAR(20)
);

-- Tabla de objetos para prestar
CREATE TABLE IF NOT EXISTS objetos_prestamos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_objeto VARCHAR(100),
    cantidad_total INT,
    cantidad_disponibles INT,
    en_prestamo INT,
    veces_prestado INT DEFAULT 0
);

-- Tabla historial de prestamos
CREATE TABLE IF NOT EXISTS historial_prestamos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apellidos_presta VARCHAR(100),
    nombres_presta VARCHAR(100),
    lu_usuario_presta VARCHAR(20),
    id_objeto INT,
    nombre_objeto VARCHAR(100),
    fecha_prestamo DATE,
    hora_prestamo TIME,
    apellidos_beneficiario VARCHAR(100),
    nombres_beneficiario VARCHAR(100),
    lu_beneficiario VARCHAR(20),
    apellidos_recibe VARCHAR(100),
    nombres_recibe VARCHAR(100),
    lu_usuario_recibe VARCHAR(20),
    fecha_devolucion DATE,
    hora_devolucion TIME,
    devuelto BOOLEAN,
    objeto_danado BOOLEAN,
    corresponde_falta BOOLEAN
);

-- Tabla de objetos para vender
CREATE TABLE IF NOT EXISTS objetos_ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    articulo VARCHAR(100),
    precio DECIMAL(10, 2), 
    stock INT,
    reponer_stock INT,
    veces_vendido INT 
);

-- Tabla historial de las ventas
CREATE TABLE IF NOT EXISTS historial_ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_usuario VARCHAR(20),
    fecha DATE,
    hora TIME,
    articulos_y_cantidades TEXT, 
    forma_pago VARCHAR(50),
    total DECIMAL(10, 2)
);

-- Tabla historial de la caja de ventas
CREATE TABLE IF NOT EXISTS historial_caja_ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_usuario VARCHAR(20),
    fecha_cierre DATE,
    entrada_efectivo DECIMAL(10, 2),
    entrada_transferencia DECIMAL(10, 2),
    salida_efectivo DECIMAL(10, 2),
    salida_transferencia DECIMAL(10, 2),
    caja_efectivo DECIMAL(10, 2),
    caja_transferencia DECIMAL(10, 2),
    caja_total DECIMAL(10, 2)
);

-- Tabla de objetos perdidos
CREATE TABLE IF NOT EXISTS objetos_perdidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_usuario INT,
    datos_persona_encuentra VARCHAR(200),
    fecha_encuentro DATE,
    hora_encuentro TIME,
    descripcion_objeto TEXT,
    lugar_encuentro VARCHAR(150),
    ubicacion_en_cei VARCHAR(150),
    fecha_registro DATE,
    hora_registro TIME,
    ruta_foto VARCHAR(255)
);

-- Tabla de objetos guardados
CREATE TABLE IF NOT EXISTS objetos_guardados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_beneficiario INT,
    lu_usuario_registra VARCHAR(20),
    lu_usuario_entrega VARCHAR(20),
    tipo_item VARCHAR(50),
    descripcion TEXT,
    lugar_guardado VARCHAR(150),
    ubicacion_en_cei VARCHAR(150),
    fecha_registro DATE,
    hora_registro TIME,
    fecha_entrega DATE,
    hora_entrega TIME
);

-- Tabla historial de ediciones
CREATE TABLE IF NOT EXISTS historial_edicion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tabla VARCHAR(50),
    tipo_edicion VARCHAR(50), 
    apellido_usuario VARCHAR(100),
    nombre_usuario VARCHAR(100),
    lu_usuario VARCHAR(20),
    fecha DATE,
    hora TIME
);

-- Tabla historial de pancitos
CREATE TABLE IF NOT EXISTS historial_pancitos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lu_usuario VARCHAR(20),
    lu_beneficiario VARCHAR(20),
    apellido_beneficiario VARCHAR(100),
    nombre_beneficiario VARCHAR(100),
    fecha DATE,
    hora TIME,
    entrego_pancito BOOLEAN
);

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

-- 4. Insertar un usuario de prueba 

-- Registramos en beneficiarios
INSERT INTO beneficiarios (apellidos, nombres, dni, lu, telefono, correo, pan)
VALUES ('Urtiaga', 'Mauricio Juan Alejandro', '42205633', '316449', '3876196764', 'juanurtiaga77@gmail.com', 0);

-- Damos acceso en usuarios comision
INSERT INTO usuarios_comision (lu_usuario, contrasena, num_prestamos, num_recibidos, horas_logueado)
VALUES ('316449', '455232', 0, 0, 0);