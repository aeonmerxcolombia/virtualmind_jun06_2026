-- 006_create_folders.sql

DROP TABLE IF EXISTS folders;

CREATE TABLE folders (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  nombre        VARCHAR(255) NOT NULL,
  descripcion   TEXT,
  parent_id     INT NULL,
  subido_por_uid VARCHAR(255)
      CHARACTER SET utf8mb4
      COLLATE utf8mb4_unicode_ci
      NULL,
  fecha_creado  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  estado        TINYINT(1) DEFAULT 1,
  CONSTRAINT fk_folders_padre
    FOREIGN KEY (parent_id)
      REFERENCES folders(id)
      ON DELETE CASCADE,
  CONSTRAINT fk_folders_usuario
    FOREIGN KEY (subido_por_uid)
      REFERENCES usuarios(uid)
      ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

