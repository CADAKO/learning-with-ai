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
            cursor.execute("SELECT is_active FROM products WHERE name = %s;",
                           ("Laptop",))
            result = cursor.fetchone()[0]
            assert result is True, "Precondition failed: Товар 'Laptop' уже не активен перед тестом"
            allure.attach(str(result), 'Исходный статус is_active',
                          attachment_type=allure.attachment_type.TEXT)

        with allure.step("Действие: Имитация вызова API (UPDATE в БД)"):
            # Имитация действия API:
            cursor.execute(
                "UPDATE products SET is_active = FALSE WHERE name = %s;",
                ('Laptop',))
            db_connection.commit()  # Применяем изменения

        with allure.step("Валидация: Проверка нового статуса"):
            cursor.execute("SELECT is_active FROM products WHERE name = %s;",
                           ("Laptop",))
            result = cursor.fetchone()[0]
            assert result is False, "Validation failed: Товар 'Laptop' остался активным после обновления"
            allure.attach(str(result), 'Новый статус is_active',
                          attachment_type=allure.attachment_type.TEXT)

    finally:
        # --- CLEANUP (Восстановление исходного состояния) ---
        with allure.step(
                "Очистка: Возвращаем товар 'Laptop' в активное состояние"):
            cursor.execute(
                "UPDATE products SET is_active = TRUE WHERE name = %s;",
                ('Laptop',))
            db_connection.commit()
            cursor.close()

        # Можете добавить финальную проверку, что cleanup прошел успешно, если хотите
        print("Cleanup завершен: Laptop снова активен.")


@allure.feature("Product Management GET Via API")
class TestGetProduct:
    @allure.story("Get valid product")
    def test_get_valid_product(self, db_connection, product_setup):
        with allure.step("Получение данных через API"):
            product_id = product_setup
            response = requests.get(f"{API_URL}/product/{product_id}")
            assert response.status_code == 200
            response_data = response.json()
            product_data_from_api = response_data  # Получаем словарь продукта
            name = product_data_from_api['name']
            price = product_data_from_api['price']
            active = product_data_from_api['is_active']
        with allure.step("Сравнение с данными из базы"):
            cursor = db_connection.cursor()
            cursor.execute(
                "SELECT name, price, is_active FROM products WHERE id = %s",
                (product_id,))
            product_data = cursor.fetchone()
            name_from_bd, price_from_bd, active_from_bd = product_data
            assert name == name_from_bd
            assert Decimal(price) == price_from_bd
            assert active == active_from_bd
            cursor.close()

    @allure.story("Get product from invalid ID")
    def test_get_invalid_id_product(self):
        with allure.step("Получение данных из ID=9999999"):
            invalid_id = 9999999
            response = requests.get(f"{API_URL}/product/{invalid_id}")
            assert response.status_code == 404


