# 从当前目录的 spider_engine.py 文件中导入 SpiderEngine 类
from .spider_engine import SpiderEngine

# 定义当外部使用 from core.crawler import * 时，哪些类会被暴露出来
__all__ = ['SpiderEngine']