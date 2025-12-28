import redis
import json

class TaskQueue:
    def __init__(self, host='localhost', port=6379, db=0):
        # 建立连接池，提高并发效率
        pool = redis.ConnectionPool(host=host, port=port, db=db, decode_responses=True)
        self.r = redis.Redis(connection_pool=pool)
        self.queue_key = 'vuln_scan_queue'

    def push_task(self, url, method='GET', params=None, cookies=None):
        """将扫描任务压入队列"""
        task = {
            "url": url,
            "method": method,
            "params": params or {},
            "cookies": cookies or {}
        }
        # 将字典序列化为字符串存入列表左侧
        return self.r.lpush(self.queue_key, json.dumps(task))

    def pop_task(self):
        """从队列右侧取出一个任务（FIFO：先进先出）"""
        task_raw = self.r.rpop(self.queue_key)
        if task_raw:
            return json.loads(task_raw)
        return None

    def get_queue_size(self):
        """获取当前队列积压的任务数"""
        return self.r.llen(self.queue_key)

    def clear_queue(self):
        """清空所有任务"""
        self.r.delete(self.queue_key)