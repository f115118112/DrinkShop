# 🧋 茶語時光 點餐小幫手

一個飲料店的線上點餐聊天機器人。顧客可以用自然的對話查菜單、問價格、點飲料，也能查詢或取消訂單；店員可以在「訂單列表」頁面看到所有訂單。

## 使用的技術
- **Tool calling（Agent 呼叫工具）**：Gemini 模型會根據顧客說的話，自己選擇要呼叫哪個工具
- **SQLite 資料庫**：存放菜單（讀取）和訂單（寫入）
- **Gradio**：聊天介面
- **模型**：Gemini（在 `.env` 裡設定，預設 `gemini-3.5-flash-lite`）

## 工具列表
| 工具 | 功能 | 讀/寫 |
|---|---|---|
| `get_menu` | 取得完整菜單和價格 | 讀 |
| `get_drink_price` | 查詢單一飲料價格 | 讀 |
| `place_order` | 建立訂單 | 寫 |
| `get_order` | 用訂單編號查詢訂單 | 讀 |
| `cancel_order` | 取消訂單 | 寫 |

## 檔案說明
- `app.py`：Gradio 介面、系統提示詞、呼叫 Gemini
- `db.py`：資料庫建立、菜單資料、所有工具函式
- `drinks.db`：SQLite 資料庫（第一次執行時自動建立）
- `requirements.txt`：需要安裝的套件
- `.env.example`：環境變數範例

## 執行方式
```bash

# 0. 進入專案資料夾
cd drink-shop

# 1. 安裝套件
pip install -r requirements.txt

# 2. 設定 API key：複製 .env.example 成 .env，再填入你的 key
cp .env.example .env

# 3. 啟動
python app.py
```
啟動後，用瀏覽器打開終端機顯示的網址（通常是 http://127.0.0.1:7860）。

## 對話範例
- 「有什麼飲料？」
- 「葡萄柚綠茶大杯多少錢？」
- 「我叫小明，我要兩杯珍珠奶茶，大杯半糖少冰」
- 「查詢訂單 A001」
- 「幫我取消 A001」
- 「查詢訂單 B9999」→ 回答找不到（不會亂編）

## 資料來源
菜單與價格皆為自行編造的假資料。
