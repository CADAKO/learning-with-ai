# discount_service/app.py
from flask import Flask, request, jsonify
import psycopg2
import os
from decimal import Decimal, InvalidOperation
import requests

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "te"
                                    "stdb")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASS = os.environ.get("DB_PASS", "password")


def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


@app.route('/product_discount', methods=['GET'])
def make_discount():
    price = request.args.get('price')
    coupon_code = request.args.get('coupon_code')
    if not price:
        return jsonify({"error": "Missing price"}), 400
    try:
        price_decimal = Decimal(str(price))
    except InvalidOperation:
        return jsonify({"error": "Price must be a valid number"}), 400

    discount_percent = Decimal('0.00')  # По умолчанию скидки нет (0%)

    # >>>>> Используем правильный контекстный менеджер БД и параметризованный запрос
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT discount_percent FROM coupons WHERE code = %s;", (coupon_code,))
            result = cursor.fetchone()

            if result is not None:
                discount_percent = result[0]  # Получаем процент из БД (например, 10.00)

    # >>>>> Корректный расчет новой цены
    # Новая цена = Старая цена * (100 - процент скидки) / 100
    if discount_percent > 0:
        discount_multiplier = Decimal('1') - (discount_percent / Decimal('100'))
        new_price_decimal = price_decimal * discount_multiplier
    else:
        new_price_decimal = price_decimal
    return jsonify({"status": "success", "price": new_price_decimal}), 200  # <-- 200 OK


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
