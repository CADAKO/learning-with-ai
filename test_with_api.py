import requests
import os
from decimal import Decimal
import allure
from unittest.mock import MagicMock, patch
import pytest

API_URL = os.environ.get("API_URL", "http://localhost:5000")


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


@allure.feature("Product Management Via API")
class TestAddProduct:
    @allure.story("Add new product")
    def test_add_new_product_via_api_and_verify_in_db(self, db_connection):
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
            assert price_decimal == Decimal("269.99")
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

    @allure.story("Add product without price")
    def test_add_product_without_price_via_api_and_verify_in_db(self, db_connection):
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

    @allure.story("Add new product")
    def test_add_new_product_with_discount_via_api_and_verify_in_db(self, db_connection):
        """
        Отправляем POST-запрос через API и проверяем результат SQL-запросом.
        """
        with allure.step("Подготовка данных и отправка запроса API"):
            new_product_data = {
                "name": "Phone",
                "price": "300.00"
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

            name, price_discount, is_active = result

            assert name == "Phone"
            # Используем Decimal для точного сравнения цены
            assert price_discount == Decimal("270.0000")
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

    @allure.story("Add product with Invalid price")
    def test_add_product_with_invalid_price_via_api(self, db_connection):
        with allure.step("Подготовка данных и отправка запроса API"):
            new_product_data = {"name": "Invalid Price Item", "price": "abc"}
            response = requests.post(f"{API_URL}/product", json=new_product_data)
            assert response.status_code == 400

        # 2. Валидация в БД: Проверяем, что запись не появилась
        with allure.step("Валидация данных в базе данных"):
            cursor = db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM products WHERE name = %s;", ("Invalid Price Item",))
            result = cursor.fetchone()[0]
            assert result == 0, "Продукт найден в базе данных после запроса API"

        cursor.close()

    @allure.story("Add new product with zero price")
    def test_add_zero_price_product(self, db_connection):
        with allure.step("Подготовка данных и отправка запроса API"):
            new_product_data = {"name": "Free Item", "price": "0.00"}
            response = requests.post(f"{API_URL}/product", json=new_product_data)
            assert response.status_code == 201

        # 2. Валидация в БД: Проверяем, что запись появилась
        with allure.step("Валидация данных в базе данных"):
            cursor = db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM products WHERE name = %s;", ("Free Item",))
            result = cursor.fetchone()[0]
            assert result == 1, "Продукт не найден в базе данных после запроса API"
        cursor.execute("DELETE FROM products WHERE name = %s;", ("Free Item",))
        db_connection.commit()

        cursor.close()

    @allure.story("Add new product with minus price")
    def test_add_minus_price_product(self, db_connection):
        with allure.step("Подготовка данных и отправка запроса API"):
            new_product_data = {"name": "Minus Item", "price": "-1.00"}
            response = requests.post(f"{API_URL}/product", json=new_product_data)
            assert response.status_code == 400

        # 2. Валидация в БД: Проверяем, что запись не появилась
        with allure.step("Валидация данных в базе данных"):
            cursor = db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM products WHERE name = %s;", ("Minus Item",))
            result = cursor.fetchone()[0]
            assert result == 0, "Продукт найден в базе данных после запроса API"

        cursor.close()

    @allure.story("Add new product without name and price")
    def test_add_without_name_without_price_product(self, db_connection):
        with allure.step("Подготовка данных и отправка запроса API"):
            new_product_data = {"name": "", "price": ""}
            response = requests.post(f"{API_URL}/product", json=new_product_data)
            assert response.status_code == 400

    @allure.story("Add new product with long name")
    def test_add_with_long_name_product(self, db_connection):
        with allure.step("Подготовка данных и отправка запроса API"):
            long_name = str("q" * 100)
            new_product_data = {"name": f"{long_name}", "price": "1.00"}
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

            name, price, is_active = result

            assert name == long_name
            assert price == Decimal("0.90")
        with allure.step("Очистка тестовых данных"):
            # Чистим за собой
            cursor.execute("DELETE FROM products WHERE id = %s;", (new_product_id,))
            db_connection.commit()
            # Проверяем, что хорошо почистили
            cursor.execute("SELECT name, price, is_active FROM products WHERE id = %s;", (new_product_id,))
            result = cursor.fetchone()

            assert result is None, "Продукт найден в базе данных после чистки"
        cursor.close()

    @allure.story("Add new product with extra long name")
    def test_add_with_extra_long_name_product(self, db_connection):
        with allure.step("Подготовка данных и отправка запроса API"):
            extra_long_name = str("q" * 101)
            new_product_data = {"name": f"{extra_long_name}", "price": "1.00"}
            response = requests.post(f"{API_URL}/product", json=new_product_data)
            assert response.status_code == 400
            # 2. Валидация в БД: Проверяем, что запись не появилась
        with allure.step("Валидация данных в базе данных"):
            cursor = db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM products WHERE name = %s;", (extra_long_name,))
            result = cursor.fetchone()[0]
            assert result == 0, "Продукт найден в базе данных после запроса API"

        cursor.close()


class TestUpdateProduct:
    @allure.story("Update product with valid data")
    def test_update_product_and_verify_in_db(self, db_connection, product_setup):
        product_id=product_setup
        with allure.step("Обновление данных"):
            product_new_data = {
                "name": "Pineapple Phone",
                "price": "330.00"
            }
            response = requests.put(f"{API_URL}/product/{product_id}", json=product_new_data)
            assert response.status_code == 200
        cursor = db_connection.cursor()
        with allure.step("Проверка"):
            cursor.execute("SELECT name, price, is_active FROM products WHERE id = %s;", (product_id,))
            result = cursor.fetchone()
            assert result is not None, "Продукт не найден в базе данных"
            name, price, active = result
            assert name == product_new_data["name"]
            assert price == Decimal(product_new_data["price"])
            assert active is True
            cursor.close()

