import streamlit as st
import pandas as pd
import chardet
import io
import os
from pathlib import Path
from src.data_processor import process_csv

# ページ設定
st.set_page_config(
    page_title="MT5 Data Converter",
    page_icon="📊",
    layout="wide"
)

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

def find_trade_data_start(df):
    """約定データの開始行を検索"""
    # 各行をチェック
    for idx, row in df.iterrows():
        # 列名に"約定"が含まれている行を探す
        if any('約定' in str(val) for val in row):
            # その行の内容を確認
            row_values = [str(val).strip() for val in row if pd.notna(val)]
            # "約定"という単独の値が含まれているかチェック
            if '約定' in row_values:
                return idx + 1
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
            
            # 約定データの開始行を検索
            start_idx = find_trade_data_start(main_df)
            if start_idx > 0:
                # 約定データ以降を抽出
                main_df = main_df.iloc[start_idx:]
                
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

def main():
    st.title("MT5 Data Converter")

    # タブの作成
    tab1, tab2 = st.tabs(["HTML変換", "CSV変換（15分足）"])
    
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
                
                # 空行削除オプション
                remove_empty = st.checkbox('空行を削除してダウンロード', True)
                
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
                    st.download_button(
                        "💾 CSVをダウンロード",
                        csv,
                        f"converted_{Path(uploaded_file.name).stem}.csv",
                        "text/csv"
                    )
                else:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer) as writer:
                        output_df.to_excel(writer, index=False)
                    st.download_button(
                        "💾 Excelをダウンロード",
                        buffer,
                        f"converted_{Path(uploaded_file.name).stem}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    with tab2:
        # CSV変換機能（15分足）
        st.markdown("""
            <div class="drop-zone">
                <h3>📊 15分足データに変換</h3>
                <p>CSVファイルをドラッグ&ドロップまたはクリックして選択</p>
                <small>対応形式: CSV</small>
            </div>
        """, unsafe_allow_html=True)
        
        csv_file = st.file_uploader("CSVファイルを選択", type=['csv'], key="csv_uploader")
        
        if csv_file:
            # 一時ファイルとして保存
            input_path = f"data/input/{csv_file.name}"
            os.makedirs('data/input', exist_ok=True)
            
            with open(input_path, 'wb') as f:
                f.write(csv_file.getbuffer())
            
            if st.button('15分足データに変換'):
                with st.spinner('データを変換中...'):
                    # データ処理の実行
                    output_path = process_csv(input_path)
                    
                    if output_path and os.path.exists(output_path):
                        # 変換結果のダウンロードボタンを表示
                        with open(output_path, 'rb') as f:
                            st.download_button(
                                label="💾 変換済みファイルをダウンロード",
                                data=f,
                                file_name=os.path.basename(output_path),
                                mime='text/csv'
                            )
                        st.success('変換が完了しました！')
                    else:
                        st.error('変換中にエラーが発生しました。')
    
    # フッター
    st.markdown("---")
    st.caption("MT5 Data Converter v1.0.0")

if __name__ == "__main__":
    main()
