from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <html><body>
        <h1>实验审计靶场</h1>
        <a href="http://127.0.0.1:8000/search?id=1">SQL注入测试点</a><br>
        <a href="http://127.0.0.1:8000/profile?user_id=2">越权测试点</a>
    </body></html>
    """

@app.route('/search')
def search():
    user_id = request.args.get('id', '')
    # 适配 SQLDetector 的真假对比逻辑
    if "1=2" in user_id:
        return "未找到任何结果", 200 # 对应 resp_false
    if "1=1" in user_id or user_id == "1":
        return "查询成功：[Admin] 管理员账号数据", 200 # 对应 resp_true
    return f"普通搜索结果: {user_id}", 200

@app.route('/profile')
def profile():
    user_id = request.args.get('user_id', '')
    # 适配 AuthzDetector 的越权逻辑
    # 只要不是 403 且不含 login，你的探测器就会报漏洞
    if user_id == "1":
        return "这是管理员的私密数据：Secret_Key_888", 200
    return f"这是用户 {user_id} 的普通档案", 200

if __name__ == '__main__':
    app.run(port=8000)