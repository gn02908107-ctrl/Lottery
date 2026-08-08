import sqlite3
from pathlib import Path
import pandas as pd

#-----資料清洗與格式化------
def clean_and_format(df):
    df['開獎日期'] = pd.to_datetime(df['開獎日期']).dt.strftime('%Y-%m-%d')   #統一日期格式
    cols_numbers = ["獎號1", "獎號2", "獎號3", "獎號4", "獎號5"]   #獎號排序
    df[cols_numbers] = df[cols_numbers].apply(pd.to_numeric,errors='coerce')   #獎號轉為數值
    df[cols_numbers] = pd.DataFrame([sorted(x) for x in df[cols_numbers].values],columns=cols_numbers,index=df.index)
    return df

#------資料夾路徑------
base_dir = Path.cwd() / "data"

#------建立連線資料庫------
db_file = base_dir / "今彩539.db"
conn = sqlite3.connect(db_file)

print(f'開始將CSV匯入資料庫:{db_file}...\n')

#------掃描根目錄及資料夾------
for file_path in base_dir.rglob('*'):
    if file_path.is_file() and file_path.suffix == '.csv' and file_path.name != 'lottery.db':   #只處理檔案，跳過.db
        try:
            df = pd.read_csv(file_path,encoding='utf-8-sig',on_bad_lines='warn')  #讀取csv檔案
            cols = ['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5']  #篩選指定欄位
            
            if all(col in df.columns for col in cols):   #檢查檔案是否包含這些欄位
                df = df[cols]
                df = clean_and_format(df)   #清洗資料
                                
                table_name = 'lotto_539'   #所有年份資料寫入'lotto_539'
                
                #------寫入資料庫並合併------
                df.to_sql(table_name,conn,if_exists='append',index=False)
                print(f'成功將{file_path.name}寫入{table_name}')
            else:
                print(f'{file_path.name}缺少必要欄位')
        
        except Exception as e:
            print(f'處理檔案{file_path.name}失敗，錯誤訊息:{e}')
            
#------建立唯一索引------
try:
    cursor = conn.cursor()
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_term ON lotto_539 (期別);')
    conn.commit()
    print('已建立期別防重複機制!')
    
except Exception as e:
    print(f'建立索引時發生錯誤:{e}')
    
#------關閉連線------
conn.close()
print(f'\n匯入完成!資料庫位置:{db_file}')