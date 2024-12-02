import streamlit as st
import pandas as pd
import chardet
import io
from pathlib import Path

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
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: rgba(72, 187, 120, 0.1);
        border: 1px solid rgba(72, 187, 120, 0.2);
    }
</style>
""", unsafe_allow_html=True)

def detect_encoding(file_content):
    """ファイルのエンコーディングを検出"""
    result = chardet.detect(file_content)
    return result['encoding']

def convert_html_to_df(html_content):
    """HTMLをDataFrameに変換"""
    try:
        dfs = pd.read_html(html_content)
        if dfs:
            df = pd.concat(dfs)
            return df.dropna(how='all').drop_duplicates()
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
    
    # ファイルアップロードエリア
    st.markdown("""
        <div class="drop-zone">
            <h3>📊 MT5ファイルを変換</h3>
            <p>HTMLファイルをドラッグ&ドロップまたはクリックして選択</p>
            <small>対応形式: HTML, HTM</small>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=['html', 'htm'])
    
    if uploaded_file:
        content = uploaded_file.read()
        encoding = detect_encoding(content)
        st.info(f"📝 検出されたエンコーディング: {encoding}")
        
        html_content = content.decode(encoding)
        df = convert_html_to_df(html_content)
        
        if df is not None:
            # データ統計
            show_stats(df)
            
            # オプション設定（上部に集約）
            col1, col2, col3 = st.columns(3)
            with col1:
                view_mode = st.radio("表示範囲", ["全データ", "上半分", "下半分"])
            with col2:
                process_method = st.radio("処理方法", ["自動（下半分を抽出）", "手動で範囲選択"])
            with col3:
                remove_duplicates = st.checkbox('重複行を除去', True)
                remove_empty = st.checkbox('空行を除去', True)
            
            # データプレビュー（フル幅）
            st.subheader("データプレビュー")
            
            if view_mode == "上半分":
                preview_df = df.iloc[:len(df)//2]
            elif view_mode == "下半分":
                preview_df = df.iloc[len(df)//2:]
            else:
                preview_df = df
            
            st.dataframe(preview_df, height=400, use_container_width=True)
            
            # データ処理
            if process_method == "自動（下半分を抽出）":
                processed_df = df[len(df)//2:].reset_index(drop=True)
            else:
                range_select = st.slider(
                    "データ範囲",
                    0, len(df), (len(df)//2, len(df))
                )
                processed_df = df[range_select[0]:range_select[1]].reset_index(drop=True)
            
            # データクリーニング
            if remove_duplicates:
                processed_df = processed_df.drop_duplicates()
            if remove_empty:
                processed_df = processed_df.dropna(how='all')
            
            # 出力オプション
            col4, col5 = st.columns([1, 2])
            with col4:
                output_format = st.selectbox(
                    "出力形式",
                    ["CSV (UTF-8)", "CSV (Shift-JIS)", "Excel"]
                )
                
                if output_format.startswith("CSV"):
                    encoding = 'utf-8-sig' if "UTF-8" in output_format else 'shift-jis'
                    csv = processed_df.to_csv(index=False).encode(encoding)
                    st.download_button(
                        "💾 変換データをダウンロード",
                        csv,
                        f"converted_{Path(uploaded_file.name).stem}.csv",
                        "text/csv"
                    )
                else:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer) as writer:
                        processed_df.to_excel(writer, index=False)
                    st.download_button(
                        "💾 変換データをダウンロード",
                        buffer,
                        f"converted_{Path(uploaded_file.name).stem}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with col5:
                st.markdown(f"""
                    <div class="success-box">
                        ✅ 処理完了<br>
                        📊 出力データ: {len(processed_df):,}行
                    </div>
                """, unsafe_allow_html=True)
    
    # フッター
    st.markdown("---")
    st.caption("MT5 Data Converter v1.0.0")

if __name__ == "__main__":
    main()