# 都道府県間 転出・転入フローマップ

e-Stat の住民基本台帳人口移動報告（2020〜2025年）をもとに、都道府県間の人口移動差分（転入超過数）をインタラクティブに可視化するデモアプリです。

## デモ

**公開URL**: https://pons-llc.github.io/moving_bi/build/

ローカルで動かす場合：

```bash
cd build && python -m http.server 8080
```

## 機能

- 都道府県セレクター（地図上のドットをクリックでも選択可）
- 年度フィルター（2020〜2025 / 全期間累計）
- 転入超過・転出超過のフロー線（Bezier 曲線、太さ・透明度が人数規模に比例）
- 粒子アニメーション（フロー方向に沿って流れる）
- 転入超過上位 / 転出超過上位ランキング（バーチャート付き）
- 「東京都を除外する」チェックボックス（東京を除いて他県のスケールを再計算）
- フィルターパネル・凡例の折りたたみ（スマホ幅では自動で閉じた状態で起動）

## 技術スタック

| 技術 | 用途 |
|------|------|
| [MapLibre GL JS v4](https://maplibre.org/) | インタラクティブ地図レンダリング |
| 国土地理院タイル (`blank`) | 白地図ベースレイヤー |
| Canvas 2D API | フロー線・矢印・粒子アニメーションのオーバーレイ描画 |
| Bezier 曲線 | 都道府県間フロー線（`quadraticCurveTo`） |
| requestAnimationFrame | 60fps 粒子アニメーションループ |
| [e-Stat API](https://api.e-stat.go.jp/) | 人口移動データ取得（住民基本台帳人口移動報告） |
| FastMCP + Python | e-Stat API を MCP サーバーとして Claude に公開 |

### データ処理の流れ

```
e-Stat API (getStatsData)
  └─ cdCat01: 都道府県コード（01000〜47000）= 転入先
  └─ cdArea:  都道府県コード（01000〜47000）= 転出元
  └─ cdCat02: 60000（総数）
  └─ 転入・転出を年度別に集計
  └─ 差分（net = 転入 − 転出）を算出
  └─ build/index.html に JSON としてインライン埋め込み
```

## 開発背景

このアプリは **Claude Code の `/goal` コマンド1発でほぼワンショット生成**されました。  
プロンプトで仕様を記述し、MCP サーバー経由で e-Stat から実データを取得・加工、単一 HTML ファイルとして出力するまでを自律的に実行しています。

- 使用モデル: Claude Sonnet 4.6
- MCP サーバー: e-Stat API（`server.py`）
- ビルドスクリプト: `build_html.py`（データ取得・HTML 生成）

## セットアップ

```bash
python -m venv venv
source venv/bin/activate
pip install httpx fastmcp python-dotenv pandas
```

### ⚠️ API キーの取り扱い

e-Stat の API キーは **`.env` ファイルに記載**し、Git にはコミットしないでください。

```
# .env
ESTAT_API_KEY=あなたのAPIキー
```

`.gitignore` に必ず追加してください：

```gitignore
.env
.env.*
```

API キーは [e-Stat 利用者登録](https://api.e-stat.go.jp/api-info/) で無料取得できます。  
キーが漏洩した場合は e-Stat の管理画面から即座に無効化してください。

## データ更新・再ビルド

### 新しい年度のデータセット ID を調べる

e-Stat の `getStatsList` API で `surveyYears` を指定すると目的の統計表 ID が取得できます。

```python
import httpx
r = httpx.get('https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList', params={
    'appId': '<YOUR_KEY>',
    'statsCode': '00200523',   # 住民基本台帳人口移動報告の統計調査コード
    'surveyYears': '2026',     # 調べたい年度
    'limit': 20,
})
```

見つかったら `fetch_pref_flows.py` の `DATASETS` 辞書に追記してください。

> **注意**: `getStatsList` の `searchWord` パラメータは日本語キーワードでヒットしないことがあります。  
> `statsCode` + `surveyYears` の組み合わせが確実です。

### e-Stat MCP サーバーの制約

[参考記事](https://note.com/clean_lynx1895/n/n007cdb3dac0c) の MCP サーバー実装は `statsDataId` / `limit` / `startPosition` しか受け付けないため、**`cdCat01`・`cdArea`・`cdCat02` によるフィルタリングができません**。  
47×47 の都道府県マトリクスを効率よく取得するには、`fetch_pref_flows.py` のように e-Stat REST API を直接呼ぶ必要があります。

### データ再取得 → 再ビルド

```bash
python fetch_pref_flows.py       # pref_flows_data.json を更新
python -c "
import json
with open('pref_flows_data.json') as f: data = json.load(f)
mini = {yr: [f for f in flows if f['from']!=f['to']] for yr, flows in data.items()}
import json; open('/tmp/flows_mini.json','w').write(json.dumps(mini, ensure_ascii=False, separators=(',',':')))
"
python build_html.py             # build/index.html を上書き出力
```

## 参考

- [構想元ポスト (X @tsurezure_lab)](https://x.com/tsurezure_lab/status/2056801184737063362?s=20)
- [e-Stat MCP サーバーの解説 (note)](https://note.com/clean_lynx1895/n/n007cdb3dac0c)

## ライセンス

[Apache License 2.0](LICENSE)

## 免責

本アプリはデモ目的で作成されています。データの加工・集計における正確性は保証しません。
