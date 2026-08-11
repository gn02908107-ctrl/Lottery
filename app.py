import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
from pathlib import Path
import os,random
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="第五屆樂透資料查詢分析系統", layout="wide")

# 資料庫連線
DB_NAME = Path(__file__).parent / "data" / "今彩539.db"

st.title("🏆 第五屆樂透資料查詢分析系統")

if DB_NAME.exists():
    mtime_utc = datetime.fromtimestamp(os.path.getmtime(DB_NAME), tz=timezone.utc)
    mtime_tw = mtime_utc.astimezone(ZoneInfo("Asia/Taipei"))
    st.caption(f"資料每日台灣時間 21:00 自動更新　｜　資料庫最後更新時間：{mtime_tw.strftime('%Y-%m-%d %H:%M')}")
else:
    st.caption("資料每日台灣時間 21:00 自動更新")

# --- 側邊欄：玩法切換 ---
game_mode = st.sidebar.selectbox("請選擇玩法", ["今彩539", "未來擴充玩法..."])


@st.cache_data(ttl=3600)
def load_data(table_name):
    try:
        conn = sqlite3.connect(DB_NAME)
        # 讀取對應的檢視表
        df = pd.read_sql(f'SELECT * FROM v_{table_name}', conn)
        conn.close()
        
        # 確保開獎日期是 datetime 格式，供後續篩選使用
        if '開獎日期' in df.columns:
            df['開獎日期'] = pd.to_datetime(df['開獎日期'])
            
        return df
    except Exception as e:
        st.error(f'資料讀取失敗:{e}')
        return pd.DataFrame()

if game_mode == "今彩539":
    st.subheader("今彩539 歷史開獎資料")
    df = load_data("lotto_539")
    cols_numbers = ["獎號1", "獎號2", "獎號3", "獎號4", "獎號5"]
    
    # 增加防呆：確保有讀取到資料才繼續執行
    if not df.empty:
        
        #------最新一期開獎結果------
        latest = df.sort_values('開獎日期',ascending=False).iloc[0]
        latest_date = latest['開獎日期'].strftime('%Y-%m-%d')
        latest_numbers = '、'.join([f'{int(latest[c]):02d}' for c in cols_numbers])
        
        st.subheader('最新一期開獎結果')
        col1,col2,col3 = st.columns([1,1,2])
        with col1:
            st.metric('開獎日期',latest_date)
        with col2:
            st.metric('期別',latest['期別'])
        with col3:
            st.metric('開獎獎號',latest_numbers)
            
        st.divider()
        
        # --- 側邊欄：日期篩選 ---
        st.sidebar.header("篩選條件")
        min_date = df['開獎日期'].min().date()
        max_date = df['開獎日期'].max().date()
        
        date_range = st.sidebar.date_input(
            "選擇日期範圍",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # 根據日期過濾資料
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df['開獎日期'].dt.date >= start_date) & (df['開獎日期'].dt.date <= end_date)
            filtered_df = df.loc[mask].copy()
        else:
            filtered_df = df.copy()

    # ------區塊 1：號碼出現次數統計與圖表------
        st.divider()
        st.subheader('📊 號碼出現頻率統計')
        cols_numbers = ["獎號1", "獎號2", "獎號3", "獎號4", "獎號5"]   # 統計的欄位
        
        # 平坦化並計算
        all_numbers = [int(n) for n in filtered_df[cols_numbers].values.flatten() if pd.notna(n)]
        
        # 計算出現次數
        freq_series = pd.Series(all_numbers).value_counts()
        
        # 檢查是否有出現0次的號碼
        freq_series = freq_series.reindex(range(1, 40), fill_value=0)
        freq_df = freq_series.sort_index().reset_index()
        freq_df.columns = ['號碼', '出現次數']
        
    #------冷熱號分析------
        col1, col2, col3 = st.columns(3)
        
        # 熱門號碼
        hot_df = freq_df.sort_values(by=['出現次數', '號碼'], ascending=[False, True]).head(5)
        hot_nums = ", ".join([f"{n:02d}" for n in hot_df['號碼']])
        
        # 冷門號碼
        cold_df = freq_df.sort_values(by=['出現次數', '號碼'], ascending=[True, True]).head(5)
        cold_nums = ", ".join([f"{n:02d}" for n in cold_df['號碼']])
        
    #------近五期未開出號碼------
        last_5_df = filtered_df.sort_values('開獎日期', ascending=False).head(5)
        
        # 抓出近五期所有開出號碼，轉為集合
        recent_drawn = set(last_5_df[cols_numbers].values.flatten())
        recent_drawn = {int(x) for x in recent_drawn if pd.notna(x)}
        
        # 找出未出現在近五期內的號碼
        missing_in_recent = [n for n in range(1, 40) if n not in recent_drawn]
        
        # 格式化輸出
        recent_missing_nums = ", ".join([f"{n:02d}" for n in missing_in_recent]) if missing_in_recent else "無"
        actual_periods = len(last_5_df) # 如果使用者選的區間不到 5 期，動態顯示實際期數
        
        with col1:
            st.error(f"**🔥 最熱門號碼**\n\n### {hot_nums}")
        with col2:
            st.info(f"**❄️ 最冷門號碼**\n\n### {cold_nums}")
        with col3:
            st.warning(f"**近 {actual_periods} 期未開出**\n\n{recent_missing_nums}")
            
        st.write("")
            
                
        # 長條圖
        chart = alt.Chart(freq_df).mark_bar().encode(
            x=alt.X('號碼:O', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('出現次數:Q'),
            tooltip=['號碼', '出現次數']
        ).properties(
            height=400
        )
        st.altair_chart(chart, use_container_width=True)
        
        # 顯示統計表格
        with st.expander('查看完整統計數據'):
            st.dataframe(freq_df, use_container_width=True, hide_index=True)
        
    # ------區塊 2：顯示資料表與下載------
        st.divider()
        st.subheader('歷史開獎紀錄')
        
        # 格式化回純字串 (YYYY-MM-DD)
        filtered_df['開獎日期'] = filtered_df['開獎日期'].dt.strftime('%Y-%m-%d')
        
        # 顯示過濾後的資料
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # 下載按鈕
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("下載篩選後的歷史資料 (CSV)", csv, "539_filtered_history.csv", "text/csv")

    # ------區塊 3：幸運號碼小遊戲------
        st.divider()
        st.subheader("🎲 幸運號碼小遊戲")
        st.caption("僅供娛樂，號碼由亂數隨機產生，不代表任何統計預測或中獎保證")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🎰 純隨機抽號（僅供娛樂參考）"):
                lucky_numbers = sorted(random.sample(range(1, 40), 5))
                lucky_str = "、".join([f"{n:02d}" for n in lucky_numbers])
                st.success(f"🍀 你的幸運號碼：{lucky_str}")

        with col_b:
            if st.button("🎰 熱門加權抽號（僅供娛樂參考）"):
                weights = freq_df.set_index('號碼')['出現次數'] + 1
                lucky_numbers = sorted(
                    pd.Series(weights.index).sample(n=5, weights=weights, replace=False)
                )
                lucky_str = "、".join([f"{n:02d}" for n in lucky_numbers])
                st.info(f"🎯 根據歷史熱門度抽出：{lucky_str}")
