CREATE TABLE client_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL,
    nombre_cliente VARCHAR(255),
    nit VARCHAR(50),
    tipo_entidad VARCHAR(100),
    organizacion VARCHAR(255),
    persona_contacto VARCHAR(255),
    cargo_contacto VARCHAR(255),
    correo_contacto VARCHAR(255),
    whatsapp VARCHAR(50),
    ciudad VARCHAR(100),
    observaciones TEXT,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE
);

