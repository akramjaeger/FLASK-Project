CREATE DATABASE IF NOT EXISTS marketplace_db;
USE marketplace_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    category ENUM('gift_card', 'video_game') NOT NULL,
    platform VARCHAR(100) DEFAULT '',
    region VARCHAR(60) DEFAULT '',
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    image_url VARCHAR(255) DEFAULT '',
    description TEXT,
    is_hidden TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_user_product (user_id, product_id),
    CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_cart_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('paid', 'cancelled') NOT NULL DEFAULT 'paid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    title_snapshot VARCHAR(150) NOT NULL,
    price_snapshot DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

INSERT INTO users (username, password_hash, role)
VALUES
('admin', 'scrypt:32768:8:1$RoJ2bsFsUJrV0wwO$21b8f2360a0d0e07de8f9221d3d27cc999a1b3d425063811fd908e2c555914bac435c8550938ddfde20a88fd7435caefc785249adbc0111cacde1c7899294b90', 'admin'),
('player1', 'scrypt:32768:8:1$EbyWXCoHTF0hfKlD$ab4f241667dfd0c70fe8865b8d1d11aac2e79e9108f5dd1649be7cc3e1f4abe40e6536c7fa40844afeb5e8f83b0bb9940ea6725f6fe3a450e2a915525cb4efe2', 'user')
ON DUPLICATE KEY UPDATE username = VALUES(username);

INSERT INTO products (title, category, platform, region, price, stock, image_url, description)
VALUES
('Steam Wallet $50', 'gift_card', 'Steam', 'Global', 45.00, 10, 'https://images.unsplash.com/photo-1614294148960-9aa740632a87?auto=format&fit=crop&w=1200&q=80', 'Instant delivery Steam wallet gift card for global use.'),
('PlayStation Store $25', 'gift_card', 'PlayStation', 'US', 22.00, 7, 'https://images.unsplash.com/photo-1605901309584-818e25960a8f?auto=format&fit=crop&w=1200&q=80', 'US region PlayStation Store card, redeemable on PSN.'),
('Elden Ring (PC)', 'video_game', 'PC', 'Global', 39.99, 5, 'https://images.unsplash.com/photo-1542751110-97427bbecf20?auto=format&fit=crop&w=1200&q=80', 'Digital code for Elden Ring on PC.'),
('FIFA 25 (PS5)', 'video_game', 'PlayStation 5', 'EU', 54.99, 3, 'https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1200&q=80', 'EU version digital edition for PS5.'),
('Xbox Gift Card $50', 'gift_card', 'Xbox', 'US', 47.50, 8, 'https://images.unsplash.com/photo-1605902711622-cfb43c44367e?auto=format&fit=crop&w=1200&q=80', 'Xbox Live gift card code, US region.'),
('Nintendo eShop $20', 'gift_card', 'Nintendo Switch', 'Global', 18.00, 12, 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80', 'Nintendo eShop card, digital code.'),
('Steam Wallet $20', 'gift_card', 'Steam', 'Global', 18.50, 15, 'https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=1200&q=80', 'Smaller Steam Wallet top-up.'),
('Google Play $25', 'gift_card', 'Google Play', 'Global', 23.00, 9, 'https://images.unsplash.com/photo-1526378724330-1d6f6a1b3f13?auto=format&fit=crop&w=1200&q=80', 'Google Play credit code.'),
('Discord Nitro 1mo', 'gift_card', 'Discord', 'Global', 4.99, 25, 'https://images.unsplash.com/photo-1545235617-9465d0b1b3b4?auto=format&fit=crop&w=1200&q=80', 'One month Discord Nitro subscription code.'),
('Minecraft (PC)', 'video_game', 'PC', 'Global', 26.95, 6, 'https://images.unsplash.com/photo-1600486913747-55e5470f3f73?auto=format&fit=crop&w=1200&q=80', 'Minecraft Java Edition digital code.'),
('Among Us (PC)', 'video_game', 'PC', 'Global', 2.99, 20, 'https://images.unsplash.com/photo-1606813902484-3d5d1b1f6f20?auto=format&fit=crop&w=1200&q=80', 'Casual multiplayer game code.'),
('Call of Duty (PS5)', 'video_game', 'PlayStation 5', 'US', 59.99, 4, 'https://images.unsplash.com/photo-1606813902484-3d5d1b1f6f20?auto=format&fit=crop&w=1200&q=80', 'PS5 digital edition code.'),
('Rocket League (Switch)', 'video_game', 'Nintendo Switch', 'Global', 19.99, 7, 'https://images.unsplash.com/photo-1597262975002-c5c3b14bbd62?auto=format&fit=crop&w=1200&q=80', 'Rocket League digital copy for Switch.'),
('Frostborn DLC', 'video_game', 'PC', 'Global', 9.99, 10, 'https://images.unsplash.com/photo-1593642532400-2682810df593?auto=format&fit=crop&w=1200&q=80', 'Expansion/DLC code for Frostborn.'),
('Xbox Game Pass 3mo', 'gift_card', 'Xbox', 'Global', 29.99, 5, 'https://images.unsplash.com/photo-1593642532973-d31b6557fa68?auto=format&fit=crop&w=1200&q=80', 'Three month Game Pass subscription code.');
