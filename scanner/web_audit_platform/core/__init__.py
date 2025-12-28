# WebAuditPlatform/core/__init__.py

from .crawler import SpiderEngine
from .detector import run_all_checks
from .utils import TaskQueue, scanner_log

# 这里的封装能让外层 main.py 极简
__all__ = ['SpiderEngine', 'run_all_checks', 'TaskQueue', 'scanner_log']