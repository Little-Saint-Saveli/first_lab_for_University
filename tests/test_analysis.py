"""
Unit-тесты для модуля analysis.py
"""

import unittest
from datetime import datetime, timedelta
import os
import tempfile
import shutil

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Product, Client, Order
from analysis import DataAnalyzer


class TestDataAnalyzer(unittest.TestCase):
    """Тесты анализатора данных."""

    def setUp(self):
        self.client1 = Client("Иванов", "ivan@mail.ru", "+79991111111", "Москва", client_id=1)
        self.client2 = Client("Петров", "petr@mail.ru", "+79992222222", "СПб", client_id=2)
        self.client3 = Client("Сидоров", "sid@mail.ru", "+79993333333", "Москва", client_id=3)

        self.p1 = Product("Ноутбук", 50000.0, product_id=1)
        self.p2 = Product("Мышь", 1000.0, product_id=2)
        self.p3 = Product("Клавиатура", 2000.0, product_id=3)

        self.orders = []

        # Клиент 1 — 3 заказа
        for i in range(3):
            o = Order(self.client1, order_id=i + 1)
            o.order_date = datetime.now() - timedelta(days=i * 2)
            o.add_item(self.p1, 1)
            o.add_item(self.p2, 2)
            self.orders.append(o)

        # Клиент 2 — 2 заказа
        for i in range(2):
            o = Order(self.client2, order_id=10 + i)
            o.order_date = datetime.now() - timedelta(days=i + 5)
            o.add_item(self.p3, 1)
            self.orders.append(o)

        # Клиент 3 — 1 заказ
        o = Order(self.client3, order_id=20)
        o.order_date = datetime.now() - timedelta(days=1)
        o.add_item(self.p2, 5)
        self.orders.append(o)

        self.analyzer = DataAnalyzer(
            self.orders,
            clients=[self.client1, self.client2, self.client3],
            products=[self.p1, self.p2, self.p3],
        )
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_top_clients(self):
        df = self.analyzer.top_clients_by_orders(3)
        self.assertEqual(len(df), 3)
        # Иванов должен быть первым (3 заказа)
        self.assertEqual(df.iloc[0]["client_name"], "Иванов")
        self.assertEqual(df.iloc[0]["orders_count"], 3)

    def test_orders_dynamics(self):
        df = self.analyzer.orders_dynamics()
        self.assertFalse(df.empty)
        self.assertIn("orders_count", df.columns)

    def test_top_products(self):
        df = self.analyzer.top_products(5)
        self.assertFalse(df.empty)
        # Мышь должна быть в топе (2*3 + 5 = 11 шт)
        products = df["product"].tolist()
        self.assertIn("Мышь", products)

    def test_sales_by_city(self):
        df = self.analyzer.sales_by_city()
        self.assertFalse(df.empty)
        cities = df["city"].tolist()
        self.assertIn("Москва", cities)

    def test_total_revenue(self):
        total = self.analyzer.total_revenue()
        expected = sum(o.total_amount for o in self.orders)
        self.assertAlmostEqual(total, expected)

    def test_plot_top_clients(self):
        path = os.path.join(self.tmpdir, "top_clients.png")
        result = self.analyzer.plot_top_clients(path)
        self.assertTrue(os.path.exists(result))
        self.assertGreater(os.path.getsize(result), 0)

    def test_plot_dynamics(self):
        path = os.path.join(self.tmpdir, "dynamics.png")
        result = self.analyzer.plot_orders_dynamics(path)
        self.assertTrue(os.path.exists(result))

    def test_plot_top_products(self):
        path = os.path.join(self.tmpdir, "products.png")
        result = self.analyzer.plot_top_products(path)
        self.assertTrue(os.path.exists(result))

    def test_client_graph_city(self):
        path = os.path.join(self.tmpdir, "graph.png")
        result = self.analyzer.build_client_graph("city", path)
        self.assertTrue(os.path.exists(result))

    def test_empty_orders(self):
        empty_analyzer = DataAnalyzer([])
        self.assertTrue(empty_analyzer.top_clients_by_orders().empty)
        self.assertEqual(empty_analyzer.total_revenue(), 0.0)


if __name__ == "__main__":
    unittest.main()
