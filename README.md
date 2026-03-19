## 1. 安装依赖

请确保您的系统环境已安装 Python (建议 3.8+ 版本)。
打开终端进入内层项目主目录，并一键安装 `requirements.txt` 清单中的所有第三方模块：

```bash
cd a2ui_order_system
pip install -r requirements.txt
```

## 2. 配置与启动

依赖安装完毕后，在使用前需要临时配置您的环境 API 密钥。在终端内顺次输入以下命令启动服务：

```cmd
:: 1. 注入 Google AI Studio 中生成的密钥
$env:GEMINI_API_KEY="YOUR_KEY"


:: 2. 运行项目本体
uvicorn main:app --reload
```

当终端出现绿色字样的启动成功提示后，请您直接在浏览器中打开：
获取数据并传回数据演示（点餐）🔗 **http://127.0.0.1:8000/static/index.html** 。


简单传参演示（地铁节点）**http://127.0.0.1:8000**