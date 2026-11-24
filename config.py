"""Global configuration for High Utility Pattern Mining with Extended FP-Growth."""

from pathlib import Path
from typing import Dict

BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"

PRESET_DATASETS: Dict[str, Dict[str, str]] = {
    "benchmark": {
        "name": "دیتاست استاندارد مرجع UP-Growth (۵ تراکنش - آیتم‌های a تا g)",
        "trans_path": str(DATA_DIR / "benchmark_upgrowth.csv"),
        "profit_path": str(DATA_DIR / "benchmark_upgrowth_profits.csv"),
        "desc": "دیتاست کلاسیک مقالات UP-Growth و IHUP با مقادیر تعداد (Internal Utility) و سود واحد (External Utility)",
        "default_min_util": 30,
    },
    "electronics": {
        "name": "فروشگاه کالای دیجیتال (۸ تراکنش - لپ‌تاپ، مانیتور، لوازم جانبی)",
        "trans_path": str(DATA_DIR / "electronics_store.csv"),
        "profit_path": str(DATA_DIR / "electronics_store_profits.csv"),
        "desc": "نمایش تفاوت سود بالا (مثل لپ‌تاپ و مانیتور) با تکرار بالا (مثل فلش USB و ماوس)",
        "default_min_util": 600,
    },
    "supermarket": {
        "name": "سوپرمارکت و اقلام خوراکی (۸ تراکنش - زعفران، عسل، خشکبار، لبنیات)",
        "trans_path": str(DATA_DIR / "supermarket_utility.csv"),
        "profit_path": str(DATA_DIR / "supermarket_utility_profits.csv"),
        "desc": "تحلیل سبد خرید اقلام لوکس و پرمنفعت در کنار کالاهای پرتکرار روزمره",
        "default_min_util": 220,
    },
}
