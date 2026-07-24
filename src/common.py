# -*- coding: utf-8 -*-
"""共通ユーティリティ: パス解決・日本語フォント設定・データ整形。

全スクリプトはここを経由することで、実行環境（OS・作業ディレクトリ）に
依存せず再現できるようにしている。
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import pandas as pd
from matplotlib import font_manager

matplotlib.use("Agg")  # 画面を開かずファイル出力に徹する

# Windows コンソールでの文字化け回避（対応環境のみ）
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

# ---- パス（このファイルの位置から相対解決。ハードコード絶対パス禁止）----
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_RAW: Path = PROJECT_ROOT / "data" / "raw" / "faers_reports_by_year.xlsx"
DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed" / "faers_by_year_clean.csv"
FIG_DIR: Path = PROJECT_ROOT / "figures"

# 迅速→非迅速→直接→…の順（構成比プロットの積み上げ順に対応）
CATEGORIES: list[str] = ["Expedited", "Non-Expedited", "Direct", "30-DAY", "5-DAY", "BSR"]


def setup_japanese_font() -> None:
    """利用可能な CJK フォントを順に探して matplotlib に設定する。

    Windows(Yu Gothic 等)/macOS(Hiragino)/Linux(Noto, IPAex) のいずれでも
    動くよう複数候補を試す。見つからない場合は警告のみ（描画は続行）。
    """
    candidates = [
        "Yu Gothic", "Meiryo", "MS Gothic",          # Windows
        "Hiragino Sans", "Hiragino Maru Gothic Pro",   # macOS
        "Noto Sans CJK JP", "Noto Sans JP",            # Linux/一般
        "IPAexGothic", "TakaoPGothic",                 # Linux(日本語パッケージ)
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            matplotlib.rcParams["font.family"] = name
            break
    else:
        print("[warn] 日本語フォントが見つかりません。図中の日本語が文字化けする場合があります。")
    matplotlib.rcParams["axes.unicode_minus"] = False


def load_clean(save_csv: bool = True) -> pd.DataFrame:
    """生データを読み込み、分析可能な形へ整形して返す。

    整形内容:
      - 先頭の集計行(Year=="Total Reports")を除外
      - 全カテゴリ列の "-"(該当なし) を NaN に変換
      - 全欠損の "Report Type" 列を削除
      - Year 昇順に整列
    注意: NaN のまま保持し、0 埋め/欠損除外は各分析側で目的に応じて行う。

    Args:
        save_csv: True のとき整形後データを processed/ に CSV 保存する。

    Returns:
        整形済み DataFrame。
    """
    df = pd.read_excel(DATA_RAW, sheet_name="Sheet1")
    df = df[df["Year"] != "Total Reports"].copy()          # 集計行を除外
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Total Reports"] = pd.to_numeric(df["Total Reports"], errors="coerce")
    for c in CATEGORIES:
        df[c] = pd.to_numeric(df[c], errors="coerce")       # "-" -> NaN
    df = df.dropna(subset=["Year"]).sort_values("Year").reset_index(drop=True)
    df = df.drop(columns=["Report Type"], errors="ignore")  # 全欠損列

    if save_csv:
        DATA_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(DATA_PROCESSED, index=False, encoding="utf-8-sig")
    return df


def million_formatter(v: float, _pos=None) -> str:
    """軸ラベルを 1.2M / 300k のように短く整形する。"""
    if abs(v) >= 1e6:
        return f"{v / 1e6:.1f}M"
    if abs(v) >= 1e3:
        return f"{v / 1e3:.0f}k"
    return f"{v:.0f}"
