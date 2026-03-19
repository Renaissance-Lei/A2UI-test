# A2UI Dynamic Order System MVP (Google Gemini Edition)

这是一个基于 Google A2UI (Agent-to-User Interface) 理念设计的最小可行性产品 (MVP)。

系统通过对接官方的 Google Generative AI (Gemini) 大语言模型获取后端数据并感知用户意图，生成具有交互组件的标准化 JSON UI 描述，前端动态解析并渲染原生点餐卡片表单，实现完整的声明式 UI 生成与交互回传逻辑。



- **后端**: Python 3, FastAPI, Pydantic
- **数据库**: SQLite3内置库 (自动建表与注入)
- **模型接入**: 官方 Google Generative AI Python SDK (`google-generativeai`)
- **前端**: HTML + 原生 Vanilla JS，单页应用动态渲染 A2UI 模板

## 运行步骤

1. 安装依赖包：

```bash
pip install fastapi "uvicorn[standard]" pydantic 
```

2. 写入您的 Google Gemini API Key：
在命令行中设置环境变量：
**Windows (CMD/PowerShell)：**
```cmd
$env:GEMINI_API_KEY="YOUR_KEY" 
#填入你的Google Gemini API Key,或者更改其他厂商API接入方式
```


3. 启动服务：
```bash
uvicorn main:app --reload
```

4. 访问并测试系统：
请在浏览器打开本地链接：[http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

**测试聊天用例：**
- 意图匹配：“我想吃海鲜”、“有川菜吗”
- 综合要求：“点一份便宜点的甜点”
