#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究1c: PDA由来の指標は血管トーヌスを捉えているか（数値トラックのみ・波形不要）。

なぜ必要か
----------
研究1の陽性対照は **年齢と高血圧既往**、すなわち慢性・構造的な血管性状に対してのみ
ΔT の妥当性を示した。しかし esCCO の動的補正が要求するのは **急性の血管トーヌス変化**
であり、そこに対する妥当性は一度も検証していない。ΔT が妥当なスティフネス指標で
ありながら急性トーヌスには盲目、という状態はありうる。この穴が埋まらない限り、
研究1の陰性も今後のどの補正研究も、未検証の測定器の上に立つ。

二段構え
--------
C-2（副次・本スクリプトの既定）
    EV1000/SVR・SVRI を主解析ウィンドウに結合し、症例内で SI・RI との順位相関を見る。
    **限界**: EV1000 の SVR は (MAP−CVP)/CO で、CO は動脈圧波形由来。よって
    部分的に循環しており、単独では否定の根拠にならない。主解析にはしない。

C-1（主解析・SAP-1c 凍結後）
    Orchestra/PHEN_RATE（フェニレフリン）のレート変化を自然実験として使う。
    α₁選択的で直接の変力作用がほぼなく、外因性の介入なので循環論法がない。
    事前予測は **ΔT 短縮・RI 上昇**（血管収縮 → 反射波の到達が早まる）。
    **本スクリプトは既定では実行可能性の下見（症例数・on/off ウィンドウ数・
    遷移回数）しか出さない。** 効果量を見るには --peek が要る。
    C-1 の主解析は SAP-1c を凍結してからでなければ走らせないこと。

限界（先に書いておく）
----------------------
- Orchestra は**輸液ポンプの記録**であり、麻酔科医が手押しした昇圧薬ボーラスは
  記録されない。したがって「非投与期間」に未記録の血管収縮が混入する。
  これは**帰無仮説の側にバイアスする**（＝陽性が出れば信頼できる）
- 昇圧薬投与時は血圧・心拍も同時に動くため、MAP・HR で調整した解析を併記する
- ΔT と SI は症例内で 1+ΔSI% = 1/(1+ΔT%) の関係にあり、順位相関では
  **符号が反転するだけ**。本スクリプトは SI で報告し、ΔT の符号は逆と読む

出力
----
data/vasotone/case_{id}.csv … 主解析と同じ t0 で1行（svr, svri, phen, nepi）

使い方
------
    python scripts/16_vasotone.py --limit 874 --jobs 4
    python scripts/16_vasotone.py --stats-only
    python scripts/16_vasotone.py --stats-only --peek     # C-1 の効果量を覗く
    python scripts/16_vasotone.py --selftest              # ネットワーク不要
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

WIN_S = 60.0
DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
VTONE = DATA / "vasotone"

TRACKS = {"svr": "EV1000/SVR", "svri": "EV1000/SVRI",
          "phen": "Orchestra/PHEN_RATE", "nepi": "Orchestra/NEPI_RATE"}
NUM_HZ = 1.0                     # 数値トラックは1Hzで十分
MIN_PAIRS = 10                   # 症例内相関に要求する最小ウィンドウ数


# ---------------------------------------------------------------- 抽出
def _window_median(vals: np.ndarray, t0: float) -> float:
    """数値トラック（1Hz）を主解析ウィンドウ [t0, t0+60) の中央値に畳む。"""
    i0, i1 = int(t0 * NUM_HZ), int((t0 + WIN_S) * NUM_HZ)
    seg = vals[i0:i1]
    seg = seg[np.isfinite(seg)]
    return float(np.median(seg)) if seg.size else float("nan")


def case_tracks(caseid: int, available: set[str]) -> dict:
    """症例が実際に持つトラックだけを取得する。持たない列は NaN で返す。"""
    import vitaldb
    want = [k for k, t in TRACKS.items() if t in available]
    out = {}
    if not want:
        return out
    arr = vitaldb.load_case(caseid, [TRACKS[k] for k in want], NUM_HZ)
    if arr is None or arr.size == 0:
        return out
    for j, k in enumerate(want):
        out[k] = np.asarray(arr[:, j], float)
    return out


