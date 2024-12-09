import pandas as pd
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_summary_row(row: pd.Series) -> bool:
    """集計行かどうかを判定する"""
    return pd.isna(row['時間']) or 'end of test' in str(row['時間'])

def extract_time_balance(df: pd.DataFrame) -> pd.DataFrame:
    """時間と残高のデータを抽出して整形する"""
    logger.info("データの抽出を開始")
    
    # 集計行を除外
    df = df[~df.apply(is_summary_row, axis=1)]
    
    # 必要な列のみを選択して列名を変更
    result = df[['時間', '残高']].copy()
    result.columns = ['DateTime', 'Balance']
    
    logger.info(f"抽出完了: {len(result)}行")
    return result

def clean_balance_data(df: pd.DataFrame) -> pd.DataFrame:
    """残高データをクリーニング"""
    logger.info("残高データのクリーニング開始")
    
    # スペースを削除して数値に変換
    df['Balance'] = (df['Balance']
                    .astype(str)
                    .str.replace(' ', '')
                    .astype(float))
    
    return df

def format_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """日時データを整形"""
    logger.info("日時データの整形開始")
    
    # 日時を変換
    df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y.%m.%d %H:%M:%S')
    
    # 重複と欠損値を除去
    df = df.drop_duplicates(subset=['DateTime'])
    df = df.dropna(subset=['DateTime'])
    
    # 時間でソートしてインデックスをリセット
    df = df.sort_values('DateTime')
    df = df.reset_index(drop=True)
    
    # フォーマットを元に戻す
    df['DateTime'] = df['DateTime'].dt.strftime('%Y.%m.%d %H:%M:%S')
    
    return df

def get_output_path(input_path: str) -> str:
    """入力パスから_BDを追加した出力パスを生成する"""
    input_path = Path(input_path)
    # 元のファイル名の拡張子前に_BDを追加
    return str(input_path.parent / f"{input_path.stem}_BD{input_path.suffix}")

def process_csv(file_path: str) -> Optional[pd.DataFrame]:
    """
    CSVファイルから時間と残高のデータを抽出・整形し、15分間隔のデータを生成する
    
    Args:
        file_path: 処理対象のCSVファイルパス
    
    Returns:
        整形済みのDataFrame。エラー時はNone
    """
    try:
        logger.info(f"CSVファイル読み込み開始: {file_path}")
        # CSVファイルを読み込み（日本語列名に対応）
        df = pd.read_csv(file_path)
        logger.info(f"CSVファイル読み込み完了: {len(df)}行")

        # 必要な列のみを抽出
        df = df[['時間', '残高']].copy()
        
        # 列名を英語に変更
        df.columns = ['DateTime', 'Balance']
        
        # 残高の数値変換（スペースを削除）
        df['Balance'] = df['Balance'].astype(str).str.replace(' ', '').astype(float)
        
        # DateTime列を日時型に変換
        df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y.%m.%d %H:%M:%S')
        
        # データを時間順にソート
        df = df.sort_values('DateTime')
        
        # 最初と最後の時間を取得
        start_time = df['DateTime'].min()
        end_time = df['DateTime'].max()
        
        # 15分間隔の時間範囲を生成
        time_range = pd.date_range(
            start=start_time,
            end=end_time,
            freq='15min'
        )
        
        # 新しいデータフレームを作成
        new_df = pd.DataFrame({'DateTime': time_range})
        
        # 元のデータとマージ
        merged_df = pd.merge(new_df, df, on='DateTime', how='left')
        
        # 欠損値を前方補完（直前の値で埋める）
        merged_df['Balance'] = merged_df['Balance'].fillna(method='ffill')
        
        # 必要な列のみを選択
        result_df = merged_df[['DateTime', 'Balance']]
        
        # DateTime列を指定の形式に変換
        result_df['DateTime'] = result_df['DateTime'].dt.strftime('%Y.%m.%d %H:%M:%S')
        
        # 結果を保存
        output_path = get_output_path(file_path)
        result_df.to_csv(output_path, index=False)
        logger.info(f"処理結果を保存しました: {output_path}")
        
        return result_df

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