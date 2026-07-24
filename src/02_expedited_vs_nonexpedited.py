# -*- coding: utf-8 -*-
"""分析2: Expedited と Non-Expedited の相関。

両者は互いに独立な内訳（部分-全体ではない）。年トレンドを制御した偏相関で
「共通要因による連動」を検討し、比率の推移から 2000 年の逆転を示す。
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

    d = df.dropna(subset=["Expedited", "Non-Expedited"]).sort_values("Year").reset_index(drop=True)
    e = d["Expedited"].to_numpy(float)          # 迅速
    ne = d["Non-Expedited"].to_numpy(float)     # 非迅速
    yr = d["Year"].to_numpy(float)
    n = len(d)

    pr, pp = stats.pearsonr(e, ne)
    sr, sp = stats.spearmanr(e, ne)
    slope, icept, rv, _, _ = stats.linregress(ne, e)

    def detrend(v: np.ndarray, t: np.ndarray) -> np.ndarray:
        return v - np.polyval(np.polyfit(t, v, 1), t)

    re_, rne = detrend(e, yr), detrend(ne, yr)
    ppar, ppar_p = stats.pearsonr(re_, rne)

    ratio = e / ne  # 迅速/非迅速（>1 で迅速が多い）
    crossed = d.loc[ratio >= 1.0, "Year"]
    first_cross = int(crossed.min()) if len(crossed) else None

    print("=" * 62)
    print(f"[分析2] Expedited vs Non-Expedited   n={n} ({int(yr.min())}-{int(yr.max())})")
    print(f"Pearson  r = {pr:.4f}  (p={pp:.2e})")
    print(f"Spearman rho = {sr:.4f}  (p={sp:.2e})")
    print(f"回帰: Expedited = {slope:.4f}*NonExpedited + {icept:,.0f}   R^2={rv**2:.4f}")
    print(f"[年を制御] 偏相関 r = {ppar:.4f}  (p={ppar_p:.2e})")
    print(f"迅速/非迅速 比: 平均 {ratio.mean():.2f} / 範囲 {ratio.min():.2f}-{ratio.max():.2f}")
    print(f"迅速が非迅速を初めて上回った年: {first_cross}")
    print("=" * 62)

    # ---- 可視化 ----
    fmt = FuncFormatter(C.million_formatter)
    fig, ax = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    fig.suptitle("Expedited(迅速) vs Non-Expedited(非迅速) — 独立な内訳同士", fontsize=15, fontweight="bold")

    a = ax[0, 0]
    sc = a.scatter(ne, e, c=yr, cmap="viridis", s=48, edgecolor="white", lw=0.5, zorder=3)
    xs = np.linspace(ne.min(), ne.max(), 100)
    a.plot(xs, slope * xs + icept, color="crimson", lw=2, label=f"回帰直線 (R²={rv**2:.3f})")
    hi = max(e.max(), ne.max())
    a.plot([0, hi], [0, hi], "--", color="gray", lw=1, label="y=x (迅速=非迅速)")
    a.set(xlabel="Non-Expedited (非迅速)", ylabel="Expedited (迅速)",
          title=f"① 散布図: Pearson r = {pr:.3f}")
    a.xaxis.set_major_formatter(fmt); a.yaxis.set_major_formatter(fmt)
    a.legend(loc="upper left"); a.grid(alpha=0.3)
    fig.colorbar(sc, ax=a, label="年")

    a = ax[0, 1]
    a.plot(yr, e, marker="o", ms=3, color="#d62728", label="Expedited(迅速)")
    a.plot(yr, ne, marker="s", ms=3, color="#1f77b4", label="Non-Expedited(非迅速)")
    if first_cross:
        a.axvline(first_cross, color="gray", ls=":", lw=1.5, label=f"逆転 {first_cross}年")
    a.set(xlabel="年", ylabel="報告数", title="② 年次推移と逆転")
    a.yaxis.set_major_formatter(fmt); a.legend(); a.grid(alpha=0.3)

    a = ax[1, 0]
    a.scatter(rne, re_, c=yr, cmap="viridis", s=48, edgecolor="white", lw=0.5, zorder=3)
    xs2 = np.linspace(rne.min(), rne.max(), 100)
    a.plot(xs2, np.polyval(np.polyfit(rne, re_, 1), xs2), color="crimson", lw=2)
    a.axhline(0, color="gray", lw=0.8); a.axvline(0, color="gray", lw=0.8)
    a.set(xlabel="非迅速 残差（年トレンド除去後）", ylabel="迅速 残差（年トレンド除去後）",
          title=f"③ 偏相関（年を制御）: r = {ppar:.3f}")
    a.grid(alpha=0.3)

    a = ax[1, 1]
    a.plot(yr, ratio, marker="o", ms=3, color="#9467bd")
    a.axhline(1.0, color="crimson", ls="--", lw=1.2, label="迅速=非迅速 (比=1)")
    a.set(xlabel="年", ylabel="迅速 / 非迅速 比", title="④ 迅速/非迅速 比の推移")
    a.legend(); a.grid(alpha=0.3)

    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = C.FIG_DIR / "02_expedited_vs_nonexpedited.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print(f"図を保存: {out.relative_to(C.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
