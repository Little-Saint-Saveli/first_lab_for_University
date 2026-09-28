"""
Модуль analysis.py
==================

Функции визуализации и анализа данных заказов.

Использует pandas, matplotlib, seaborn, networkx.

Автор: студент 2 курса
"""

from typing import List, Optional, Tuple
from collections import Counter
from datetime import datetime
import os

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import networkx as nx

from models import Order, Client, Product, custom_sort_orders, recursive_sum_amounts

# Настройка matplotlib для работы без GUI (если нужно)
matplotlib.use("Agg")
plt.rcParams["font.family"] = "DejaVu Sans"
sns.set_theme(style="whitegrid", palette="muted")


class DataAnalyzer:
    """
    Класс для анализа и визуализации данных.

    Parameters
    ----------
    orders : list of Order
        Список заказов.
    clients : list of Client, optional
        Список клиентов.
    products : list of Product, optional
        Список товаров.
    """

    def __init__(
        self,
        orders: List[Order],
        clients: Optional[List[Client]] = None,
        products: Optional[List[Product]] = None,
    ):
        self.orders = orders
        self.clients = clients or []
        self.products = products or []
        self._df = self._build_dataframe()

    def _build_dataframe(self) -> pd.DataFrame:
        """Построение DataFrame из заказов."""
        if not self.orders:
            return pd.DataFrame(
                columns=["order_id", "client_id", "client_name", "city",
                         "order_date", "status", "total_amount", "items_count"]
            )

        records = []
        for o in self.orders:
            records.append({
                "order_id": o.id,
                "client_id": o.client.id,
                "client_name": o.client.name,
                "city": o.client.city,
                "order_date": o.order_date,
                "status": o.status,
                "total_amount": o.total_amount,
                "items_count": o.items_count,
            })
        df = pd.DataFrame(records)
        df["order_date"] = pd.to_datetime(df["order_date"])
        df["date_only"] = df["order_date"].dt.date
        return df

    def top_clients_by_orders(self, n: int = 5) -> pd.DataFrame:
        """
        Топ N клиентов по числу заказов.

        Parameters
        ----------
        n : int
            Количество клиентов.

        Returns
        -------
        pd.DataFrame
            Таблица с клиентами и количеством заказов.
        """
        if self._df.empty:
            return pd.DataFrame(columns=["client_name", "orders_count", "total_spent"])

        grouped = (
            self._df.groupby(["client_id", "client_name"])
            .agg(orders_count=("order_id", "count"), total_spent=("total_amount", "sum"))
            .reset_index()
            .sort_values("orders_count", ascending=False)
            .head(n)
        )
        return grouped

    def orders_dynamics(self) -> pd.DataFrame:
        """
        Динамика количества заказов по датам.

        Returns
        -------
        pd.DataFrame
            Дата и количество заказов.
        """
        if self._df.empty:
            return pd.DataFrame(columns=["date_only", "orders_count"])

        dynamics = (
            self._df.groupby("date_only")
            .size()
            .reset_index(name="orders_count")
            .sort_values("date_only")
        )
        return dynamics

    def top_products(self, n: int = 5) -> pd.DataFrame:
        """
        Топ N товаров по количеству продаж.

        Parameters
        ----------
        n : int
            Количество товаров.

        Returns
        -------
        pd.DataFrame
        """
        product_counter: Counter = Counter()
        product_revenue: Counter = Counter()

        for order in self.orders:
            for item in order.items:
                name = item.product.name
                product_counter[name] += item.quantity
                product_revenue[name] += item.total_price

        if not product_counter:
            return pd.DataFrame(columns=["product", "quantity", "revenue"])

        data = [
            {"product": name, "quantity": qty, "revenue": product_revenue[name]}
            for name, qty in product_counter.most_common(n)
        ]
        return pd.DataFrame(data)

    def sales_by_city(self) -> pd.DataFrame:
        """Продажи по городам."""
        if self._df.empty:
            return pd.DataFrame(columns=["city", "orders_count", "total_amount"])

        return (
            self._df.groupby("city")
            .agg(orders_count=("order_id", "count"), total_amount=("total_amount", "sum"))
            .reset_index()
            .sort_values("total_amount", ascending=False)
        )

    def total_revenue(self) -> float:
        """Общая выручка (с использованием рекурсии из models)."""
        return recursive_sum_amounts(self.orders)

    def plot_top_clients(self, filepath: str = "data/top_clients.png", n: int = 5) -> str:
        """
        График топ клиентов по числу заказов.

        Returns
        -------
        str
            Путь к сохранённому файлу.
        """
        df = self.top_clients_by_orders(n)
        if df.empty:
            return ""

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=df, x="client_name", y="orders_count", ax=ax, hue="client_name", legend=False)
        ax.set_title(f"Топ {n} клиентов по числу заказов", fontsize=14)
        ax.set_xlabel("Клиент")
        ax.set_ylabel("Количество заказов")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fig.savefig(filepath, dpi=120)
        plt.close(fig)
        return filepath

    def plot_orders_dynamics(self, filepath: str = "data/orders_dynamics.png") -> str:
        """
        График динамики заказов по датам.

        Returns
        -------
        str
            Путь к файлу.
        """
        df = self.orders_dynamics()
        if df.empty:
            return ""

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["date_only"], df["orders_count"], marker="o", linewidth=2, color="#2c7bb6")
        ax.fill_between(df["date_only"], df["orders_count"], alpha=0.3, color="#2c7bb6")
        ax.set_title("Динамика количества заказов по датам", fontsize=14)
        ax.set_xlabel("Дата")
        ax.set_ylabel("Количество заказов")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fig.savefig(filepath, dpi=120)
        plt.close(fig)
        return filepath

    def plot_top_products(self, filepath: str = "data/top_products.png", n: int = 5) -> str:
        """График топ товаров."""
        df = self.top_products(n)
        if df.empty:
            return ""

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=df, x="quantity", y="product", ax=ax, orient="h", hue="product", legend=False)
        ax.set_title(f"Топ {n} товаров по продажам", fontsize=14)
        ax.set_xlabel("Количество проданных единиц")
        ax.set_ylabel("Товар")
        plt.tight_layout()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fig.savefig(filepath, dpi=120)
        plt.close(fig)
        return filepath

    def plot_sales_by_city(self, filepath: str = "data/sales_by_city.png") -> str:
        """Круговая диаграмма продаж по городам."""
        df = self.sales_by_city()
        if df.empty:
            return ""

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(
            df["total_amount"],
            labels=df["city"],
            autopct="%1.1f%%",
            startangle=90,
            colors=sns.color_palette("pastel", len(df)),
        )
        ax.set_title("Распределение продаж по городам", fontsize=14)
        plt.tight_layout()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fig.savefig(filepath, dpi=120)
        plt.close(fig)
        return filepath

    def build_client_graph(
        self,
        mode: str = "city",
        filepath: str = "data/client_graph.png",
    ) -> str:
        """
        Построение графа связей клиентов.

        Parameters
        ----------
        mode : str
            'city' — связь по городу, 'products' — по общим товарам.
        filepath : str
            Путь для сохранения.

        Returns
        -------
        str
            Путь к файлу.
        """
        G = nx.Graph()

        if not self.orders:
            return ""

        # Добавляем узлы
        client_ids = set()
        for o in self.orders:
            cid = o.client.id
            if cid not in client_ids:
                G.add_node(cid, name=o.client.name, city=o.client.city)
                client_ids.add(cid)

        if mode == "city":
            # Связь, если один город
            cities: dict = {}
            for o in self.orders:
                city = o.client.city
                cid = o.client.id
                if city not in cities:
                    cities[city] = []
                if cid not in cities[city]:
                    cities[city].append(cid)

            for city, cids in cities.items():
                for i in range(len(cids)):
                    for j in range(i + 1, len(cids)):
                        G.add_edge(cids[i], cids[j], reason=city)

        elif mode == "products":
            # Связь, если покупали одинаковые товары
            client_products: dict = {}
            for o in self.orders:
                cid = o.client.id
                if cid not in client_products:
                    client_products[cid] = set()
                for item in o.items:
                    if item.product.id:
                        client_products[cid].add(item.product.id)

            cids = list(client_products.keys())
            for i in range(len(cids)):
                for j in range(i + 1, len(cids)):
                    common = client_products[cids[i]] & client_products[cids[j]]
                    if common:
                        G.add_edge(cids[i], cids[j], weight=len(common))

        if G.number_of_nodes() == 0:
            return ""

        fig, ax = plt.subplots(figsize=(10, 8))
        pos = nx.spring_layout(G, seed=42, k=1.5)

        node_labels = {n: G.nodes[n].get("name", str(n)) for n in G.nodes()}
        nx.draw_networkx_nodes(G, pos, node_color="#66c2a5", node_size=800, ax=ax)
        nx.draw_networkx_edges(G, pos, alpha=0.5, width=1.5, ax=ax)
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8, ax=ax)

        title = "Граф связей клиентов по городам" if mode == "city" else "Граф связей клиентов по общим товарам"
        ax.set_title(title, fontsize=14)
        ax.axis("off")
        plt.tight_layout()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fig.savefig(filepath, dpi=120)
        plt.close(fig)
        return filepath

    def generate_all_plots(self, output_dir: str = "data") -> dict:
        """
        Сгенерировать все графики.

        Returns
        -------
        dict
            Словарь {название: путь}.
        """
        os.makedirs(output_dir, exist_ok=True)
        results = {}
        results["top_clients"] = self.plot_top_clients(f"{output_dir}/top_clients.png")
        results["dynamics"] = self.plot_orders_dynamics(f"{output_dir}/orders_dynamics.png")
        results["top_products"] = self.plot_top_products(f"{output_dir}/top_products.png")
        results["by_city"] = self.plot_sales_by_city(f"{output_dir}/sales_by_city.png")
        results["graph_city"] = self.build_client_graph("city", f"{output_dir}/client_graph_city.png")
        results["graph_products"] = self.build_client_graph("products", f"{output_dir}/client_graph_products.png")
        return {k: v for k, v in results.items() if v}
