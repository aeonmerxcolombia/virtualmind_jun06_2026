-- 001_create_usuarios.sql

CREATE TABLE usuarios (
  uid VARCHAR(255) PRIMARY KEY,
  nombre VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  roles JSON NOT NULL,
  estado BOOLEAN DEFAULT TRUE
);

