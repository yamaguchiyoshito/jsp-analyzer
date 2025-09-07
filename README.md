## JSP 解析ツール (jsp-analyzer)

このリポジトリは、JSP / tag / tagx ファイルを横断して解析し、依存関係・使用状況・複雑度を検出して、CSV / Markdown / JSON形式でレポートを生成する軽量ツールです。

### 主な機能
- JSP / JSPF / .tag / .tagx ファイルの再帰走査
- include（ディレクティブ、`<jsp:include>`、JSTL `c:import`）の抽出と依存グラフ化
- スクリプトレット / EL / JSTL / カスタムタグ / フォーム / セッション等の抽出
- 各ファイルの簡易な複雑度メトリクス算出（行数・スクリプトレット数・EL数 等）
- 依存関係グラフのクラスタリングとプロット出力（networkx / matplotlib）
- CSV / Markdown / JSON / テキスト形式のレポート出力

### 要件
- Python 3.8+（動作確認は Python 3.9 / 3.13 等で行われています）
- 依存パッケージ（詳細は requirements.txt）：
  - networkx
  - beautifulsoup4（HTML の構造解析を改善。未インストールでも最小解析は実行可能）
  - numpy
  - matplotlib
  - pydot
  - javalang（スクリプトレットの AST ベース解析を行う場合に推奨）

### インストール

1. 仮想環境の作成（任意）

````bash
python -m venv .venv
source .venv/bin/activate
````

2. 依存パッケージのインストール

````bash
pip install -r requirements.txt
````

### 使い方

スクリプトは jsp-analyzer.py（実行可能なメインスクリプト）です。基本的な実行例:

````bash
# プロジェクトルートに対して解析を実行し、output/ にレポートを出力
.venv/bin/python jsp-analyzer.py /path/to/your/project

# 出力フォルダを指定して CSV のみ出力
.venv/bin/python jsp-analyzer.py /path/to/your/project -o ./reports -f csv -p myprefix

# 詳細ログを表示
.venv/bin/python jsp-analyzer.py /path/to/your/project -v
````

#### コマンドライン引数
- project_dir: 解析対象のプロジェクトディレクトリ
- -o, --output-dir: レポートの出力ディレクトリ（デフォルト: ./output）
- -f, --format: 出力フォーマット（csv, markdown, json, text, all）。デフォルトは `all`
- -p, --prefix: 出力ファイル名のプレフィックス（デフォルト: jsp_analysis）
- -v, --verbose: 詳細ログ表示

#### 出力ファイル（デフォルトプレフィックス: `jsp_analysis`）
- jsp_analysis.csv — 全ファイルの集計 CSV  
- jsp_analysis.md — 集計 Markdown レポート  
- jsp_analysis.json — JSON レポート  
- jsp_analysis_summary.txt — テキストサマリ  
- jsp_analysis_jsp_calls.csv / .md — JSP 呼び出し関係  
- jsp_analysis_include_usage.csv / .md — include / import の使用状況  
- jsp_analysis_include_graph.png — include 関係のグラフ画像  
- jsp_clusters.png — 依存クラスタのプロット（ある場合）

### 注意点
- BeautifulSoup が未インストールの場合、HTML のパース機能が制限されます。解析開始時に警告が出ますが、基本的な正規表現ベースの抽出は動作します。  
- javalang があると、スクリプトレット内の Java コードに対して AST ベースの簡易解析が行われ、複雑度計算の精度が上がります。無くても動作しますが、一部の詳細メトリクスは簡略化されます。  
- 走査対象はデフォルトでプロジェクト配下の `**/*.jsp, *.jspf, *.tag, *.tagx` です。`build` / `target` / `dist` ディレクトリ配下は除外されます（ただし `WEB-INF/tags` 配下は除外対象から除かれます）。

### テスト

簡単なユニットテストが test_extractors.py にあります。仮想環境を有効化した上で実行してください。

````bash
.venv/bin/python -m pytest -q
````

### トラブルシューティング
- 文字エンコーディングエラー: JSP ファイルは複数のエンコーディング（utf-8, shift-jis, euc-jp, iso-2022-jp, latin-1）で順に読み込みを試みます。読み込めない場合はファイルのエンコーディングを確認してください。  
- matplotlib による画像生成でエラーが出る場合は、ヘッドレス環境ではバックエンドの指定が必要になることがあります: `MPLBACKEND=Agg` を設定して再実行してみてください。

### 開発メモ / 今後の改善案
- スクリプトレット解析をより安全に行うため、Java パーサー連携の拡張（エラーハンドリング、部分コードの補完）  
- HTML 構造解析を強化してフォームやカスタムタグの検出精度を向上  
- 出力結果の Web UI 化（静的サイト生成）

### ライセンス
特に明記がない場合は社内利用向けの簡易ツールとして扱ってください。公開する場合は適切な OSS ライセンスを追加してください。

### お問い合わせ
質問や不具合報告はリポジトリの Issues を利用してください。
