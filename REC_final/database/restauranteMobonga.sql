CREATE DATABASE restauranteMobonga;
USE restauranteMobonga;

-- ==========================
-- Usuários
-- ==========================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('CLIENTE', 'ATENDENTE', 'ADMIN') NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email, password, role) VALUES ('ADM', 'admin@admin.com', '111', 'ADMIN');
INSERT INTO users (name, email, password, role) VALUES ('ATENDENTE', 'atendente@atendente.com', '111', 'ATENDENTE');
INSERT INTO users (name, email, password, role) VALUES ('CLIENTE', 'cliente@cliente.com', '111', 'CLIENTE');

-- ==========================
-- Cardápio
-- ==========================
CREATE TABLE menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO menu_items (name, description, price, available) VALUES
('Hambúrguer Clássico', 'Pão, carne bovina, queijo e alface', 28.90, TRUE),
('X-Bacon', 'Hambúrguer com bacon e cheddar', 34.90, TRUE),
('Batata Frita', 'Porção média', 18.00, TRUE),
('Refrigerante Lata', '350ml', 6.50, TRUE),
('Suco Natural', 'Laranja 500ml', 9.90, TRUE),
('Pizza Calabresa', 'Pizza média de calabresa', 54.90, TRUE),
('Pizza Frango com Catupiry', 'Pizza média', 59.90, TRUE),
('Água Mineral', '500ml', 4.00, TRUE),
('Milk Shake Chocolate', '400ml', 17.90, TRUE),
('Sorvete', 'Taça com duas bolas', 14.90, FALSE);

-- ==========================
-- Comandas
-- ==========================
CREATE TABLE orders (
    -- Código incremental
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    created_by INT NOT NULL,
    closed_by INT NULL,
    paid_by INT NULL,
    status ENUM('OPEN','CLOSED','PAID') DEFAULT 'OPEN',
    total DECIMAL(10,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME NULL,
    paid_at DATETIME NULL,
    FOREIGN KEY (customer_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (closed_by) REFERENCES users(id),
    FOREIGN KEY (paid_by) REFERENCES users(id)
);

-- ==========================
-- Itens da comanda
-- ==========================
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    menu_item_id INT NOT NULL,
    quantity INT NOT NULL,
    -- preço no momento da compra
    unit_price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
);

-- ==========================
-- Pagamentos
-- ==========================
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT UNIQUE NOT NULL,
    payment_method ENUM('Dinheiro', 'Cartão de Crédito', 'Cartão de Débito', 'PIX') NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    amount_received DECIMAL(10,2) NOT NULL,
    change_amount DECIMAL(10,2) NOT NULL,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);