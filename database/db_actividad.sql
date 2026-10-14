CREATE DATABASE IF NOT EXISTS Aplicacion;
USE Aplicacion;

-- 1. Tabla de Usuarios (Autenticación y Datos Base)
CREATE TABLE usuarios(
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    carrera VARCHAR(100) NOT NULL,
    estado_geografico VARCHAR(50) DEFAULT NULL, -- Renombrado para evitar confusión
    municipio VARCHAR(50) DEFAULT NULL,
    estado_cuenta VARCHAR(20) DEFAULT 'Activa', -- Nuevo: Para saber si está baneado/activo
    rol_sistema VARCHAR(30) DEFAULT 'Estudiante', -- Nuevo: Para escalabilidad futura
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Perfiles (Relación 1 a 1 con Usuarios)
CREATE TABLE perfiles_usuarios(
    usuario_id INT PRIMARY KEY,
    nombre_mostrar VARCHAR(100),
    datos_crudos JSON, 
    atributos_dinamicos JSON, -- Nuevo: Para meter cosas de deportes, e-sports, etc. sin alterar la tabla
    resumen_publico_ia TEXT,
    perfil_estructurado_ia JSON,
    embedding_perfil JSON, -- Usamos JSON para guardar el arreglo de floats de Nomic
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- 3. Tabla de Eventos / Proyectos
CREATE TABLE eventos(
    id_evento INT AUTO_INCREMENT PRIMARY KEY,
    creador_id INT NOT NULL,
    categoria_principal VARCHAR(50) NOT NULL DEFAULT 'Academico', -- Nuevo: Academico, Deportivo, Social
    titulo VARCHAR(150) NOT NULL,
    descripcion_libre TEXT, -- Lo que escribe el usuario originalmente
    detalles_especificos JSON,
    requisitos_ia JSON, 
    embedding_requisitos JSON,
    estado VARCHAR(30) DEFAULT 'Abierto',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creador_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- 4. Tabla de Solicitudes (Invitaciones enviadas por la plataforma o usuarios)
CREATE TABLE solicitudes_equipo(
    id_solicitud INT AUTO_INCREMENT PRIMARY KEY,
    id_evento INT NOT NULL, -- Faltaba saber a qué evento lo están invitando
    id_remitente INT NOT NULL, 
    id_destinatario INT NOT NULL,
    estado VARCHAR(50) DEFAULT 'Pendiente', -- Pendiente, Aceptada, Rechazada
    mensaje_explicacion TEXT, -- Aquí va la justificación generada por la IA
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE,
    FOREIGN KEY (id_remitente) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_destinatario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- 5. NUEVA: Tabla de Participantes (Los que ya están dentro del equipo)
CREATE TABLE participantes_evento(
    id_participacion INT AUTO_INCREMENT PRIMARY KEY,
    id_evento INT NOT NULL,
    id_usuario INT NOT NULL,
    rol VARCHAR(50) DEFAULT 'Participante', -- Líder, Defensa, Desarrollador, etc.
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    UNIQUE(id_evento, id_usuario) -- Evita que un usuario se una dos veces al mismo evento
);