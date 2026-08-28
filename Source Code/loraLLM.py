# Augmentation and Generation
import json
from datetime import datetime  # ✨ 匯入日期模組
from ollama import Client
from pydantic import BaseModel, Field
from typing import  List

class IepRow(BaseModel):
    category: str = Field(
        description="【問題】請判斷這是哪個領域的目標？（例如：learning, social, personal-growth, emotion）"
    )
    long_term: str = Field(
        description="【問題】根據學生的背景與能力，他需要達成的長期目標是什麼？"
    )
    short_term: str = Field(
        description="【問題】此「短期目標」的預計執行起訖日期。格式為 ['YYYY-MM-DD', 'YYYY-MM-DD']。請根據系統指定的當前學年度時間，設定一個為期約 3 到 6 個月的合理區間。"
    )
    period: List[str] = Field(
        description="【問題】此「短期目標」的預計執行起訖日期。格式必須嚴格為 ['YYYY-MM-DD', 'YYYY-MM-DD']。請根據系統指定的當前學年度時間，設定一個在該學年度範圍內的合理區間。警告：絕對不要加上 'T00:00:00' 等時間標記！"
    )
    methodSchool: str = Field(
        description="【問題】綜合參考文獻與學生現況，學校老師在課堂上應該採取哪 3 項具體的輔導策略？請條列說明。"
    )
    methodParent: str = Field(
        description="【問題】家長在家中可以如何配合支援？請提供 3 項具體建議並條列說明。"
    )
    staff: str = Field(
        description="【問題】這項計畫需要哪些學校人員（如班主任、社工、特教統籌主任）共同參與？"
    )
    assessment: str = Field(
        description="【問題】這項目標將如何進行評估？請寫出具體的評估標準與負責記錄的人員。"
    )
    rationale: str = Field(
        description="【問題】為什麼要制定這個目標與策略？請根據學生的 SEN 狀況與參考文獻，寫出背後的教育理據。"
    )

# 第二層：定義 IEP 陣列
class IepData(BaseModel):
    iep_rows: List[IepRow] = Field(
        description="這是該學生的個別化教育計畫 (IEP) 目標清單，請針對不同領域生成多筆計畫。"
    )

# 第三層：主意圖結構
class QuestionIntent(BaseModel):
    iep: IepData = Field(
        description="最終輸出的 IEP 完整資料結構。"
    )

def generate_final_iep(student_profile: str, golden_context_1: str):
    """
    RAG 最終階段：將精準檢索到的文獻與學生現況進行提示詞增強，並呼叫 LLM 生成結構化 JSON。
    """
    # 1. 取得當前的學年度時間錨點 (動態計算)
    # 假設目前是 2026 年，我們會動態生成：
    # 開始時間: 2026-09-01，結束時間: 2027-06-30
    current_year = datetime.now().year
    next_year = current_year + 1
    current_academic_start = f"{current_year}-09-01"
    current_academic_end = f"{next_year}-06-30"

    client = Client(
        host='http://localhost:11434'
    )

    schema_dict = QuestionIntent.model_json_schema()

    # 2. 在 System Prompt 中加入「時間錨點」與「強制規則」
    system_prompt = f"""
你是一位資深的特殊教育統籌主任。
請根據使用者的需求與提供的參考資料，為學生規劃一份極具專業度的個別化教育計畫 (IEP)。

【🔴 當前學年度時間規則 - 極重要】：
- 系統當前的真實時間是 {current_year} 年。目前的學年度範圍為：{current_academic_start} 至 {current_academic_end}。
- 請根據你設計的 IEP 目標長短（例如：短期目標為期 3~6 個月，長期目標為全學年），合理分配 `period` 的起訖日期。
- 所有的日期都【必須】落在上述的當前學年度範圍內！絕對禁止使用 2023 或 2024 等過去的歷史年份！

【嚴格指令】：
1. 你必須「完全依據」使用者提供給你的「參考資料」來撰寫各個欄位，不得憑空捏造策略。
2. 輸出的格式必須「嚴格遵守」以下的 JSON Schema 定義。
3. 不要輸出任何 Markdown 標記 (例如 ```json 或 ```)。
4. 輸出必須是唯一的、合法的 JSON 字串。
5. 🔴 【強制類別要求】：你必須為這份 IEP 產出至少 4 個不同面向的目標，`iep_rows` 陣列中必須同時包含 `learning`、`social`、`personal-growth` 與 `emotion` 這四個 category，缺一不可！如果參考資料中對某個面向描述較少，請務必根據學生的綜合現況進行專業且合理的推論來補足，確保這四個面向全數產出。

【JSON Schema 定義】：
{json.dumps(schema_dict, ensure_ascii=False, indent=2)}
"""

    # 3. 設計「增強型」用戶提示詞
    user_prompt = f"""
請為以下學生規劃 IEP（執行期間請統一設定為 {current_year} 學年，即 {current_academic_start} 至 {current_academic_end}）：

【學生基本現況】：
{student_profile}

【精準篩選之文獻參考資料 (請務必將以下內容對應填入 JSON 的各個問題欄位中)】：
{golden_context_1}
"""

    print(f"🚀 正在發送至本地 LLM... (已鎖定執行期間為: {current_academic_start} ~ {current_academic_end})")

    response = client.chat(
        model="sen_learning_v3",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        format=schema_dict,
        options={"temperature":0.1}
    )

    raw_json_output = response.message.content
    try:
        validated_iep = QuestionIntent.model_validate_json(raw_json_output)
        print("\n🎉 成功！最終 IEP 報告已生成，並完美通過 Pydantic 格式驗證！")
        return validated_iep
    except Exception as e:
        print("\n❌ 格式驗證失敗！", e)
        return None