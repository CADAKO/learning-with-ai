# test_advanced_db.py
from decimal import Decimal

def test_max_price_active(db_connection):
    """Проверка общего количества товаров в таблице."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT MAX(price) FROM products WHERE is_active = TRUE")
    price = cursor.fetchone()[0]
    expected_price= Decimal("9999.50")
    assert price == expected_price, f"Ожидали цену 9999.50, но получили {price}"
    cursor.close()


def test_active_product_present(db_connection):
    cursor = db_connection.cursor()
    # SQL-запрос для выборки цены товара "Keyboard", который не активен (is_active = FALSE)
    cursor.execute("SELECT * FROM products WHERE name = %s AND is_active = TRUE;", ('Mouse',))
    result = cursor.fetchone()
    assert result is not None, "Товар 'Mouse' не найден или не неактивен"
    cursor.close()


def test_count_active(db_connection):
    cursor = db_connection.cursor()
    # SQL-запрос для выборки цены товара "Keyboard", который не активен (is_active = FALSE)
    cursor.execute("SELECT COUNT(*) FROM products WHERE  is_active = TRUE;")
    count = cursor.fetchone()[0]
    assert count == 2, f"Ожидалось 2 товара, а нашлось {count}"
    cursor.close()
