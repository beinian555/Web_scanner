import requests
import redis
import json

class SQLDetector:
    def __init__(self):
        self.headers = {'User-Agent': 'AuditBot/1.0'}
        # 初始化 Redis 连接，用于向前端推送结果
        self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.payloads = [
            ("' AND 1=1 -- ", "' AND 1=2 -- "),
            ("\" AND 1=1 -- ", "\" AND 1=2 -- "),
        ]

    def check(self, url, params=None):
        if not params:
            return False
        
        for param_name in params:
            for true_pay, false_pay in self.payloads:
                test_params_true = params.copy()
                test_params_true[param_name] += true_pay
                
                test_params_false = params.copy()
                test_params_false[param_name] += false_pay

                try:
                    resp_true = requests.get(url, params=test_params_true, headers=self.headers, timeout=5)
                    resp_false = requests.get(url, params=test_params_false, headers=self.headers, timeout=5)

                    # --- 核心判定逻辑 ---
                    if resp_true.text != resp_false.text:
                        # 1. 构造漏洞详情字典
                        finding = {
                            "type": "SQL Injection",
                            "url": url,
                            "param": param_name,
                            "payload": true_pay,
                            "severity": "High"
                        }
                        
                        # 2. 【新增】推送到 Redis 列表，让 app.py 能读取到
                        self.r.lpush("audit_findings", json.dumps(finding))
                        
                        print(f"  [!] 发现 SQL 注入: {url} 参数: {param_name}")
                        return True
                        
                except Exception as e:
                    continue
        return False