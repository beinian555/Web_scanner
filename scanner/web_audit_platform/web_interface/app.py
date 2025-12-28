import sys
import os
import json
import threading
import redis

# --- 1. 自动处理项目路径（防止 Import 报错） ---
# 获取当前文件的绝对路径：.../WebAuditPlatform/web_interface/app.py
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录：.../WebAuditPlatform/
project_root = os.path.dirname(current_dir)
# 将根目录添加到 Python 搜索路径，以便能识别 core 文件夹
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, render_template, request, jsonify

# --- 2. 配置与初始化 ---
app = Flask(__name__)

# 初始化 Redis 连接（确保与探测器中的配置一致）
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 核心：必须与探测器脚本中的 self.r.lpush 目标 Key 保持一致
VULN_RESULTS_KEY = "audit_findings"

# --- 3. 路由定义 ---

@app.route('/')
def index():
    """主页：显示扫描任务控制台"""
    return render_template('index.html')

@app.route('/start_scan', methods=['POST'])
def start_scan():
    """启动扫描任务接口"""
    target_url = request.form.get('url')
    if not target_url:
        return jsonify({"status": "error", "msg": "请输入有效的 URL"})

    # 在启动新扫描前，清空 Redis 中旧的漏洞结果，防止干扰演示
    r.delete(VULN_RESULTS_KEY)
    
    # 异步启动后台审计主进程
    def run_backend():
        try:
            # 延迟导入 main 模块，确保路径已生效
            from main import start_audit_platform
            start_audit_platform(target_url)
        except Exception as e:
            print(f"❌ 后台审计引擎启动失败: {e}")

    # 使用线程池/多线程运行审计引擎，防止网页前端卡死
    audit_thread = threading.Thread(target=run_backend)
    audit_thread.start()
    
    return jsonify({
        "status": "success", 
        "msg": f"已成功启动对 {target_url} 的全自动化审计任务"
    })

@app.route('/get_status')
def get_status():
    """
    实时获取扫描进度与漏洞详情
    前端 JavaScript 会通过定时器轮询这个接口
    """
    try:
        # 从 Redis 获取所有已发现的漏洞结果
        # LRANGE 获取列表所有内容
        raw_vulns = r.lrange(VULN_RESULTS_KEY, 0, -1)
        
        # 将 Redis 中的 JSON 字符串解析回 Python 对象
        vuln_list = []
        for v in raw_vulns:
            try:
                vuln_list.append(json.loads(v))
            except json.JSONDecodeError:
                continue

        # 获取当前爬虫队列的剩余长度（可选，取决于你的 TaskQueue 实现）
        queue_size = r.llen("vuln_scan_queue") # 假设你的 Redis 队列名为此

        return jsonify({
            "status": "running",
            "queue_size": queue_size,
            "vulns_found": len(vuln_list),
            "details": vuln_list  # 这些详情将直接刷在前端表格里
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

# --- 4. 程序入口 ---

if __name__ == '__main__':
    # 0.0.0.0 允许局域网内其他设备访问（如果是虚拟机环境很有用）
    # debug=True 在修改代码后会自动重启 Flask
    print("✨ 自动化审计平台前端已启动：http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)