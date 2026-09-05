#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究0 の予備実行で第2版の採択率が極端に低いときに、**原因を記述する**（閾値は動かさない）。

判定規則の順序 1（600 名の予備実行）は「表の形・拍の切り出し・不採用の理由を確認する」段である。
第2版 歪みガウスの採択が 0% なら、それが手法の挙動なのか配管の欠陥なのかを、全例（約 3 時間）を
回す前に分けておく必要がある。本台本は 2 つのことをする。

  A  26番の CSV（被験者別の診断量）だけから、型ごと・規準ごとに何が引っかかっているかを数える
     （鍵点が模型側に無いのか、あるがずれているのか。Errx の内訳。張り付き。顕著さとの関係）
  B  型1 の拍を数例だけ再分解し、データ側と模型側の鍵点（S・切痕・D）の位置を並べて印字し、
     波形と当てはめの図を残す（--pwdb が要る。Mac で）

出力はすべて記述であり、採否の規準には触れない（規準の感度は 27番 A 層で見る）。

使い方
------
    python3 scripts/29_pwdb_reject_diag.py --csv data/pwdb/pwdb_compare_limit600.csv
    python3 scripts/29_pwdb_reject_diag.py --csv data/pwdb/pwdb_compare_limit600.csv --pwdb ~/pwdb --examples 8
    python3 scripts/29_pwdb_reject_diag.py --selftest
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import pda2  # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "pwdb"
ROUTES = [("v2", "skew", "第2版 歪みガウス"), ("v2g", "gamma", "第2版 ガンマ")]


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _q(v, qs=(10, 50, 90)):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return "—"
    return " / ".join(f"{np.percentile(v, q):.3g}" for q in qs)


# ================================================================ A. CSV の記述
def describe_csv(d) -> None:
    print("=" * 78)
    print("A. 26番の CSV から: 何が規準に引っかかっているか（記述。閾値は動かさない）")
    print("=" * 78)
    n = len(d)
    if "klass_own" not in d:
        print("  klass_own 列が無い（26番の古い出力）。"); return
    kl = d["klass_own"].to_numpy(float)
    print(f"被験者 {n}。データ側の型: " + "・".join(f"型{int(k)} {int((kl == k).sum())}" for k in sorted(set(kl[np.isfinite(kl)]))))
    if "prom_own" in d:
        for k in (1, 3):
            print(f"  型{k} の鍵点の顕著さ（10/50/90%）: {_q(d.loc[kl == k, 'prom_own'])}"
                  f"（閾値 型1 {pda2.EXTREMA_MIN_PROM}・型3 {pda2.PROXY_MIN_PROM}）")
    if "ok_v1" in d:
        for k in (1, 3, 4):
            m = kl == k
            if m.any():
                print(f"  凍結版の採択 型{k}: {int(d.loc[m, 'ok_v1'].sum())}/{int(m.sum())}")

    for tag, route, label in ROUTES:
        if f"ok_{tag}" not in d:
            continue
        print("-" * 78)
        print(f"{label}")
        print("-" * 78)
        ok = d[f"ok_{tag}"].fillna(0).to_numpy(int)
        why = d[f"why_{tag}"].fillna("").astype(str)
        for k in sorted(set(kl[np.isfinite(kl)])):
            m = kl == k
            c = Counter(why[m])
            print(f"  型{int(k)}: n={int(m.sum())} 採用 {int(ok[m].sum())}  理由 "
                  + "、".join(f"{r or 'ok'} {v}" for r, v in c.most_common()))
        m1 = kl == 1
        if not m1.any():
            print("  型1 の拍が無い"); continue
        g = lambda c: d.loc[m1, c].to_numpy(float) if c in d else np.full(int(m1.sum()), np.nan)  # noqa: E731
        nrmse, errx, erry, nlm = g(f"nrmse_{tag}"), g(f"errx_{tag}_ms"), g(f"erry_{tag}"), g(f"nlm_{tag}")
        se, amb, noref = g(f"dtse_{tag}_ms"), g(f"amb_{tag}"), g(f"noref_{tag}")
        npin, esc, esct, nw = g(f"npin_{tag}"), g(f"esc_{tag}"), g(f"esct_{tag}"), g(f"nw_{tag}")
        print(f"  型1 の拍 {int(m1.sum())} での診断量（10/50/90%）:")
        print(f"    NRMSE {_q(nrmse)}（上限 {pda2.NRMSE_MAX}）  Errx[ms] {_q(errx)}（上限 {pda2.ERRX_MS:.0f}）"
              f"  Erry {_q(erry)}（上限 {pda2.ERRY}）  ΔT の SE[ms] {_q(se)}（上限 {pda2.SE_DT_MAX_MS:.0f}）")
        c_nlm = Counter(int(x) for x in nlm[np.isfinite(nlm)])
        print("    模型側で一致した鍵点の数 nlm: " + "・".join(f"{k}点 {v}" for k, v in sorted(c_nlm.items()))
              + "（3 点未満は模型に極値が無い。欠けた鍵点 1 つにつき Errx に 12 ms の罰則）")
        pen = 2.0 * pda2.ERRX_MS * np.clip(3 - nlm, 0, 3)
        print(f"    罰則を除いた Errx（一致した鍵点だけのずれ）[ms] {_q(errx - pen)}")
        crit = {
            f"NRMSE ≤ {pda2.NRMSE_MAX}": nrmse <= pda2.NRMSE_MAX,
            f"Errx ≤ {pda2.ERRX_MS:.0f} ms": errx <= pda2.ERRX_MS,
            f"Erry ≤ {pda2.ERRY}": erry <= pda2.ERRY,
            "鍵点 2 点以上": nlm >= 2,
            f"SE ≤ {pda2.SE_DT_MAX_MS:.0f} ms（有限）": np.isfinite(se) & (se <= pda2.SE_DT_MAX_MS),
            "曖昧でない": amb != 1,
            "反射波あり": noref != 1,
        }
        print("    規準ごとの通過率（型1・単独）:")
        for name, c in crit.items():
            print(f"      {name:<22} {np.nanmean(c.astype(float)):6.1%}")
        allc = np.ones(int(m1.sum()), bool)
        for c in crit.values():
            allc &= c
        print(f"      すべて同時                {allc.mean():6.1%}")
        for drop in ("Errx ≤ %.0f ms" % pda2.ERRX_MS, f"Erry ≤ {pda2.ERRY}", f"NRMSE ≤ {pda2.NRMSE_MAX}"):
            c2 = np.ones(int(m1.sum()), bool)
            for name, c in crit.items():
                if name != drop:
                    c2 &= c
            print(f"      {drop} だけ外す      {c2.mean():6.1%}（27番 A 層の行と同じ趣旨。閾値を変える根拠にはしない）")
        print(f"    張り付いた母数のある拍 {np.nanmean((npin > 0).astype(float)):.1%}・成分を増やした {np.nanmean(esc):.1%}"
              f"・増やそうとした {np.nanmean(esct):.1%}・成分数の中央値 {np.nanmedian(nw):.0f}")
        if "prom_own" in d:
            p = d.loc[m1, "prom_own"].to_numpy(float)
            gm = np.isfinite(p) & np.isfinite(errx)
            if gm.sum() >= 8 and np.ptp(p[gm]) > 0:
                from scipy.stats import spearmanr
                r = spearmanr(p[gm], errx[gm]).correlation
                print(f"    顕著さと Errx の順位相関（型1）: {r:+.2f}（負なら切痕が浅い拍ほど鍵点がずれる）")


