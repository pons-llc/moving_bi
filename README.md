# 都道府県間 転出・転入フローマップ

e-Stat の住民基本台帳人口移動報告（2020〜2023年）をもとに、都道府県間の人口移動差分（転入超過数）をインタラクティブに可視化するデモアプリです。

## デモ

`build/index.html` をブラウザで開くか、HTTP サーバーで配信してください。

```bash
cd build && python -m http.server 8080
```

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
e-Stat API
  └─ 都道府県コード（XX000）でフィルタリング
  └─ 転入（to=選択県）・転出（from=選択県）を年度別に集計
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

## 再ビルド

データや UI を変更した場合は `build_html.py` を再実行してください。

```bash
python build_html.py
# → build/index.html を上書き出力
```

## 参考

- [構想元ポスト (X @tsurezure_lab)](https://x.com/tsurezure_lab/status/2056801184737063362?s=20)
- [e-Stat MCP サーバーの解説 (note)](https://note.com/clean_lynx1895/n/n007cdb3dac0c)

## ライセンス

[Apache License 2.0](LICENSE)

## 免責

本アプリはデモ目的で作成されています。データの加工・集計における正確性は保証しません。
