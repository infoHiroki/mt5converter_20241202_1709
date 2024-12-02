import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import io
import chardet
import lxml

st.set_page_config(
    page_title="MT5 Data Converter",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def detect_encoding(file_content):
    """ファイルのエンコーディングを検出"""
    result = chardet.detect(file_content)
    return result['encoding']

def convert_html_to_df(html_content):
    """HTMLテーブルをDataFrameに変換"""
    try:
        # 全てのテーブルを読み込む（より寛容なパーサーを使用）
        dfs = pd.read_html(html_content, flavor='lxml', encoding='utf-8', 
                          thousands=',', decimal='.',
                          displayed_only=False)
        
        if dfs:
            # 全てのDataFrameを結合
            df = pd.concat(dfs, ignore_index=True)
            # 重複行を削除
            df = df.drop_duplicates()
            # 空の行を削除
            df = df.dropna(how='all')
            st.info(f"読み込んだデータ: {len(df)}行")
            return df
    except Exception as e:
        st.error(f"テーブル解析エラー: {str(e)}")
        
    # BeautifulSoupを使用したバックアップ方法
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        tables = []
        
        # 全てのテーブル要素を検索
        for table in soup.find_all(['table', 'tbody']):
            rows = []
            for tr in table.find_all('tr'):
                row = []
                for td in tr.find_all(['td', 'th']):
                    # セル内のテキストを取得（改行や空白を整理）
                    cell_text = ' '.join(td.get_text(strip=True, separator=' ').split())
                    row.append(cell_text)
                if row:  # 空でない行のみ追加
                    rows.append(row)
            
            if rows:
                # 最初の行をヘッダーとして使用
                headers = rows[0]
                # データフレームを作成
                df = pd.DataFrame(rows[1:], columns=headers)
                tables.append(df)
        
        if tables:
            # 全てのテーブルを結合
            final_df = pd.concat(tables, ignore_index=True)
            # 重複行を削除
            final_df = final_df.drop_duplicates()
            # 空の行を削除
            final_df = final_df.dropna(how='all')
            st.info(f"読み込んだデータ: {len(final_df)}行")
            return final_df
            
    except Exception as e:
        st.error(f"バックアップ解析エラー: {str(e)}")
    
    return None

st.title("MT5 Data Converter")

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
st.caption("MT5 Data Converter")

# バージョン情報
st.sidebar.markdown("### バージョン情報")
st.sidebar.text("v1.0.0")
st.sidebar.markdown("---")
st.sidebar.markdown("### 開発者情報")
st.sidebar.markdown("MT5 Data Converter Team")
