import pytest
import psycopg2
import requests
import os
import time
from typing import List


from locators import BaseLocators


# Получаем данные подключения из переменных окружения, переданных через docker-compose.yml

@pytest.fixture(
    scope="function")
def db_connection():
    """Фикстура Pytest для установки и закрытия соединения с БД."""
    conn = None

    # --- SETUP (Логика подключения с повторами) ---
    for attempt in range(5):
        try:
            conn = psycopg2.connect(
                host=BaseLocators.DB_HOST,
                dbname=BaseLocators.DB_NAME,
                user=BaseLocators.DB_USER,
                password=BaseLocators.DB_PASS
            )
            print("Успешное подключение к БД!")
            # Если подключились, выходим из цикла
            break
        except psycopg2.OperationalError as e:
            print(f"Попытка {attempt + 1}/5: Ошибка подключения к БД: {e}")
            time.sleep(2)
    else:
        # Если 5 попыток не удались, выбрасываем исключение
        raise Exception(
            "Не удалось установить соединение с базой данных после 5 попыток.")

    # --- ЕДИНСТВЕННЫЙ YIELD (Передача управления тестам) ---
    try:
        yield conn

    # --- TEARDOWN (Логика очистки после выполнения всех тестов в сессии) ---
    finally:
        if conn:
            # Важно: делаем ROLLBACK перед закрытием, чтобы отменить все незавершенные транзакции
            conn.rollback()
            conn.close()
            print("Соединение с БД закрыто.")

API_URL = os.environ.get("API_URL", "http://localhost:5000")


@pytest.fixture(scope="function")
def product_setup(db_connection):
    new_product = {"name": "Test Product",
                   "price": "100.00",
                   "is_active": True,
                   "original_price": "100.00"
                   }
    response = requests.post(f"{API_URL}/product", json=new_product)
    assert response.status_code == 201
    new_product_id = response.json()["id"]

    yield new_product_id

    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s;", (new_product_id,))
    db_connection.commit()
    cursor.close()


@pytest.fixture(scope="function")
def custom_product_cleanup(db_connection):
    # Список ID, которые нужно будет удалить в конце
    product_ids_to_delete: List[int] = []

    def register_for_cleanup(product_id: int):
        product_ids_to_delete.append(product_id)

    # 'yield' возвращает функцию регистрации в тест
    yield register_for_cleanup

    # --- Teardown (Очистка данных) ---
    if product_ids_to_delete:
        print(f"\nCleaning up custom product IDs: {product_ids_to_delete}")
        cursor = db_connection.cursor()
        # Используем оператор IN для удаления всех ID за один запрос
        cursor.execute("DELETE FROM products WHERE id = ANY(%s);", (product_ids_to_delete,))
        db_connection.commit()
        cursor.close()
