import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import io
import chardet

st.set_page_config(
    page_title="AI-Trad",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def detect_encoding(file_content):
    """ファイルのエンコーディングを検出"""
    result = chardet.detect(file_content)
    return result['encoding']

def convert_html_to_df(html_content):
    """HTMLテーブルをDataFrameに変換"""
    soup = BeautifulSoup(html_content, 'html.parser')
    # StringIOを使用して警告を回避
    html_io = io.StringIO(str(soup))
    tables = pd.read_html(html_io)
    if tables:
        df = tables[0]
        # 行数を表示（デバッグ用）
        st.info(f"読み込んだデータ: {len(df)}行")
        return df
    return None

st.title("AI-Trad データ変換ツール")

# メインエリア
uploaded_file = st.file_uploader(
    "HTMLファイルをドロップ",
    type=['html', 'htm'],
    help="MT5から出力されたHTMLファイルをドラッグ&ドロップしてください"
)

if uploaded_file:
    try:
        # ファイルの内容を読み込み
        content = uploaded_file.read()
        # エンコーディングを検出
        encoding = detect_encoding(content)
        st.info(f"検出されたエンコーディング: {encoding}")
        # デコード
        html_content = content.decode(encoding)
        df = convert_html_to_df(html_content)
        
        if df is not None:
            # データ分割の選択
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("元データ")
                st.dataframe(df, height=300)
            
            with col2:
                st.subheader("処理オプション")
                process_option = st.radio(
                    "データ処理方法",
                    ["自動（下半分を抽出）", "手動で行を選択"]
                )
                
                half_index = len(df) // 2
                if process_option == "自動（下半分を抽出）":
                    processed_df = df[half_index:].reset_index(drop=True)
                else:
                    start_row = st.number_input("開始行", 0, len(df)-1, half_index)
                    end_row = st.number_input("終了行", start_row, len(df), len(df))
                    processed_df = df[start_row:end_row].reset_index(drop=True)
            
            # 処理結果の表示
            st.subheader("処理結果")
            st.dataframe(processed_df, height=300)
            
            # 出力オプション
            col3, col4 = st.columns(2)
            with col3:
                # CSVダウンロードボタン
                csv = processed_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 CSVをダウンロード",
                    csv,
                    f"converted_{uploaded_file.name.replace('.html', '')}.csv",
                    "text/csv",
                    help="変換したデータをCSVとしてダウンロード"
                )
            
            with col4:
                st.info(f"出力データ: {len(processed_df)}行")
                
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
else:
    st.info("👆 HTMLファイルをドロップしてください")

# フッター
st.markdown("---")
st.caption("AI-Trad Data Converter")

# バージョン情報
st.sidebar.markdown("### バージョン情報")
st.sidebar.text("v1.0.0")
st.sidebar.markdown("---")
st.sidebar.markdown("### 開発者情報")
st.sidebar.markdown("AI-Trad Team")
