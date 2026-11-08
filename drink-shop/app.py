"""飲料店點餐小幫手：Gradio 聊天介面 + Gemini tool calling。

執行方式：python app.py
"""

import os

import gradio as gr
from dotenv import load_dotenv
from google import genai
from google.genai import types

import db

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """你是「茶語時光」飲料店的線上點餐小幫手，用繁體中文、親切簡短地回答。

規則：
1. 菜單、價格、訂單的資訊，一定要呼叫工具取得，絕對不能自己猜或編造。
2. 工具回傳「找不到」或「沒有」時，要誠實告訴顧客，不要假裝有。
3. 點餐前要問齊：顧客名字、飲料、杯型(M/L)、甜度、冰塊、杯數。
   顧客沒說的項目要問，不要自己決定。
4. 下單前先把內容和總價複述一次，等顧客說「確認」或「好」之後才呼叫 place_order。
5. 下單成功後，告訴顧客訂單編號和總價。
6. 只回答和本店點餐有關的問題。其他問題（例如天氣、寫作業）請禮貌地說你只能幫忙點飲料。
"""

config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=db.TOOLS,  # SDK 會自動執行模型選擇的函式，再把結果交回模型
)


def chat(message, history):
    # 把 Gradio 的對話紀錄轉成 Gemini 的格式
    contents = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=str(turn["content"]))]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    try:
        response = client.models.generate_content(
            model=MODEL, contents=contents, config=config
        )
        return response.text or "抱歉，我沒有聽懂，可以再說一次嗎？"
    except Exception as e:
        return f"系統發生錯誤：{e}"


ORDER_HEADERS = ["訂單編號", "顧客", "飲料", "杯型", "甜度", "冰塊", "杯數", "總價", "狀態", "時間"]

with gr.Blocks(title="茶語時光 點餐小幫手") as demo:
    gr.Markdown("# 🧋 茶語時光 點餐小幫手\n查菜單、點飲料、查詢或取消訂單，都可以直接問我！")

    with gr.Tab("點餐聊天"):
        gr.ChatInterface(
            fn=chat,
            type="messages",
            examples=["有什麼飲料？", "珍珠奶茶大杯多少錢？", "我要點一杯飲料", "查詢訂單 A001"],
        )

    with gr.Tab("訂單列表（店員用）"):
        table = gr.Dataframe(headers=ORDER_HEADERS, value=db.list_orders, interactive=False)
        gr.Button("重新整理").click(fn=db.list_orders, outputs=table)

if __name__ == "__main__":
    db.init_db()
    demo.launch()
