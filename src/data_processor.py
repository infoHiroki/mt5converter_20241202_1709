import pandas as pd
import logging
from typing import Optional
from pathlib import Path

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
    CSVファイルから時間と残高のデータを抽出・整形し、_BDを付けて保存する
    
    Args:
        file_path: 処理対象のCSVファイルパス
    
    Returns:
        整形済みのDataFrame。エラー時はNone
    """
    try:
        logger.info(f"CSVファイル読み込み開始: {file_path}")
        df = pd.read_csv(file_path)
        logger.info(f"CSVファイル読み込み完了: {len(df)}行")

        # データの抽出と整形を順番に実行
        df = extract_time_balance(df)
        df = clean_balance_data(df)
        df = format_datetime(df)
        
        # 結果を保存
        output_path = get_output_path(file_path)
        df.to_csv(output_path, index=False)
        logger.info(f"処理結果を保存しました: {output_path}")
        
        return df

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