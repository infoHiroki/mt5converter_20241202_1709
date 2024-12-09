import streamlit as st
import pandas as pd
import chardet
import io
import os
import tempfile
from pathlib import Path
from src.data_processor import process_csv
from src.time_utils import round_time_to_nearest_15min
from datetime import datetime
from src.merge_processor import merge_h1_g2_files, validate_file_compatibility, generate_h4_filename

# ページ設定
st.set_page_config(
    page_title="MT5 Data Converter",
    page_icon="📊",
    layout="wide"
)

# MT5データのカラム名定義
MT5_COLUMNS = ['時間', '約定', '銘柄', 'タイプ', '新規・決済', '数量', '価格', '注文', '手数料', 'スワップ', '損益', '残高', 'コメント']

# スタイル定義
st.markdown("""
<style>
    .drop-zone {
        background: rgba(45, 55, 72, 0.1);
        border: 2px dashed rgba(100, 116, 139, 0.2);
        padding: 2rem;
        border-radius: 0.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def detect_encoding(file_content):
    """ファイルのエンコーディングを検出"""
    result = chardet.detect(file_content)
    return result['encoding']

def find_data_start(df):
    """実データの開始行を検索"""
    # "約定"と"時間"が連続する行を探す
    for idx in range(len(df) - 1):
        current_row = df.iloc[idx].astype(str)
        next_row = df.iloc[idx + 1].astype(str)
        if any('約定' in str(val) for val in current_row) and any('時間' in str(val) for val in next_row):
            return idx + 2  # "時間"の行の次から実データ開始
    return 0

def convert_html_to_df(html_content):
    """HTMLから約定データを抽出"""
    try:
        # StringIOオブジェクトを使用してHTMLを読み込む
        html_io = io.StringIO(html_content)
        dfs = pd.read_html(html_io)
        
        if dfs:
            # 最も行数の多いテーブルを選択
            main_df = max(dfs, key=len)
            
            # 実データの開始行を検索
            start_idx = find_data_start(main_df)
            if start_idx > 0:
                # 実データ部分を抽出
                main_df = main_df.iloc[start_idx:]
                
                # カラム名を設定
                main_df.columns = MT5_COLUMNS
                
                # 'end of test'を含む行までのデータを抽出（その行も含める）
                if 'end of test' in main_df.values:
                    end_idx = main_df.apply(lambda x: x.astype(str).str.contains('end of test')).any(axis=1).idxmax()
                    main_df = main_df.iloc[:end_idx + 1]  # +1 で end of test の行も含める
                
                # 'balance'行の除去
                main_df = main_df[~main_df.apply(lambda x: x.astype(str).str.contains('balance', case=False)).any(axis=1)]
                
                return main_df
            
    except Exception as e:
        st.error(f"変換エラー: {str(e)}")
    return None

def show_stats(df):
    """基本統計情報の表示"""
    cols = st.columns(4)
    metrics = [
        ("📊 データ行数", len(df)),
        ("🔄 重複行", df.duplicated().sum()),
        ("📈 数値列数", df.select_dtypes(include=['number']).columns.size),
        ("⚠️ 欠損値数", df.isna().sum().sum())
    ]
    
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, f"{value:,}")

def round_time_column(df):
    """時間列の丸め処理"""
    result_df = df.copy()
    # NaNでない値のみを処理
    mask = pd.notna(result_df['時間'])
    if mask.any():
        try:
            # まず YYYY.MM.DD HH:MM:SS 形式で変換を試みる
            valid_times = pd.to_datetime(result_df.loc[mask, '時間'].astype(str), format='%Y.%m.%d %H:%M:%S')
        except ValueError:
            try:
                # 次に YYYY-MM-DD HH:MM:SS 形式で変換を試みる
                valid_times = pd.to_datetime(result_df.loc[mask, '時間'].astype(str), format='%Y-%m-%d %H:%M:%S')
            except ValueError:
                # どちらの形式でもない場合は一般的な形式で解析を試みる
                valid_times = pd.to_datetime(result_df.loc[mask, '時間'].astype(str))
        
        # 時間を15分単位に丸める
        rounded_times = valid_times.apply(round_time_to_nearest_15min)
        
        # 元の形式を判定して適切な形式で戻す
        if '.' in str(result_df.loc[mask, '時間'].iloc[0]):
            # YYYY.MM.DD HH:MM:SS 形式
            result_df.loc[mask, '時間'] = rounded_times.dt.strftime('%Y.%m.%d %H:%M:%S')
        else:
            # YYYY-MM-DD HH:MM:SS 形式
            result_df.loc[mask, '時間'] = rounded_times.dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return result_df

def main():
    st.title("MT5 Data Converter")
    
    # タブの作成
    tab1, tab2, tab3 = st.tabs(["HTML変換", "時間・残高抽出", "データマージ"])
    
    with tab1:
        # ファイルアップロードエリア
        st.markdown("""
            <div class="drop-zone">
                <h3>📊 MT5ファイルを変換</h3>
                <p>HTMLファイルをドラッグ&ドロップまたはクリックして選択</p>
                <small>対応形式: HTML, HTM</small>
            </div>
        """, unsafe_allow_html=True)
        
        # ファイルアップローダーにラベルを追加
        uploaded_file = st.file_uploader("HTMLファイルを選択", type=['html', 'htm'], label_visibility="collapsed", key="html_uploader")
        
        if uploaded_file:
            content = uploaded_file.read()
            encoding = detect_encoding(content)
            st.info(f"📝 検出されたエンコーディング: {encoding}")
            
            html_content = content.decode(encoding)
            df = convert_html_to_df(html_content)
            
            if df is not None:
                # データ統計
                show_stats(df)
                
                # データプレビュー
                st.subheader("データプレビュー")
                st.dataframe(df, height=400, use_container_width=True)
                
                # 出力オプション
                st.subheader("データ出力")
                
                # 空行削除オプ��ョン
                remove_empty = st.checkbox('空行を削除してダウンロード', True)

                # 時間丸めオプション
                round_time = st.checkbox('時間を15分単位に丸める', False)
                if round_time:
                    try:
                        df = round_time_column(df)
                        st.success("✅ 時間を15分単位に丸めました")
                    except Exception as e:
                        st.error(f"時間の丸め処理でエラーが発生しました: {str(e)}")
                
                output_format = st.selectbox(
                    "出力形式を選択",
                    ["CSV (UTF-8)", "CSV (Shift-JIS)", "Excel"]
                )
                
                # データの処理
                output_df = df.copy()
                if remove_empty:
                    output_df = output_df.dropna(how='all')
                    st.info(f"空行削除後のデータ行数: {len(output_df)}")
                
                # 選択された形式でダウンロードボタンを表示
                if output_format.startswith("CSV"):
                    encoding = 'utf-8-sig' if "UTF-8" in output_format else 'shift-jis'
                    csv = output_df.to_csv(index=False).encode(encoding)
                    # 元のファイル名から先頭2文字を削除してH1を付加
                    output_filename = 'H1' + Path(uploaded_file.name).stem[2:] + '.csv'
                    st.download_button(
                        "💾 CSVをダウンロード",
                        csv,
                        output_filename,
                        "text/csv"
                    )
                else:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer) as writer:
                        output_df.to_excel(writer, index=False)
                    # 元のファイル名から先頭2文字を削除してH1を付加
                    output_filename = 'H1' + Path(uploaded_file.name).stem[2:] + '.xlsx'
                    st.download_button(
                        "💾 Excelをダウンロード",
                        buffer,
                        output_filename,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    with tab2:
        # 時間・残高抽出機能
        st.markdown("""
            <div class="drop-zone">
                <h3>📊 時間・残高データを抽出</h3>
                <p>CSVファイルをドラッグ&ドロップまたはクリックして選択</p>
                <small>対応形式: CSV</small>
            </div>
        """, unsafe_allow_html=True)
        
        csv_file = st.file_uploader("CSVファイルを選択", type=['csv'], key="csv_uploader")
        
        if csv_file:
            # 一時ファイルとして保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(csv_file.getbuffer())
                input_path = tmp_file.name
            
            if st.button('データを抽出'):
                with st.spinner('データを処理中...'):
                    try:
                        # データ処理の実行
                        output_df = process_csv(input_path)
                        
                        if output_df is not None:
                            # 変換結果のダウンロードボタンを表示
                            output_filename = 'H2' + Path(csv_file.name).stem[2:] + '_BD.csv'
                            csv = output_df.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="💾 抽出済みファイルをダウンロード",
                                data=csv,
                                file_name=output_filename,
                                mime='text/csv'
                            )
                            st.success('抽出が完了しました！')
                        else:
                            st.error('処理中にエラーが発生しました。')
                    finally:
                        # 一時ファイルを削除
                        try:
                            os.unlink(input_path)
                        except:
                            pass
    
    with tab3:
        
        # ドロップゾーンのスタイルを統一
        st.markdown("""
            <div class="drop-zone">
                <h3>📊 H1とG2ファイルをマージ</h3>
                <p>CSVファイルをドラッグ&ドロップまたはクリックして選択</p>
                <small>対応形式: CSV</small>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            h1_file = st.file_uploader(
                "H1ファイル",
                type=['csv'],
                key="merge_h1_uploader"
            )
            if h1_file:
                st.success(f"✓ {h1_file.name}")

        with col2:
            g2_file = st.file_uploader(
                "G2ファイル",
                type=['csv'],
                key="merge_g2_uploader"
            )
            if g2_file:
                st.success(f"✓ {g2_file.name}")

        if h1_file and g2_file:
            if st.button("ファイルをマージ", type="primary", use_container_width=True):
                with st.spinner("マージ処理中..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as h1_temp, \
                             tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as g2_temp:
                            h1_temp.write(h1_file.getvalue())
                            g2_temp.write(g2_file.getvalue())
                            
                            merged_df, _ = merge_h1_g2_files(h1_temp.name, g2_temp.name)
                            
                            if merged_df is not None:
                                output_filename = generate_h4_filename(h1_file.name, g2_file.name)
                                st.success("✨ マージが完了しました")
                                
                                with st.expander("データプレビュー"):
                                    st.dataframe(merged_df.head())
                                    st.caption(f"総行数: {len(merged_df):,}行")
                                
                                csv = merged_df.to_csv(index=False).encode('utf-8-sig')
                                st.download_button(
                                    "📥 H4ファイルをダウンロード",
                                    csv,
                                    output_filename,
                                    "text/csv",
                                    use_container_width=True
                                )
                            
                            os.unlink(h1_temp.name)
                            os.unlink(g2_temp.name)
                            
                    except Exception as e:
                        st.error("マージ処理に失敗しました")

    # フッター
    st.markdown("---")
    st.caption("MT5 Data Converter v3.0.0")

if __name__ == "__main__":
    main()
