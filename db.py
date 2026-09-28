"""
Модуль db.py
============

Работа с базой данных Excel и импорт/экспорт в CSV/JSON.

Хранение данных в Excel файле между запусками приложения.

Автор: студент 2 курса
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Optional, Tuple
import pandas as pd

from models import Product, Client, Order, OrderItem


class Database:
    """
    Класс для работы с Excel базой данных.

    Parameters
    ----------
    db_path : str
        Путь к файлу базы данных (Excel).
    """

    def __init__(self, db_path: str = "data/shop.xlsx"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Инициализация таблиц в Excel."""
        try:
            if os.path.exists(self.db_path):
                return  # Файл уже существует

            # Создаём пустые таблицы в Excel
            with pd.ExcelWriter(self.db_path, engine="openpyxl") as writer:
                # Таблица товаров
                products_df = pd.DataFrame(columns=["id", "name", "price", "category", "stock"])
                products_df.to_excel(writer, sheet_name="products", index=False)

                # Таблица клиентов
                clients_df = pd.DataFrame(columns=["id", "name", "email", "phone", "city"])
                clients_df.to_excel(writer, sheet_name="clients", index=False)

                # Таблица заказов
                orders_df = pd.DataFrame(columns=["id", "client_id", "order_date", "status"])
                orders_df.to_excel(writer, sheet_name="orders", index=False)

                # Таблица позиций заказов
                order_items_df = pd.DataFrame(columns=["id", "order_id", "product_id", "quantity", "price"])
                order_items_df.to_excel(writer, sheet_name="order_items", index=False)
        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")
            raise

    def _read_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Чтение листа из Excel файла."""
        try:
            if not os.path.exists(self.db_path):
                return pd.DataFrame()
            df = pd.read_excel(self.db_path, sheet_name=sheet_name)
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            print(f"Ошибка чтения листа {sheet_name}: {e}")
            return pd.DataFrame()

    def _write_sheet(self, sheet_name: str, df: pd.DataFrame) -> None:
        """Запись листа в Excel файл."""
        try:
            # Читаем все листы
            existing_sheets = {}
            try:
                xl_file = pd.ExcelFile(self.db_path)
                for name in xl_file.sheet_names:
                    if name != sheet_name:
                        existing_sheets[name] = pd.read_excel(self.db_path, sheet_name=name)
            except:
                pass

            # Добавляем обновлённый лист
            existing_sheets[sheet_name] = df

            # Пишем всё обратно
            with pd.ExcelWriter(self.db_path, engine="openpyxl") as writer:
                for name, data in existing_sheets.items():
                    data.to_excel(writer, sheet_name=name, index=False)
        except Exception as e:
            print(f"Ошибка записи листа {sheet_name}: {e}")
            raise

    def _get_next_id(self, sheet_name: str) -> int:
        """Получить следующий ID для таблицы."""
        df = self._read_sheet(sheet_name)
        if df.empty or "id" not in df.columns:
            return 1
        return int(df["id"].max()) + 1 if not df["id"].isna().all() else 1

    # ========== PRODUCTS ==========

    def add_product(self, product: Product) -> int:
        """Добавить товар. Возвращает ID."""
        try:
            df = self._read_sheet("products")
            product_id = self._get_next_id("products")

            new_row = pd.DataFrame([{
                "id": product_id,
                "name": product.name,
                "price": product.price,
                "category": product.category,
                "stock": product.stock,
            }])

            df = pd.concat([df, new_row], ignore_index=True)
            self._write_sheet("products", df)
            product.id = product_id
            return product_id
        except Exception as e:
            raise RuntimeError(f"Ошибка добавления товара: {e}")

    def get_product(self, product_id: int) -> Optional[Product]:
        """Получить товар по ID."""
        try:
            df = self._read_sheet("products")
            row = df[df["id"] == product_id]
            if row.empty:
                return None
            r = row.iloc[0]
            return Product(
                name=r["name"],
                price=r["price"],
                category=r["category"],
                stock=int(r["stock"]),
                product_id=int(r["id"]),
            )
        except Exception as e:
            raise RuntimeError(f"Ошибка получения товара: {e}")

    def get_all_products(self) -> List[Product]:
        """Получить все товары."""
        try:
            df = self._read_sheet("products")
            if df.empty:
                return []
            products = []
            for _, r in df.iterrows():
                products.append(Product(
                    name=r["name"],
                    price=r["price"],
                    category=r["category"],
                    stock=int(r["stock"]),
                    product_id=int(r["id"]),
                ))
            return sorted(products, key=lambda p: p.name)
        except Exception as e:
            raise RuntimeError(f"Ошибка получения товаров: {e}")

    def update_product(self, product: Product) -> None:
        """Обновить товар."""
        try:
            df = self._read_sheet("products")
            mask = df["id"] == product.id
            if mask.any():
                df.loc[mask, "name"] = product.name
                df.loc[mask, "price"] = product.price
                df.loc[mask, "category"] = product.category
                df.loc[mask, "stock"] = product.stock
                self._write_sheet("products", df)
        except Exception as e:
            raise RuntimeError(f"Ошибка обновления товара: {e}")

    def delete_product(self, product_id: int) -> bool:
        """Удалить товар."""
        try:
            df = self._read_sheet("products")
            initial_len = len(df)
            df = df[df["id"] != product_id]
            if len(df) < initial_len:
                self._write_sheet("products", df)
                return True
            return False
        except Exception as e:
            raise RuntimeError(f"Ошибка удаления товара: {e}")

    # ========== CLIENTS ==========

    def add_client(self, client: Client) -> int:
        """Добавить клиента. Возвращает ID."""
        try:
            df = self._read_sheet("clients")
            # Проверка на дубликат email
            if not df.empty and client.email in df["email"].values:
                raise ValueError(f"Клиент с email {client.email} уже существует")

            client_id = self._get_next_id("clients")
            new_row = pd.DataFrame([{
                "id": client_id,
                "name": client.name,
                "email": client.email,
                "phone": client.phone,
                "city": client.city,
            }])

            df = pd.concat([df, new_row], ignore_index=True)
            self._write_sheet("clients", df)
            client.id = client_id
            return client_id
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Ошибка добавления клиента: {e}")

    def get_client(self, client_id: int) -> Optional[Client]:
        """Получить клиента по ID."""
        try:
            df = self._read_sheet("clients")
            row = df[df["id"] == client_id]
            if row.empty:
                return None
            r = row.iloc[0]
            return Client(
                name=r["name"],
                email=r["email"],
                phone=r["phone"],
                city=r["city"],
                client_id=int(r["id"]),
            )
        except Exception as e:
            raise RuntimeError(f"Ошибка получения клиента: {e}")

    def get_all_clients(self) -> List[Client]:
        """Получить всех клиентов."""
        try:
            df = self._read_sheet("clients")
            if df.empty:
                return []
            clients = []
            for _, r in df.iterrows():
                clients.append(Client(
                    name=r["name"],
                    email=r["email"],
                    phone=r["phone"],
                    city=r["city"],
                    client_id=int(r["id"]),
                ))
            return sorted(clients, key=lambda c: c.name)
        except Exception as e:
            raise RuntimeError(f"Ошибка получения клиентов: {e}")

    def update_client(self, client: Client) -> None:
        """Обновить клиента."""
        try:
            df = self._read_sheet("clients")
            mask = df["id"] == client.id
            if mask.any():
                df.loc[mask, "name"] = client.name
                df.loc[mask, "email"] = client.email
                df.loc[mask, "phone"] = client.phone
                df.loc[mask, "city"] = client.city
                self._write_sheet("clients", df)
        except Exception as e:
            raise RuntimeError(f"Ошибка обновления клиента: {e}")

    def delete_client(self, client_id: int) -> bool:
        """Удалить клиента."""
        try:
            df = self._read_sheet("clients")
            initial_len = len(df)
            df = df[df["id"] != client_id]
            if len(df) < initial_len:
                self._write_sheet("clients", df)
                return True
            return False
        except Exception as e:
            raise RuntimeError(f"Ошибка удаления клиента: {e}")

    # ========== ORDERS ==========

    def add_order(self, order: Order) -> int:
        """Добавить заказ. Возвращает ID."""
        try:
            df = self._read_sheet("orders")
            order_id = self._get_next_id("orders")

            new_row = pd.DataFrame([{
                "id": order_id,
                "client_id": order.client.id,
                "order_date": order.order_date.isoformat(),
                "status": order.status,
            }])

            df = pd.concat([df, new_row], ignore_index=True)
            self._write_sheet("orders", df)

            # Добавляем позиции заказа
            for item in order.items:
                self._add_order_item(order_id, item)

            order.id = order_id
            return order_id
        except Exception as e:
            raise RuntimeError(f"Ошибка добавления заказа: {e}")

    def _add_order_item(self, order_id: int, item: OrderItem) -> int:
        """Добавить позицию заказа."""
        try:
            df = self._read_sheet("order_items")
            item_id = self._get_next_id("order_items")

            new_row = pd.DataFrame([{
                "id": item_id,
                "order_id": order_id,
                "product_id": item.product.id,
                "quantity": item.quantity,
                "price": item.product.price,
            }])

            df = pd.concat([df, new_row], ignore_index=True)
            self._write_sheet("order_items", df)
            return item_id
        except Exception as e:
            raise RuntimeError(f"Ошибка добавления позиции заказа: {e}")

    def get_order(self, order_id: int) -> Optional[Order]:
        """Получить заказ по ID."""
        try:
            orders_df = self._read_sheet("orders")
            row = orders_df[orders_df["id"] == order_id]
            if row.empty:
                return None

            r = row.iloc[0]
            client = self.get_client(int(r["client_id"]))
            if not client:
                return None

            order = Order(
                client=client,
                order_date=pd.to_datetime(r["order_date"]).to_pydatetime(),
                status=r["status"],
                order_id=int(r["id"]),
            )

            # Получаем позиции заказа
            items_df = self._read_sheet("order_items")
            items_rows = items_df[items_df["order_id"] == order_id]
            for _, item_row in items_rows.iterrows():
                product = self.get_product(int(item_row["product_id"]))
                if product:
                    order.add_item(product, int(item_row["quantity"]))

            return order
        except Exception as e:
            raise RuntimeError(f"Ошибка получения заказа: {e}")

    def get_all_orders(self) -> List[Order]:
        """Получить все заказы."""
        try:
            orders_df = self._read_sheet("orders")
            if orders_df.empty:
                return []

            orders = []
            for _, r in orders_df.iterrows():
                order = self.get_order(int(r["id"]))
                if order:
                    orders.append(order)
            return sorted(orders, key=lambda o: o.order_date, reverse=True)
        except Exception as e:
            raise RuntimeError(f"Ошибка получения заказов: {e}")

    def update_order_status(self, order_id: int, new_status: str) -> None:
        """Обновить статус заказа."""
        try:
            df = self._read_sheet("orders")
            mask = df["id"] == order_id
            if mask.any():
                df.loc[mask, "status"] = new_status
                self._write_sheet("orders", df)
        except Exception as e:
            raise RuntimeError(f"Ошибка обновления статуса заказа: {e}")

    def delete_order(self, order_id: int) -> bool:
        """Удалить заказ."""
        try:
            # Удаляем позиции заказа
            items_df = self._read_sheet("order_items")
            items_df = items_df[items_df["order_id"] != order_id]
            self._write_sheet("order_items", items_df)

            # Удаляем сам заказ
            orders_df = self._read_sheet("orders")
            initial_len = len(orders_df)
            orders_df = orders_df[orders_df["id"] != order_id]
            if len(orders_df) < initial_len:
                self._write_sheet("orders", orders_df)
                return True
            return False
        except Exception as e:
            raise RuntimeError(f"Ошибка удаления заказа: {e}")

    # ========== EXPORT / IMPORT ==========

    def export_to_json(self, filepath: str) -> None:
        """Экспорт всех данных в JSON."""
        try:
            data = {
                "products": [p.to_dict() for p in self.get_all_products()],
                "clients": [c.to_dict() for c in self.get_all_clients()],
                "orders": [o.to_dict() for o in self.get_all_orders()],
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (OSError, TypeError) as e:
            raise RuntimeError(f"Ошибка экспорта в JSON: {e}")

    def import_from_json(self, filepath: str) -> Tuple[int, int, int]:
        """
        Импорт данных из JSON.
        Возвращает (кол-во товаров, клиентов, заказов).
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            products_count = 0
            clients_count = 0
            orders_count = 0

            # Товары
            for p_data in data.get("products", []):
                try:
                    product = Product.from_dict(p_data)
                    existing = [p for p in self.get_all_products() if p.name == product.name]
                    if not existing:
                        self.add_product(product)
                        products_count += 1
                except (ValueError, KeyError):
                    continue

            # Клиенты
            for c_data in data.get("clients", []):
                try:
                    client = Client.from_dict(c_data)
                    existing = [c for c in self.get_all_clients() if c.email == client.email]
                    if not existing:
                        self.add_client(client)
                        clients_count += 1
                except (ValueError, KeyError):
                    continue

            return products_count, clients_count, orders_count
        except (OSError, json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Ошибка импорта из JSON: {e}")

    def export_to_csv(self, entity: str, filepath: str) -> None:
        """
        Экспорт сущности в CSV.

        Parameters
        ----------
        entity : str
            'products', 'clients' или 'orders'.
        filepath : str
            Путь к файлу.
        """
        try:
            if entity == "products":
                items = self.get_all_products()
                fieldnames = ["id", "name", "price", "category", "stock"]
                rows = [p.to_dict() for p in items]
            elif entity == "clients":
                items = self.get_all_clients()
                fieldnames = ["id", "name", "email", "phone", "city"]
                rows = [c.to_dict() for c in items]
            elif entity == "orders":
                items = self.get_all_orders()
                fieldnames = ["id", "client_id", "client_name", "order_date", "status", "total_amount"]
                rows = [
                    {
                        "id": o.id,
                        "client_id": o.client.id,
                        "client_name": o.client.name,
                        "order_date": o.order_date.isoformat(),
                        "status": o.status,
                        "total_amount": o.total_amount,
                    }
                    for o in items
                ]
            else:
                raise ValueError(f"Неизвестная сущность: {entity}")

            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        except (OSError, ValueError) as e:
            raise RuntimeError(f"Ошибка экспорта в CSV: {e}")

    def import_products_from_csv(self, filepath: str) -> int:
        """Импорт товаров из CSV. Возвращает количество добавленных."""
        count = 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        product = Product(
                            name=row["name"],
                            price=float(row["price"]),
                            category=row.get("category", "Общее"),
                            stock=int(row.get("stock", 0)),
                        )
                        existing = [p for p in self.get_all_products() if p.name == product.name]
                        if not existing:
                            self.add_product(product)
                            count += 1
                    except (ValueError, KeyError):
                        continue
            return count
        except (OSError, csv.Error) as e:
            raise RuntimeError(f"Ошибка импорта товаров из CSV: {e}")

    def import_clients_from_csv(self, filepath: str) -> int:
        """Импорт клиентов из CSV. Возвращает количество добавленных."""
        count = 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        client = Client(
                            name=row["name"],
                            email=row["email"],
                            phone=row["phone"],
                            city=row.get("city", "Не указан"),
                        )
                        existing = [c for c in self.get_all_clients() if c.email == client.email]
                        if not existing:
                            self.add_client(client)
                            count += 1
                    except (ValueError, KeyError):
                        continue
            return count
        except (OSError, csv.Error) as e:
            raise RuntimeError(f"Ошибка импорта клиентов из CSV: {e}")

    def seed_demo_data(self) -> None:
        """Заполнение демонстрационными данными."""
        if self.get_all_products():
            return  # уже есть данные

        products = [
            Product("Ноутбук ASUS", 54990.0, "Электроника", 15),
            Product("Смартфон Samsung", 32990.0, "Электроника", 30),
            Product("Наушники Sony", 8990.0, "Аксессуары", 50),
            Product("Клавиатура Logitech", 3490.0, "Аксессуары", 40),
            Product("Монитор LG 27\"", 18990.0, "Электроника", 20),
            Product("Мышь беспроводная", 1290.0, "Аксессуары", 100),
            Product("SSD 1TB", 7990.0, "Комплектующие", 25),
            Product("Веб-камера HD", 2490.0, "Аксессуары", 35),
        ]
        for p in products:
            self.add_product(p)

        clients = [
            Client("Иванов Иван", "ivanov@mail.ru", "+7 (999) 123-45-67", "Москва"),
            Client("Петрова Мария", "petrova@gmail.com", "8 (916) 234-56-78", "Санкт-Петербург"),
            Client("Сидоров Алексей", "sidorov@yandex.ru", "+7 903 345-67-89", "Москва"),
            Client("Козлова Анна", "kozlova@mail.ru", "89163456789", "Казань"),
            Client("Смирнов Дмитрий", "smirnov@gmail.com", "+7(495)456-78-90", "Москва"),
            Client("Васильева Елена", "vasilieva@yandex.ru", "8 800 555-35-35", "Новосибирск"),
        ]
        for c in clients:
            self.add_client(c)

        # Несколько заказов
        all_products = self.get_all_products()
        all_clients = self.get_all_clients()

        if all_products and all_clients:
            from datetime import timedelta
            import random

            for i in range(12):
                client = random.choice(all_clients)
                order = Order(client=client, status=random.choice(["новый", "в обработке", "отправлен", "доставлен"]))
                order.order_date = datetime.now() - timedelta(days=random.randint(1, 60))
                # 1-3 товара
                for _ in range(random.randint(1, 3)):
                    prod = random.choice(all_products)
                    order.add_item(prod, random.randint(1, 2))
                self.add_order(order)
