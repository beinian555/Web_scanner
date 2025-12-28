# WebAuditPlatform/main.py

import time
import json
import redis
from urllib.parse import urlparse, parse_qs
from core import SpiderEngine, TaskQueue, scanner_log

# 导入你刚才提供的探测器类
# 注意：请根据你 core 文件夹下的实际文件名进行调整
# 假设路径是 core/detector/sql_check.py 和 authz_check.py
from core.detector.sql_check import SQLDetector
from core.detector.authz_check import AuthzDetector

def run_all_checks(url, params=None):
    """
    封装所有的检测逻辑
    返回发现的漏洞列表
    """
    findings = []
    
    # 1. 实例化探测器
    sql_detector = SQLDetector()
    authz_detector = AuthzDetector()

    # 2. 执行 SQL 注入探测
    # 探测器内部会自动 LPOP 到 audit_findings 队列，这里我们返回布尔值或结果
    if sql_detector.check(url, params):
        findings.append("SQL Injection")

    # 3. 执行越权 (IDOR) 探测
    if authz_detector.check(url, params):
        findings.append("IDOR (越权访问)")

    return findings

def start_audit_platform(target_url):
    scanner_log.info(f"--- 启动自动化审计平台 ---")
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # 1. 初始化
    r.delete("audit_findings") # 清空旧漏洞
    domain = urlparse(target_url).netloc
    visited_key = f"visited_urls:{domain}"
    r.delete(visited_key) # 清空旧资产
    
    # 2. 阶段 1: 爬虫发现资产
    scanner_log.info("阶段 1: 正在进行资产发现 (智能爬虫)...")
    crawler = SpiderEngine(target_url)
    crawler.run() 

    # 3. 阶段 2: 漏洞审计 (核心修改点)
    scanner_log.info("阶段 2: 正在从资产池提取 URL 进行漏洞审计...")
    
    # 【修改】：直接从 Redis 的集合(Set)中获取爬虫抓到的所有唯一链接
    all_urls = r.smembers(visited_key)
    
    vulnerabilities_found = 0
    processed_count = 0

    for current_url in all_urls:
        processed_count += 1
        
        # 解析参数
        parsed = urlparse(current_url)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        scanner_log.info(f"[{processed_count}] 正在审计: {current_url}")

        # 调用检测逻辑
        findings = run_all_checks(base_url, params=params)

        if findings:
            vulnerabilities_found += len(findings)
            for vuln_type in findings:
                scanner_log.warning(f"!!! [发现漏洞] 类型: {vuln_type} | 位置: {current_url}")

    scanner_log.info("--- 审计任务结束 ---")
    scanner_log.info(f"总计审计 URL: {processed_count}")
    scanner_log.info(f"共计发现漏洞: {vulnerabilities_found}")

if __name__ == "__main__":
    # 演示时填入本地靶场地址
    TARGET = "http://127.0.0.1:8000" 
    start_audit_platform(TARGET)