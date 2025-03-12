# 改善されたコード（テストしやすい設計）
from datetime import datetime

def say_hello(name, now=None):
    if now is None:
        now = datetime.now()

    current_hour = now.hour

    if 6 <= current_hour < 10:
        return f"Good morning, {name}!"
    if 10 <= current_hour < 18:
        return f"Hello, {name}!"
    return f"Good evening, {name}!"