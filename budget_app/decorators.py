import time
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")


# 함수 실행 시간을 측정하여 출력
def measure_time(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start_time = time.perf_counter()

        result = func(*args, **kwargs)

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        print(
            f"[실행 시간] {func.__name__}: "
            f"{elapsed_time:.4f}초"
        )

        return result

    return wrapper