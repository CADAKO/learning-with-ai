from decimal import Decimal, InvalidOperation
import os
import requests

DISCOUNT_SERVICE_URL = os.environ.get("DISCOUNT_SERVICE_URL",
                                      "http://localhost:5001")


def get_discount(price: Decimal, coupon_code: str) -> Decimal:
    try:
        response = requests.get(
            f"{DISCOUNT_SERVICE_URL}/product_discount?price={price}&coupon_code={coupon_code}")
        if response.status_code == 200 or response.status_code == 201:
            discount_data = response.json()
            # Возвращаем новую цену из ответа
            new_price = discount_data['price']
            return Decimal(str(new_price))
        else:
            # Обработка ошибки, если сервис скидок недоступен или вернул ошибку
            print(f"Discount service error: {response.status_code}")
            return Decimal(
                str(price))  # Возвращаем оригинальную цену по умолчанию
    except requests.exceptions.RequestException as e:
        print(f"Connection error to discount service: {e}")
        return Decimal(
            str(price))  # Возвращаем оригинальную цену в случае сетевой ошибки
