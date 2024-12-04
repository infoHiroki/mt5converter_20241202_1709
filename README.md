# MT5バックテストデータ変換ツール

MT5から出力されたHTMLファイルのデータを抽出し、CSVファイルに変換するWebアプリケーションです。

## 機能

- HTMLファイルのドラッグ&ドロップによるアップロード
- テーブルデータの自動抽出
- データ処理オプション
  - 自動（下半分を抽出）
  - 手動で行を選択
- CSVファイルへの変換とダウンロード
- データ行数の表示機能
- 自動エンコーディング検出

## デモ

アプリケーションは以下のURLでアクセスできます：
[AI-Trad Data Converter](https://ai-trad.streamlit.app)

## ローカル開発環境のセットアップ

1. 仮想環境の作成と有効化
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
.\venv\Scripts\activate  # Windows
```

2. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

3. アプリケーションの起動
```bash
streamlit run src/app.py
```

4. ブラウザで以下のURLにアクセス
```
http://localhost:8501
```

## 使用方法

1. HTMLファイルをドラッグ&ドロップ
2. データの自動抽出を確認
3. 処理オプションを選択
   - 自動：下半分のデータを抽出
   - 手動：開始行と終了行を指定
4. 処理結果を確認
5. CSVファイルをダウンロード

## デプロイ手順

1. GitHubにリポジトリを作成

2. Streamlit Cloudにサインイン
   - https://share.streamlit.io/

3. 「New app」をクリック
   - GitHubリポジトリを選択
   - ブランチを選択（main）
   - デプロイするファイルを選択（src/app.py）

4. 「Deploy」をクリック

## 技術スタック

- Python 3.8+
- Streamlit
- pandas
- BeautifulSoup4
- chardet

## ライセンス

MIT License

## 開発者

MT5Converter Team