def extract_case_vasotone(caseid: int, available: set[str]) -> tuple:
    import pandas as pd
    outp = VTONE / f"case_{caseid}.csv"
    if outp.exists():
        try:
            return caseid, len(pd.read_csv(outp)), None
        except Exception:
            pass
    try:
        main = pd.read_csv(FEAT / f"case_{caseid}.csv")
    except Exception:
        return caseid, None, "主解析キャッシュなし"
    tr = case_tracks(caseid, available)
    if not tr:
        return caseid, None, "対象トラックなし"
    rows = []
    for t0 in main["t0"]:
        row = {"t0": float(t0)}
        for k in TRACKS:
            row[k] = _window_median(tr[k], float(t0)) if k in tr else float("nan")
        rows.append(row)
    df = pd.DataFrame(rows)
    VTONE.mkdir(parents=True, exist_ok=True)
    df.to_csv(outp, index=False)
    return caseid, len(df), None


def _one(args_tuple):
    caseid, available = args_tuple
    try:
        return extract_case_vasotone(caseid, available)
    except Exception as e:  # noqa: BLE001
        return caseid, None, f"失敗: {e}"


# ---------------------------------------------------------------- 統計
def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    """順位相関。単調変換に不変なので SI と ΔT では符号だけが反転する。"""
    g = np.isfinite(x) & np.isfinite(y)
    if g.sum() < MIN_PAIRS:
        return float("nan")
    a, b = x[g], y[g]
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return float("nan")
    from scipy.stats import rankdata
    ra, rb = rankdata(a), rankdata(b)
    return float(np.corrcoef(ra, rb)[0, 1])


def _sign_test(rhos: np.ndarray) -> tuple:
    """症例ごとの相関が 0 のまわりに散っているだけか、片側に寄っているか。"""
    v = rhos[np.isfinite(rhos)]
    if v.size < 5:
        return float("nan"), float("nan"), 0
    pos = int((v > 0).sum())
    n = int(v.size)
    from scipy.stats import binomtest
    return float(np.median(v)), float(binomtest(pos, n, 0.5).pvalue), n


def _titration_steps(rate: np.ndarray, frac: float = 0.30) -> int:
    """ウィンドウ間で用量が frac 以上変わった回数（0をまたぐ変化も1回と数える）。

    実データのフェニレフリンは持続投与のまま細かく増減されることが多く
    （実測: ある症例で on/off 遷移は少ないが用量は頻繁に動く）、
    on/off の二値だけでは C-1 の材料を大きく取りこぼす。SAP-1c では
    「用量ステップ」を単位に定義するのが妥当かどうか、この数で判断する。
    """
    r = np.nan_to_num(np.asarray(rate, float), nan=0.0)
    if r.size < 2:
        return 0
    a, b = r[:-1], r[1:]
    cross = (a <= 0) != (b <= 0)
    both = (a > 0) & (b > 0)
    rel = np.zeros_like(a, dtype=bool)
    rel[both] = np.abs(b[both] - a[both]) / np.maximum(a[both], 1e-9) >= frac
    return int(np.sum(cross | rel))


