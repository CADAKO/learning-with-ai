# api/app.py
from flask import Flask, request, jsonify, Response
from models import Product
from manager import ProductManager
from typing import Tuple, Dict, Any

from decimal import Decimal, InvalidOperation

app = Flask(__name__)
manager = ProductManager()


@app.route('/health', methods=['GET'])
def health_check() -> Tuple[Response, int]:
    return jsonify({"status": "healthy"}), 200


@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id) -> Tuple[Response, int]:
    product = manager.get_product_by_id(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
        # Преобразуем объект Product DTO в словарь для JSON
    return jsonify(product.__dict__), 200


@app.route('/product', methods=['POST'])
def add_product() -> Tuple[Response, int]:
    data: Dict[str, Any] = request.get_json()
    name = data.get('name')
    price_str = data.get('price')
    if not name or not price_str:
        return jsonify({"error": "Missing name or price"}), 400
    if len(name) > 100 or len(
            name) < 1:
        return jsonify({"error": "Invalid name"}), 400
    try:
        price_decimal = Decimal(str(price_str))
        if price_decimal < 0:
            return jsonify({"error": "Price must be positive"}), 400
    except InvalidOperation:
        return jsonify({"error": "Price must be a valid number"}), 400

    product = Product(name=name, price=price_decimal,
                      is_active=data.get('is_active', True),
                      original_price=price_decimal)
    product_id = manager.add_product(product)
    return jsonify({"status": "success", "id": product_id}), 201


@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id: int) -> Tuple[Response, int]:
    data: Dict[str, Any] = request.get_json()
    name = data.get('name')
    price_str = data.get('price')

    if not name or not price_str:
        return jsonify({"error": "Missing name or price"}), 400
    if len(name) > 100 or len(name) < 1:
        return jsonify({"error": "Invalid name length (1-100)"}), 400

    try:
        Decimal(str(price_str))
    except InvalidOperation:
        return jsonify({"error": "Price must be a valid number"}), 400

    update_data: Dict[str, Any] = {
        'name': name,
        'price': price_str,  # Отправляем как строку
        'is_active': data.get('is_active', True),
        'coupon_code': data.get('coupon_code', None)
    }
    status_success = manager.update_product(product_id, update_data)

    if not status_success:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({"status": "success", "id": product_id}), 200


@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id) -> Tuple[Response, int]:
    manager.delete_product(product_id)
    return Response("", status=204), 204


@app.route('/products', methods=['GET'])
def get_all_products() -> Tuple[Response, int]:
    products_list = manager.get_all_products()
    products_dict_list = [p.__dict__ for p in products_list]
    return jsonify(products_dict_list), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
