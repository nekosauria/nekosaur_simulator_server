import time
from contextlib import contextmanager


# 計算 cost time
class StepTimer:

    def __init__(self):
        self.costs = {}

    @contextmanager
    def track(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.costs[name] = round(time.perf_counter() - start, 3)