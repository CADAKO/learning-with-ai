# discount_service/app.py
from flask import Flask, request, jsonify
# import psycopg2
# import os
from decimal import Decimal


app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


@app.route('/product_discount', methods=['GET'])
def make_discount():
    price = request.args.get('price')

    if not price:
        return jsonify({"error": "Missing price"}), 400
    try:
        price_decimal = Decimal(str(price))  # Приводим к Decimal сразу
        new_price_decimal = price_decimal * Decimal('0.90')  # Умножаем на Decimal
        return jsonify({"status": "success", "price": new_price_decimal}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
