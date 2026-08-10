[![Update Lottery Data](https://github.com/gn02908107-ctrl/Lottery/actions/workflows/update.yml/badge.svg)](https://github.com/gn02908107-ctrl/Lottery/actions/workflows/update.yml)

# 🏆 今彩539 歷史資料查詢與自動化分析系統

自動化抓取台灣彩券今彩539開獎資料，並提供歷史數據查詢與統計分析的 Streamlit 互動式網頁應用。

DEMO連結：https://lottery-4knzpxaripgubiqm5fxfzz.streamlit.app/

## 專案架構

```
官方網站歷史資料 (下載 + 一次性清洗匯入) ─┐
                                       ├─> SQLite 資料庫 ─> Streamlit 網頁介面
每日新開獎號碼 (爬蟲自動抓取) ───────────┘        ↑
                                          GitHub Actions
                                         (每日定時執行)
```

## 資料來源與建置流程

本專案資料庫由兩個階段建立：

1. **歷史資料初始化（一次性工具，已執行完畢）**：`Lottery_Database.py` 掃描從台彩官網下載的歷史開獎 CSV，清洗、格式化後匯入 SQLite 資料庫。此腳本僅在專案初期執行過一次，之後不再需要，也未納入自動化流程。
2. **每日增量更新（持續運作）**：`Lottery_fetch.py` 呼叫台彩官方 API，抓取最新一期開獎號碼並寫入資料庫，透過 GitHub Actions 排程每日自動執行，確保資料庫維持在最新狀態。

`Lottery_fetch.py` 與 `app.py` 為長期共用同一個 SQLite 資料庫的兩支腳本，皆以腳本自身檔案位置（`Path(__file__).parent`）為基準組出資料庫路徑，確保不論從哪個工作目錄執行，都能正確定位到 `data/今彩539.db`。

## 功能特性

- **自動更新**：GitHub Actions 每日 UTC 16:00（台灣時間 00:00）自動執行爬蟲，補登最新開獎資料。
- **重複資料防呆**：以「期別」作為唯一鍵，避免同一期資料被重複寫入。
- **資料整合**：統一日期格式，並自動將開獎號碼由小到大排序。
- **日期區間篩選**：可自訂日期範圍查詢歷史開獎資料。
- **號碼統計分析**：號碼出現頻率長條圖、熱門／冷門號碼、近期未開出號碼。
- **網頁查詢介面**：透過 Streamlit 瀏覽篩選後的歷史開獎資料，並可下載 CSV。
- **多玩法擴充**：架構預留，未來可擴充大樂透、威力彩等玩法。

## 技術棧

- **資料擷取**：Python、requests（呼叫台彩官方 API）
- **資料處理**：pandas
- **資料庫**：SQLite
- **網頁介面 / 視覺化**：Streamlit、Altair
- **自動化排程**：GitHub Actions

## 使用方式

1. Clone 本專案並安裝依賴套件：
   ```bash
   pip install -r requirements.txt
   ```
2. 啟動網頁介面：
   ```bash
   streamlit run app.py
   ```

## 自動化說明

- Workflow 檔案：`.github/workflows/update.yml`
- 每日透過 GitHub Actions 執行 `Lottery_fetch.py`，抓取最新開獎號碼並寫入資料庫。
- 資料更新後由 Actions 自動 commit 並推送回本 Repository。
- 亦可透過 `workflow_dispatch` 手動觸發執行。

## 已知限制 / TODO

- 目前僅支援今彩539，其餘玩法（大樂透、威力彩）待擴充。
- `Lottery_Database.py` 為一次性歷史資料建置工具，未涵蓋在自動化流程與重複執行的防呆設計內。
- 台彩 API 目前以 `verify=False` 關閉 SSL 憑證驗證，待日後改善為憑證釘選或其他更安全的作法。
