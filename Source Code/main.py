from pydantic import BaseModel, Field
from typing import  List
import RAG, loraLLM
import time



name = "陳同學"

student_context = f"""
【基本資料】
- 姓名: 陳同學
- 年級/年齡: 小四乙 / 10歲

【特殊教育需要 (SEN) 狀況】
- 已確診: 輕度智障
- 懷疑/觀察中: 無

【強弱項與性格描述】
- 強弱項:
- 強項 / 潛質 :個性溫和,情緒平穩。願意聽從老師的教導。喜歡攝影、有繪畫天份。母親是全職家庭主婦,樂意與學校合作教導兒子。由於生活接觸面廣,生活常識不錯,對常識科特別感興趣。
- 弱項 / 困難 :上課易分心。喜歡在書簿上畫畫。因認知能力的問題,對學習欠信心。因手肌較弱,不喜歡做一些抄寫的課業。詞彙較少、語言組織能力較弱。學生自覺表達及溝通能力較弱。很少主動與同學交談。影響社交生活。
- 弱項(中文):閱讀能力尚可。能理解文章內的事實性資料。寫作記敘文時內容貧乏。
- 弱項(英文):詞彙少。在提示下尚能明白簡單的指示。
- 弱項(數學):未能處理文字題。

"""

# 印出來檢查看看


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




# ==========================================
# 測試執行
# ==========================================
if __name__ == "__main__":
    start_time = time.time()
    golden_context = RAG.retrieve_context_with_reranking(student_context)
    final_report =loraLLM.generate_final_iep(student_context, golden_context)

    if final_report:
        # 1. 取得排版整齊的 JSON 字串
        json_string = final_report.model_dump_json(indent=2, ensure_ascii=False)
        # print(json_string)

        # 2. 直接從 Pydantic 物件中讀取學生姓名 (假設你的欄位叫做 student_name)
        # 如果你的欄位名稱不同，請自行修改 (例如 final_report.name)

        # 3. 組合動態檔名
        file_name = f"{name}_IEP.json"

        # 4. 存成實體檔案
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(json_string)
            print(f"\n📁 儲存成功！檔案已自動命名並輸出至：{file_name}")

    print("--- %s seconds ---" % (time.time() - start_time))