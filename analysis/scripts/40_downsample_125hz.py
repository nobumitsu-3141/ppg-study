#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【前提確認】125 Hz でも 4 指標は同じものを測るか（MIMIC-III が使えるかの判断）。

なぜ要るか
----------
熱希釈由来の CO は動脈圧波形と独立なので、VitalDB の EV1000 で行き詰まった
「指標は血管抵抗を見ているのか、FloTrac の CO 推定を見ているのか」に決着をつけられる。
公開データベースでその条件を満たすのは実質 MIMIC-III だが、**MIMIC-III の波形は 125 Hz** で、
本研究の凍結版 PDA は **500 Hz** で開発・凍結した。σ の下限 0.015 s は 125 Hz では 1.9 標本、
ΔT の分解能は 8 ms になる。**測定そのものが変わる可能性がある。**

MIMIC の利用申請より先に、**手元の 500 Hz のデータを 125 Hz に間引いて同じ指標を計算し、
どれだけ一致するかを見る。**一致しないなら、MIMIC に PAC 症例が何例あっても意味がない。

3 系統を同じウィンドウで比べる
------------------------------
  A  500 Hz のまま（基準。39番と同じ処理）
  B  **生波形を 125 Hz に間引いてから**拍切り出し・品質判定・加算平均・指標
     … MIMIC で実際に得られるもの
  C  間引いた波形に **A と同じ拍境界**を当てて加算平均・指標
     … 拍検出の劣化と、当てはめ・指標そのものの劣化を分ける

間引きは**必ず 60 秒のウィンドウ全体に対して行う。**1 拍（500 点）だけを間引くと、
低域通過フィルタの長さ（121 タップ）が信号長に対して無視できず、端の影響が入る。
系統 C も、間引き済みのウィンドウから拍を切り出す。

判定規準（**実行前に固定**）
----------------------------
主要な量は **ρ(Δ指標%_A, Δ指標%_B)**（症例内の相対変化どうしの順位相関の症例中央値）である。
測定誤差が独立なら、外部変数との相関はおよそこの値の分だけ減衰する。

  採用   ρ ≥ 0.80 **かつ** 歩留まりの低下が 10 ポイント以内
  不採用 ρ < 0.50 **または** 歩留まりが半分以下
  保留   その間（減衰を明記したうえでなら使える）

0.80 と 0.50 の根拠。手元で最も強い指標でも外部変数との ρ は 0.20〜0.31 である
（39番 `--dose`）。減衰係数 0.80 なら 0.16〜0.25 で読めるが、0.50 なら 0.10〜0.15 となり、
今の信頼区間の幅では雑音と区別できない。

限界
----
- MIMIC の 125 Hz は監視装置が元から 125 Hz で出したものであり、500 Hz を間引いたものではない。
  ただし PPG は 20 Hz より上にほとんど成分を持たないので、折り返し雑音を防ぐ低域通過を
  かけてから間引く本手順は妥当な近似である。
- **量子化は模擬しない。**MIMIC の波形は整数で保存されており分解能が限られるが、
  その影響は本試験に含まれない。したがって本試験は**楽観側に偏る。**
- 動脈圧は使わない（本試験は指標を指標自身と比べるだけなので平均血圧が要らない）。
  そのぶんダウンロードが 3 分の 2 になる。ウィンドウの採否は品質通過拍 8 以上のみ。

使い方
------
    python3 scripts/40_downsample_125hz.py --selftest
    python3 scripts/40_downsample_125hz.py --run --limit 20 --jobs 4
    python3 scripts/40_downsample_125hz.py --stats

出力
----
    data/downsample/case_{id}.csv
    ../docs/research/results/40_downsample_125hz.txt
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import decimate

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.beats import segment_beats, sqi, ensemble_average            # noqa: E402


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M39 = _load("39_ri_svr_standalone.py", "m39_40")

FS = 500.0            # VitalDB の標本化周波数
FS_LOW = 125.0        # MIMIC-III の波形の標本化周波数
Q = int(FS / FS_LOW)  # 間引き比 4
WIN_S = 60.0
MIN_GOOD = 8          # ウィンドウに要求する品質通過拍数（39番と同一）
MIN_WIN = 12          # 症例に要求する有効ウィンドウ数（同上）
NAN = float("nan")
WAVES = ["SNUADC/PLETH", "SNUADC/ECG_II"]

