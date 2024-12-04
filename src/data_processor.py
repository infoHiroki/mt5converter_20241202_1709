import pandas as pd
from typing import Optional

def process_csv(file_path: str) -> Optional[str]:
    """
    CSVファイルを処理し、指定された変換を行って新しいCSVファイルに保存する関数。
    
    Parameters:
    - file_path (str): CSVファイルのパス
    
    Returns:
    - Optional[str]: 保存された新しいCSVファイルのパス。エラー時はNone
    """
    try:
        # CSVファイルを読み込む
        df = pd.read_csv(file_path)
        
        # 指定された列B〜KとMを削除する（0ベースのインデックスで1-10および12）
        df_dropped = df.drop(columns=df.columns[1:11].tolist() + [df.columns[12]])
        
        # "時間"と"残高"データが始まる行を検出
        start_row = df_dropped[(df_dropped.iloc[:, 0].astype(str).str.contains('時間', na=False)) & 
                               (df_dropped.iloc[:, 1].astype(str).str.contains('残高', na=False))].index[0] + 1
        
        # 検出された行以降の必要な情報を抽出
        necessary_info = df_dropped.iloc[start_row:]
        
        # 必要な列 '時間' (Time) と '残高' (Balance) だけを選択
        time_balance_info = necessary_info.iloc[:, [0, 1]]
        
        # 列名を 'DateTime' と 'Balance' に変更
        time_balance_info.columns = ['DateTime', 'Balance']
        
        # 数値データから不要なスペースを削除し、型を変換
        time_balance_info['Balance'] = time_balance_info['Balance'].astype(str).str.replace(' ', '').astype(float)
        
        # DateTimeの形式を [YYYY.MM.DD hh:mm] から [YYYY/MM/DD hh:mm] に変換
        time_balance_info['DateTime'] = pd.to_datetime(time_balance_info['DateTime'].str.replace('.', '/'), errors='coerce')
        
        # 時刻を15分単位に丸める（最近傍の15分に調整）
        time_balance_info['DateTime'] = time_balance_info['DateTime'].dt.round('15min')
        
        # 重複行とDateTimeの値が欠けている行を削除
        time_balance_info = time_balance_info.drop_duplicates(subset=['DateTime'])
        time_balance_info = time_balance_info.dropna(subset=['DateTime'])
        
        # 15分間隔の完全な日付範囲を作成
        full_date_range = pd.date_range(start=time_balance_info['DateTime'].min(), 
                                      end=time_balance_info['DateTime'].max(), 
                                      freq='15T')
        missing_dates = full_date_range.difference(time_balance_info['DateTime'])
        
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
        
        # 出力ファイル名を入力ファイル名に基づいて「_BD」を追加して保存
        final_output_csv_path = file_path.replace('.csv', '_BD.csv')
        data_combined.to_csv(final_output_csv_path, index=False, encoding='utf-8-sig')
        
        return final_output_csv_path
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return None
