# 网站嵌入测试

> 来源：特殊场景测试方法
> 更新：2026-04-14

---

## 背景

网站嵌入测试需要写简单的 JS 脚本来完成，以下说明核心步骤和注意事项。

---

## 一、构建侧

1. 发布智能体后，点击"网站嵌入"（L2、L3、L4 都支持）
2. 点击新增网站，推荐按输入：`127.0.0.1:5000` 或 `localhost:5000`
3. 点击完成查看代码，复制 JS 代码备用

---

## 二、调试代码

### 2.1 创建调试项目目录

```
项目文件夹/
├── app.py
└── templates/
    └── index.html
```

### 2.2 启动代理服务

目的：将本地服务调用的接口通过代理转发到测试环境。

#### Python 脚本

```python
from flask import Flask, render_template, request, jsonify
import requests
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# 测试环境地址
TARGET_SERVER = "https://seaf.360.cn:30080/"
# TARGET_SERVER = "http://11.123.252.212:30080/"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    target_url = f"{TARGET_SERVER}/{path}"
    headers = {key: value for key, value in request.headers if key != 'Host'}
    try:
        if request.method == 'GET':
            response = requests.get(target_url, headers=headers, params=request.args, timeout=30)
        elif request.method == 'POST':
            response = requests.post(target_url, headers=headers, params=request.args, data=request.get_data(), timeout=30)
        elif request.method == 'PUT':
            response = requests.put(target_url, headers=headers, data=request.get_data(), timeout=30)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, headers=headers, timeout=30)
        elif request.method == 'OPTIONS':
            response = requests.options(target_url, headers=headers, timeout=30)
        else:
            return jsonify({"error": "Unsupported method"}), 405
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in response.raw.headers.items() if name.lower() not in excluded_headers]
        return (response.content, response.status_code, response_headers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

#### JS 代理示例

```js
// proxy.js
const httpProxy = require("http-proxy");
const finalhandler = require("finalhandler");
const serveStatic = require("serve-static");
const CONFIG = require("./config.js");

function createProxyServer(options = {}) {
  const { port = 5500, staticDir = "./", proxyPath = "/seaf", target = "测试环境地址域名" } = options;
  const proxy = httpProxy.createProxyServer({});
  const serve = serveStatic(staticDir);
  const server = require("http").createServer((req, res) => {
    if (req.url.startsWith(proxyPath)) {
      proxy.web(req, res, { target: target, changeOrigin: true, secure: false });
      return;
    }
    serve(req, res, finalhandler(req, res));
  });
  server.listen(port, () => {
    console.log(`Proxy server running on http://localhost:${port}`);
    console.log(`Proxying ${proxyPath}/* to ${target}`);
  });
  return server;
}

if (require.main === module) { createProxyServer(); }

module.exports = { createProxyServer };
```

### 2.3 HTML 代码示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgentSDK 集成页面</title>
  <style>
    #yourDomId {
      width: 100%;
      height: 1200px;
      border: 1px solid #ccc;
      margin-top: 20px;
    }
    .container { max-width: 1800px; margin: 0 auto; padding: 20px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>AgentSDK 集成示例</h1>
    <div id="yourDomId"></div>
  </div>
  <script src="https://seaf.360.cn:30080/agentSDK.js"></script>
  <script>
    // 复制的 JS 代码放到这里
  </script>
</body>
</html>
```

### 2.4 注意事项

> HTML 中嵌入的 JS 代码中的 **account 需要有当前智能体访问权限**，否则会提示无访问权限。

---

## 三、测试点

### 3.1 智能体状态变更

- 智能体由**已发布 → 未发布**，SDK 调用是否有报错
- 智能体由**已发布 → 已下架**，SDK 调用是否有报错
- 智能体**发布新版本**，SDK 调用内容是否更新
- 智能体由**已发布 → 未发布 → 删除**，SDK 调用是否有报错

### 3.2 对话页基本功能

- 智能体基本信息显示
- 发送与接收消息及对话内容渲染交互（与用户侧一致性）
- 停止对话
- 清除上下文
- 上传文件、图片
- 语音输入

### 3.3 智能体权限

- 当前 account 从**有权限 → 无权限**，SDK 调用是否有报错

---

*最后更新：2026-04-14*
