"""
Модуль main.py
==============

Точка входа в программу.

Запуск:
    python main.py

Автор: студент 2 курса
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import Database
from gui import OrderManagementApp


def main() -> None:
    """
    Главная функция запуска приложения.
    """
    try:
        # Путь к БД (Excel) относительно скрипта
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "data", "shop.xlsx")

        db = Database(db_path=db_path)

        # Если база пустая — предлагаем демо-данные (в GUI можно загрузить вручную)
        app = OrderManagementApp(db)
        app.run()
    except Exception as e:
        print(f"Критическая ошибка при запуске: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