# 実行前に固定した判定規準
RHO_PASS, RHO_FAIL = 0.80, 0.50
YIELD_DROP_PASS = 0.10

DATA = ROOT / "data"
OUT = DATA / "downsample"
COLS = M39.INDEX_COLS                       # ri_v1 / ri_cou / ri_lm / amb
ARMS = ("a", "b", "c")
ARM_NAME = {"a": "A 500 Hz のまま", "b": "B 生波形を 125 Hz に間引く",
            "c": "C 同じ拍境界を間引いた波形に当てる"}


# ════════════════════════════════════════════════ 間引き
def downsample(x: np.ndarray, q: int = Q) -> np.ndarray:
    """折り返し雑音を防ぐ低域通過をかけてから q 分の 1 に間引く。

    有限インパルス応答フィルタを使い、`zero_phase=True` で群遅延を打ち消す。
    無限インパルス応答だと立ち上がりの急峻な部分で振動が出るため使わない。
    """
    x = np.asarray(x, float)
    if x.size < 30 * q:
        return np.asarray(x[::q], float)
    return np.asarray(decimate(x, q, ftype="fir", zero_phase=True), float)


def map_slices(cuts: list[tuple[int, int]], q: int = Q) -> list[tuple[int, int]]:
    """500 Hz の拍境界を、間引いた波形の添字に写す。"""
    return [(int(s) // q, int(e) // q) for s, e in cuts]


# ════════════════════════════════════════════════ 1 ウィンドウ → 3 系統の指標
def window_row(seg_p: np.ndarray, seg_e: np.ndarray, t0: float) -> dict | None:
    row: dict = {"t0": float(t0)}

    # --- A: 500 Hz のまま
    try:
        beats = segment_beats(seg_p, FS, ecg=seg_e)
        good = [(s, e) for s, e in beats if sqi(seg_p[s:e], FS)["ok"]]
    except Exception:      # noqa: BLE001
        return None
    if len(good) < MIN_GOOD:
        return None
    ens_a = ensemble_average([seg_p[s:e] for s, e in good])
    row["n_good_a"] = len(good)
    for k, v in M39.indices_on_beat(ens_a, FS).items():
        row[f"{k}_a"] = v

    for k in COLS:
        row[f"{k}_b"] = NAN
        row[f"{k}_c"] = NAN
    row["n_good_b"] = 0
    p_lo, e_lo = downsample(seg_p), downsample(seg_e)      # ウィンドウ全体を一度だけ間引く

    # --- C: A と同じ拍境界を間引いた波形に当てる（拍検出の劣化を含まない）
    try:
        cuts = [(a, b) for a, b in map_slices(good) if b - a >= 8]
        if len(cuts) >= MIN_GOOD:
            ens_c = ensemble_average([p_lo[a:b] for a, b in cuts])
            for k, v in M39.indices_on_beat(ens_c, FS_LOW).items():
                row[f"{k}_c"] = v
    except Exception:      # noqa: BLE001
        pass

    # --- B: 間引いた波形から拍を切り直す（MIMIC で実際に得られるもの）
    try:
        beats_b = segment_beats(p_lo, FS_LOW, ecg=e_lo)
        good_b = [(s, e) for s, e in beats_b if sqi(p_lo[s:e], FS_LOW)["ok"]]
        row["n_good_b"] = len(good_b)
        if len(good_b) >= MIN_GOOD:
            ens_b = ensemble_average([p_lo[s:e] for s, e in good_b])
            for k, v in M39.indices_on_beat(ens_b, FS_LOW).items():
                row[f"{k}_b"] = v
    except Exception:      # noqa: BLE001
        pass
    return row


def _task(args):
    t0, seg_p, seg_e = args
    try:
        return window_row(seg_p, seg_e, t0)
    except Exception:      # noqa: BLE001
        return None


# ════════════════════════════════════════════════ 抽出
def extract_case(caseid: int, jobs: int) -> int:
    from multiprocessing import Pool
    import vitaldb
    p = OUT / f"case_{caseid}.csv"
    if p.exists():
        return -1
    wav = vitaldb.load_case(caseid, WAVES, 1 / FS)
    pleth = np.nan_to_num(np.asarray(wav[:, 0], float))
    ecg = np.nan_to_num(np.asarray(wav[:, 1], float))
    tasks = []
    for t0 in np.arange(0, len(pleth) / FS - WIN_S, WIN_S):
        i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
        if pleth[i0:i1].size < int(WIN_S * FS) * 0.9 or not np.any(pleth[i0:i1]):
            continue
        tasks.append((float(t0), pleth[i0:i1], ecg[i0:i1]))
    if not tasks:
        return 0
    with Pool(jobs) as pool:
        rows = [r for r in pool.map(_task, tasks) if r]
    if not rows:
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(p, index=False)
    return len(rows)


def run(limit: int | None, jobs: int) -> None:
    cp = DATA / "standalone" / "cases.csv"
    ids = (pd.read_csv(cp)["caseid"].astype(int).tolist() if cp.exists()
           else M39.build_case_list()["caseid"].astype(int).tolist())
    if limit:
        ids = sorted(np.random.default_rng(0).permutation(ids)[:limit].tolist())
    print(f"\n抽出 {len(ids)} 例（既にある症例は飛ばす）")
    for k, cid in enumerate(ids, 1):
        t = time.time()
        try:
            n = extract_case(cid, jobs)
        except Exception as e:      # noqa: BLE001
            print(f"  [{k}/{len(ids)}] {cid}: 失敗 {str(e)[:60]}")
            continue
        tag = "既にある" if n < 0 else f"{n} ウィンドウ"
        print(f"  [{k}/{len(ids)}] {cid}: {tag}（{(time.time()-t)/60:.1f} 分）")


# ════════════════════════════════════════════════ 集計
def agree(a: np.ndarray, b: np.ndarray) -> dict:
    """2 系統の一致。**相対変化どうしの順位相関が主要な量である。**

    基準は「両系統とも値が取れた最初のウィンドウ」に取る（追記54 の修正と同じ）。
    生の値どうしの順位相関と、相対差の中央値・一致限界も併せて返す。
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < MIN_WIN:
        return {"n": int(ok.sum()), "rho_rel": NAN, "rho_raw": NAN,
                "bias": NAN, "loa_lo": NAN, "loa_hi": NAN}
    x, y = a[ok], b[ok]
    d = (y - x) / np.where(np.abs(x) > 1e-9, np.abs(x), 1e-9)
    return {"n": int(ok.sum()),
            "rho_rel": M39.spearman(M39.rel(x), M39.rel(y)),
            "rho_raw": M39.spearman(x, y),
            "bias": float(np.median(d)),
            "loa_lo": float(np.percentile(d, 2.5)),
            "loa_hi": float(np.percentile(d, 97.5))}


def cv(v: np.ndarray) -> float:
    """症例内変動係数。間引きが雑音を足したなら上がる。"""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size < MIN_WIN or abs(np.mean(v)) < 1e-9:
        return NAN
    return float(np.std(v, ddof=1) / abs(np.mean(v)))


def verdict(rho: float, drop: float) -> str:
    if not np.isfinite(rho):
        return "判定不能"
    if rho >= RHO_PASS and np.isfinite(drop) and drop <= YIELD_DROP_PASS:
        return "採用"
    if rho < RHO_FAIL or (np.isfinite(drop) and drop > 0.5):
        return "不採用"
    return "保留"


def stats() -> int:
    files = sorted(OUT.glob("case_*.csv"))
    out = ["=" * 92,
           "【前提確認】125 Hz でも 4 指標は同じものを測るか（40番）",
           f"判定規準は実行前に固定: 採用 ρ ≥ {RHO_PASS:.2f} かつ 歩留まり低下 ≤ "
           f"{YIELD_DROP_PASS:.0%}／不採用 ρ < {RHO_FAIL:.2f} または 歩留まり半減",
           "=" * 92,
           f"\n抽出済み症例: {len(files)}"]
    if not files:
        out.append("\n先に --run を実行すること。")
        print("\n".join(out))
        return 1
    frames = [pd.read_csv(f) for f in files]
    tot = int(sum(len(d) for d in frames))
    out.append(f"ウィンドウ計: {tot:,}")
    nga = float(np.mean([d["n_good_a"].mean() for d in frames]))
    ngb = float(np.mean([d["n_good_b"].mean() for d in frames]))
    out.append(f"品質を通った拍数の平均: 500 Hz {nga:.1f} 拍／125 Hz {ngb:.1f} 拍"
               f"（1 ウィンドウ 60 秒あたり）")

    for col in COLS:
        out.append(f"\n■ {M39.INDEX_NAME[col]}")
        ya = int(sum(np.isfinite(d[f"{col}_a"]).sum() for d in frames))
        yb = int(sum(np.isfinite(d[f"{col}_b"]).sum() for d in frames))
        yc = int(sum(np.isfinite(d[f"{col}_c"]).sum() for d in frames))
        out.append(f"  歩留まり  A {ya/tot:6.1%}   B {yb/tot:6.1%}   C {yc/tot:6.1%}"
                   f"　（B の低下 {(ya-yb)/tot:+.1%}）")
        rows_b = [agree(d[f"{col}_a"], d[f"{col}_b"]) for d in frames]
        rows_c = [agree(d[f"{col}_a"], d[f"{col}_c"]) for d in frames]
        out.append(f"  {'比較':28s}{'例':>4s}{'ρ 相対変化':>12s}{'ρ 生の値':>11s}"
                   f"{'ずれ中央値':>12s}{'一致限界':>22s}")
        for lab, rr in (("B 対 A（MIMIC 相当）", rows_b), ("C 対 A（指標のみ）", rows_c)):
            t = pd.DataFrame(rr)
            t = t[np.isfinite(t["rho_rel"])]
            if not len(t):
                out.append(f"  {lab:28s}{'—':>4s}")
                continue
            loa = (f"[{np.nanmedian(t['loa_lo']):+.1%}, "
                   f"{np.nanmedian(t['loa_hi']):+.1%}]")
            out.append(f"  {lab:28s}{len(t):>4d}"
                       f"{np.nanmedian(t['rho_rel']):>+12.3f}"
                       f"{np.nanmedian(t['rho_raw']):>+11.3f}"
                       f"{np.nanmedian(t['bias']):>+12.1%}{loa:>22s}")
        cva = float(np.nanmedian([cv(d[f"{col}_a"].to_numpy(float)) for d in frames]))
        cvb = float(np.nanmedian([cv(d[f"{col}_b"].to_numpy(float)) for d in frames]))
        out.append(f"  症例内変動係数の中央値  A {cva:.3f} → B {cvb:.3f}")
        t = pd.DataFrame(rows_b)
        rho = float(np.nanmedian(t["rho_rel"])) if len(t) else NAN
        out.append(f"  ★ 判定: {verdict(rho, (ya - yb) / tot)}"
                   f"（ρ={rho:+.3f}・歩留まり低下 {(ya-yb)/tot:+.1%}）")

    out.append("""
  【読み方】主要な量は「ρ 相対変化」の B 対 A である。本研究の解析は相対変化の上で
  行うので、外部変数との相関はおよそこの値の分だけ減衰する。
  【A・B・C の差の意味】B と C がともに低ければ当てはめ・指標そのものが 125 Hz に耐えない。
  C だけ高ければ、劣化の主因は拍の切り出しと品質判定である（この場合、心電図の
  R 波検出を 125 Hz 向けに直せば救える見込みがある）。
  【限界】量子化を模擬していないので、本試験は**楽観側に偏る。**MIMIC の実波形では
  これより悪くなる。また MIMIC の 125 Hz は監視装置が元から出したものであって、
  500 Hz を間引いたものではない。""")
    out.append("=" * 92)
    text = "\n".join(out)
    print(text)
    dst = ROOT.parent / "docs" / "research" / "results" / "40_downsample_125hz.txt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text + "\n", encoding="utf-8")
    print(f"\n書き出し: {dst}", file=sys.stderr)
    return 0


# ════════════════════════════════════════════════ 自己検査
def selftest() -> int:
    ok, ng = 0, []

    def chk(name, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  PASS  {name}")
        else:
            ng.append(name)
            print(f"  FAIL  {name}")

    n = 5000
    t = np.arange(n) / FS
    s = np.sin(2 * np.pi * 1.2 * t)
    d = downsample(s)
    chk("間引き後の長さが 4 分の 1", abs(d.size - n // Q) <= 1)
    chk("1.2 Hz の正弦波の振幅が保たれる", abs(np.ptp(d) - np.ptp(s)) < 0.02)
    hi = np.sin(2 * np.pi * 200.0 * t)
    chk("200 Hz は低域通過で落ちる（折り返さない）", np.ptp(downsample(hi)) < 0.2)
    chk("短い入力でも落ちない", downsample(np.ones(10)).size > 0)

    # 合成拍。**凍結版 PDA はこの理想波形では 500 Hz でも当てはめが通らない**
    # （39番の自己検査も ri_cou と amb しか見ていない）。ここで見るのは
    # 「125 Hz でも処理が最後まで走るか」であって、値の一致ではない。
    tb = np.arange(0, 1.0, 1 / FS)
    beat = (1.00 * np.exp(-((tb - 0.20) / 0.055) ** 2)
            + 0.45 * np.exp(-((tb - 0.33) / 0.070) ** 2)
            + 0.25 * np.exp(-((tb - 0.50) / 0.090) ** 2))
    train = np.tile(beat, 12)                      # 12 拍つないで端の影響を避ける
    lo = downsample(train)
    mid5, mid1 = train[5 * 500:6 * 500], lo[5 * 125:6 * 125]
    r500, r125 = M39.indices_on_beat(mid5, FS), M39.indices_on_beat(mid1, FS_LOW)
    chk("合成拍は 500 Hz で R1_d・特徴点法 RI・早期振幅比が有限",
        all(np.isfinite(r500[c]) for c in ("ri_cou", "ri_lm", "amb")))
    chk("同じ 3 指標が 125 Hz でも有限",
        all(np.isfinite(r125[c]) for c in ("ri_cou", "ri_lm", "amb")))
    chk("特徴点法 RI は間引きでほぼ変わらない（振幅比なので）",
        abs(r500["ri_lm"] - r125["ri_lm"]) < 0.02)
    chk("早期振幅比も間引きでほぼ変わらない",
        abs(r500["amb"] - r125["amb"]) < 0.02)

    chk("拍境界の写像は 4 分の 1", map_slices([(0, 500), (500, 1000)]) == [(0, 125), (125, 250)])
    chk("間引きはウィンドウ全体に一度だけ掛ける（端の影響を避ける）",
        abs(downsample(train).size - train.size // Q) <= 1)

    x = np.linspace(0.30, 0.50, 40)
    chk("agree 同一系列で ρ=1", abs(agree(x, x)["rho_rel"] - 1.0) < 1e-9)
    chk("agree 同一系列でずれ 0", abs(agree(x, x)["bias"]) < 1e-12)
    chk("agree 一定倍率でも順位相関は 1",
        abs(agree(x, 1.5 * x)["rho_rel"] - 1.0) < 1e-9)
    chk("agree 点数不足は NaN", not np.isfinite(agree(x[:5], x[:5])["rho_rel"]))
    y = x.copy()
    y[::2] = NAN
    chk("agree は片側欠測を除いて数える", agree(x, y)["n"] == 20)

    chk("判定 採用", verdict(0.90, 0.02) == "採用")
    chk("判定 不採用（相関）", verdict(0.40, 0.02) == "不採用")
    chk("判定 不採用（歩留まり）", verdict(0.95, 0.80) == "不採用")
    chk("判定 保留", verdict(0.70, 0.02) == "保留")
    chk("判定 採用の境界は 0.80 と 10 ポイント",
        verdict(0.80, 0.10) == "採用" and verdict(0.79, 0.10) == "保留"
        and verdict(0.80, 0.11) == "保留")
    chk("cv 一定値は 0", abs(cv(np.full(30, 0.4))) < 1e-12)
    chk("cv 点数不足は NaN", not np.isfinite(cv(np.full(5, 0.4))))

    print(f"\n  {ok}/{ok + len(ng)} PASS" + ("  ALL PASS" if not ng else f"  FAIL: {ng}"))
    return 0 if not ng else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="波形を取得して 3 系統を計算する")
    ap.add_argument("--stats", action="store_true", help="集計だけ行う")
    ap.add_argument("--selftest", action="store_true", help="ネットワーク不要の自己検査")
    ap.add_argument("--limit", type=int, default=None, help="症例数を絞る（seed 0 で無作為）")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.run:
        run(a.limit, a.jobs)
        sys.exit(stats())
    if a.stats:
        sys.exit(stats())
    ap.print_help()


if __name__ == "__main__":
    main()
