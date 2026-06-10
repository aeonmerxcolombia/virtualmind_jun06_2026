-- 008_add_folder_id_to_archivos.sql

ALTER TABLE archivos
  ADD COLUMN folder_id INT NULL,
  ADD INDEX idx_archivos_folder (folder_id),
  ADD CONSTRAINT fk_archivos_folder
    FOREIGN KEY (folder_id)
    REFERENCES folders(id)
    ON DELETE SET NULL;

