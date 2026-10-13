Create database if not exists Aplicacion;

create table usuarios(
id_usuario	INT AUTO_INCREMENT PRIMARY KEY,
nombre VARCHAR (150) NOT NULL
corrreo VARCHAR (50) NOT NULL,
carrera VARCHAR (100) NOT NULL,
estado VARCHAR (50) NOT NULL,
municipio VARCHAR (50) NOT NULL,
password_hash VARCHAR (250) NOT NULL
);

create table perfiles_usuarios(
usuario_id INT AUTO_INCREMENT PRIMARY KEY,
datos_crudos JSON, 
resumen_publico_ia TEXT
perfil_estructurado_ia JSON,
embedding_perfil JSON
);

create table eventos(
id INT PRIMARY KEY 
creador_id FOREIGN KEY,
titulo VARCHAR(150) NOT NULL,
detalles_especificos JSON,
requisitos_ia JSON 
embendding_requisitos BLOB
);

create table solicitudes_equipo(
id_solicitud INT PRIMARY KEY,
id_remitente INT REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
id_destinario INT REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
estado VARCHAR(50) DEFAULT 'Pendiente',
mensaje_explicacion TEXT,
fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (id_) REFERENCES 
);
