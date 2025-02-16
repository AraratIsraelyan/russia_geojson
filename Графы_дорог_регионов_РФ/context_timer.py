import time
from contextlib import contextmanager


@contextmanager
def timer():
    """
    Контекстный менеджер для измерения времени выполнения блока кода.

    Параметры:
    name (str): Название блока кода (по умолчанию "Блок кода").

    Возвращает:
    float: Время выполнения блока в секундах.
    """
    start = time.perf_counter()
    # Возвращаем функцию, которая вычисляет разницу во времени
    yield lambda: time.perf_counter() - start