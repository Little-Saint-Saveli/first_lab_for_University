"""
Модуль models.py
================

Классы данных для системы учёта заказов интернет-магазина.

Содержит базовые сущности: Product, Client, Order.
Демонстрирует ООП: инкапсуляция, наследование, полиморфизм.

Автор: студент 2 курса
"""

from datetime import datetime
from typing import List, Optional
import re


class BaseEntity:
    """
    Базовый класс для всех сущностей системы.

    Parameters
    ----------
    entity_id : int, optional
        Уникальный идентификатор сущности.
    """

    def __init__(self, entity_id: Optional[int] = None):
        self._id = entity_id

    @property
    def id(self) -> Optional[int]:
        """Геттер идентификатора (инкапсуляция)."""
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        """Сеттер идентификатора с проверкой."""
        if value is not None and value < 0:
            raise ValueError("ID не может быть отрицательным")
        self._id = value

    def __str__(self) -> str:
        """Строковое представление (полиморфизм)."""
        return f"{self.__class__.__name__}(id={self._id})"

    def __repr__(self) -> str:
        return self.__str__()


class Product(BaseEntity):
    """
    Класс товара.

    Parameters
    ----------
    name : str
        Название товара.
    price : float
        Цена товара.
    category : str, optional
        Категория товара.
    stock : int, optional
        Количество на складе.
    product_id : int, optional
        ID товара.
    """

    def __init__(
        self,
        name: str,
        price: float,
        category: str = "Общее",
        stock: int = 0,
        product_id: Optional[int] = None,
    ):
        super().__init__(product_id)
        self.name = name  # через setter с валидацией
        self.price = price
        self.category = category
        self.stock = stock

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Название товара не может быть пустым")
        self._name = value.strip()

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Цена не может быть отрицательной")
        self._price = float(value)

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, value: str) -> None:
        self._category = value if value else "Общее"

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, value: int) -> None:
        if value < 0:
            raise ValueError("Остаток не может быть отрицательным")
        self._stock = int(value)

    def to_dict(self) -> dict:
        """Преобразование в словарь для сериализации."""
        return {
            "id": self._id,
            "name": self._name,
            "price": self._price,
            "category": self._category,
            "stock": self._stock,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """Создание объекта из словаря."""
        return cls(
            name=data["name"],
            price=data["price"],
            category=data.get("category", "Общее"),
            stock=data.get("stock", 0),
            product_id=data.get("id"),
        )

    def __str__(self) -> str:
        return f"Товар '{self._name}' (id={self._id}, цена={self._price:.2f} руб.)"


class Client(BaseEntity):
    """
    Класс клиента.

    Parameters
    ----------
    name : str
        ФИО клиента.
    email : str
        Электронная почта.
    phone : str
        Номер телефона.
    city : str, optional
        Город проживания.
    client_id : int, optional
        ID клиента.
    """

    # Регулярные выражения для валидации
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    PHONE_PATTERN = re.compile(
        r"^(\+7|8)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$"
    )

    def __init__(
        self,
        name: str,
        email: str,
        phone: str,
        city: str = "Не указан",
        client_id: Optional[int] = None,
    ):
        super().__init__(client_id)
        self.name = name  # через setter
        self.email = email
        self.phone = phone
        self._city = city

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Имя клиента не может быть пустым")
        self._name = value.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not self.validate_email(value):
            raise ValueError(f"Некорректный email: {value}")
        self._email = value.strip().lower()

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        if not self.validate_phone(value):
            raise ValueError(f"Некорректный номер телефона: {value}")
        self._phone = value.strip()

    @property
    def city(self) -> str:
        return self._city

    @city.setter
    def city(self, value: str) -> None:
        self._city = value if value else "Не указан"

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Проверка email с помощью регулярного выражения.

        Parameters
        ----------
        email : str
            Строка с email.

        Returns
        -------
        bool
            True, если email корректный.
        """
        if not email:
            return False
        return bool(Client.EMAIL_PATTERN.match(email.strip()))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Проверка номера телефона с помощью регулярного выражения.

        Parameters
        ----------
        phone : str
            Строка с номером.

        Returns
        -------
        bool
            True, если номер корректный.
        """
        if not phone:
            return False
        return bool(Client.PHONE_PATTERN.match(phone.strip()))

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "name": self._name,
            "email": self._email,
            "phone": self._phone,
            "city": self._city,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Client":
        return cls(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            city=data.get("city", "Не указан"),
            client_id=data.get("id"),
        )

    def __str__(self) -> str:
        return f"Клиент {self._name} (id={self._id}, {self._email})"


class OrderItem:
    """
    Позиция в заказе (товар + количество).

    Parameters
    ----------
    product : Product
        Товар.
    quantity : int
        Количество.
    """

    def __init__(self, product: Product, quantity: int = 1):
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")
        self.product = product
        self.quantity = quantity

    @property
    def total_price(self) -> float:
        """Стоимость позиции."""
        return self.product.price * self.quantity

    def to_dict(self) -> dict:
        return {
            "product_id": self.product.id,
            "product_name": self.product.name,
            "price": self.product.price,
            "quantity": self.quantity,
            "total": self.total_price,
        }


class Order(BaseEntity):
    """
    Класс заказа.

    Parameters
    ----------
    client : Client
        Клиент, сделавший заказ.
    items : list of OrderItem, optional
        Список позиций заказа.
    order_date : datetime, optional
        Дата заказа.
    status : str, optional
        Статус заказа.
    order_id : int, optional
        ID заказа.
    """

    def __init__(
        self,
        client: Client,
        items: Optional[List[OrderItem]] = None,
        order_date: Optional[datetime] = None,
        status: str = "новый",
        order_id: Optional[int] = None,
    ):
        super().__init__(order_id)
        self.client = client
        self._items: List[OrderItem] = items if items else []
        self._order_date = order_date if order_date else datetime.now()
        self._status = status

    @property
    def items(self) -> List[OrderItem]:
        return self._items

    @property
    def order_date(self) -> datetime:
        return self._order_date

    @order_date.setter
    def order_date(self, value: datetime) -> None:
        self._order_date = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        allowed = {"новый", "в обработке", "отправлен", "доставлен", "отменён"}
        if value not in allowed:
            raise ValueError(f"Недопустимый статус: {value}")
        self._status = value

    def add_item(self, product: Product, quantity: int = 1) -> None:
        """Добавить товар в заказ."""
        for item in self._items:
            if item.product.id == product.id:
                item.quantity += quantity
                return
        self._items.append(OrderItem(product, quantity))

    def remove_item(self, product_id: int) -> bool:
        """Удалить товар из заказа по ID."""
        for i, item in enumerate(self._items):
            if item.product.id == product_id:
                self._items.pop(i)
                return True
        return False

    @property
    def total_amount(self) -> float:
        """Общая стоимость заказа."""
        return sum(item.total_price for item in self._items)

    @property
    def items_count(self) -> int:
        """Количество позиций."""
        return len(self._items)

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "client_id": self.client.id,
            "client_name": self.client.name,
            "order_date": self._order_date.isoformat(),
            "status": self._status,
            "total_amount": self.total_amount,
            "items": [item.to_dict() for item in self._items],
        }

    def __str__(self) -> str:
        return (
            f"Заказ #{self._id} от {self.client.name} "
            f"({self._order_date.strftime('%d.%m.%Y')}) "
            f"на сумму {self.total_amount:.2f} руб. [{self._status}]"
        )


