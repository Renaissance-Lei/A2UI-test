import os
import json
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Client (兼容 Google Gemini 的 API)
client = AsyncOpenAI(
    api_key=os.environ.get("GEMINI_API_KEY", os.environ.get("OPENAI_API_KEY", "sk-placeholder")),
    base_url=os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
)

MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

class ChatRequest(BaseModel):
    text: str

class ExecuteRequest(BaseModel):
    station: str
    crowd_flow: float
    weather: str

SYSTEM_PROMPT = """
你是一个地铁网络韧性测试助手。用户的输入包含测试所需参数。测试必填参数为三个：
1. station (站点, string, 要求必须从 "A站", "B站", "C站", "D站", "E站" 中选择)
2. crowd_flow (人流量, number, 注意单位是“万”。例如提取到“5000人”，则这里的值应该是 0.5；如果是“5万”，则是 5)
3. weather (天气, string, 必须是 "sunny", "heavy_rain", 或 "typhoon")

你需要判断用户输入信息是否包含这三个关键参数。

如果这三个参数都存在并且完整，请严格返回如下格式的 JSON 对象：
{
  "status": "complete",
  "data": {
    "station": "（提取到的站点，如C站）",
    "crowd_flow": （提取到的人数转换成万为单位的数字，如0.5或5）,
    "weather": "（提取到的天气英文名词）"
  }
}

如果参数不完整（缺少任意一个或多个），大模型不能执行测试，需要返回一个状态且携带 google/A2UI 协议的 JSON，包含让前端渲染的表单组件来收集【缺失的参数】。

对于缺失的参数，请在 `components` 中按以下规则生成对应的组件：
- 缺少 station 时，生成 MultipleChoice 组件 (id: "station-choice", 选项为 A站/B站/C站/D站/E站 等)
- 缺少 crowd_flow 时，生成 TextField 组件 (id: "crowdflow-input", label.literalString: "请输入预估人流量 (单位/万)", textFieldType: "number")
- 缺少 weather 时，生成 MultipleChoice 组件 (id: "weather-choice", 选项为 sunny/heavy_rain/typhoon)

你必须包含一个提交按钮 Button (id: "submit-btn")，且 Button 的 action.context 必须包含 key 为 "station", "crowd_flow", "weather" 的三个完整上下文定义。
- 如果用户之前提供了该参数，请直接写为 `{"literalString": "..."}` 或 `{"literalNumber": ...}`。
- 如果是本次通过表单收集的参数，请写为指向那个组件的 path（例如 `{"path": "/station-choice/selections"}`、`{"path": "/crowdflow-input/text"}` 或 `{"path": "/weather-choice/selections"}`）。

请严格输出 JSON 格式（不要包含 markdown 代码块和多余的文字）。
例如如果用户只输入了"我想测试"，三个参数全部缺失，你应该生成类似：
{
  "status": "incomplete",
  "a2ui": [
    { "beginRendering": { "surfaceId": "weather-form", "root": "form-column", "styles": { "primaryColor": "#00BFFF", "font": "sans-serif" } } },
    { "surfaceUpdate": {
        "surfaceId": "weather-form",
        "components": [
          { "id": "form-column", "component": { "Column": { "children": { "explicitList": ["station-choice", "crowdflow-input", "weather-choice", "submit-btn"] } } } },
          { "id": "station-choice", "component": { "MultipleChoice": { "selections": {"literalArray": []}, "options": [ {"label": {"literalString": "A站"}, "value": "A站"}, {"label": {"literalString": "B站"}, "value": "B站"}, {"label": {"literalString": "C站"}, "value": "C站"} ], "maxAllowedSelections": 1 } } },
          { "id": "crowdflow-input", "component": { "TextField": { "label": { "literalString": "人流量估计(万)" }, "textFieldType": "number" } } },
          { "id": "weather-choice", "component": { "MultipleChoice": { "selections": {"literalArray": []}, "options": [ {"label": {"literalString": "晴天(sunny)"}, "value": "sunny"}, {"label": {"literalString": "大雨(heavy_rain)"}, "value": "heavy_rain"}, {"label": {"literalString": "台风(typhoon)"}, "value": "typhoon"} ], "maxAllowedSelections": 1 } } },
          { "id": "submit-btn", "component": { "Button": { "child": "submit-text", "primary": true, "action": { "name": "submit_weather", "context": [ {"key": "station", "value": {"path": "/station-choice/selections"}}, {"key": "crowd_flow", "value": {"path": "/crowdflow-input/text"}}, {"key": "weather", "value": {"path": "/weather-choice/selections"}} ] } } } },
          { "id": "submit-text", "component": { "Text": { "text": {"literalString": "提交参数"} } } }
        ]
    } }
  ]
}
如果用户给了某几个参数，则 components 列表里不要包含对应的输入框，并在 context 对应填入字面量(literal)。
"""

def extract_json_from_text(text: str) -> str:
    # Handle possible markdown wrapping
    match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat")
async def chat_interaction(req: ChatRequest):
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.text}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = extract_json_from_text(response.choices[0].message.content)
        return JSONResponse(content=json.loads(content))
    except json.JSONDecodeError:
        return JSONResponse(status_code=500, content={"error": "解析大模型返回的结果失败，可能是不合法的 JSON"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "msg": "调用模型出错，检查API配置"})

@app.post("/execute")
async def execute_task(req: ExecuteRequest):
    print("=" * 40)
    print(f"✅ 地铁网络韧性测试开始：\n站点: {req.station}\n人流: {req.crowd_flow} 万\n天气: {req.weather}")
    print("=" * 40)
    
    try:
        from metro import run_resilience_test
        # 传入 show_plot=True，这样在前端点击提交时，后端的机器上会直接弹窗展示图形
        result = run_resilience_test(req.station, req.crowd_flow, req.weather, show_plot=True)
        return {
            "message": result["report"],
            "image": "data:image/png;base64," + result["image_b64"],
            "params": req.model_dump()
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"message": f"执行图计算遇到错误: {str(e)}", "image": None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
