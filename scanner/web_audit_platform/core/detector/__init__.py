from .sql_check import SQLDetector
from .authz_check import AuthzDetector

# 实例化检测器
sql_engine = SQLDetector()
authz_engine = AuthzDetector()

def run_all_checks(url, params=None, cookies=None):
    """一键运行所有插件"""
    results = []
    if sql_engine.check(url, params):
        results.append("SQL Injection")
    
    # 越权检测通常需要特定逻辑，这里作为示例
    if cookies and authz_engine.check(url, cookies):
        results.append("Broken Access Control")
        
    return results