import pytest
import time
import psycopg2
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