@allure.feature("Product Management ADD Via API")
class TestAddProduct:
    @allure.story("Add new product")
    def test_add_new_product_via_api_and_verify_in_db(self, db_connection, custom_product_cleanup):
        """
        Отправляем POST-запрос через API и проверяем результат SQL-запросом.
        """
        with allure.step("Подготовка данных и отправка запроса API"):
            new_product_data = {
                "name": "Monitor",
                "price": "299.99",
                "original_price": "299.99"
            }

            # 1. Действие: Отправляем запрос к API
            response = requests.post(f"{API_URL}/product",
                                     json=new_product_data)
            assert response.status_code == 201
            response_data = response.json()
            new_product_id = response_data['id']
        custom_product_cleanup(new_product_id)

        # 2. Валидация в БД: Проверяем, что запись появилась и данные верны
        with allure.step("Валидация данных в базе данных"):
            cursor = db_connection.cursor()
            cursor.execute(
                "SELECT name, price, is_active, original_price FROM products WHERE id = %s;",
                (new_product_id,))
            result = cursor.fetchone()
            assert result is not None, "Продукт не найден в базе данных после запроса API"

            allure.attach(str(result), 'Данные из БД',
                          attachment_type=allure.attachment_type.TEXT)

            name, price_decimal, is_active, original_price = result

            assert name == "Monitor"
            # Используем Decimal для точного сравнения цены
            assert price_decimal == Decimal("299.99")
            assert is_active is True  # Проверяем, что по умолчанию он активен
            assert original_price == Decimal("299.99")
            cursor.close()

    @allure.story("Add new product")
    def test_add_new_product_with_discount_via_api_and_verify_in_db(self,
                                                                    db_connection, custom_product_cleanup):
        """
        Отправляем POST-запрос через API и проверяем результат SQL-запросом.
        """
        with allure.step("Подготовка данных и отправка запроса API"):
            new_product_data = {
                "name": "Phone",
                "price": "300.00",
                "original_price": "300.00"
            }

            # 1. Действие: Отправляем запрос к API
            response = requests.post(f"{API_URL}/product",
                                     json=new_product_data)
            assert response.status_code == 201
            response_data = response.json()
            new_product_id = response_data['id']
        custom_product_cleanup(new_product_id)

        # 2. Валидация в БД: Проверяем, что запись появилась и данные верны
        with db_connection.cursor() as cursor:
            with allure.step("Валидация данных в базе данных"):
                cursor.execute(
                    "SELECT name, price, is_active, original_price FROM products WHERE id = %s;",
                    (new_product_id,))
                result = cursor.fetchone()
                assert result is not None, "Продукт не найден в базе данных после запроса API"

                allure.attach(str(result), 'Данные из БД',
                              attachment_type=allure.attachment_type.TEXT)

                name, price_discount, is_active, original_price = result

                assert name == "Phone"
                # Используем Decimal для точного сравнения цены
                assert price_discount == Decimal("300.0000")
                assert original_price == Decimal("300.0000")
                assert is_active is True  # Проверяем, что по умолчанию он активен

    @allure.story("Add new product with zero price")
    def test_add_zero_price_product(self, db_connection,
                                    custom_product_cleanup):
        with allure.step("Подготовка данных и отправка запроса API"):
            new_product_data = {"name": "Free Item", "price": "0.00",
                                "original_price": "0.00"}
            response = requests.post(f"{API_URL}/product",
                                     json=new_product_data)
            assert response.status_code == 201
            product_id = response.json()['id']
        custom_product_cleanup(product_id)
        # 2. Валидация в БД: Проверяем, что запись появилась
        with allure.step("Валидация данных в базе данных"):
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM products WHERE name = %s;",
                               ("Free Item",))
                result = cursor.fetchone()[0]
                assert result == 1, "Продукт не найден в базе данных после запроса API"



    @allure.story("Add new product with long name")
    def test_add_with_long_name_product(self, db_connection, custom_product_cleanup):
        with allure.step("Подготовка данных и отправка запроса API"):
            long_name = str("q" * 100)
            new_product_data = {"name": f"{long_name}", "price": "1.00",
                                "original_price": "1.00"}
            response = requests.post(f"{API_URL}/product",
                                     json=new_product_data)
            assert response.status_code == 201
            response_data = response.json()
            new_product_id = response_data['id']
            custom_product_cleanup(new_product_id)

            # 2. Валидация в БД: Проверяем, что запись появилась и данные верны
        with db_connection.cursor() as cursor:
            with allure.step("Валидация данных в базе данных"):
                cursor.execute(
                    "SELECT name, price, is_active, original_price FROM products WHERE id = %s;",
                    (new_product_id,))
                result = cursor.fetchone()
                assert result is not None, "Продукт не найден в базе данных после запроса API"

                allure.attach(str(result), 'Данные из БД',
                              attachment_type=allure.attachment_type.TEXT)

                name, price, is_active, original_price = result

                assert name == long_name
                assert price == Decimal("1.00")
                assert original_price == Decimal("1.00")


