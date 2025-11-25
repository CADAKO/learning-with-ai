import pytest
import time
import psycopg2
import requests
import os

from locators import BaseLocators


# Получаем данные подключения из переменных окружения, переданных через docker-compose.yml

@pytest.fixture(scope="module")
def db_connection():
    """Фикстура Pytest для установки и закрытия соединения с БД."""
    conn = None
    # Иногда БД может быть еще не полностью готова, добавим небольшую задержку/повтор
    for _ in range(5):
        try:
            conn = psycopg2.connect(
                host=BaseLocators.DB_HOST,
                dbname=BaseLocators.DB_NAME,
                user=BaseLocators.DB_USER,
                password=BaseLocators.DB_PASS
            )
            print("Успешное подключение к БД!")
            yield conn
            break
        except psycopg2.OperationalError:
            print("Ожидание готовности БД...")
            time.sleep(2)
    else:
        raise Exception("Не удалось подключиться к базе данных.")

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