def custom_sort_orders(
    orders: List[Order],
    key: str = "date",
    reverse: bool = False,
) -> List[Order]:
    """
    Собственная сортировка заказов (без встроенного sorted для демонстрации).

    Реализована пузырьковой сортировкой с лямбда-выражениями.

    Parameters
    ----------
    orders : list of Order
        Список заказов.
    key : str
        Ключ сортировки: 'date' или 'amount'.
    reverse : bool
        Сортировка по убыванию.

    Returns
    -------
    list of Order
        Отсортированный список.
    """
    result = orders.copy()
    n = len(result)

    # Лямбда-функции для ключей
    get_key = (
        (lambda o: o.order_date)
        if key == "date"
        else (lambda o: o.total_amount)
    )

    # Пузырьковая сортировка
    for i in range(n):
        for j in range(0, n - i - 1):
            a = get_key(result[j])
            b = get_key(result[j + 1])
            if (a > b and not reverse) or (a < b and reverse):
                result[j], result[j + 1] = result[j + 1], result[j]

    return result


def recursive_sum_amounts(orders: List[Order], index: int = 0) -> float:
    """
    Рекурсивный подсчёт общей суммы всех заказов.

    Parameters
    ----------
    orders : list of Order
        Список заказов.
    index : int
        Текущий индекс (для рекурсии).

    Returns
    -------
    float
        Сумма.
    """
    if index >= len(orders):
        return 0.0
    return orders[index].total_amount + recursive_sum_amounts(orders, index + 1)
