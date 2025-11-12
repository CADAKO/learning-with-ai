import requests
import os
from decimal import Decimal
import allure

API_URL = os.environ.get("API_URL", "http://localhost:5000")


@allure.feature("Product Management")
@allure.story("Add new product")
def test_add_new_product_via_api_and_verify_in_db(db_connection):
    """
    Отправляем POST-запрос через API и проверяем результат SQL-запросом.
    """
    with allure.step("Подготовка данных и отправка запроса API"):
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
    with allure.step("Валидация данных в базе данных"):
        cursor = db_connection.cursor()
        cursor.execute("SELECT name, price, is_active FROM products WHERE id = %s;", (new_product_id,))
        result = cursor.fetchone()
        assert result is not None, "Продукт не найден в базе данных после запроса API"

        allure.attach(str(result), 'Данные из БД', attachment_type=allure.attachment_type.TEXT)

        name, price_decimal, is_active = result

        assert name == "Monitor"
        # Используем Decimal для точного сравнения цены
        assert price_decimal == Decimal("299.99")
        assert is_active is True  # Проверяем, что по умолчанию он активен
    with allure.step("Очистка тестовых данных"):
        # Чистим за собой
        cursor.execute("DELETE FROM products WHERE id = %s;", (new_product_id,))
        db_connection.commit()
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


import allure
import psycopg2
import pytest
from decimal import Decimal


# ... остальные импорты (requests, os, time, BaseLocators)

# ... (фикстура db_connection и API_URL) ...

@allure.feature("Product Management")
@allure.story("Deactivate existing product")
def test_deactivate_laptop_via_mock_api(db_connection):
    """
    Имитирует деактивацию товара через API и проверяет статус в БД,
    восстанавливая исходное состояние после теста.
    """
    cursor = db_connection.cursor()

    try:
        with allure.step("Подготовка: Проверка, что товар 'Laptop' активен"):
            cursor.execute("SELECT is_active FROM products WHERE name = %s;", ("Laptop",))
            result = cursor.fetchone()[0]
            assert result is True, "Precondition failed: Товар 'Laptop' уже не активен перед тестом"
            allure.attach(str(result), 'Исходный статус is_active', attachment_type=allure.attachment_type.TEXT)

        with allure.step("Действие: Имитация вызова API (UPDATE в БД)"):
            # Имитация действия API:
            cursor.execute("UPDATE products SET is_active = FALSE WHERE name = %s;", ('Laptop',))
            db_connection.commit()  # Применяем изменения

        with allure.step("Валидация: Проверка нового статуса"):
            cursor.execute("SELECT is_active FROM products WHERE name = %s;", ("Laptop",))
            result = cursor.fetchone()[0]
            assert result is False, "Validation failed: Товар 'Laptop' остался активным после обновления"
            allure.attach(str(result), 'Новый статус is_active', attachment_type=allure.attachment_type.TEXT)

    finally:
        # --- CLEANUP (Восстановление исходного состояния) ---
        with allure.step("Очистка: Возвращаем товар 'Laptop' в активное состояние"):
            cursor.execute("UPDATE products SET is_active = TRUE WHERE name = %s;", ('Laptop',))
            db_connection.commit()
            cursor.close()

        # Можете добавить финальную проверку, что cleanup прошел успешно, если хотите
        print("Cleanup завершен: Laptop снова активен.")


