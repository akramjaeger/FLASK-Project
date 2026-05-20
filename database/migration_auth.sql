USE marketplace_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, password_hash, role)
VALUES
('admin', 'scrypt:32768:8:1$RoJ2bsFsUJrV0wwO$21b8f2360a0d0e07de8f9221d3d27cc999a1b3d425063811fd908e2c555914bac435c8550938ddfde20a88fd7435caefc785249adbc0111cacde1c7899294b90', 'admin'),
('player1', 'scrypt:32768:8:1$EbyWXCoHTF0hfKlD$ab4f241667dfd0c70fe8865b8d1d11aac2e79e9108f5dd1649be7cc3e1f4abe40e6536c7fa40844afeb5e8f83b0bb9940ea6725f6fe3a450e2a915525cb4efe2', 'user')
ON DUPLICATE KEY UPDATE username = VALUES(username);
