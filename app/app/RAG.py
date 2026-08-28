from pydantic import BaseModel, Field
from typing import  List
import os

#Schema-Driven Prompting的架構
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

serverAddress = os.getenv("POSTGRES_SERVER")

from sentence_transformers import SentenceTransformer, CrossEncoder
import psycopg2
from pgvector.psycopg2 import register_vector

# (此處省略你的 IepRow, IepData, QuestionIntent 定義)

def retrieve_context_with_reranking(student_profile: str):
    """
    動態讀取 Schema，利用 pgvector 撈取 Top 15，再用 BGE-Reranker 篩選出最強的 Top 3。
    """
    # 1. 載入兩個不同層級的模型
    print("⏳ 正在載入模型...")
    embed_model = SentenceTransformer('/code/data/SentenceTransformer',local_files_only=True)
    rerank_model = CrossEncoder('/code/data/CrossEncoder',local_files_only=True)

    # 2. 連線資料庫
    conn = psycopg2.connect(dbname="vectordb", user="myuser", password="mypassword", host=serverAddress)
    register_vector(conn)
    cursor = conn.cursor()

    collected_contexts = []

    # 3. 遍歷 Schema 欄位
    for field_name, field_info in IepRow.model_fields.items():
        description = field_info.description

        if "【問題】" in description:
            search_query = f"學生狀況：{student_profile}。{description}"
            print(f"\n🔍 處理欄位 [{field_name}]...")

            # --- 階段一：向量粗篩 (LIMIT 15) ---
            query_vector = embed_model.encode(search_query).tolist()
            cursor.execute("""
                           SELECT source_file, sub_topic, content
                           FROM structured_documents
                           ORDER BY embedding <=> %s::vector
                               LIMIT 15;
                           """, (query_vector,))

            candidates = cursor.fetchall()
            print(f"  -> [粗篩] 從資料庫撈出 {len(candidates)} 筆候選資料。")

            if not candidates:
                continue

            # --- 階段二：Cross-Encoder 精細重排 ---
            pairs = []
            for row in candidates:
                candidate_text = f"分類:{row[1]}。內容:{row[2]}"
                pairs.append([search_query, candidate_text])

            scores = rerank_model.predict(pairs)

            # 將分數與原始資料綁定
            scored_candidates = []
            for i, score in enumerate(scores):
                scored_candidates.append({
                    "source_file": candidates[i][0],
                    "sub_topic": candidates[i][1],
                    "content": candidates[i][2],
                    "rerank_score": float(score)
                })

            # 根據 Re-ranker 給的分數「由高到低」重新排序
            scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

            # --- 階段三：只保留最高分的前 3 名 ---
            # ✨ 修改處 1：確保切片取前 3 筆 (索引 0, 1, 2)
            final_top_3= scored_candidates[:3]

            # ✨ 修改處 2：將 print 訊息修正為「前 3 筆」
            print(f"  -> [重排] 已挑選出最相關的前 3 筆 (最高分: {final_top_3[0]['rerank_score']:.4f})")

            # 格式化寫入黃金上下文
            collected_contexts.append(f"### 關於 [{field_name}] 的參考資料 ###")
            for doc in final_top_3:
                collected_contexts.append(
                    f"- 來源 ({doc['source_file']} - {doc['sub_topic']}) [得分: {doc['rerank_score']:.3f}]:\n  {doc['content']}"
                )
            collected_contexts.append("\n")

    cursor.close()
    conn.close()

    return "\n".join(collected_contexts)
