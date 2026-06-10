ALTER TABLE folders
  ADD COLUMN creado_por_uid VARCHAR(255) NULL,
  ADD INDEX idx_folders_creado_por (creado_por_uid),
  ADD CONSTRAINT fk_folders_usuario
    FOREIGN KEY (creado_por_uid)
    REFERENCES usuarios(uid)
    ON DELETE SET NULL;

