import os
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import database

from openai import AsyncOpenAI

app = FastAPI()

# Make sure static directory exists
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_event():
    # Initialize DB with table and seed data
    database.init_db()

class ChatRequest(BaseModel):
    message: str

# 使用 OpenAI SDK 兼容接入 Gemini API
client = AsyncOpenAI(
    api_key=os.environ.get("GEMINI_API_KEY", os.environ.get("OPENAI_API_KEY", "sk-placeholder")),
    base_url=os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
)

MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    text = request.message
    
    # 1. Fetch entire menu and pass to LLM for semantic matching
    all_menu = database.get_all_menu()
    menu_str = json.dumps(all_menu, ensure_ascii=False)
    
    system_prompt = f"""
你是一个精通 A2UI (Agent-to-User Interface) 规范的智能点餐助手。
以下是餐厅数据库中的所有菜品：
{menu_str}

用户的需求是："{text}"

【A2UI 动态组件规则】
除了恒定需要的 `number_input` (份数) 和 `text_input` (备注)，你必须根据菜品的实际属性**智能地生成**额外的单选选项：
- 如果是口味重的热炒、海鲜（如川菜、小龙虾等），请生成 "辣度" 选择（如微辣、中辣、特辣）。
- 如果是粥、糖水或甜点，**绝对不要尝试生成辣度！** 你可以灵活地生成 "温度"（如常温、加热）或 "甜度"（如全糖、半糖），或者不生成任何多余选项。
请你：根据需求从菜单中挑选菜品，并根据动态组件规则为您选出的各菜品生成独有的表单控件，最后输出规范 JSON。

【强约束返回格式】
必须严格输出合法的 JSON 格式，且不要包裹在任何 Markdown 语法中。结构要求：
{{
  "action": "render_menu",
  "ui_components": [
    {{
      "type": "item_card",
      "id": "<菜品拼音缩写字母>", 
      "title": "<菜品真实名称>",
      "price": <价格数值>,
      "controls": [
        {{"type": "number_input", "id": "qty_<菜品拼音缩写字母>", "label": "份数", "default": 0}},
        // 请在此处根据上方的“动态组件规则”，智能生成合适的 radio_group 元素。例如如果是粥，绝不能放辣度！
        {{"type": "text_input", "id": "remark_<菜品拼音缩写字母>", "label": "备注"}}
      ]
    }}
  ],
  "submit_button": {{
    "label": "确认下单",
    "action_id": "submit_order"
  }}
}}
务必保证输出的仅仅是一段有效的JSON字符串！
"""

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        reply = response.choices[0].message.content
        
        # 清理可能附带的markdown代码块
        reply = reply.strip()
        if reply.startswith("```json"): reply = reply[7:]
        if reply.startswith("```"): reply = reply[3:]
        if reply.endswith("```"): reply = reply[:-3]
            
        return json.loads(reply)
        
    except Exception as e:
        print(f"Error generating A2UI JSON: {e}")
        return {
            "action": "message",
            "message": f"🤖 **大模型请求报错了**！\n\n**错误代码**：\n```text\n{str(e)}\n```\n(提示：由于底层报错，系统截断了 A2UI 数据生成流程，因此没有返回点单卡片。请检查模型是否配置正确。)"
        }

import datetime

@app.post("/api/submit_order")
async def submit_order(order: dict):
    # 3. Backend Settlement & Console Print
    print("\n" + "="*40)
    print("=== 🌟 收到新订单 🌟 ===")
    print(json.dumps(order, ensure_ascii=False, indent=2))
    print("========================================" + "\n")
    
    # 提取下单菜品名称及份数
    ordered_items = []
    items = order.get("items", [])
    for item in items:
        title = item.get("title", "未知菜品")
        # 动态找出以 qty_ 开头的数量字段
        qty = 0
        for key, value in item.items():
            if key.startswith("qty_"):
                qty = value
                break
        if qty > 0:
            ordered_items.append(f"{title} x {qty}份")
            
    summary_text = "、".join(ordered_items) if ordered_items else "未知菜品"
    
    # 记录到 txt 文件里面
    with open("orders.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] 新订单: {summary_text} | 原始数据: {json.dumps(order, ensure_ascii=False)}\n")
    
    return {"status": "success", "message": f"下单成功！您点了：【{summary_text}】。账单已存档到本地文本中！"}
