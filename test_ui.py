# test_ui.py (новый файл в корне проекта)
'''
from playwright.sync_api import Page, expect
import os

# Получаем URL фронтенда из переменной окружения (добавим в docker-compose.yml)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost")


@pytest.mark.ui  # Специальная метка для UI-тестов
def test_products_list_displays_laptop(page: Page):
    page.goto(FRONTEND_URL)

    # Используем методы Playwright для поиска элемента
    # Ищем строку таблицы, содержащую текст "Laptop"
    laptop_row = page.locator("tbody#product-list >> text=Laptop")

    # Проверяем, что элемент видим
    expect(laptop_row).to_be_visible()

    # Проверяем, что в той же строке цена 1200.50
    # Используем CSS-селектор для поиска второй ячейки (цены) в найденной строке
    price_cell = laptop_row.locator("xpath=./following-sibling::td[1]")
    expect(price_cell).to_have_text("9999.50")
'''