def stats(peek: bool) -> None:
    import pandas as pd
    files = sorted(VTONE.glob("case_*.csv"))
    if not files:
        print("data/vasotone/ が空です。先に抽出を走らせてください。")
        return
    print(f"\n{'='*66}\n研究1c 血管トーヌス解析（探索的）\n{'='*66}")

    rows, n_svr, n_phen, n_nepi = [], 0, 0, 0
    trans = steps = 0
    for f in files:
        cid = int(f.stem.split("_")[1])
        try:
            v = pd.read_csv(f)
            m = pd.read_csv(FEAT / f"case_{cid}.csv")
        except Exception:
            continue
        d = m.merge(v, on="t0", how="inner")
        if len(d) < MIN_PAIRS:
            continue
        rec = {"caseid": cid, "n": len(d)}
        if d["svr"].notna().sum() >= MIN_PAIRS:
            n_svr += 1
            rec["rho_svr_si"] = _spearman(d["svr"].to_numpy(), d["si"].to_numpy())
            rec["rho_svr_ri"] = _spearman(d["svr"].to_numpy(), d["ri"].to_numpy())
            rec["rho_svr_map"] = _spearman(d["svr"].to_numpy(), d["map"].to_numpy()) \
                if "map" in d else float("nan")
        for drug, cnt in (("phen", "n_phen"), ("nepi", "n_nepi")):
            r = d[drug].fillna(0.0).to_numpy()
            on = r > 0
            if on.any() and (~on).any():
                if drug == "phen":
                    n_phen += 1
                else:
                    n_nepi += 1
                trans += int(np.sum(np.diff(on.astype(int)) != 0))
                rec[f"{drug}_on"] = int(on.sum())
                rec[f"{drug}_off"] = int((~on).sum())
                rec[f"{drug}_steps"] = _titration_steps(r)
                steps += rec[f"{drug}_steps"]
                if peek:
                    for col in ("si", "ri", "pwtt"):
                        if col in d:
                            a = d[col].to_numpy()[on]
                            b = d[col].to_numpy()[~on]
                            a, b = a[np.isfinite(a)], b[np.isfinite(b)]
                            rec[f"{drug}_{col}_delta"] = (
                                float(np.median(a) / np.median(b) - 1.0)
                                if a.size >= 3 and b.size >= 3 and np.median(b) != 0
                                else float("nan"))
        rows.append(rec)

    df = pd.DataFrame(rows)
    print(f"\n結合できた症例: {len(df)}")
    print(f"  SVR あり           : {n_svr} 例")
    print(f"  フェニレフリン on/off 両方あり: {n_phen} 例")
    print(f"  ノルアドレナリン  同           : {n_nepi} 例")
    print(f"  on/off の遷移回数（合計）     : {trans}")
    print(f"  用量ステップ（±30%以上・合計）: {steps}")

    # ---- C-2: SVR との症例内相関 ----
    if n_svr:
        print(f"\n-- C-2 副次: SVR との症例内順位相関（n={n_svr}例）--")
        print("   事前予測: 血管収縮 → 反射波が早く戻る → ΔT 短縮 → SI 上昇。")
        print("   よって rho(SVR, SI) > 0、rho(SVR, RI) > 0 なら予測どおり。")
        print("   ΔT との相関は SI の符号を反転して読む。\n")
        for lab, col in (("SVR × SI", "rho_svr_si"), ("SVR × RI", "rho_svr_ri"),
                         ("SVR × MAP（参考）", "rho_svr_map")):
            if col not in df:
                continue
            v = df[col].to_numpy(float)
            med, pval, n = _sign_test(v)
            if n < 5:
                n_fin = int(np.isfinite(v).sum())
                print(f"   {lab:20s} 症例数不足（有効 {n_fin} 例 < 5）")
                continue
            frac = float(np.mean(np.abs(v[np.isfinite(v)]) > 0.3))
            print(f"   {lab:20s} 中央値 rho {med:+.3f}  符号検定 p={pval:.4g}  "
                  f"|rho|>0.3 の症例 {frac:.0%}  (n={n})")
        print("\n   注意: EV1000 の SVR は (MAP−CVP)/CO で CO が動脈圧波形由来。")
        print("   部分的に循環しているため、これ単独では妥当性の証明にも否定にもならない。")

    # ---- C-1: 実行可能性 ----
    print(f"\n-- C-1 主解析の実行可能性 --")
    if n_phen + n_nepi == 0:
        print("   昇圧薬の on/off が両方あるウィンドウを持つ症例がありません。")
        print("   コホートを主解析の862例に限らず、PLETH+ECG+ART が揃う3,458例へ")
        print("   広げる必要があります（参照COは不要）。")
    else:
        print(f"   使える症例 {n_phen + n_nepi} 例・on/off 遷移 {trans} 回・"
              f"用量ステップ {steps} 回。")
        if steps > 2 * max(trans, 1):
            print("   用量ステップが on/off 遷移をはるかに上回っています。"
                  "SAP-1c では二値の on/off ではなく用量ステップを解析単位に"
                  "する設計を検討すること。")
    if not peek:
        print("\n   効果量は表示しません。C-1 は SAP-1c を凍結してからの主解析であり、")
        print("   先に結果を見てから定義を決めるのは事前指定の意味を壊します。")
        print("   実行可能性の確認だけが目的なら、これで十分です。")
        print("   どうしても下見が要る場合のみ --peek（探索的・論文には使わない）。")
    else:
        print("\n   ** --peek: 以下は探索的な下見であり、論文には使いません **")
        for drug in ("phen", "nepi"):
            for col in ("si", "ri", "pwtt"):
                k = f"{drug}_{col}_delta"
                if k in df and df[k].notna().any():
                    v = df[k].dropna().to_numpy()
                    med, pval, n = _sign_test(v)
                    print(f"   {drug} 投与時の {col:5s} 相対変化 中央値 {med:+.3%}  "
                          f"符号検定 p={pval:.4g}  (n={n})")

    outp = DATA / "vasotone_summary.csv"
    df.to_csv(outp, index=False)
    print(f"\n症例別の要約: {outp}")


