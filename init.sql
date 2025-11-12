-- init.sql

-- Создание таблицы товаров
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Вставка тестовых данных
INSERT INTO products (name, price, is_active) VALUES
('Laptop', 1200.50, TRUE),
('Mouse', 25.00, TRUE),
('Keyboard', 75.20, FALSE)
ON CONFLICT (id) DO NOTHING; -- Чтобы не вставлять данные повторно при перезапуске
