# api/manager.py
from database import get_db_connection
from models import Product
from services import get_discount
from dataclasses import replace
from typing import Optional, List, Dict, Any


class ProductManager:
    """
    Класс для управления бизнес-логикой продуктов.
    Использует ООП подход вместо набора функций.
    """

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получает продукт по ID."""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, price, is_active, original_price FROM products WHERE id = %s;",
                    (product_id,))
                result = cursor.fetchone()
                if result is None:
                    return None
                # Используем Product DTO вместо сырого кортежа
                return Product(id=result[0], name=result[1], price=result[2],
                               is_active=result[3], original_price=result[4])

    def add_product(self, product: Product) -> int:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO products (name, price, is_active, original_price) VALUES (%s, %s, %s, %s) RETURNING id;",
                    (product.name, product.price, product.is_active,
                     product.original_price)
                )
                result = cursor.fetchone()
                if result is None:
                    raise Exception("Failed to retrieve new product ID.")
                new_id=result[0]
                conn.commit()
                return new_id

    def _apply_discount_logic(self, product: Product,
                              coupon_code: str) -> Product:
        final_price = product.price
        if coupon_code:
            final_price = get_discount(product.original_price, coupon_code)
        elif coupon_code == "":
            final_price = product.original_price
        return replace(product, price=final_price)

    def update_product(self, product_id: int,
                       update_data: Dict[str, Any]) -> bool:
        existing_product = self.get_product_by_id(product_id)
        if existing_product is None:
            return False  # Продукт не найден
        updated_product = existing_product
        coupon_code = update_data.pop('coupon_code',
                                      None)
        updated_product = replace(existing_product, **update_data)
        final_product = self._apply_discount_logic(updated_product, coupon_code)
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE products SET name = %s, price = %s, is_active = %s, original_price = %s WHERE id = %s;",
                    (final_product.name, final_product.price,
                     final_product.is_active, final_product.original_price,
                     product_id)
                )
                conn.commit()

        return True

    def delete_product(self, product_id: int) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM products WHERE id = %s;", (product_id,)
                )
                conn.commit()
                return True

    def get_all_products(self) -> List[Product]:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, price, is_active, original_price FROM products;")
                result = cursor.fetchall()
                products: List[Product] = []
                for items in result:
                    id_val, name_val, price_val, is_active_val, \
                    original_price_val = items
                    # Используем dataclass для создания объекта
                    products.append(Product(
                        id=id_val,
                        name=name_val,
                        price=price_val,
                        is_active=is_active_val,
                        original_price=original_price_val
                    ))
                return products
