document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('start-btn');
    const targetInput = document.getElementById('target-url');
    const loader = document.getElementById('scan-loader');

    // 1. 提交扫描任务
    startBtn.onclick = async function() {
        const url = targetInput.value;
        if (!url) {
            alert("请先输入目标 URL");
            return;
        }

        const formData = new FormData();
        formData.append('url', url);

        loader.style.display = 'block';
        startBtn.disabled = true;

        try {
            // 使用标准相对路径
            const response = await fetch('/start_scan', {
                method: 'POST',
                body: formData
            });

            // 先检查 HTTP 状态码
            if (!response.ok) {
                throw new Error(`HTTP 错误! 状态码: ${response.status}`);
            }

            const data = await response.json();
            alert(data.msg);
        } catch (err) {
            console.error("提交任务失败:", err);
            alert("任务启动失败: " + err.message);
            loader.style.display = 'none';
            startBtn.disabled = false;
        }
    };

    // 2. 轮询更新状态
    async function updateStatus() {
        try {
            const response = await fetch('/get_status');
            
            // 如果返回的是 HTML (404 页面) 而非 JSON，这里会报错
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                return; // 静默失败，不抛出异常影响界面
            }

            const data = await response.json();

            // 更新 UI 数字
            document.getElementById('queue-count').innerText = data.queue_size;
            document.getElementById('vuln-count').innerText = data.vulns_found;

            // 更新漏洞表格
            const tbody = document.getElementById('vuln-table-body');
            if (data.details && data.details.length > 0) {
                tbody.innerHTML = ''; 
                data.details.forEach(item => {
                    const row = `<tr class="vuln-row">
                        <td><span class="badge bg-danger">${item.type}</span></td>
                        <td class="text-break"><code>${item.url}</code></td>
                        <td><span class="text-muted">${item.param || 'N/A'}</span></td>
                        <td><span class="severity-${item.severity.toLowerCase()}">${item.severity}</span></td>
                    </tr>`;
                    tbody.innerHTML += row;
                });
            }
        } catch (err) {
            console.warn("状态更新轮询中...");
        }
    }

    // 每 2.5 秒更新一次
    setInterval(updateStatus, 2500);
});