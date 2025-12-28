import redis

# 1. 连接 Redis (默认地址为 localhost, 端口 6379)
r = redis.Redis(host='localhost', port=6379, db=0)

# 2. 模拟爬虫存入任务 (生产者)
print("爬虫模块：发现新 URL，存入队列...")
r.lpush('scan_tasks', 'http://example.com/login.php?id=1')

# 3. 模拟检测引擎获取任务 (消费者)
task = r.rpop('scan_tasks')
if task:
    print(f"检测引擎：获取到任务 -> {task.decode('utf-8')}")
    print("检测引擎：准备开始 SQL 注入分析...")