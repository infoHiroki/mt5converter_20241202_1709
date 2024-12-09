import re
import pandas as pd
import logging
import os
from pathlib import Path
from typing import Optional, Tuple
import io

class StreamlitLogger:
    def __init__(self):
        self.logs = io.StringIO()
        
    def info(self, message: str):
        self.logs.write(f"INFO: {message}\n")
        
    def error(self, message: str):
        self.logs.write(f"ERROR: {message}\n")
        
    def exception(self, message: str):
        self.logs.write(f"EXCEPTION: {message}\n")
        
    def get_logs(self) -> str:
        return self.logs.getvalue()

logger = StreamlitLogger()

def validate_file_compatibility(h1_filename: str, g2_filename: str) -> bool:
    """
    H1ファイルとG2ファイルの互換性を確認
    
    Args:
        h1_filename: H1ファイルの名前
        g2_filename: G2ファイルの名前
        
    Returns:
        bool: ファイルが互換性を持つ場合はTrue
    """
    def extract_identifiers(filename: str) -> Optional[Tuple[str, str]]:
        """ファイル名からCTとPdを抽出"""
        pattern = r'(?:H1|G2).*?(CT\d+)_(Pd\d+)'
        match = re.search(pattern, filename)
        if match:
            return match.group(1), match.group(2)
        return None
    
    h1_ids = extract_identifiers(h1_filename)
    g2_ids = extract_identifiers(g2_filename)
    
    if not (h1_ids and g2_ids):
        logger.error("ファイル名のパターンが一致しません")
        return False
    
    if h1_ids != g2_ids:
        logger.error(f"CTまたはPdが一致しません: H1={h1_ids}, G2={g2_ids}")
        return False
    
    return True

def generate_h4_filename(h1_filename: str, g2_filename: str) -> str:
    """
    H4ファイル名を生成
    
    Args:
        h1_filename: H1ファイルの名前
        g2_filename: G2ファイルの名前
        
    Returns:
        str: 生成されたH4ファイル名
    """
    h1_parts = Path(h1_filename).stem.split('_')
    g2_parts = Path(g2_filename).stem.split('_')
    
    # FIr*-*部分を取得
    fi_part = next(part for part in g2_parts if part.startswith('FI'))
    
    # H4ファイル名を構築
    output_parts = ['H4'] + h1_parts[1:] + [fi_part]
    return '_'.join(output_parts) + '.csv'

def merge_h1_g2_files(h1_file: str, g2_file: str) -> Tuple[Optional[pd.DataFrame], str]:
    """
    H1ファイルとG2ファイルをマージ
    
    Returns:
        Tuple[DataFrame, str]: (マージしたDataFrame, ログメッセージ)
    """
    try:
        # ファイルの存在確認
        if not os.path.exists(h1_file):
            logger.error(f"H1ファイルが見つかりません: {h1_file}")
            return None, logger.get_logs()
        if not os.path.exists(g2_file):
            logger.error(f"G2ファイルが見つかりません: {g2_file}")
            return None, logger.get_logs()
            
        logger.info("ファイルの読み込みを開始")
        
        # H1ファイルの読み込み
        logger.info(f"H1ファイル読み込み開始: {h1_file}")
        try:
            h1_df = pd.read_csv(h1_file, encoding='utf-8')
        except UnicodeDecodeError:
            logger.info("UTF-8での読み込みに失敗。CP932で試行")
            h1_df = pd.read_csv(h1_file, encoding='cp932')
        
        logger.info(f"H1ファイル読み込み完了: {len(h1_df)}行")
        logger.info(f"H1列: {h1_df.columns.tolist()}")
        
        # G2ファイルの読み込み
        logger.info(f"G2ファイル読み込み開始: {g2_file}")
        try:
            g2_df = pd.read_csv(g2_file, encoding='utf-8')
        except UnicodeDecodeError:
            logger.info("UTF-8での読み込みに失敗。CP932で試行")
            g2_df = pd.read_csv(g2_file, encoding='cp932')
            
        logger.info(f"G2ファイル読み込み完了: {len(g2_df)}行")
        logger.info(f"G2列: {g2_df.columns.tolist()}")
        
        # データの前処理
        logger.info("データの前処理開始")
        
        # H1ファイルの前処理
        if '時間' not in h1_df.columns:
            logger.error("H1ファイルに'時間'列が見つかりません")
            logger.info(f"利用可能な列: {h1_df.columns.tolist()}")
            return None, logger.get_logs()
            
        # G2ファイルの前処理
        if 'Time' not in g2_df.columns:
            logger.error("G2ファイルに'Time'列が見つかりません")
            logger.info(f"利用可能な列: {g2_df.columns.tolist()}")
            return None, logger.get_logs()
        
        # 日時変換
        logger.info("日時変換開始")
        try:
            # H1ファイルの時間列が既にdatetime型の場合はそのまま使用
            if not pd.api.types.is_datetime64_any_dtype(h1_df['時間']):
                h1_df['時間'] = pd.to_datetime(h1_df['時間'])
            
            # G2ファイルの時間列を変換（フォーマットを明示的に指定）
            g2_df['Time'] = pd.to_datetime(g2_df['Time'], format='%Y.%m.%d %H:%M')
        except Exception as e:
            logger.error(f"日時変換でエラー: {str(e)}")
            logger.error(f"H1の時間列サンプル: {h1_df['時間'].head()}")
            logger.error(f"G2のTime列サンプル: {g2_df['Time'].head()}")
            return None, logger.get_logs()
        
        logger.info("データのマージを開始")
        
        # G2ファイルの'Time'列を一時的に保存
        g2_time = g2_df['Time'].copy()
        
        # マージ（時間列をキーとして）
        merged_df = pd.merge(
            h1_df,
            g2_df,
            left_on='時間',
            right_on='Time',
            how='left'
        )
        
        # 重複する'Time'列を削除
        if 'Time' in merged_df.columns:
            merged_df = merged_df.drop('Time', axis=1)
        
        logger.info(f"マージ完了: {len(merged_df)}行")
        logger.info(f"マージ後の列: {merged_df.columns.tolist()}")
        
        # 時間でソート
        merged_df = merged_df.sort_values('時間')
        
        # 時間列を元の形式に戻す
        merged_df['時間'] = merged_df['時間'].dt.strftime('%Y.%m.%d %H:%M:%S')
        
        # 結果の確認
        if len(merged_df) == 0:
            logger.error("マージ結果が0行です")
            return None, logger.get_logs()
            
        return merged_df, logger.get_logs()
        
    except Exception as e:
        logger.error(f"マージ処理でエラーが発生しました: {str(e)}")
        logger.exception(f"詳細なエラー情報: {type(e).__name__}")
        return None, logger.get_logs()