CREATE TABLE profiles (
    uid VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL,
    foto_url VARCHAR(255),
    direccion VARCHAR(255),
    telefono VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE
);

