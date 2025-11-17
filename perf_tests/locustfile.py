# perf_tests/locustfile.py
from locust import HttpUser, task, between
import random


class ApiUser(HttpUser):
    # Время ожидания между задачами (от 1 до 3 секунд)
    wait_time = between(1, 3)

    @task
    def add_product(self):
        # Генерируем уникальное имя для каждого запроса, чтобы не было конфликтов
        item_id = random.randint(1, 100000)
        payload = {
            "name": f"TestLoadItem_{item_id}",
            "price": "50.00"
        }

        # 'self.client' - это встроенный клиент Locust, похожий на 'requests'
        # Он автоматически собирает метрики
        self.client.post("/product", json=payload, name="Add Product API")

# Примечание: Locust сам поднимет веб-интерфейс для запуска нагрузки.