@allure.feature("Product API Negative Scenarios")
class TestProductNegative:

    # >>>>> Используем PARAMETRIZE для разных входных данных <<<<<
    @pytest.mark.parametrize(
        "name, price, expected_status, test_name",
        [
            # Неверное имя (слишком длинное)
            ("q" * 101, "100.00", 400, "long_name"),
            # Неверное имя (пустое)
            ("", "100.00", 400, "empty_name"),
            # Неверная цена (отрицательная)
            ("Valid name", "-10.00", 400, "negative_price"),
            # Неверная цена (не число)
            ("Valid name", "abc", 400, "invalid_price"),
        ]
    )
    def test_add_product_invalid_data(self, name, price, expected_status,
                                      test_name, db_connection):
        allure.dynamic.story(f"Test invalid product data: {test_name}")

        with allure.step(
                f"Отправка POST запроса с невалидными данными: Name='{name}',"
                f" Price='{price}'"):
            payload = {"name": name, "price": price}
            response = requests.post(f"{API_URL}/product", json=payload)
            try:
                test_id = response.json()['id']
            except KeyError:
                test_id = None
            assert response.status_code == expected_status

        with allure.step("Проверка отсутствия товара в БД"):
            cursor = db_connection.cursor()
            cursor.execute(
                "SELECT * FROM products WHERE id = %s;",
                (test_id,))
            result = cursor.fetchone()
            assert result is None, "Продукт найден в базе данных после запроса"

    @allure.story("Test GET, PUT, DELETE with non-existent ID")
    def test_crud_non_existent_id(self):
        non_existent_id = 999999

        # Тест GET
        response_get = requests.get(f"{API_URL}/product/{non_existent_id}")
        assert response_get.status_code == 404

        # Тест PUT
        response_put = requests.put(f"{API_URL}/product/{non_existent_id}",
                                    json={"name": "test", "price": "100"})
        assert response_put.status_code == 404

        # Тест DELETE
        response_delete = requests.delete(
            f"{API_URL}/product/{non_existent_id}")
        # NOTE: В вашем API delete всегда возвращает 204, но в реальном мире часто 404
        assert response_delete.status_code == 204


