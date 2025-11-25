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


def get_discount(price, coupon_code):
    try:
        response = requests.get(f"{DISCOUNT_SERVICE_URL}/product_discount?price={price}&coupon_code={coupon_code}")
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
    is_active = data.get('is_active', True)
    original_price = price

    if not name or not price:
        return jsonify({"error": "Missing name or price"}), 400
    if price[0] == "-" or len(name) > 100 or len(name) < 1:
        return jsonify({"error": "Invalid name or price"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            Decimal(str(price))  # Попытка преобразования
        except InvalidOperation:
            return jsonify({"error": "Price must be a valid number"}), 400
        # price = get_discount(price)
        cursor.execute(
            "INSERT INTO products (name, price, is_active, original_price) VALUES (%s, %s, %s, %s) RETURNING id;",
            (name, price, is_active, original_price)
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


@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT name, price, is_active, original_price FROM products WHERE id = %s;", (product_id,))
        product_data = cursor.fetchone()
        if product_data is None:
            return jsonify({"error": "Product not found"}), 404
        # Преобразуем результат в словарь для красивого JSON-ответа
        name, price, is_active, original_price = product_data
        response_data = {
            "name": name,
            "price": str(price),
            "is_active": is_active,
            "original_price": original_price
        }
        return jsonify({"status": "success", "product": response_data}), 200
    finally:
        cursor.close()
        conn.close()


@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    # Устанавливаем соединение с базой
    conn = get_db_connection()
    # Достаем курсор
    cursor = conn.cursor()

    try:
        # Посмотрим сначала, есть ли такой продукт
        cursor.execute(
            "SELECT original_price FROM products WHERE id = %s;",
            (product_id,))
        result = cursor.fetchone()
        if result is None:
            return jsonify({"error": "Product not found"}), 404
        data = request.get_json()
        name = data.get('name')
        price = data.get('price')
        active = data.get('is_active', True)
        original_price = Decimal(str(result[0]))
        coupon_code = data.get('coupon_code')
        if not name or not price:
            return jsonify({"error": "Missing name or price"}), 400
        if len(name) > 100 or len(name) < 1:
            return jsonify({"error": "Invalid name length (1-100)"}), 400
        try:
            Decimal(str(price))  # Попытка преобразования
        except InvalidOperation:
            return jsonify({"error": "Price must be a valid number"}), 400
        final_price = Decimal(str(price))
        if coupon_code:
            final_price = get_discount(original_price, coupon_code)
        cursor.execute(
            "UPDATE products SET name = %s, price = %s, is_active = %s WHERE id = %s;",
            (name, final_price, active, product_id,)
        )
        conn.commit()
        return jsonify({"status": "success", "id": product_id}), 200
    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    # Устанавливаем соединение с базой
    conn = get_db_connection()
    # Достаем курсор
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM products WHERE id = %s;", (product_id,))
        conn.commit()
        return "", 204
    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/products', methods=['GET'])
def get_all_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, name, price, is_active, original_price FROM products ORDER BY id DESC;')
        products = cursor.fetchall()
        product_list = []
        for id, name, price, is_active, original_price in products:
            product_list.append({
                "id": id,
                "name": name,
                "price": price,
                "is_active": is_active,
                "original_price": original_price
            })
        return jsonify(product_list), 200
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
