"""
Unit-тесты для модуля models.py
"""

import unittest
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    Product,
    Client,
    Order,
    OrderItem,
    BaseEntity,
    custom_sort_orders,
    recursive_sum_amounts,
)


class TestProduct(unittest.TestCase):
    """Тесты класса Product."""

    def test_create_product(self):
        p = Product("Тест", 100.0, "Категория", 5)
        self.assertEqual(p.name, "Тест")
        self.assertEqual(p.price, 100.0)
        self.assertEqual(p.category, "Категория")
        self.assertEqual(p.stock, 5)

    def test_price_negative(self):
        p = Product("Тест", 100.0)
        with self.assertRaises(ValueError):
            p.price = -10

    def test_empty_name(self):
        with self.assertRaises(ValueError):
            Product("", 50.0)

    def test_to_dict_from_dict(self):
        p = Product("Товар", 99.9, "Электроника", 10, product_id=1)
        d = p.to_dict()
        p2 = Product.from_dict(d)
        self.assertEqual(p2.name, p.name)
        self.assertEqual(p2.price, p.price)
        self.assertEqual(p2.id, 1)

    def test_str(self):
        p = Product("Мышь", 500.0, product_id=7)
        s = str(p)
        self.assertIn("Мышь", s)
        self.assertIn("7", s)


class TestClient(unittest.TestCase):
    """Тесты класса Client и валидации regex."""

    def test_create_client(self):
        c = Client("Иванов", "ivan@mail.ru", "+7 (999) 111-22-33", "Москва")
        self.assertEqual(c.name, "Иванов")
        self.assertEqual(c.email, "ivan@mail.ru")
        self.assertEqual(c.city, "Москва")

    def test_valid_emails(self):
        self.assertTrue(Client.validate_email("test@example.com"))
        self.assertTrue(Client.validate_email("user.name+tag@domain.co.uk"))
        self.assertFalse(Client.validate_email("bad-email"))
        self.assertFalse(Client.validate_email("@nodomain.com"))
        self.assertFalse(Client.validate_email(""))

    def test_valid_phones(self):
        self.assertTrue(Client.validate_phone("+7 (999) 123-45-67"))
        self.assertTrue(Client.validate_phone("89991234567"))
        self.assertTrue(Client.validate_phone("8 999 123 45 67"))
        self.assertFalse(Client.validate_phone("123"))
        self.assertFalse(Client.validate_phone(""))

    def test_invalid_email_raises(self):
        with self.assertRaises(ValueError):
            Client("Test", "not-an-email", "+79991234567")

    def test_invalid_phone_raises(self):
        with self.assertRaises(ValueError):
            Client("Test", "test@mail.ru", "abc")

    def test_to_dict(self):
        c = Client("Петров", "petrov@gmail.com", "89161234567", "Казань", client_id=2)
        d = c.to_dict()
        self.assertEqual(d["name"], "Петров")
        self.assertEqual(d["email"], "petrov@gmail.com")
        self.assertEqual(d["id"], 2)


class TestOrder(unittest.TestCase):
    """Тесты класса Order."""

    def setUp(self):
        self.client = Client("Клиент", "c@mail.ru", "+79990001122", "Москва", client_id=1)
        self.product1 = Product("Товар1", 100.0, product_id=1)
        self.product2 = Product("Товар2", 250.0, product_id=2)

    def test_create_order(self):
        order = Order(self.client)
        self.assertEqual(order.client.name, "Клиент")
        self.assertEqual(order.status, "новый")
        self.assertEqual(order.total_amount, 0.0)

    def test_add_item(self):
        order = Order(self.client)
        order.add_item(self.product1, 2)
        order.add_item(self.product2, 1)
        self.assertEqual(order.items_count, 2)
        self.assertEqual(order.total_amount, 100 * 2 + 250)

    def test_add_same_item_increases_qty(self):
        order = Order(self.client)
        order.add_item(self.product1, 1)
        order.add_item(self.product1, 3)
        self.assertEqual(order.items_count, 1)
        self.assertEqual(order.items[0].quantity, 4)

    def test_invalid_status(self):
        order = Order(self.client)
        with self.assertRaises(ValueError):
            order.status = "неизвестный"

    def test_to_dict(self):
        order = Order(self.client, order_id=10)
        order.add_item(self.product1, 1)
        d = order.to_dict()
        self.assertEqual(d["id"], 10)
        self.assertEqual(d["client_name"], "Клиент")
        self.assertEqual(len(d["items"]), 1)


class TestSortingAndRecursion(unittest.TestCase):
    """Тесты собственной сортировки и рекурсии."""

    def setUp(self):
        client = Client("A", "a@mail.ru", "+79991112233", client_id=1)
        p = Product("P", 100.0, product_id=1)

        self.orders = []
        for i, days in enumerate([5, 1, 10, 3]):
            o = Order(client, order_id=i + 1)
            o.order_date = datetime.now() - timedelta(days=days)
            o.add_item(p, i + 1)  # суммы: 100, 200, 300, 400
            self.orders.append(o)

    def test_sort_by_date_asc(self):
        sorted_o = custom_sort_orders(self.orders, key="date", reverse=False)
        dates = [o.order_date for o in sorted_o]
        self.assertEqual(dates, sorted(dates))

    def test_sort_by_date_desc(self):
        sorted_o = custom_sort_orders(self.orders, key="date", reverse=True)
        dates = [o.order_date for o in sorted_o]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_sort_by_amount(self):
        sorted_o = custom_sort_orders(self.orders, key="amount", reverse=False)
        amounts = [o.total_amount for o in sorted_o]
        self.assertEqual(amounts, sorted(amounts))

    def test_recursive_sum(self):
        total = recursive_sum_amounts(self.orders)
        expected = sum(o.total_amount for o in self.orders)
        self.assertAlmostEqual(total, expected)

    def test_recursive_sum_empty(self):
        self.assertEqual(recursive_sum_amounts([]), 0.0)


class TestInheritance(unittest.TestCase):
    """Проверка наследования."""

    def test_product_is_base(self):
        p = Product("X", 1.0)
        self.assertIsInstance(p, BaseEntity)

    def test_client_is_base(self):
        c = Client("Y", "y@y.ru", "+79990000000")
        self.assertIsInstance(c, BaseEntity)

    def test_order_is_base(self):
        c = Client("Y", "y@y.ru", "+79990000000")
        o = Order(c)
        self.assertIsInstance(o, BaseEntity)


if __name__ == "__main__":
    unittest.main()