@allure.feature("Product Management UPDATE Via API")
class TestUpdateProduct:
    @allure.story("Update product with valid data")
    def test_update_product_and_verify_in_db(self, db_connection,
                                             product_setup):
        product_id = product_setup
        with allure.step("Обновление данных"):
            product_new_data = {
                "name": "Pineapple Phone",
                "price": "330.00",
            }
            response = requests.put(f"{API_URL}/product/{product_id}",
                                    json=product_new_data)
            assert response.status_code == 200
        with db_connection.cursor() as cursor:
            with allure.step("Проверка"):
                cursor.execute(
                    "SELECT name, price, is_active FROM products WHERE id = %s;",
                    (product_id,))
                result = cursor.fetchone()
                assert result is not None, "Продукт не найден в базе данных"
                name, price, active = result
                assert name == product_new_data["name"]
                assert str(price) == product_new_data["price"]
                assert active is True

    @allure.story("Update product with no name")
    def test_update_product_without_name(self, db_connection, product_setup):
        product_id = product_setup
        with db_connection.cursor() as cursor:
            with allure.step("Копируем исходные данные"):
                cursor.execute(
                    "SELECT name, price FROM products WHERE id = %s;",
                    (product_id,))
                old_data = cursor.fetchone()
            allure.attach(f'product_id = {product_id}')
            with allure.step("Обновление данных"):
                product_new_data = {
                    "name": "",
                    "price": "1.00"
                }
                response = requests.put(f"{API_URL}/product/{product_id}",
                                        json=product_new_data)
                assert response.status_code == 400
                allure.attach(f'response= {response.json()}')

            with allure.step("Проверка"):
                cursor.execute(
                    "SELECT name, price FROM products WHERE id = %s;",
                    (product_id,))
                result = cursor.fetchone()
                assert old_data == result

    @allure.story("Update product with no price")
    def test_update_product_without_price(self, db_connection, product_setup):
        product_id = product_setup
        with db_connection.cursor() as cursor:
            with allure.step("Копируем исходные данные"):
                cursor.execute(
                    "SELECT name, price FROM products WHERE id = %s;",
                    (product_id,))
                old_data = cursor.fetchone()
            with allure.step("Обновление данных"):
                product_new_data = {
                    "name": "Test",
                    "price": ""
                }
                response = requests.put(f"{API_URL}/product/{product_id}",
                                        json=product_new_data)
                assert response.status_code == 400

            with allure.step("Проверка"):
                cursor.execute(
                    "SELECT name, price FROM products WHERE id = %s;",
                    (product_id,))
                result = cursor.fetchone()
                assert old_data == result

    @allure.story("Update product with discount")
    def test_update_product_with_discount(self, db_connection, product_setup):
        product_id = product_setup
        with db_connection.cursor() as cursor:
            with allure.step("Копируем исходные данные"):
                cursor.execute(
                    "SELECT name, price FROM products WHERE id = %s;",
                    (product_id,))
                old_data = cursor.fetchone()
                old_name, old_price = old_data
                allure.attach(f"old price = {old_price}")
            with allure.step("Обновление данных"):
                product_new_data = {
                    "name": old_name,
                    "price": str(old_price),
                    "coupon_code": "SALE10",
                    "is_active": True
                }
                response = requests.put(f"{API_URL}/product/{product_id}",
                                        json=product_new_data)
                assert response.status_code == 200

            with allure.step("Проверка"):
                cursor.execute(
                    "SELECT name, price, original_price FROM products WHERE id = %s;",
                    (product_id,))
                result = cursor.fetchone()
                new_name, new_price, original_price = result
                allure.attach(f"original price = {original_price}")
                cursor.execute(
                    "SELECT discount_percent FROM coupons WHERE code = %s",
                    ("SALE10",))
                discount_percent = cursor.fetchone()[0]
                allure.attach(f"discount percent = {discount_percent}")
                assert old_name == new_name
                discount_price = original_price * (
                            Decimal("1.00") - discount_percent / Decimal(
                        "100.00"))
                allure.attach(
                    f"new price ({new_price} == discount price ({discount_price})")
                assert new_price == discount_price

    @allure.story("Update product with fake discount")
    def test_update_product_with_fake_discount(self, db_connection,
                                               product_setup):
        product_id = product_setup
        with db_connection.cursor() as cursor:
            with allure.step("Копируем исходные данные"):
                cursor.execute(
                    "SELECT name, price FROM products WHERE id = %s;",
                    (product_id,))
                old_data = cursor.fetchone()
                old_name, old_price = old_data
            with allure.step("Обновление данных"):
                product_new_data = {
                    "name": old_name,
                    "price": str(old_price),
                    "coupon_code": "FAKESALE",
                    "is_active": True
                }
                response = requests.put(f"{API_URL}/product/{product_id}",
                                        json=product_new_data)
                assert response.status_code == 200

            with allure.step("Проверка"):
                cursor.execute("SELECT price FROM products WHERE id = %s;",
                               (product_id,))
                result = cursor.fetchone()
                new_price = result[0]
                assert new_price == old_price

    @allure.story("Update invalid ID product")
    def test_update_invalid_id_product(self):
        invalid_id = 99999999
        with allure.step("Обновление данных"):
            product_new_data = {
                "name": "test",
                "price": "1.00"
            }
            response = requests.put(f"{API_URL}/product/{invalid_id}",
                                    json=product_new_data)
            assert response.status_code == 404


@allure.feature("Product Management DELETE Via API")
class TestDeleteProduct:
    @allure.story("Delete valid product")
    def test_delete_valid_product(self, product_setup, db_connection):
        with allure.step("Удаление подготовленных данных"):
            product_id = product_setup
            response = requests.delete(f"{API_URL}/product/{product_id}")
            assert response.status_code == 204
        with allure.step("Проверка в базе данных"):
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM products WHERE ID=%s",
                               (product_id,))
                result = cursor.fetchone()[0]
                assert result == 0, "Продукт был найден в базе данных"

    @allure.story("Delete not exist product")
    def test_delete_invalid_id_product(self, db_connection):
        with allure.step("удаление заведомо несуществующего ID"):
            product_id = 9999999
            response = requests.delete(f"{API_URL}/product/{product_id}")
            assert response.status_code == 204
