CREATE TABLE project_participants (
  project_id INTEGER NOT NULL
    REFERENCES projects(id) ON DELETE CASCADE,
  user_uid   VARCHAR(255) NOT NULL
    REFERENCES usuarios(uid) ON DELETE CASCADE,
  PRIMARY KEY (project_id, user_uid)
);