# ---------------------------------------------------------------- 自己検証
def selftest() -> int:
    print("== 16_vasotone 自己検証（合成データ・ネットワーク不要） ==\n")
    ok = True
    rng = np.random.default_rng(0)

    # ウィンドウ畳み込み: 1Hz の値を60秒窓の中央値にできるか
    vals = np.arange(600, dtype=float)
    got = _window_median(vals, 120.0)
    w_ok = abs(got - 149.5) < 1e-6
    ok &= w_ok
    print(f"  ウィンドウ中央値 t0=120s → {got}（期待 149.5）  {'PASS' if w_ok else 'FAIL'}")

    # 順位相関: 既知の単調関係を拾えるか、単調変換で符号だけ反転するか
    x = rng.normal(size=200)
    y = 2.0 * x + 0.3 * rng.normal(size=200)
    r_pos = _spearman(x, y)
    r_inv = _spearman(x, 1.0 / (1.0 + 0.1 * y))     # SI ↔ ΔT の関係と同じ形
    s_ok = r_pos > 0.8 and r_inv < -0.8
    ok &= s_ok
    print(f"  順位相関 rho(x,y)={r_pos:+.3f} / 単調逆変換 {r_inv:+.3f}"
          f"（符号のみ反転）  {'PASS' if s_ok else 'FAIL'}")

    # 欠測・定数入力で落ちないか
    n_ok = (not np.isfinite(_spearman(np.full(50, np.nan), np.arange(50.0)))
            and not np.isfinite(_spearman(np.ones(50), np.arange(50.0)))
            and not np.isfinite(_spearman(np.arange(5.0), np.arange(5.0))))
    ok &= n_ok
    print(f"  全欠測・定数・本数不足で NaN を返す  {'PASS' if n_ok else 'FAIL'}")

    # 符号検定: 片側に寄った分布を検出できるか / 0中心を検出しないか
    med1, p1, _ = _sign_test(rng.normal(0.4, 0.2, 100))
    med0, p0, _ = _sign_test(rng.normal(0.0, 0.3, 100))
    t_ok = p1 < 0.01 and p0 > 0.05
    ok &= t_ok
    print(f"  符号検定 偏りあり p={p1:.2g} / 0中心 p={p0:.2g}  {'PASS' if t_ok else 'FAIL'}")

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=874)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--stats-only", action="store_true")
    ap.add_argument("--peek", action="store_true",
                    help="C-1 の効果量を下見する（探索的・論文には使わない）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    import pandas as pd
    if not args.stats_only:
        trks_p = DATA / "trks.csv"
        avail: dict[int, set[str]] = {}
        if trks_p.exists():
            t = pd.read_csv(trks_p)
            want = set(TRACKS.values())
            t = t[t["tname"].isin(want)]
            for cid, g in t.groupby("caseid"):
                avail[int(cid)] = set(g["tname"])
            print(f"trks.csv から対象トラックを持つ症例 {len(avail)} 件を特定しました")
        else:
            print("警告: data/trks.csv がありません。全症例に問い合わせます（遅くなります）")

        tc = pd.read_csv(DATA / "target_cases.csv")
        work = []
        for cid in tc["caseid"].astype(int):
            if len(work) >= args.limit:
                break
            if not (FEAT / f"case_{cid}.csv").exists():
                continue
            a = avail.get(int(cid), set(TRACKS.values()) if not avail else set())
            if a:
                work.append((int(cid), a))
        print(f"{len(work)} 症例を処理します / jobs={args.jobs}", flush=True)

        tally = Counter()
        if args.jobs > 1:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(max_workers=args.jobs) as ex:
                futs = {ex.submit(_one, w): w[0] for w in work}
                for n, fu in enumerate(as_completed(futs), 1):
                    cid, nn, err = fu.result()
                    tally["ok" if err is None else "skip"] += 1
                    print(f"[{n}/{len(work)}] caseid={cid}: "
                          + (f"skip（{err}）" if err else f"{nn} ウィンドウ"), flush=True)
        else:
            for n, w in enumerate(work, 1):
                cid, nn, err = _one(w)
                tally["ok" if err is None else "skip"] += 1
                print(f"[{n}/{len(work)}] caseid={cid}: "
                      + (f"skip（{err}）" if err else f"{nn} ウィンドウ"), flush=True)
        print(f"\n抽出完了: ok {tally['ok']} / skip {tally['skip']}")

    stats(args.peek)


if __name__ == "__main__":
    main()
