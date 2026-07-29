# -*- coding: utf-8 -*-
"""FDA 有害事象報告データ — 相関と構造変化（通し実行スクリプト）。

分析1〜3を順に実行し、統計量の出力と figures/ 以下の全図の再生成をまとめて行う。
リポジトリのどこからでも `python analysis.py` で全体を再現できる。

各分析の実装（統計量の計算と4パネルの作図）は `src/` にあり、本スクリプトは
解説を挟みながらそれらを順に呼び出す入口として振る舞う。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

PROJECT_ROOT: Path = Path(__file__).resolve().parent
SRC_DIR: Path = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))  # src/ をリポジトリ相対で解決してから common を読む

import common as C  # noqa: E402  (sys.path を設定した後でなければ解決できない)

INTRO = """\
FDA 有害事象報告データ — 相関と構造変化

分析の流れ:
  分析1: Total Reports × Expedited      （部分-全体の交絡）
  分析2: Expedited × Non-Expedited      （独立な内訳同士・偏相関）
  分析3: 迅速シェアの構造変化           （変化点検定）

データ: FDA FAERS Public Dashboard（パブリックドメイン）。
        年次の集計件数であり、安全性の指標でも因果の証拠でもない。
"""

# (src/ のファイル名, 見出し, その分析の狙い)
ANALYSES: list[tuple[str, str, str]] = [
    (
        "01_total_vs_expedited.py",
        "分析1: Total Reports と Expedited",
        "強い相関が出るが、Expedited は Total の構成要素なので半ば定義的。\n"
        "年トレンドも両者に共通する。",
    ),
    (
        "02_expedited_vs_nonexpedited.py",
        "分析2: Expedited と Non-Expedited（独立な内訳同士）",
        "互いに他方を含まない。年を制御しても相関が残れば、時間以外の共通要因を\n"
        "示唆する（ただし相関は因果ではない）。",
    ),
    (
        "03_structural_change.py",
        "分析3: 構造変化の検出（変化点検定）",
        "迅速シェア（Expedited / Total）に、動的計画法によるピースワイズ定数分割\n"
        "（l2 コスト）を適用して変化点を探す。",
    ),
]

CONCLUSION = """\
考察（要点）

- 相関→偏相関: 迅速×非迅速は年を制御した後も r≈0.93。時間以外の共通要因が
  両者を同時に動かしている可能性を示す。ただし相関は因果ではない。消せたのは
  「時間」という1つの交絡だけで、影響の方向は特定できない。

- 水準と割合の区別: 「薬剤・利用者が増えて両方の件数が増えた」は実数の増加は
  説明できるが、迅速シェアの上昇（0.2% → 57%）は説明できない。シェアが上がるには
  迅速が非迅速より速く増える必要があり、迅速に固有の要因（報告制度・基準の変更など）
  を示唆する。

- 構造変化: 1981年・1998年に転換。約20年続く持続的な水準シフトであり、単一薬剤に
  よる一時的スパイクとは形が異なる。

限界
  相関≠因果 / 2026年は年途中の暫定値 / 変化点はモデル選択に依存（BIC は過分割しやすい）
  / 集計データゆえ層別は不可。

詳細は README.md を参照。
"""


def load_src_module(filename: str) -> ModuleType:
    """数字始まりで通常の import ができない `src/` のスクリプトを読み込む。

    Args:
        filename: `src/` 直下のファイル名（例: "01_total_vs_expedited.py"）。

    Returns:
        読み込み済みモジュール。`__name__` ガードがあるため main() は自動実行されない。
    """
    path = SRC_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:  # 実質起こらないが型を確定させる
        raise ImportError(f"読み込めません: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def banner(title: str) -> None:
    """節の見出しを出力する。"""
    print("\n" + "#" * 70)
    print(f"# {title}")
    print("#" * 70)


def show_data_overview() -> None:
    """整形後データの形と先頭数行を表示する。"""
    df = C.load_clean()  # 集計行除外・"-"→NaN・型変換（processed CSV も更新）
    years = f"{int(df['Year'].min())}-{int(df['Year'].max())}"
    print(f"\n整形後データ: {df.shape[0]} 行 × {df.shape[1]} 列 / 対象年 {years}")
    cols = ["Year", "Total Reports", "Expedited", "Non-Expedited", "Direct"]
    print(df[cols].head().to_string(index=False))
    print(f"整形済み CSV: {C.DATA_PROCESSED.relative_to(PROJECT_ROOT)}")


def main() -> None:
    """全分析を順に実行し、図を再生成する。"""
    print(INTRO)
    show_data_overview()

    for filename, title, lead in ANALYSES:
        banner(title)
        print(lead)
        load_src_module(filename).main()

    banner("まとめ")
    print(CONCLUSION)
    print(f"図の出力先: {C.FIG_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
