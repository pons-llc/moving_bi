import os
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

API_KEY = os.getenv("ESTAT_API_KEY")
if not API_KEY:
    raise RuntimeError("ESTAT_API_KEY is not set in .env")

BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json"
CSV_ROOT = Path(os.getenv("ESTAT_CSV_DIR", Path(__file__).parent)).resolve()

mcp = FastMCP("estat")


@mcp.tool
async def search_stats(
    keyword: str,
    limit: int = 20,
    start_position: int = 1,
) -> dict:
    """e-Stat の統計表一覧をキーワードで検索する。

    Args:
        keyword: 検索キーワード（例: "人口", "労働力調査"）。
        limit: 返却件数の上限。
        start_position: 取得開始位置（1始まり）。

    Returns:
        統計表のリスト（STAT_NAME, TITLE, @id など）と総ヒット件数を含む辞書。
    """
    params = {
        "appId": API_KEY,
        "searchWord": keyword,
        "limit": limit,
        "startPosition": start_position,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{BASE_URL}/getStatsList", params=params)
        r.raise_for_status()
        data = r.json()

    list_inf = data.get("GET_STATS_LIST", {})
    result_inf = list_inf.get("RESULT", {})
    if result_inf.get("STATUS", 0) != 0:
        return {"error": result_inf.get("ERROR_MSG", "unknown error"), "raw": result_inf}

    datalist_inf = list_inf.get("DATALIST_INF", {})
    table_inf = datalist_inf.get("TABLE_INF", [])
    if isinstance(table_inf, dict):
        table_inf = [table_inf]

    items = []
    for t in table_inf:
        items.append({
            "id": t.get("@id"),
            "stat_name": (t.get("STAT_NAME") or {}).get("$"),
            "gov_org": (t.get("GOV_ORG") or {}).get("$"),
            "title": (t.get("TITLE") or {}).get("$") if isinstance(t.get("TITLE"), dict) else t.get("TITLE"),
            "survey_date": t.get("SURVEY_DATE"),
            "updated_date": t.get("UPDATED_DATE"),
            "overall_total_number": t.get("OVERALL_TOTAL_NUMBER"),
        })

    return {
        "total": datalist_inf.get("RESULT_INF", {}).get("TOTAL_NUMBER"),
        "from_number": datalist_inf.get("RESULT_INF", {}).get("FROM_NUMBER"),
        "to_number": datalist_inf.get("RESULT_INF", {}).get("TO_NUMBER"),
        "items": items,
    }


@mcp.tool
async def get_stats_data(
    stats_data_id: str,
    limit: int = 100,
    start_position: int = 1,
) -> dict:
    """統計表IDを指定して統計データを取得する。

    Args:
        stats_data_id: 統計表ID（search_stats の `id` フィールド）。
        limit: 取得する値（VALUE）の最大件数。
        start_position: 取得開始位置（1始まり）。

    Returns:
        分類情報（CLASS_OBJ）と数値（VALUE）の配列を含む辞書。
    """
    params = {
        "appId": API_KEY,
        "statsDataId": stats_data_id,
        "limit": limit,
        "startPosition": start_position,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(f"{BASE_URL}/getStatsData", params=params)
        r.raise_for_status()
        data = r.json()

    sd = data.get("GET_STATS_DATA", {})
    result_inf = sd.get("RESULT", {})
    if result_inf.get("STATUS", 0) != 0:
        return {"error": result_inf.get("ERROR_MSG", "unknown error"), "raw": result_inf}

    statistical = sd.get("STATISTICAL_DATA", {})
    table_inf = statistical.get("TABLE_INF", {})
    class_inf = statistical.get("CLASS_INF", {}).get("CLASS_OBJ", [])
    if isinstance(class_inf, dict):
        class_inf = [class_inf]
    data_inf = statistical.get("DATA_INF", {})
    values = data_inf.get("VALUE", [])
    if isinstance(values, dict):
        values = [values]

    return {
        "title": (table_inf.get("TITLE") or {}).get("$") if isinstance(table_inf.get("TITLE"), dict) else table_inf.get("TITLE"),
        "stat_name": (table_inf.get("STAT_NAME") or {}).get("$"),
        "result_total": statistical.get("RESULT_INF", {}).get("TOTAL_NUMBER"),
        "from_number": statistical.get("RESULT_INF", {}).get("FROM_NUMBER"),
        "to_number": statistical.get("RESULT_INF", {}).get("TO_NUMBER"),
        "class_obj": class_inf,
        "values": values,
    }


@mcp.tool
def list_local_csv() -> list[dict]:
    """ローカルの CSV ディレクトリ配下にある CSV ファイル一覧を返す。

    既定では server.py と同じディレクトリ配下を再帰的に走査する。
    環境変数 ESTAT_CSV_DIR で走査ルートを変更できる。

    Returns:
        各ファイルの相対パス、絶対パス、サイズ（バイト）、更新時刻のリスト。
    """
    if not CSV_ROOT.exists():
        return []

    files = []
    for p in sorted(CSV_ROOT.rglob("*.csv")):
        try:
            stat = p.stat()
        except OSError:
            continue
        files.append({
            "relative_path": str(p.relative_to(CSV_ROOT)),
            "absolute_path": str(p),
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
        })
    return files


@mcp.tool
def read_local_csv(
    path: str,
    rows: int = 100,
    encoding: str = "utf-8",
) -> dict:
    """ローカルの CSV ファイルを読み込み、ヘッダと先頭 N 行を返す。

    Args:
        path: 読み込む CSV のパス。相対パスは ESTAT_CSV_DIR 基準。
        rows: 返却する行数（先頭から）。
        encoding: ファイルのエンコーディング。日本語CSVは "cp932" や "shift_jis" を試す。

    Returns:
        columns（列名）、rows（辞書のリスト）、total_rows（全体行数）を含む辞書。
    """
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (CSV_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(CSV_ROOT)
    except ValueError:
        return {"error": f"path is outside CSV root: {CSV_ROOT}"}

    if not candidate.exists():
        return {"error": f"file not found: {candidate}"}

    try:
        df = pd.read_csv(candidate, encoding=encoding)
    except UnicodeDecodeError:
        df = pd.read_csv(candidate, encoding="cp932")

    head = df.head(rows)
    return {
        "path": str(candidate),
        "columns": list(df.columns),
        "total_rows": int(len(df)),
        "rows": head.to_dict(orient="records"),
    }


if __name__ == "__main__":
    mcp.run()
