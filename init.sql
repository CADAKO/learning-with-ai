-- init.sql

-- Создание таблицы товаров
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    original_price DECIMAL(10, 2) NOT NULL
);

-- Вставка тестовых данных
INSERT INTO products (name, price, is_active, original_price) VALUES
('Laptop', 9999.50, TRUE, 1200.50),
('Mouse', 25.00, TRUE, 25.00),
('Keyboard', 75.20, FALSE, 75.20)
ON CONFLICT (id) DO NOTHING; -- Чтобы не вставлять данные повторно при перезапуске


CREATE TABLE IF NOT EXISTS coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    discount_percent DECIMAL(5, 2) NOT NULL
);

-- Добавим один купон для теста
INSERT INTO coupons (code, discount_percent) VALUES ('SALE10', 10.00);

