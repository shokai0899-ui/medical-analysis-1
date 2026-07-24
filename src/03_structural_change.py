# -*- coding: utf-8 -*-
"""分析3: 構造変化の検出。

迅速シェア(Expedited/Total)に対し、動的計画法によるピースワイズ定数分割
（l2 コスト）で変化点を検出。構成比・実数・成長率の推移も併せて示す。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

import common as C


def _cost_matrix(y: np.ndarray) -> np.ndarray:
    """区間[i,j]の平均まわり残差平方和(SSE)を格納した行列を返す。"""
    n = len(y)
    cost = np.full((n, n), np.inf)
    for i in range(n):
        s = s2 = 0.0
        for j in range(i, n):
            s += y[j]
            s2 += y[j] * y[j]
            m = j - i + 1
            cost[i, j] = s2 - s * s / m
    return cost


def best_partition(y: np.ndarray, kmax: int = 6) -> dict[int, tuple[float, list[int]]]:
    """先頭からの最適な k 区間ピースワイズ定数分割を動的計画法で求める。

    Returns:
        {区間数k: (最小SSE, 変化点インデックスの昇順リスト)}
    """
    n = len(y)
    cost = _cost_matrix(y)
    dp = np.full((kmax + 1, n + 1), np.inf)
    dp[0, 0] = 0.0
    prev = np.full((kmax + 1, n + 1), -1, dtype=int)
    for k in range(1, kmax + 1):
        for j in range(1, n + 1):
            for t in range(k - 1, j):          # 直前区間の開始位置
                v = dp[k - 1, t] + cost[t, j - 1]
                if v < dp[k, j]:
                    dp[k, j] = v
                    prev[k, j] = t
    results: dict[int, tuple[float, list[int]]] = {}
    for k in range(1, kmax + 1):
        bps: list[int] = []
        j, kk = n, k
        while kk > 0:
            t = prev[kk, j]
            bps.append(t)
            j, kk = t, kk - 1
        results[k] = (float(dp[k, n]), sorted(b for b in bps if b > 0))
    return results


def _cagr(series: pd.Series) -> float:
    """区間内 CAGR（最初の正の値から最後の値まで）。算出不能なら NaN。"""
    pos = series[series > 0]
    span = len(series) - 1
    if pos.empty or span <= 0 or series.iloc[-1] <= 0:
        return float("nan")
    return (series.iloc[-1] / pos.iloc[0]) ** (1 / span) - 1


def main() -> None:
    C.setup_japanese_font()
    df = C.load_clean().copy()
    for c in C.CATEGORIES:
        df[c] = df[c].fillna(0.0)  # 構成比・変化点検出では "-" を 0(=当時ほぼ皆無) とみなす

    yr = df["Year"].to_numpy(float)
    share_exp = (df["Expedited"] / df["Total Reports"]).to_numpy(float)
    n = len(share_exp)

    res = best_partition(share_exp, kmax=6)
    print("=" * 66)
    print("[分析3] 迅速シェア(Expedited/Total) の変化点検定  — 動的計画法(l2)")
    print(f"{'k':>3} {'SSE':>10} {'BIC':>10}   変化年")
    best_k, best_bic = 1, np.inf
    for k in sorted(res):
        sse, bps = res[k]
        params = 2 * k - 1
        bic = n * np.log(sse / n + 1e-12) + params * np.log(n)
        if bic < best_bic:
            best_bic, best_k = bic, k
        print(f"{k:>3} {sse:>10.4f} {bic:>10.1f}   {[int(yr[b]) for b in bps]}")

    # 注: BIC は l2 コストでは過分割しやすい。SSE のエルボー(k=3)で見る
    #     安定した本質的変化点は 1981 と 1998。
    _, bps_bic = res[best_k]
    _, bps_elbow = res[3]
    change_years = [int(yr[b]) for b in bps_elbow]
    print(f"BIC最小 -> k={best_k}: {[int(yr[b]) for b in bps_bic]}")
    print(f"採用(SSEエルボー k=3): 変化年 = {change_years}")

    # 区間別の統計
    seg_edges = [0] + bps_elbow + [n]
    print("-" * 66)
    print(f"{'期間':>12} {'年数':>4} {'迅速ｼｪｱ平均':>10} {'Total_CAGR':>10} {'迅速_CAGR':>9}")
    seg_info = []
    for a, b in zip(seg_edges[:-1], seg_edges[1:]):
        sub = df.iloc[a:b]
        y0, y1 = int(sub["Year"].iloc[0]), int(sub["Year"].iloc[-1])
        ms = share_exp[a:b].mean()
        seg_info.append((y0, y1, ms))
        print(f"{y0}-{y1:>7} {b-a:>4} {ms*100:>9.1f}% "
              f"{_cagr(sub['Total Reports'])*100:>9.1f}% {_cagr(sub['Expedited'])*100:>8.1f}%")

    appear = int(df.loc[df["30-DAY"] > 0, "Year"].min())
    print(f"新カテゴリ 30-DAY/5-DAY の出現年: {appear}")
    print("=" * 66)

    # ---- 可視化 ----
    palette = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b"]
    fig, ax = plt.subplots(2, 2, figsize=(15, 10.5), constrained_layout=True)
    fig.suptitle("報告構造の変化 — 変化点検定・構成推移・成長率", fontsize=15, fontweight="bold")

    a = ax[0, 0]
    a.plot(yr, share_exp, marker="o", ms=3, color="#333", lw=1, zorder=3)
    for i, (y0, y1, ms) in enumerate(seg_info):
        a.hlines(ms, y0, y1, color="crimson", lw=2.5, zorder=4, label="区間平均" if i == 0 else None)
    for cy in change_years:
        a.axvline(cy, color="steelblue", ls="--", lw=1.5)
        a.text(cy, 0.62, str(cy), color="steelblue", ha="center", fontsize=9, fontweight="bold")
    a.set(xlabel="年", ylabel="Expedited / Total", ylim=(0, 0.7),
          title=f"① 迅速シェアの変化点（採用: {change_years}）")
    a.yaxis.set_major_formatter(PercentFormatter(1.0))
    a.legend(loc="lower right"); a.grid(alpha=0.3)

    a = ax[0, 1]
    comp = df[C.CATEGORIES].to_numpy(float)
    tot = comp.sum(axis=1, keepdims=True); tot[tot == 0] = 1
    a.stackplot(yr, (comp / tot).T, labels=C.CATEGORIES, colors=palette, alpha=0.9)
    for cy in change_years:
        a.axvline(cy, color="white", ls="--", lw=1.2)
    a.set(xlabel="年", ylabel="構成比", xlim=(yr.min(), yr.max()), ylim=(0, 1),
          title="② カテゴリ構成比（100%積み上げ）")
    a.yaxis.set_major_formatter(PercentFormatter(1.0))
    a.legend(loc="upper left", ncol=2, fontsize=8, framealpha=0.85)

    a = ax[1, 0]
    for c, col in zip(C.CATEGORIES, palette):
        v = np.where(df[c].to_numpy(float) <= 0, np.nan, df[c].to_numpy(float))
        a.plot(yr, v, marker=".", ms=3, color=col, label=c)
    for cy in change_years:
        a.axvline(cy, color="gray", ls="--", lw=1)
    a.set_yscale("log")
    a.set(xlabel="年", ylabel="報告数 (log)", title="③ カテゴリ別 実数推移（対数軸）")
    a.legend(fontsize=8, ncol=2); a.grid(alpha=0.3, which="both")

    a = ax[1, 1]
    a.plot(yr, df["Expedited"].pct_change() * 100, marker="o", ms=3, color="#d62728", label="迅速 YoY")
    a.plot(yr, df["Non-Expedited"].pct_change() * 100, marker="s", ms=3, color="#1f77b4", label="非迅速 YoY")
    a.axhline(0, color="gray", lw=0.8)
    for cy in change_years:
        a.axvline(cy, color="gray", ls="--", lw=1)
    a.set(xlabel="年", ylabel="前年比 (%)", ylim=(-60, 150),
          title="④ 前年比成長率（1998–2002 に迅速が急伸）")
    a.legend(); a.grid(alpha=0.3)

    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = C.FIG_DIR / "03_structural_change.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print(f"図を保存: {out.relative_to(C.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