# ================================================================ B. 数拍の再分解
def _fit_once(t, ys, lm, w, route, nw):
    if route == "skew":
        fit = pda2.fit_waves(t, ys, lm, n_waves=nw, w=w)
    else:
        fit = pda2.fit_gamma(t, ys, lm, n_kernels=nw, w=w)
    if fit is None:
        return None, None
    return fit, fit["model"](fit["sols"][0].x)


def _lm_str(lm):
    f = lambda v: f"{v * 1000:6.0f}" if np.isfinite(v) else "     —"  # noqa: E731
    return f"S{f(lm['sys_t'])} 切痕{f(lm['notch_t'])} D{f(lm['dia_t'])}"


def examples(root: Path, route: str, k: int, out_png: Path | None, klass_want: int = 1) -> list:
    M = _load("20_pwdb_validity.py", "m20")
    hae, cfg, ppg, _ = M.load_pwdb(Path(root).expanduser())
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    age_by = dict(zip(hae["subj_no"].astype(int), hae["age"].astype(float))) if "age" in hae else {}
    picks = []
    stride = max(1, len(ppg) // (k * 12))
    for i in range(0, len(ppg), stride):
        subj = int(ppg.iloc[i, 0])
        y, fs = M.beat_of(ppg.iloc[i].to_numpy(float), hr_by.get(subj, np.nan))
        if y is None:
            continue
        t = np.arange(y.size) / fs
        ys, amp = pda2.preprocess(t, y, fs)
        if ys is None:
            continue
        lm = pda2.find_landmarks(t, ys)
        if lm["klass"] != klass_want:
            continue
        picks.append((subj, t, ys, lm, fs))
        if len(picks) >= k:
            break
    print("=" * 78)
    print(f"B. 型{klass_want} の拍 {len(picks)} 例を再分解（経路 {route}）。データ側と模型側の鍵点 [ms]")
    print("=" * 78)
    print(f"{'被験者':>6} {'年齢':>4} {'HR':>5} {'顕著さ':>6}  {'成分':>4}  {'データ側の鍵点':<28}{'模型側の鍵点':<28}"
          f"{'模型型':>4} {'NRMSE':>7} {'Errx':>6} {'Erry':>6} {'nlm':>4}  採否")
    rows = []
    for subj, t, ys, lm, fs in picks:
        w = pda2._weights(t, lm, pda2.W_KEY)
        nw0 = 2 if route == "skew" else 3
        fits = []
        for nw in (nw0, nw0 + 1):
            fit, yhat = _fit_once(t, ys, lm, w, route, nw)
            if fit is None:
                continue
            acc = pda2.acceptance(t, ys, yhat, lm, w)
            src = lm.get("source")
            lmh = pda2.find_landmarks(t, yhat, force_proxy=(src == "d1"), allow_proxy=(src != "extrema"))
            fits.append((nw, yhat, acc, lmh))
            print(f"{subj:>6} {age_by.get(subj, np.nan):>4.0f} {hr_by.get(subj, np.nan):>5.0f} {lm.get('prom', np.nan):>6.3f}"
                  f"  {nw:>4}  {_lm_str(lm):<28}{_lm_str(lmh):<28}{lmh['klass']:>4} {acc['nrmse']:>7.4f}"
                  f" {acc['errx_ms']:>6.1f} {acc['erry']:>6.3f} {acc['n_landmark_matched']:>4}  {'採用' if acc['ok'] else '不採用'}")
        rows.append((subj, t, ys, lm, fits))
    if out_png is not None and rows:
        try:
            import warnings
            warnings.filterwarnings("ignore")          # 日本語の字形が無いフォントの警告を黙らせる
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(len(rows), 1, figsize=(9, 2.4 * len(rows)), squeeze=False)
            for ax, (subj, t, ys, lm, fits) in zip(axes[:, 0], rows):
                ax.plot(t * 1000, ys, "k", lw=1.8, label="データ")
                for nw, yhat, acc, lmh in fits:
                    ax.plot(t * 1000, yhat, lw=1.2, label=f"模型 {nw} 成分 Errx {acc['errx_ms']:.0f} ms")
                for key, mk in (("sys_t", "o"), ("notch_t", "v"), ("dia_t", "^")):
                    if np.isfinite(lm[key]):
                        ax.plot(lm[key] * 1000, np.interp(lm[key], t, ys), "k" + mk, ms=6)
                    for nw, yhat, acc, lmh in fits:
                        if np.isfinite(lmh[key]):
                            ax.plot(lmh[key] * 1000, np.interp(lmh[key], t, yhat), mk, ms=5, alpha=.7)
                ax.set_title(f"subj {subj}  型{lm['klass']} 顕著さ {lm.get('prom', np.nan):.3f}", fontsize=9)
                ax.legend(fontsize=7, loc="upper right")
            axes[-1, 0].set_xlabel("ms")
            fig.tight_layout()
            out_png.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(out_png, dpi=110)
            print(f"  図: {out_png}（黒＝データ、色＝模型。○ S・▽ 切痕・△ D。黒い印がデータ側、色つきが模型側）")
        except Exception as e:      # noqa: BLE001
            print(f"  図は描けなかった: {e}")
    return rows


# ================================================================ 自己検証
def selftest() -> int:
    import contextlib
    import io
    import tempfile
    import pandas as pd
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}")

    print("== 29_pwdb_reject_diag 自己検証（模擬 PWDB・ネットワーク不要） ==\n")
    csv = OUT / "_selftest_pwdb_compare.csv"
    if csv.exists():
        d = pd.read_csv(csv)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            describe_csv(d)
        out = buf.getvalue()
        rep("A: 26番の自己検証 CSV から型・規準ごとの記述が出る", "規準ごとの通過率" in out and "nlm" in out)
        rep("A: 型1 の全規準同時の通過率が採択率と一致する",
            abs(float(out.split("すべて同時")[1].split("%")[0]) / 100
                - d.loc[d["klass_own"] == 1, "ok_v2"].mean()) < 0.02)
    else:
        rep("A: 26番の自己検証 CSV が無い（先に 26番 --selftest）。A は飛ばす", True)
    C = _load("26_pwdb_compare.py", "m26")
    with tempfile.TemporaryDirectory() as td:
        res = C._selftest_root(Path(td), n=24)
        root = res[0] if isinstance(res, tuple) else res
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rows = examples(root, "skew", 2, Path(td) / "diag.png")
        out = buf.getvalue()
        rep("B: 型1 の拍を再分解し、データ側・模型側の鍵点を並べて印字する", len(rows) == 2 and "模型側の鍵点" in out)
        rep("B: 図が書かれる", (Path(td) / "diag.png").exists())
        with contextlib.redirect_stdout(io.StringIO()):
            rows_g = examples(root, "gamma", 1, None)
        rep("B: ガンマ経路でも動く", len(rows_g) == 1)
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=str(OUT / "pwdb_compare_limit600.csv"))
    ap.add_argument("--pwdb", type=str, default=None, help="指定すると B（数拍の再分解と図）も行う")
    ap.add_argument("--examples", type=int, default=8)
    ap.add_argument("--route", type=str, default="skew", choices=["skew", "gamma"])
    ap.add_argument("--klass", type=int, default=1, help="再分解する拍の型（既定 1）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    import pandas as pd
    p = Path(args.csv).expanduser()
    if p.exists():
        describe_csv(pd.read_csv(p))
    else:
        print(f"{p} がありません（26番を先に回す）")
    if args.pwdb:
        examples(Path(args.pwdb), args.route, args.examples,
                 OUT / f"diag_examples_{args.route}_klass{args.klass}.png", klass_want=args.klass)


if __name__ == "__main__":
    main()
