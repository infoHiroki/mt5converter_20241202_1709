import pandas as pd
import logging
from typing import Optional

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_csv(file_path: str) -> Optional[pd.DataFrame]:
    """
    CSVファイルを処理し、指定された変換を行う関数。
    - 指定された列を削除し、"時間"と"残高"のデータを抽出、フォーマットや補完を行う。
    - 全ての時刻を15分刻みに丸め、データが15分間隔で揃うように整形。
    - 数値データから不要なスペースを削除する。
    
    Parameters:
    - file_path (str): CSVファイルのパス
    
    Returns:
    - Optional[pd.DataFrame]: 処理済みのデータフレーム、エラー時はNone
    """
    try:
        # CSVファイルを読み込む
        logger.info(f"CSVファイル読み込み開始: {file_path}")
        df = pd.read_csv(file_path)
        logger.info(f"CSVファイル読み込み完了: {len(df)}行")
        
        # 指定された列B〜KとMを削除する（0ベースのインデックスで1-10および12）
        logger.info("不要な列を削除中...")
        df_dropped = df.drop(columns=df.columns[1:11].tolist() + [df.columns[12]])
        
        # "時間"と"残高"データが始まる行を検出
        logger.info("時間と残高データの開始行を検出中...")
        start_row = df_dropped[(df_dropped.iloc[:, 0].astype(str).str.contains('時間', na=False)) & 
                              (df_dropped.iloc[:, 1].astype(str).str.contains('残高', na=False))].index[0] + 1
        
        # 検出された行以降の必要な情報を抽出
        necessary_info = df_dropped.iloc[start_row:]
        
        # 必要な列 '時間' (Time) と '残高' (Balance) だけを選択
        time_balance_info = necessary_info.iloc[:, [0, 1]]
        
        # 列名を 'DateTime' と 'Balance' に変更
        time_balance_info.columns = ['DateTime', 'Balance']
        logger.info("時間と残高データの抽出完了")
        
        # 数値データから不要なスペースを削除し、型を変換
        logger.info("残高データの変換中...")
        time_balance_info['Balance'] = time_balance_info['Balance'].astype(str).str.replace(' ', '').astype(float)
        
        # DateTimeの形式を [YYYY.MM.DD hh:mm] から [YYYY/MM/DD hh:mm] に変換
        logger.info("日時データの変換中...")
        time_balance_info['DateTime'] = pd.to_datetime(time_balance_info['DateTime'].str.replace('.', '/'), errors='coerce')
        
        # 時刻を15分単位に丸める（最近傍の15分に調整）
        time_balance_info['DateTime'] = time_balance_info['DateTime'].dt.round('15min')
        
        # 重複行とDateTimeの値が欠けている行を削除
        time_balance_info = time_balance_info.drop_duplicates(subset=['DateTime'])
        time_balance_info = time_balance_info.dropna(subset=['DateTime'])
        logger.info("データのクリーニング完了")
        
        # 15分間隔の完全な日付範囲を作成
        full_date_range = pd.date_range(start=time_balance_info['DateTime'].min(), 
                                      end=time_balance_info['DateTime'].max(), 
                                      freq='15T')
        missing_dates = full_date_range.difference(time_balance_info['DateTime'])
        logger.info(f"欠損している時間帯の数: {len(missing_dates)}")
        
        # 欠損日付を含むデータフレームを作成
        missing_data = pd.DataFrame({
            'DateTime': missing_dates,
            'Balance': None
        })
        
        # データの結合と昇順ソート
        data_combined = pd.concat([time_balance_info, missing_data], ignore_index=True)
        data_combined = data_combined.sort_values(by='DateTime').reset_index(drop=True)
        
        # 残高を前回のデータで補完
        data_combined['Balance'] = data_combined['Balance'].ffill()
        
        # 重複行の最終的な削除
        data_combined = data_combined.drop_duplicates(subset=['DateTime'], keep='first')
        logger.info("データの補完と整形完了")
        
        return data_combined

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = process_csv(sys.argv[1])
        if result is not None:
            print("処理が完了しました。")
            print(result.head())
        else:
            print("処理に失敗しました。")
    else:
        print("使用方法: python data_processor.py <入力CSVファイルパス>")
