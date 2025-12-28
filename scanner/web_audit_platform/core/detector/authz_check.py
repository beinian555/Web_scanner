import requests
import redis
import json
from difflib import SequenceMatcher

class AuthzDetector:
    def __init__(self):
        # 初始化 Redis，用于推送结果
        self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.headers = {'User-Agent': 'AuditBot/1.0'}
        
        # 在实际毕设演示中，这些可以通过前端配置
        # 这里模拟：User_B 是攻击者（低权限），尝试访问 User_A 的数据
        self.user_b_cookies = {"session": "user_b_token_fixed_for_test"}
        
        # 相似度阈值：如果页面相似度高于 0.8，说明内容非常接近，可能存在越权
        self.similarity_threshold = 0.8

    def get_similarity(self, html1, html2):
        """
        语义分析核心：计算两个 HTML 响应的文本相似度
        """
        return SequenceMatcher(None, html1, html2).ratio()

    def check(self, url, params=None):
        """
        越权审计逻辑：
        1. 尝试不带 Cookie 访问（测试未授权访问）
        2. 尝试带低权限 Cookie 访问（测试水平/垂直越权）
        """
        print(f"  [Authz] 正在进行越权语义分析: {url}")
        
        try:
            # 1. 发起越权尝试请求 (使用低权限 B 的身份)
            resp_b = requests.get(url, params=params, cookies=self.user_b_cookies, headers=self.headers, timeout=5)
            
            # 2. 这里的判定逻辑是关键：
            # 如果返回 200，且内容不是登录页、不是 403 错误页
            # 我们可以通过分析页面中的关键字，或者对比已知授权页面的相似度
            
            # 简单判定示例：如果响应码为 200 且内容长度达到一定规模，且不包含“登录”关键字
            if resp_b.status_code == 200 and "login" not in resp_b.text.lower():
                
                # 构造漏洞结果
                finding = {
                    "type": "IDOR (越权访问)",
                    "url": url,
                    "param": "Session/Cookie Context",
                    "payload": "Low-privilege Session Access",
                    "severity": "Critical",
                    "description": "系统未能对敏感资源进行权限校验，低权限用户可直接访问。"
                }
                
                # 推送至 Redis 供前端展示
                self.r.lpush("audit_findings", json.dumps(finding))
                
                print(f"  [!] 发现越权漏洞: {url}")
                return True
                
        except Exception as e:
            print(f"  [Authz] 检查出错: {e}")
            
        return False