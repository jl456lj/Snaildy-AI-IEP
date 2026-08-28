import json
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

def ingest_json_to_pgvector(json_filepath):
    # 1. 初始化 Embedding 模型
    print("⏳ 正在載入 Embedding 模型 (這可能需要幾秒鐘)...")
    # 使用輕量且支援中文的模型，輸出維度為 768
    model = SentenceTransformer('shibing624/text2vec-base-chinese')

    # 2. 建立資料庫連線
    print("🔗 正在連線到 PostgreSQL...")
    conn = psycopg2.connect(
        dbname="vectordb",
        user="myuser",
        password="mypassword",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    # 確保 vector 擴充套件已啟用，並註冊 pgvector 型別
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)

    # 3. 建立符合我們 JSON 結構的資料表
    print("🏗️ 檢查並建立資料表結構...")

    # 先強制把舊的 VARCHAR 限制表砍掉，確保下方的 TEXT 設定能 100% 被套用
    cursor.execute("DROP TABLE IF EXISTS structured_documents;")
    conn.commit()

    # 建立全新、全 TEXT 化、完全不限字數的強壯資料表
    print("🏭 正在重新建立完美的 TEXT 結構資料表...")
    cursor.execute("""
        CREATE TABLE structured_documents (
            id SERIAL PRIMARY KEY,
            chunk_id TEXT UNIQUE,        -- 升級為 TEXT
            source_file TEXT,            -- 升級為 TEXT
            folder_path TEXT,            -- TEXT
            main_topic TEXT,             -- 升級為 TEXT
            sub_topic TEXT,              -- 升級為 TEXT（徹底解決 255 字限制問題）
            content TEXT,                -- TEXT
            embedding vector(768)
        );
    """)
    conn.commit()
    print("✨ 資料表結構重置成功！")

    # 4. 讀取 JSON 檔案
    print(f"📖 正在讀取切塊資料: {json_filepath}")
    with open(json_filepath, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    total_chunks = len(chunks)
    print(f"總共找到 {total_chunks} 個切塊，準備開始向量化與寫入...")

    # 5. 歷遍資料，轉為向量並寫入資料庫
    success_count = 0

    for i, chunk in enumerate(chunks, 1):
        try:
            # 提取 JSON 欄位
            chunk_id = chunk.get("chunk_id")
            source_file = chunk.get("source_file", "")
            folder_path = chunk.get("folder_path", "")
            main_topic = chunk.get("main_topic", "")
            sub_topic = chunk.get("sub_topic", "")
            content = chunk.get("content", "")

            # 將核心內容 (content) 轉換為 768 維度的數字向量
            vec = model.encode(content)

            # 寫入資料庫
            cursor.execute("""
                INSERT INTO structured_documents 
                (chunk_id, source_file, folder_path, main_topic, sub_topic, content, embedding) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO NOTHING;
            """, (chunk_id, source_file, folder_path, main_topic, sub_topic, content, vec))

            success_count += 1

            # 每處理 10 筆印一次進度
            if i % 10 == 0 or i == total_chunks:
                print(f"  -> 進度: {i} / {total_chunks}")
                conn.commit()

        except Exception as e:
            print(f"⚠️ 處理 {chunk_id} 時發生錯誤: {e}")
            conn.rollback()

    # 最後確保所有交易都已提交
    conn.commit()

    # 6. 關閉連線
    cursor.close()
    conn.close()
    print(f"\n✅ 任務完成！成功寫入 {success_count} 筆資料到資料庫中。")

# ==========================================
# 執行程式
# ==========================================
if __name__ == "__main__":
    ingest_json_to_pgvector("training_dataset.json")