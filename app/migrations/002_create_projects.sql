-- 002_create_projects.sql

CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255)    NOT NULL,
  description TEXT,
  start_date DATE      NOT NULL,
  end_date   DATE,
  estado     BOOLEAN   DEFAULT TRUE
);

