import logging
import os

def get_logger(name):
    # 创建 logs 目录
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 定义日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 文件处理器：记录到文件
    file_handler = logging.FileHandler(f'logs/{name}.log')
    file_handler.setFormatter(formatter)

    # 控制台处理器：打印到屏幕
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # 避免重复添加处理器
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

# 全局扫描日志
scanner_log = get_logger('scanner')