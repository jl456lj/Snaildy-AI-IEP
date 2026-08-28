import json
from pathlib import Path


def extract_chunks_from_json(file_path):
    """
    (核心邏輯) 讀取單一 JSON 檔案並回傳結構化切塊陣列。
    """
    chunks = []
    try:
        # 讀取檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # 歷遍檔案內容進行結構化切塊 (延續之前的邏輯)
        for file_key, file_data in raw_data.items():
            filename = file_data.get("filename", "unknown_file")
            content_obj = file_data.get("content", {})
            main_topic = content_obj.get("主要主題", "未分類主題")
            sections = content_obj.get("全部詳細內容", [])

            for index, section in enumerate(sections):
                sub_topic = section.get("子主題_或_章節名稱", "無標題章節")
                core_points = section.get("詳細核心重點", [])
                strategies = section.get("具體實施策略_與_教學建議", [])
                notes = section.get("注意事項_或_補充細節", [])

                combined_text = ""
                if core_points:
                    combined_text += "【核心重點】" + " ".join(f"- {pt}" for pt in core_points)
                if strategies:
                    combined_text += "【實施策略與建議】" + " ".join(f"- {st}" for st in strategies)
                if notes:
                    combined_text += "【注意事項與補充】" + " ".join(f"- {nt}" for nt in notes)

                if not combined_text.strip():
                    continue

                final_content = f"{combined_text.strip()}"

                chunk ={
                    "main_topic": main_topic,
                    "sub_topic":sub_topic,
                    "content": final_content,
                }
                chunks.append(chunk)

    except Exception as e:
        # 防呆機制：如果遇到毀損的檔案，印出錯誤但不要中斷整個程式
        print(f"⚠️ 解析檔案 {file_path} 時發生錯誤: {e}")

    return chunks


def process_folder_recursively(input_folder, output_filepath):
    """
    (外層掃描) 遞迴遍歷主資料夾及其所有子資料夾，尋找並處理 JSON 檔案。
    """
    all_chunks = []
    input_path = Path(input_folder)

    # 檢查輸入的資料夾是否存在
    if not input_path.exists() or not input_path.is_dir():
        print(f"❌ 錯誤：找不到資料夾 '{input_folder}'")
        return

    # 使用 rglob 遞迴尋找所有以 .json 結尾的檔案
    # 這會自動往下鑽入所有子資料夾
    json_files = list(input_path.rglob('*.json'))
    print(f"🔍 掃描完成！共找到 {len(json_files)} 個 JSON 檔案，準備開始處理...\n")

    # 逐一處理找到的檔案
    for json_file in json_files:
        file_chunks = extract_chunks_from_json(json_file)
        all_chunks.extend(file_chunks)  # 將新切出的區塊加入總陣列

    # 將所有收集到的切塊統一寫入一個輸出檔案
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ 處理完成！共從 {len(json_files)} 個檔案中，生成了 {len(all_chunks)} 個切塊。")


# ==========================================
# 執行範例
# ==========================================
if __name__ == "__main__":
    # 假設你有一個資料夾叫 "my_data"，裡面有很多子資料夾與 JSON 檔
    # 處理完後，把所有的結果彙整成一個巨大的 "all_structured_chunks.json"

    process_folder_recursively(
        input_folder="C:\\Users\\jilon\\OneDrive\\Desktop\\ref_docs",
        output_filepath="training_dataset_1.json"
    )


'''
chunk = {
                    "chunk_id": f"{filename}_section_{index}",
                    "source_file": filename,
                    # 新增：記錄該檔案所在的完整相對或絕對路徑 (包含子資料夾)
                    "folder_path": str(file_path.parent),
                    "main_topic": main_topic,
                    "sub_topic": sub_topic,
                    "content": final_content
                }                
'''