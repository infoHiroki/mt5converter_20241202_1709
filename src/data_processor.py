import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """データ検証エラーを表すカスタム例外クラス"""
    pass

def validate_csv_structure(df: pd.DataFrame) -> Tuple[int, bool]:
    """
    CSVファイルの構造を検証する関数

    Parameters:
    - df (pd.DataFrame): 検証するデータフレーム

    Returns:
    - Tuple[int, bool]: (開始行のインデックス, 検証結果)

    Raises:
    - DataValidationError: データ構造が無効な場合
    """
    try:
        # "時間"と"残高"データが始まる行を検出
        start_rows = df[(df.iloc[:, 0].astype(str).str.contains('時間', na=False)) & 
                       (df.iloc[:, 11].astype(str).str.contains('残高', na=False))].index

        if len(start_rows) == 0:
            raise DataValidationError("'時間'と'残高'のヘッダーが見つかりません")

        return start_rows[0] + 1, True
    except Exception as e:
        logger.error(f"データ構造の検証中にエラーが発生: {str(e)}")
        raise DataValidationError(f"データ構造の検証に失敗: {str(e)}")

def clean_and_convert_balance(balance_series: pd.Series) -> pd.Series:
    """
    残高データをクリーニングして変換する関数

    Parameters:
    - balance_series (pd.Series): 変換する残高データ

    Returns:
    - pd.Series: 変換された残高データ
    """
    try:
        # 数値以外の文字を削除し、float型に変換
        cleaned = balance_series.astype(str).str.replace(' ', '').str.replace(',', '')
        return pd.to_numeric(cleaned, errors='coerce')
    except Exception as e:
        logger.error(f"残高データの変換中にエラーが発生: {str(e)}")
        raise

def process_csv(file_path: str) -> Optional[str]:
    """
    CSVファイルを処理し、指定された変換を行って新しいCSVファイルに保存する関数。
    
    Features:
    - 指定された列を削除し、"時間"と"残高"のデータを抽出、フォーマットや補完を行う
    - 全ての時刻を15分刻みに丸め、データが15分間隔で揃うように整形
    - 数値データから不要なスペースを削除する
    - エラーハンドリングとログ出力の実装
    
    Parameters:
    - file_path (str): CSVファイルのパス
    
    Returns:
    - Optional[str]: 保存された新しいCSVファイルのパス、エラー時はNone
    """
    try:
        logger.info(f"ファイル処理開始: {file_path}")
        
        # ファイルの存在確認
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        # CSVファイルを読み込む（データ型を明示的に指定）
        df = pd.read_csv(file_path, dtype={0: str, 11: str})
        logger.info(f"ファイル読み込み完了: {len(df)} 行")

        # 指定された列B〜KとMを削除する（0ベースのインデックスで1-10および12）
        columns_to_drop = df.columns[1:11].tolist()
        if len(df.columns) > 12:
            columns_to_drop.append(df.columns[12])
        df_dropped = df.drop(columns=columns_to_drop)
        logger.info("不要な列の削除完了")

        # データ構造の検証
        start_row, is_valid = validate_csv_structure(df_dropped)
        if not is_valid:
            raise DataValidationError("データ構造が無効です")

        # 必要なデータの抽出
        time_balance_info = df_dropped.iloc[start_row:].copy()
        time_balance_info.columns = ['DateTime', 'Balance']
        logger.info("必要なデータの抽出完了")

        # 残高データのクリーニングと変換
        time_balance_info['Balance'] = clean_and_convert_balance(time_balance_info['Balance'])
        logger.info("残高データの変換完了")

        # DateTimeの形式を変換
        time_balance_info['DateTime'] = pd.to_datetime(
            time_balance_info['DateTime'].str.replace('.', '/'), 
            errors='coerce'
        )
        logger.info("日時データの変換完了")

        # 時刻を15分単位に丸める
        time_balance_info['DateTime'] = time_balance_info['DateTime'].dt.round('15min')
        
        # 無効なデータの削除
        time_balance_info = time_balance_info.dropna(subset=['DateTime'])
        time_balance_info = time_balance_info.drop_duplicates(subset=['DateTime'])
        logger.info("データのクリーニング完了")

        # 15分間隔の完全な日付範囲を作成
        date_range = pd.date_range(
            start=time_balance_info['DateTime'].min(),
            end=time_balance_info['DateTime'].max(),
            freq='15T'
        )
        missing_dates = date_range.difference(time_balance_info['DateTime'])
        logger.info(f"欠損している時間帯の数: {len(missing_dates)}")

        # 欠損データの補完
        missing_data = pd.DataFrame({
            'DateTime': missing_dates,
            'Balance': np.nan
        })
        
        # データの結合と整形
        data_combined = pd.concat([time_balance_info, missing_data], ignore_index=True)
        data_combined = data_combined.sort_values(by='DateTime').reset_index(drop=True)
        data_combined['Balance'] = data_combined['Balance'].ffill()
        data_combined = data_combined.drop_duplicates(subset=['DateTime'], keep='first')
        logger.info("データの補完と整形完了")

        # 結果の保存
        output_path = file_path.with_name(f"{file_path.stem}_BD{file_path.suffix}")
        data_combined.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"処理完了。出力ファイル: {output_path}")

        return str(output_path)

    except Exception as e:
        logger.error(f"処理中にエラーが発生: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = process_csv(sys.argv[1])
        if result:
            print(f"処理が完了しました。出力ファイル: {result}")
        else:
            print("処理に失敗しました。")
    else:
        print("使用方法: python data_processor.py <入力CSVファイルパス>")
