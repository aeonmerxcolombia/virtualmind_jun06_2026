-- 005_create_archivos.sql

DROP TABLE IF EXISTS archivos;

CREATE TABLE archivos (
  id               INT          AUTO_INCREMENT PRIMARY KEY,
  nombre_archivo   VARCHAR(255) NOT NULL,
  url              TEXT         NOT NULL,
  tipo             VARCHAR(50),
  subido_por_uid   VARCHAR(255)
      CHARACTER SET utf8mb4
      COLLATE utf8mb4_unicode_ci
      NULL,
  fecha_subida     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_subido_por (subido_por_uid),
  CONSTRAINT fk_archivos_usuario
    FOREIGN KEY (subido_por_uid)
      REFERENCES usuarios(uid)
      ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

