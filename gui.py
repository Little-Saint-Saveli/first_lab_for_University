"""
Модуль gui.py
=============

Графический интерфейс на tkinter для системы учёта заказов.

Автор: студент 2 курса
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional
import os

from models import Product, Client, Order, OrderItem, custom_sort_orders
from db import Database
from analysis import DataAnalyzer


class OrderManagementApp:
    """
    Главное окно приложения.

    Parameters
    ----------
    db : Database
        Экземпляр базы данных.
    """

    def __init__(self, db: Database):
        self.db = db
        self.root = tk.Tk()
        self.root.title("Система учёта заказов интернет-магазина")
        self.root.geometry("1000x650")
        self.root.minsize(900, 550)

        # Стиль
        style = ttk.Style()
        style.theme_use("clam")

        self._create_menu()
        self._create_notebook()
        self._refresh_all()

    def _create_menu(self) -> None:
        """Создание меню."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Экспорт в JSON...", command=self._export_json)
        file_menu.add_command(label="Импорт из JSON...", command=self._import_json)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт товаров в CSV...", command=lambda: self._export_csv("products"))
        file_menu.add_command(label="Экспорт клиентов в CSV...", command=lambda: self._export_csv("clients"))
        file_menu.add_command(label="Экспорт заказов в CSV...", command=lambda: self._export_csv("orders"))
        file_menu.add_separator()
        file_menu.add_command(label="Импорт товаров из CSV...", command=self._import_products_csv)
        file_menu.add_command(label="Импорт клиентов из CSV...", command=self._import_clients_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)

        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Данные", menu=data_menu)
        data_menu.add_command(label="Загрузить демо-данные", command=self._seed_demo)
        data_menu.add_command(label="Обновить всё", command=self._refresh_all)

        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Анализ", menu=analysis_menu)
        analysis_menu.add_command(label="Построить все графики", command=self._run_analysis)
        analysis_menu.add_command(label="Топ клиентов", command=lambda: self._show_analysis("clients"))
        analysis_menu.add_command(label="Динамика заказов", command=lambda: self._show_analysis("dynamics"))
        analysis_menu.add_command(label="Топ товаров", command=lambda: self._show_analysis("products"))
        analysis_menu.add_command(label="Граф связей (города)", command=lambda: self._show_analysis("graph_city"))

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._about)

    def _create_notebook(self) -> None:
        """Создание вкладок."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка Клиенты
        self.clients_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.clients_frame, text="Клиенты")
        self._build_clients_tab()

        # Вкладка Товары
        self.products_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.products_frame, text="Товары")
        self._build_products_tab()

        # Вкладка Заказы
        self.orders_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.orders_frame, text="Заказы")
        self._build_orders_tab()

        # Вкладка Анализ
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Анализ")
        self._build_analysis_tab()

    # ==================== КЛИЕНТЫ ====================

    def _build_clients_tab(self) -> None:
        """Построение вкладки клиентов."""
        # Левая часть — форма
        form_frame = ttk.LabelFrame(self.clients_frame, text="Добавить / изменить клиента", padding=10)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(form_frame, text="ФИО:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.client_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.client_name_var, width=30).grid(row=0, column=1, pady=3)

        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.client_email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.client_email_var, width=30).grid(row=1, column=1, pady=3)

        ttk.Label(form_frame, text="Телефон:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.client_phone_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.client_phone_var, width=30).grid(row=2, column=1, pady=3)

        ttk.Label(form_frame, text="Город:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.client_city_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.client_city_var, width=30).grid(row=3, column=1, pady=3)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Добавить", command=self._add_client).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Очистить", command=self._clear_client_form).pack(side=tk.LEFT, padx=3)

        # Поиск
        search_frame = ttk.Frame(form_frame)
        search_frame.grid(row=5, column=0, columnspan=2, pady=5)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.client_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.client_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=3)
        search_entry.bind("<Return>", lambda e: self._search_clients())
        ttk.Button(search_frame, text="Найти", command=self._search_clients).pack(side=tk.LEFT, padx=3)
        ttk.Button(search_frame, text="Сброс", command=self._refresh_clients).pack(side=tk.LEFT)

        # Правая часть — список
        list_frame = ttk.Frame(self.clients_frame)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "name", "email", "phone", "city")
        self.clients_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        self.clients_tree.heading("id", text="ID")
        self.clients_tree.heading("name", text="ФИО")
        self.clients_tree.heading("email", text="Email")
        self.clients_tree.heading("phone", text="Телефон")
        self.clients_tree.heading("city", text="Город")
        self.clients_tree.column("id", width=40)
        self.clients_tree.column("name", width=150)
        self.clients_tree.column("email", width=160)
        self.clients_tree.column("phone", width=130)
        self.clients_tree.column("city", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=scrollbar.set)
        self.clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(list_frame, text="Удалить выбранного", command=self._delete_client).pack(pady=5)

    def _add_client(self) -> None:
        """Добавление клиента."""
        try:
            client = Client(
                name=self.client_name_var.get(),
                email=self.client_email_var.get(),
                phone=self.client_phone_var.get(),
                city=self.client_city_var.get() or "Не указан",
            )
            self.db.add_client(client)
            messagebox.showinfo("Успех", f"Клиент '{client.name}' добавлен (ID={client.id})")
            self._clear_client_form()
            self._refresh_clients()
            self._refresh_order_combos()
        except ValueError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _clear_client_form(self) -> None:
        self.client_name_var.set("")
        self.client_email_var.set("")
        self.client_phone_var.set("")
        self.client_city_var.set("")

    def _search_clients(self) -> None:
        query = self.client_search_var.get().strip()
        try:
            if query:
                clients = self.db.search_clients(query)
            else:
                clients = self.db.get_all_clients()
            self._fill_clients_tree(clients)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _refresh_clients(self) -> None:
        try:
            clients = self.db.get_all_clients()
            self._fill_clients_tree(clients)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _fill_clients_tree(self, clients: list) -> None:
        self.clients_tree.delete(*self.clients_tree.get_children())
        for c in clients:
            self.clients_tree.insert("", tk.END, values=(c.id, c.name, c.email, c.phone, c.city))

    def _delete_client(self) -> None:
        selected = self.clients_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите клиента")
            return
        item = self.clients_tree.item(selected[0])
        client_id = item["values"][0]
        if messagebox.askyesno("Подтверждение", f"Удалить клиента ID={client_id}?"):
            try:
                self.db.delete_client(client_id)
                self._refresh_clients()
                self._refresh_order_combos()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    # ==================== ТОВАРЫ ====================

    def _build_products_tab(self) -> None:
        form_frame = ttk.LabelFrame(self.products_frame, text="Добавить товар", padding=10)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(form_frame, text="Название:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.product_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.product_name_var, width=30).grid(row=0, column=1, pady=3)

        ttk.Label(form_frame, text="Цена:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.product_price_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.product_price_var, width=30).grid(row=1, column=1, pady=3)

        ttk.Label(form_frame, text="Категория:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.product_category_var = tk.StringVar(value="Общее")
        ttk.Entry(form_frame, textvariable=self.product_category_var, width=30).grid(row=2, column=1, pady=3)

        ttk.Label(form_frame, text="Остаток:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.product_stock_var = tk.StringVar(value="0")
        ttk.Entry(form_frame, textvariable=self.product_stock_var, width=30).grid(row=3, column=1, pady=3)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Добавить", command=self._add_product).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Очистить", command=self._clear_product_form).pack(side=tk.LEFT, padx=3)

        list_frame = ttk.Frame(self.products_frame)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "name", "price", "category", "stock")
        self.products_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        self.products_tree.heading("id", text="ID")
        self.products_tree.heading("name", text="Название")
        self.products_tree.heading("price", text="Цена")
        self.products_tree.heading("category", text="Категория")
        self.products_tree.heading("stock", text="Остаток")
        self.products_tree.column("id", width=40)
        self.products_tree.column("name", width=180)
        self.products_tree.column("price", width=80)
        self.products_tree.column("category", width=120)
        self.products_tree.column("stock", width=70)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(list_frame, text="Удалить выбранный", command=self._delete_product).pack(pady=5)

    def _add_product(self) -> None:
        try:
            price = float(self.product_price_var.get().replace(",", "."))
            stock = int(self.product_stock_var.get() or 0)
            product = Product(
                name=self.product_name_var.get(),
                price=price,
                category=self.product_category_var.get() or "Общее",
                stock=stock,
            )
            self.db.add_product(product)
            messagebox.showinfo("Успех", f"Товар '{product.name}' добавлен (ID={product.id})")
            self._clear_product_form()
            self._refresh_products()
            self._refresh_order_combos()
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные данные: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _clear_product_form(self) -> None:
        self.product_name_var.set("")
        self.product_price_var.set("")
        self.product_category_var.set("Общее")
        self.product_stock_var.set("0")

    def _refresh_products(self) -> None:
        try:
            products = self.db.get_all_products()
            self.products_tree.delete(*self.products_tree.get_children())
            for p in products:
                self.products_tree.insert(
                    "", tk.END, values=(p.id, p.name, f"{p.price:.2f}", p.category, p.stock)
                )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _delete_product(self) -> None:
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        item = self.products_tree.item(selected[0])
        product_id = item["values"][0]
        if messagebox.askyesno("Подтверждение", f"Удалить товар ID={product_id}?"):
            try:
                self.db.delete_product(product_id)
                self._refresh_products()
                self._refresh_order_combos()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    # ==================== ЗАКАЗЫ ====================

    def _build_orders_tab(self) -> None:
        form_frame = ttk.LabelFrame(self.orders_frame, text="Создать заказ", padding=10)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(form_frame, text="Клиент:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.order_client_var = tk.StringVar()
        self.order_client_combo = ttk.Combobox(form_frame, textvariable=self.order_client_var, width=28, state="readonly")
        self.order_client_combo.grid(row=0, column=1, pady=3)

        ttk.Label(form_frame, text="Товар:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.order_product_var = tk.StringVar()
        self.order_product_combo = ttk.Combobox(form_frame, textvariable=self.order_product_var, width=28, state="readonly")
        self.order_product_combo.grid(row=1, column=1, pady=3)

        ttk.Label(form_frame, text="Количество:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.order_qty_var = tk.StringVar(value="1")
        ttk.Entry(form_frame, textvariable=self.order_qty_var, width=30).grid(row=2, column=1, pady=3)

        # Список позиций текущего заказа
        ttk.Label(form_frame, text="Позиции заказа:").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 3))
        self.order_items_listbox = tk.Listbox(form_frame, height=6, width=40)
        self.order_items_listbox.grid(row=4, column=0, columnspan=2, pady=3)
        self._current_order_items = []  # [(product, qty), ...]

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Добавить позицию", command=self._add_order_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Очистить позиции", command=self._clear_order_items).pack(side=tk.LEFT, padx=2)

        ttk.Button(form_frame, text="Создать заказ", command=self._create_order).grid(row=6, column=0, columnspan=2, pady=10)

        # Фильтры и сортировка
        filter_frame = ttk.LabelFrame(form_frame, text="Фильтр / сортировка", padding=5)
        filter_frame.grid(row=7, column=0, columnspan=2, pady=5, sticky=tk.EW)

        ttk.Label(filter_frame, text="Сортировка:").pack(anchor=tk.W)
        self.sort_var = tk.StringVar(value="date_desc")
        ttk.Radiobutton(filter_frame, text="По дате (новые)", variable=self.sort_var, value="date_desc",
                        command=self._refresh_orders).pack(anchor=tk.W)
        ttk.Radiobutton(filter_frame, text="По дате (старые)", variable=self.sort_var, value="date_asc",
                        command=self._refresh_orders).pack(anchor=tk.W)
        ttk.Radiobutton(filter_frame, text="По сумме (убыв.)", variable=self.sort_var, value="amount_desc",
                        command=self._refresh_orders).pack(anchor=tk.W)
        ttk.Radiobutton(filter_frame, text="По сумме (возр.)", variable=self.sort_var, value="amount_asc",
                        command=self._refresh_orders).pack(anchor=tk.W)

        # Правая часть — список заказов
        list_frame = ttk.Frame(self.orders_frame)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "client", "date", "status", "amount", "items")
        self.orders_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        self.orders_tree.heading("id", text="ID")
        self.orders_tree.heading("client", text="Клиент")
        self.orders_tree.heading("date", text="Дата")
        self.orders_tree.heading("status", text="Статус")
        self.orders_tree.heading("amount", text="Сумма")
        self.orders_tree.heading("items", text="Позиций")
        self.orders_tree.column("id", width=40)
        self.orders_tree.column("client", width=140)
        self.orders_tree.column("date", width=100)
        self.orders_tree.column("status", width=100)
        self.orders_tree.column("amount", width=90)
        self.orders_tree.column("items", width=60)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=scrollbar.set)
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(list_frame, text="Удалить выбранный", command=self._delete_order).pack(pady=5)

    def _refresh_order_combos(self) -> None:
        """Обновить списки клиентов и товаров в комбобоксах."""
        try:
            clients = self.db.get_all_clients()
            self._clients_map = {f"{c.id}: {c.name}": c for c in clients}
            self.order_client_combo["values"] = list(self._clients_map.keys())

            products = self.db.get_all_products()
            self._products_map = {f"{p.id}: {p.name} ({p.price:.0f} руб.)": p for p in products}
            self.order_product_combo["values"] = list(self._products_map.keys())
        except Exception:
            pass

    def _add_order_item(self) -> None:
        key = self.order_product_var.get()
        if not key or key not in self._products_map:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        try:
            qty = int(self.order_qty_var.get())
            if qty <= 0:
                raise ValueError("Количество должно быть > 0")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        product = self._products_map[key]
        self._current_order_items.append((product, qty))
        self.order_items_listbox.insert(tk.END, f"{product.name} x{qty} = {product.price * qty:.2f} руб.")

    def _clear_order_items(self) -> None:
        self._current_order_items.clear()
        self.order_items_listbox.delete(0, tk.END)

    def _create_order(self) -> None:
        client_key = self.order_client_var.get()
        if not client_key or client_key not in self._clients_map:
            messagebox.showwarning("Внимание", "Выберите клиента")
            return
        if not self._current_order_items:
            messagebox.showwarning("Внимание", "Добавьте хотя бы одну позицию")
            return

        try:
            client = self._clients_map[client_key]
            order = Order(client=client)
            for product, qty in self._current_order_items:
                order.add_item(product, qty)
            self.db.add_order(order)
            messagebox.showinfo("Успех", f"Заказ #{order.id} создан на сумму {order.total_amount:.2f} руб.")
            self._clear_order_items()
            self._refresh_orders()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _refresh_orders(self) -> None:
        try:
            orders = self.db.get_all_orders()
            # Собственная сортировка
            sort_mode = self.sort_var.get()
            if sort_mode == "date_desc":
                orders = custom_sort_orders(orders, key="date", reverse=True)
            elif sort_mode == "date_asc":
                orders = custom_sort_orders(orders, key="date", reverse=False)
            elif sort_mode == "amount_desc":
                orders = custom_sort_orders(orders, key="amount", reverse=True)
            elif sort_mode == "amount_asc":
                orders = custom_sort_orders(orders, key="amount", reverse=False)

            self.orders_tree.delete(*self.orders_tree.get_children())
            for o in orders:
                self.orders_tree.insert(
                    "",
                    tk.END,
                    values=(
                        o.id,
                        o.client.name,
                        o.order_date.strftime("%d.%m.%Y"),
                        o.status,
                        f"{o.total_amount:.2f}",
                        o.items_count,
                    ),
                )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _delete_order(self) -> None:
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите заказ")
            return
        item = self.orders_tree.item(selected[0])
        order_id = item["values"][0]
        if messagebox.askyesno("Подтверждение", f"Удалить заказ ID={order_id}?"):
            try:
                self.db.delete_order(order_id)
                self._refresh_orders()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    # ==================== АНАЛИЗ ====================

    def _build_analysis_tab(self) -> None:
        info = ttk.Label(
            self.analysis_frame,
            text="Раздел анализа данных.\n"
                 "Используйте меню «Анализ» для построения графиков\n"
                 "или нажмите кнопку ниже.",
            font=("Arial", 11),
            justify=tk.CENTER,
        )
        info.pack(pady=20)

        ttk.Button(
            self.analysis_frame,
            text="Построить все графики и показать сводку",
            command=self._run_analysis,
        ).pack(pady=10)

        self.analysis_text = tk.Text(self.analysis_frame, height=20, width=80, wrap=tk.WORD)
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _run_analysis(self) -> None:
        try:
            orders = self.db.get_all_orders()
            clients = self.db.get_all_clients()
            products = self.db.get_all_products()

            if not orders:
                messagebox.showinfo("Информация", "Нет заказов для анализа. Загрузите демо-данные.")
                return

            analyzer = DataAnalyzer(orders, clients, products)
            plots = analyzer.generate_all_plots("data")

            top_clients = analyzer.top_clients_by_orders(5)
            dynamics = analyzer.orders_dynamics()
            top_products = analyzer.top_products(5)
            by_city = analyzer.sales_by_city()
            total = analyzer.total_revenue()

            text = "=== СВОДКА ПО АНАЛИЗУ ===\n\n"
            text += f"Всего заказов: {len(orders)}\n"
            text += f"Общая выручка: {total:.2f} руб.\n"
            text += f"Клиентов: {len(clients)}, товаров: {len(products)}\n\n"

            text += "--- Топ 5 клиентов по числу заказов ---\n"
            text += top_clients.to_string(index=False) + "\n\n"

            text += "--- Топ 5 товаров ---\n"
            text += top_products.to_string(index=False) + "\n\n"

            text += "--- Продажи по городам ---\n"
            text += by_city.to_string(index=False) + "\n\n"

            text += "--- Динамика заказов (последние записи) ---\n"
            text += dynamics.tail(10).to_string(index=False) + "\n\n"

            text += "Графики сохранены в папку data/:\n"
            for name, path in plots.items():
                text += f"  • {name}: {path}\n"

            self.analysis_text.delete("1.0", tk.END)
            self.analysis_text.insert("1.0", text)
            messagebox.showinfo("Готово", f"Анализ выполнен. Построено графиков: {len(plots)}")
        except Exception as e:
            messagebox.showerror("Ошибка анализа", str(e))

    def _show_analysis(self, kind: str) -> None:
        """Быстрый показ одного вида анализа."""
        self._run_analysis()

    # ==================== ФАЙЛЫ ====================

    def _export_json(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="export.json",
        )
        if path:
            try:
                self.db.export_to_json(path)
                messagebox.showinfo("Успех", f"Данные экспортированы в {path}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _import_json(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            try:
                p, c, o = self.db.import_from_json(path)
                messagebox.showinfo("Успех", f"Импортировано: товаров={p}, клиентов={c}")
                self._refresh_all()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _export_csv(self, entity: str) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"{entity}.csv",
        )
        if path:
            try:
                self.db.export_to_csv(entity, path)
                messagebox.showinfo("Успех", f"Экспорт в {path} выполнен")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _import_products_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                count = self.db.import_products_from_csv(path)
                messagebox.showinfo("Успех", f"Добавлено товаров: {count}")
                self._refresh_products()
                self._refresh_order_combos()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _import_clients_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                count = self.db.import_clients_from_csv(path)
                messagebox.showinfo("Успех", f"Добавлено клиентов: {count}")
                self._refresh_clients()
                self._refresh_order_combos()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _seed_demo(self) -> None:
        try:
            self.db.seed_demo_data()
            messagebox.showinfo("Успех", "Демо-данные загружены")
            self._refresh_all()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _refresh_all(self) -> None:
        self._refresh_clients()
        self._refresh_products()
        self._refresh_orders()
        self._refresh_order_combos()

    def _about(self) -> None:
        messagebox.showinfo(
            "О программе",
            "Система учёта заказов интернет-магазина\n\n"
            "Итоговая аттестация по Python\n"
            "Студент 2 курса\n\n"
            "Возможности:\n"
            "• Учёт клиентов, товаров, заказов\n"
            "• SQLite + CSV/JSON\n"
            "• Анализ и визуализация (pandas, matplotlib, seaborn, networkx)\n"
            "• Валидация email и телефона (regex)\n"
            "• Собственная сортировка, рекурсия, ООП",
        )

    def run(self) -> None:
        """Запуск главного цикла."""
        self.root.mainloop()
