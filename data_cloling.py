"""
IIDX DataをClolingするためのモジュール
"""

import logging
import os
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup


def crawl_iidx_data(iidx_id: str) -> List[List[str]]:
    """指定されたIIDX IDのデータをクローリングして返す

    - HTTPS を使用
    - User-Agent を設定
    - テーブル検出を柔軟に行い、行の長さが不足している場合はパディングする
    """
    logging.basicConfig(level=logging.INFO)
    base_url = f"https://ereter.net/iidxplayerdata/{iidx_id}/level"
    data: List[List[str]] = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        )
    }

    for i in range(1, 13):
        url = f"{base_url}/{i}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
        except requests.RequestException as e:
            logging.warning("Request failed for %s: %s", url, e)
            continue

        if response.status_code != 200:
            logging.warning(
                "Failed to retrieve data from %s (status=%s)",
                url,
                response.status_code,
            )
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        # テーブルクラス名は変わる可能性があるため柔軟に検出する
        table = None
        # try matching common patterns
        table = (
            soup.find("table", class_="table condensed")
            or soup.find("table", class_=["table", "condensed"])
            or soup.find("table")
        )

        if not table:
            logging.debug("No table found on page %s", url)
            # デバッグ用: 環境変数 IIDX_DEBUG_SAVE_HTML=1 がセットされている場合は
            # 取得した HTML をファイルに保存する（公開環境では注意）
            try:
                if os.environ.get("IIDX_DEBUG_SAVE_HTML") == "1":
                    debug_dir = os.path.join(os.getcwd(), "iidx_debug_html")
                    os.makedirs(debug_dir, exist_ok=True)
                    filename = os.path.join(
                        debug_dir, f"debug_{iidx_id}_{i}.html"
                    )
                    with open(filename, "wb") as fh:
                        fh.write(response.content)
                    logging.info("Saved debug HTML to %s", filename)
            except Exception as e:
                logging.warning("Failed to save debug html: %s", e)
            continue

        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            if not cols:
                continue
            text_cols = [col.get_text(strip=True) for col in cols]

            # 期待するカラム数に満たない場合は空文字でパディング
            if len(text_cols) < 6:
                text_cols += [""] * (6 - len(text_cols))

            # 列が多すぎる場合は先頭6列のみを使う
            if len(text_cols) > 6:
                text_cols = text_cols[:6]

            data.append(text_cols)

    return data


def create_iidx_dataframe(data: list) -> pd.DataFrame:
    """クローリングされたデータからDataFrameを作成して返す

    空のデータが来た場合は、期待されるカラム名のみを持つ空のDataFrameを返す。
    また、行の列数が異なる場合にも耐性を持つ。
    """
    column_names = [
        "Level",
        "Title",
        "Rank",
        "Details",
        "Performance",
        "Difficulty",
    ]

    if not data:
        return pd.DataFrame(columns=column_names + ["Details_Number"])

    # 正規化: 各行が正しい長さになるよう調整
    normalized = []
    for row in data:
        r = list(row)
        if len(r) < len(column_names):
            r += [""] * (len(column_names) - len(r))
        elif len(r) > len(column_names):
            r = r[: len(column_names)]
        normalized.append(r)

    df = pd.DataFrame(normalized, columns=column_names)

    # Details カラムが空のときは 0 に置換し、数値列を作る
    df["Details"] = df["Details"].replace("", "0")
    df["Details_Number"] = (
        df["Details"].str.extract(r"(\d+)").fillna(0).astype(int)
    )

    # Rank が空なら大きな数値で埋める
    df["Rank"] = df["Rank"].replace("", "99999")
    # Rank 列に数値変換できない値がある場合に備えて coercion
    df["Rank"] = (
        pd.to_numeric(df["Rank"], errors="coerce").fillna(99999).astype(int)
    )

    df.drop(columns=["Details"], inplace=True)

    return df


def crawl_and_save_iidx_data(iidx_id: str) -> pd.DataFrame:
    """IIDX IDに基づいてデータをクローリングし、Datatableを作成して返す"""
    raw_data = crawl_iidx_data(iidx_id)
    df = create_iidx_dataframe(raw_data)
    return df
