import requests
import os
from decimal import Decimal

API_URL = os.environ.get("API_URL", "http://localhost:5000")


def test_add_new_product_via_api_and_verify_in_db(db_connection):
    """
    Отправляем POST-запрос через API и проверяем результат SQL-запросом.
    """
    new_product_data = {
        "name": "Monitor",
        "price": "299.99"
    }

    # 1. Действие: Отправляем запрос к API
    response = requests.post(f"{API_URL}/product", json=new_product_data)
    assert response.status_code == 201
    response_data = response.json()
    new_product_id = response_data['id']

    # 2. Валидация в БД: Проверяем, что запись появилась и данные верны
    cursor = db_connection.cursor()
    cursor.execute("SELECT name, price, is_active FROM products WHERE id = %s;", (new_product_id,))
    result = cursor.fetchone()

    assert result is not None, "Продукт не найден в базе данных после запроса API"

    name, price_decimal, is_active = result

    assert name == "Monitor"
    # Используем Decimal для точного сравнения цены
    assert price_decimal == Decimal("299.99")
    assert is_active is True  # Проверяем, что по умолчанию он активен

    # Чистим за собой
    cursor.execute("DELETE FROM products WHERE id = %s;", (new_product_id,))

    # Проверяем, что хорошо почистили
    cursor.execute("SELECT name, price, is_active FROM products WHERE id = %s;", (new_product_id,))
    result = cursor.fetchone()

    assert result is None, "Продукт найден в базе данных после чистки"
    cursor.close()


def test_add_invalid_product_via_api_and_verify_in_db(db_connection):
    """
    Отправляем POST-запрос через API и проверяем результат SQL-запросом.
    """
    new_product_data = {
        "name": "Invalid Product"
    }

    # 1. Действие: Отправляем запрос к API
    response = requests.post(f"{API_URL}/product", json=new_product_data)
    assert response.status_code == 400

    # 2. Валидация в БД: Проверяем, что запись не появилась и данные верны
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM products WHERE name = %s;", ("Invalid Product",))
    result = cursor.fetchone()

    assert result is None, "Продукт не найден в базе данных после запроса API"

    cursor.close()


def test_mock_via_api_and_verify_in_db(db_connection):
    """
    Отправляем POST-запрос через API и проверяем результат SQL-запросом.
    """

    # 1. Подготовка (Precondition)
    cursor = db_connection.cursor()
    cursor.execute("SELECT is_active FROM products WHERE name = %s;", ("Laptop",))
    result = cursor.fetchone()[0]

    assert result is True, "Продукт не активен"

    # Имитация действия API:
    cursor.execute("UPDATE products SET is_active = FALSE WHERE name = %s;", ('Laptop',))
    db_connection.commit()  # Обязательно коммитим изменения

    cursor.execute("SELECT is_active FROM products WHERE name = %s;", ("Laptop",))
    result = cursor.fetchone()[0]

    # Валидация (Validation)
    assert result is False, "Продукт активен"
    cursor.close()
