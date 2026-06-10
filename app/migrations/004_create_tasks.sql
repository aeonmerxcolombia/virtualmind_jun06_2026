-- 004_create_tasks.sql

CREATE TABLE tasks (
  id                 SERIAL      PRIMARY KEY,
  title              VARCHAR(255) NOT NULL,
  description        TEXT,
  project_id         INTEGER      NOT NULL
    REFERENCES projects(id) ON DELETE CASCADE,
  assigned_user_uid  VARCHAR(255) NOT NULL
    REFERENCES usuarios(uid) ON DELETE CASCADE,
  estado             BOOLEAN      DEFAULT TRUE
);

