# -*- coding: utf-8 -*-
"""分析1: Total Reports と Expedited の相関。

Expedited は Total の構成要素（部分-全体）である点を検算で確認し、
相関の一部が定義由来であること、および年トレンドを制御した偏相関を示す。
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats

import common as C


def main() -> None:
    C.setup_japanese_font()
    df = C.load_clean()

    # 相関には Total と Expedited が共に有効な行のみ使用
    d = df.dropna(subset=["Total Reports", "Expedited"]).sort_values("Year").reset_index(drop=True)
    x = d["Total Reports"].to_numpy(float)
    y = d["Expedited"].to_numpy(float)
    yr = d["Year"].to_numpy(float)
    n = len(d)

    pear_r, pear_p = stats.pearsonr(x, y)
    spear_r, spear_p = stats.spearmanr(x, y)
    slope, intercept, r_val, _, _ = stats.linregress(x, y)

    # 交絡①: Total = Expedited + Non-Expedited + Direct + 30-DAY + 5-DAY + BSR の検算
    comp = df[C.CATEGORIES].fillna(0).sum(axis=1)
    match = np.isclose(comp, df["Total Reports"]).mean()

    # 交絡②: 年トレンドを除去した偏相関
    def detrend(v: np.ndarray, t: np.ndarray) -> np.ndarray:
        return v - np.polyval(np.polyfit(t, v, 1), t)

    rx, ry = detrend(x, yr), detrend(y, yr)
    partial_r, partial_p = stats.pearsonr(rx, ry)
    share = y / x

    print("=" * 60)
    print(f"[分析1] Total Reports vs Expedited   n={n} ({int(yr.min())}-{int(yr.max())})")
    print(f"Pearson  r = {pear_r:.4f}  (p={pear_p:.2e})")
    print(f"Spearman rho = {spear_r:.4f}  (p={spear_p:.2e})")
    print(f"回帰: Expedited = {slope:.4f}*Total + {intercept:,.0f}   R^2={r_val**2:.4f}")
    print(f"[交絡①] Total=各カテゴリ合計 の成立率: {match*100:.0f}% -> Expedited は Total の構成要素")
    print(f"[交絡②] 年を制御した偏相関 r = {partial_r:.4f}  (p={partial_p:.2e})")
    print(f"Expedited シェア: 平均 {share.mean()*100:.1f}% / 範囲 {share.min()*100:.1f}-{share.max()*100:.1f}%")
    print("=" * 60)

    # ---- 可視化 ----
    fmt = FuncFormatter(C.million_formatter)
    fig, ax = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    fig.suptitle("Total Reports と Expedited の相関分析", fontsize=15, fontweight="bold")

    a = ax[0, 0]
    sc = a.scatter(x, y, c=yr, cmap="viridis", s=45, edgecolor="white", linewidth=0.5, zorder=3)
    xs = np.linspace(x.min(), x.max(), 100)
    a.plot(xs, slope * xs + intercept, color="crimson", lw=2, label=f"回帰直線 (R²={r_val**2:.3f})")
    a.set(xlabel="Total Reports (総報告数)", ylabel="Expedited (迅速報告数)",
          title=f"① 散布図: Pearson r = {pear_r:.3f}")
    a.xaxis.set_major_formatter(fmt); a.yaxis.set_major_formatter(fmt)
    a.legend(loc="upper left"); a.grid(alpha=0.3)
    fig.colorbar(sc, ax=a, label="年")

    a = ax[0, 1]
    a.plot(yr, x, marker="o", ms=3, color="#1f77b4", label="Total Reports")
    a.plot(yr, y, marker="s", ms=3, color="#ff7f0e", label="Expedited")
    a.set(xlabel="年", ylabel="報告数", title="② 年次推移（両者とも右肩上がり＝共通トレンド）")
    a.yaxis.set_major_formatter(fmt); a.legend(); a.grid(alpha=0.3)

    a = ax[1, 0]
    a.scatter(rx, ry, c=yr, cmap="viridis", s=45, edgecolor="white", linewidth=0.5, zorder=3)
    xs2 = np.linspace(rx.min(), rx.max(), 100)
    a.plot(xs2, np.polyval(np.polyfit(rx, ry, 1), xs2), color="crimson", lw=2)
    a.axhline(0, color="gray", lw=0.8); a.axvline(0, color="gray", lw=0.8)
    a.set(xlabel="Total Reports 残差（年トレンド除去後）", ylabel="Expedited 残差（年トレンド除去後）",
          title=f"③ 偏相関（年を制御）: r = {partial_r:.3f}")
    a.grid(alpha=0.3)

    a = ax[1, 1]
    a.plot(yr, share * 100, marker="o", ms=3, color="#2ca02c")
    a.axhline(share.mean() * 100, color="crimson", ls="--", lw=1.2, label=f"平均 {share.mean()*100:.1f}%")
    a.set(xlabel="年", ylabel="Expedited 比率 (%)", ylim=(0, 60),
          title="④ Expedited が総報告に占める割合の推移")
    a.legend(); a.grid(alpha=0.3)

    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = C.FIG_DIR / "01_total_vs_expedited.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print(f"図を保存: {out.relative_to(C.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
