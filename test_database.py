# test_database.py
from decimal import Decimal


def test_product_count(db_connection):
    """Проверка наличия товаров в таблице."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM products;")
    count = cursor.fetchone()[0]
    assert count > 0, f"Ожидали  товар, но нашли {count}"
    cursor.close()


def test_inactive_product_price(db_connection):
    """Проверка цены неактивного товара."""
    cursor = db_connection.cursor()
    # SQL-запрос для выборки цены товара "Keyboard", который не активен (is_active = FALSE)
    cursor.execute("SELECT price FROM products WHERE name = %s AND is_active = FALSE;", ('Keyboard',))
    result = cursor.fetchone()[0]
    assert result is not None, "Товар 'Keyboard' не найден или не неактивен"
    expected_price = Decimal('75.20')
    assert result == expected_price, f"Ожидали цену 75.20, но получили {result}"
    cursor.close()
