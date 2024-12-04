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
</style>
""", unsafe_allow_html=True)

def detect_encoding(file_content):
    """ファイルのエンコーディングを検出"""
    result = chardet.detect(file_content)
    return result['encoding']

def get_column_names(num_columns):
    """列数に応じて列名を生成"""
    # 基本の列名リスト
    base_columns = ['時間', '約定', '銘柄', 'タイプ', '新規・決済', '数量', '価格', '注文', 
                   '手数料', 'スワップ', '損益', '残高', 'コメント']
    
    # 列数が基本リストより少ない場合は、必要な分だけ使用
    if num_columns <= len(base_columns):
        return base_columns[:num_columns]
    
    # 列数が基本リストより多い場合は、追加の列名を生成
    extra_columns = [f'列{i+1}' for i in range(len(base_columns), num_columns)]
    return base_columns + extra_columns

def convert_html_to_df(html_content):
    """HTMLから1393行目以降のデータを抽出"""
    try:
        dfs = pd.read_html(html_content)
        if dfs:
            # 最も行数の多いテーブルを選択
            main_df = max(dfs, key=len)
            
            # 列名が数字のみの場合、適切な列名を設定
            if all(str(col).isdigit() for col in main_df.columns):
                # 列数に応じて動的に列名を設定
                column_names = get_column_names(len(main_df.columns))
                main_df.columns = column_names
                st.info(f"検出された列数: {len(main_df.columns)}")
            
            # 1393行目以降のデータを抽出
            if len(main_df) >= 1393:
                main_df = main_df.iloc[1392:]  # 1393行目から（0-basedなので1392から）
                
                # 'end of test'までのデータを抽出
                if 'end of test' in main_df.values:
                    end_idx = main_df.apply(lambda x: x.astype(str).str.contains('end of test')).any(axis=1).idxmax()
                    main_df = main_df.iloc[:end_idx]
                
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
            # 列名の表示
            st.subheader("検出された列")
            st.write(", ".join(df.columns.tolist()))
            
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
                    f"converted_{Path(uploaded_file.name).stem}_1393plus.csv",
                    "text/csv"
                )
            else:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer) as writer:
                    output_df.to_excel(writer, index=False)
                st.download_button(
                    "💾 Excelをダウンロード",
                    buffer,
                    f"converted_{Path(uploaded_file.name).stem}_1393plus.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    # フッター
    st.markdown("---")
    st.caption("MT5 Data Converter v1.0.0")

if __name__ == "__main__":
    main()
