from datetime import datetime
import sqlite3
import pandas as pd
import requests
import urllib3
import os
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#檔案路徑
DB_NAME = Path(__file__).resolve().parent / "data" / "今彩539.db"

def fetch_api_data():
    # 使用官方網站API
    url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LastNumber"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print("正在查詢最新開獎號碼...")

    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        data = response.json()

        # 解析 JSON 結構
        content = data.get("content", {})
        last_number_list = content.get("lastNumberList", [])

        if not last_number_list:
            print("API 未回傳任何資料。")
            return None

        target_item = None
        # 從清單中找出 gameCode == 1197 的項目（今彩539）
        for item in last_number_list:
            if str(item.get("gameCode")) == "1197":
                target_item = item
                break

        if not target_item:
            print("找不到今彩539(gameCode: 1197)的資料。")
            return None

        # 取得期別、日期與獎號陣列
        period = target_item.get("period")
        draw_date = target_item.get("drawDate").split("T")[0].split(" ")[0]
        numbers = target_item.get("lotNumber", [])

        if len(numbers) < 5:
            print("獎號數量不足。")
            return None

        # 將獎號進行由小到大排序
        sorted_numbers = sorted([int(n) for n in numbers[:5]])

        parsed_data = [{
            "期別": period,
            "開獎日期": draw_date,
            "獎號1": sorted_numbers[0],
            "獎號2": sorted_numbers[1],
            "獎號3": sorted_numbers[2],
            "獎號4": sorted_numbers[3],
            "獎號5": sorted_numbers[4],
        }]

        return pd.DataFrame(parsed_data)

    except Exception as e:
        print(f"抓取 API 失敗，錯誤訊息：{e}")
        return None

def update_database():
    df = fetch_api_data()
    if df is None or df.empty:
        print("沒有新資料可更新。")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    added_count = 0

    for _, row in df.iterrows():
        try:
            cursor.execute(
                """
                    INSERT INTO lotto_539 (期別, 開獎日期, 獎號1, 獎號2, 獎號3, 獎號4, 獎號5)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["期別"],
                    row["開獎日期"],
                    row["獎號1"],
                    row["獎號2"],
                    row["獎號3"],
                    row["獎號4"],
                    row["獎號5"],
                ),
            )
            added_count += 1
        except sqlite3.IntegrityError:
            print(f"期別 {row['期別']} 已經存在資料庫中，無需重複新增。")

    # 確保檢視表存在
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_lotto_539 AS
        SELECT * FROM lotto_539 ORDER BY 期別 ASC;
    """)

    conn.commit()
    conn.close()
    
    if added_count > 0:
        print(f"✓ 成功補登 {added_count} 筆最新開獎資料到資料庫！")
    else:
        print("✓ 資料已是最新，未新增重複資料。")

if __name__ == "__main__":
    update_database()