# api/app.py
import requests
from flask import Flask, request, jsonify
import psycopg2
import os
from decimal import Decimal, InvalidOperation


app = Flask(__name__)
DISCOUNT_SERVICE_URL = os.environ.get("DISCOUNT_SERVICE_URL", "http://localhost:5001")

# Параметры БД
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "te"
                                    "stdb")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASS = os.environ.get("DB_PASS", "password")


def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn


def get_discount(price):
    try:
        response = requests.get(f"{DISCOUNT_SERVICE_URL}/product_discount?price={price}")
        if response.status_code == 200 or response.status_code == 201:
            discount_data = response.json()
            # Возвращаем новую цену из ответа
            new_price = discount_data['price']
            return Decimal(str(new_price))
        else:
            # Обработка ошибки, если сервис скидок недоступен или вернул ошибку
            print(f"Discount service error: {response.status_code}")
            return Decimal(str(price))  # Возвращаем оригинальную цену по умолчанию
    except requests.exceptions.RequestException as e:
        print(f"Connection error to discount service: {e}")
        return Decimal(str(price))  # Возвращаем оригинальную цену в случае сетевой ошибки


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


@app.route('/product', methods=['POST'])
def add_product():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')

    if not name or not price:
        return jsonify({"error": "Missing name or price"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            Decimal(str(price))  # Попытка преобразования
        except InvalidOperation:
            return jsonify({"error": "Price must be a valid number"}), 400
        price = get_discount(price)
        cursor.execute(
            "INSERT INTO products (name, price) VALUES (%s, %s) RETURNING id;",
            (name, price)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return jsonify({"status": "success", "id": new_id}), 201
    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
