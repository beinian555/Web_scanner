# core/crawler/spider_engine.py
import json
import time
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
import redis

class SpiderEngine:
    def __init__(self, start_url):
        self.start_url = start_url.rstrip('/')
        self.domain = urlparse(start_url).netloc
        # 连接 Redis 并设置 decode_responses=True 方便读取字符串
        self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.queue_key = 'vuln_scan_queue'
        self.visited_key = f'visited_urls:{self.domain}'

    def extract_links(self, page):
        """从页面中提取所有属于本站的链接"""
        # 获取所有 a 标签的 href 属性
        links = page.eval_on_selector_all("a[href]", "elements => elements.map(el => el.href)")
        valid_links = []
        for link in links:
            # 转化为绝对路径并去掉末尾斜杠
            full_url = urljoin(page.url, link).split('#')[0].rstrip('/')
            # 只要是同域名的链接就认为有效
            if urlparse(full_url).netloc == self.domain:
                valid_links.append(full_url)
        return list(set(valid_links))

    def run(self):
        """运行爬虫主逻辑"""
        # --- 核心：每次开始前清空 Redis，防止“队列已空” ---
        print("🧹 正在初始化扫描环境，清空旧缓存...")
        self.r.flushall() 

        with sync_playwright() as p:
            # 演示时建议开启 headless=False 可以亲眼看到浏览器在爬
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            print(f"🚀 爬虫启动，目标: {self.start_url}")
            
            # 1. 起始 URL 入队
            self.r.lpush(self.queue_key, json.dumps({"url": self.start_url, "method": "GET"}))

            while True:
                # 2. 从队列获取任务
                task_raw = self.r.rpop(self.queue_key)
                if not task_raw:
                    print("✅ 所有页面已爬取完毕。")
                    break
                
                task = json.loads(task_raw)
                current_url = task['url']

                # 3. 去重检查
                if self.r.sismember(self.visited_key, current_url):
                    continue

                print(f"🔎 正在爬取: {current_url}")
                
                try:
                    page.goto(current_url, wait_until="networkidle", timeout=10000)
                    self.r.sadd(self.visited_key, current_url)

                    # 4. 提取新链接并入队
                    new_links = self.extract_links(page)
                    for link in new_links:
                        if not self.r.sismember(self.visited_key, link):
                            self.r.lpush(self.queue_key, json.dumps({"url": link, "method": "GET"}))
                    
                    print(f"  └─ 发现新链接: {len(new_links)} 个")
                except Exception as e:
                    print(f"  ❌ 爬取失败 {current_url}: {e}")

            browser.close()