#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【単体】RI 系の指標は血管抵抗を追うか、それとも血圧を追うか（別マシン用・自己完結）。

37番・38番と同じ問いを、**過去の抽出結果に一切依存せず**に最初から実行する。
必要なのはこのリポジトリのコード（`src/` と 33番）と、VitalDB へのネットワークだけである。
`data/features/`・`data/vasotone/`・`data/target_cases.csv` は要らない。自分で作る。

何を測るか
----------
VitalDB の 60 秒ウィンドウごとに、同じ平均拍から 4 系統の指標を出す。

  ri_v1    凍結版 PDA（歪みガウス2成分）の反射係数 h₂/h₁      … 研究1・研究0 の主指標
  ri_cou   Couceiro 2015 の R1_d ＝ a₄ / max(g₁+g₂)          … 研究0 で唯一 pvr の規準を満たした
  ri_lm    特徴点法の反射係数（拡張期ピーク高さ ÷ 収縮期ピーク高さ）
  amb      早期振幅比 Am_b/Am_p1（上行脚のみ・当てはめ不要）

同じウィンドウの平均血圧（動脈圧波形の平均）と、EV1000/SVR を突き合わせる。

判別試験
--------
MAP ≒ CO × SVR なので血管抵抗と血圧は解離しうる。**両者が逆向きに動いたウィンドウで、
指標がどちらを追うかを見る。**SVR 側が 0 近傍で MAP 側が正なら、その指標は血圧を追っている。
MAP で調整した偏相関は主解析にしない（RI が血管収縮を測るなら MAP はその結果であり、
調整すると真の信号まで削るため）。

**限界（結果を見る前に書いておく）**
EV1000 の SVR は (MAP−CVP)×80/CO で MAP を分子に含み、CO も動脈圧波形由来である。
したがって逆向きウィンドウは定義上「FloTrac の CO が動いた」ウィンドウであり、
そこでの相関は「指標は FloTrac の CO 推定を逆に追うか」に化ける。**陽性は証明にならない。**
SVR 方向にまったく動かない場合にのみ足切りとして意味を持つ。判定（roadmap §9・§12）は動かさない。

使い方
------
    pip install numpy pandas scipy vitaldb
    python3 scripts/39_ri_svr_standalone.py --selftest              # ネットワーク不要
    python3 scripts/39_ri_svr_standalone.py --lists                 # 症例表を取得（初回のみ）
    python3 scripts/39_ri_svr_standalone.py --run --limit 40 --jobs 4
    python3 scripts/39_ri_svr_standalone.py --run --jobs 4          # 全例
    python3 scripts/39_ri_svr_standalone.py --stats
    python3 scripts/39_ri_svr_standalone.py --diag      # 症例ごとの脱落の内訳

出力
----
    data/standalone/cases.csv          … 対象症例の一覧（自分で作る）
    data/standalone/case_{id}.csv      … ウィンドウごとの指標。**再実行はここから読むので無料**
    ../docs/research/results/39_ri_svr_standalone.txt
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import pda2                                                  # noqa: E402
from src.beats import segment_beats, sqi, ensemble_average            # noqa: E402
from src.pda import fit_beat                                          # noqa: E402
from src.indices import si_ri_from_fit                                # noqa: E402


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M33 = _load("33_pwdb_literature_replica.py", "m33_39")

FS = 500.0            # 波形の標本化周波数
WIN_S = 60.0          # 解析ウィンドウ長（研究1 と同一）
MIN_GOOD = 8          # ウィンドウに要求する品質通過拍数（研究1 と同一）
MIN_WIN = 12          # 症例に要求する有効ウィンドウ数（研究1 と同一）
MIN_PAIR = 10         # 部分集合の相関に要求する最小組数
FLAT = 0.02           # 「MAP がほぼ動いていない」とみなす相対変化の幅
N_BOOT = 2000
WAVES = ["SNUADC/PLETH", "SNUADC/ECG_II", "SNUADC/ART"]
SVR_TRACK = "EV1000/SVR"
NAN = float("nan")

DATA = ROOT / "data"
OUT = DATA / "standalone"
INDEX_COLS = ("ri_v1", "ri_cou", "ri_lm", "amb")
INDEX_NAME = {"ri_v1": "凍結版 PDA の RI（2成分）", "ri_cou": "Couceiro R1_d（5成分）",
              "ri_lm": "特徴点法の RI", "amb": "早期振幅比 Am_b/Am_p1"}


# ════════════════════════════════════════════════ 相対変化と統計
def rel(x: np.ndarray) -> np.ndarray:
    """研究1 と同一の相対変化。初回を基準にし、分母に系列の中央絶対値の5%の床を敷く。"""
    x = np.asarray(x, float)
    if x.size == 0 or not np.isfinite(x[0]):
        return np.full(x.shape, NAN)
    denom = max(abs(x[0]), 0.05 * float(np.nanmedian(np.abs(x))), 1e-9)
    return (x - x[0]) / denom


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 5:
        return NAN
    a, b = x[m], y[m]
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return NAN
    ra, rb = pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


def sign_test(v: np.ndarray, positive: bool = True) -> tuple[int, int, float]:
    v = v[np.isfinite(v) & (v != 0)]
    n = v.size
    if n == 0:
        return 0, 0, NAN
    k = int((v > 0).sum()) if positive else int((v < 0).sum())
    tail = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return k, n, float(min(1.0, 2 * tail))


def boot_ci(v: np.ndarray, seed: int = 0) -> tuple[float, float]:
    v = v[np.isfinite(v)]
    if v.size < 3:
        return NAN, NAN
    rng = np.random.default_rng(seed)
    med = [float(np.median(rng.choice(v, v.size, replace=True))) for _ in range(N_BOOT)]
    return float(np.percentile(med, 2.5)), float(np.percentile(med, 97.5))


# ════════════════════════════════════════════════ 1拍から4指標
def indices_on_beat(y: np.ndarray, fs: float = FS) -> dict:
    out = {c: NAN for c in INDEX_COLS}
    t = np.arange(len(y)) / fs
    try:                                    # 凍結版 PDA（研究1 の主指標）
        fit = fit_beat(t, y)
        if fit.get("ok"):
            out["ri_v1"] = float(si_ri_from_fit(fit)["ri"])
    except Exception:      # noqa: BLE001
        pass
    ys, _amp = pda2.preprocess(t, np.asarray(y, float), fs)
    if ys is None:
        return out
    lm = pda2.find_landmarks(t, ys)
    if lm is not None and lm.get("klass") in (1, 3) \
            and np.isfinite(lm.get("dia_v", NAN)) and lm.get("sys_v", 0) > 0:
        out["ri_lm"] = float(lm["dia_v"] / lm["sys_v"])
    try:                                    # 早期振幅比（当てはめ不要）
        a = float(pda2.early_features(t, ys)["amb_amp1"])
        out["amb"] = a if np.isfinite(a) and 0.0 < a <= 1.5 else NAN
    except Exception:      # noqa: BLE001
        pass
    try:                                    # Couceiro R1_d（33番の文献条件そのまま）
        r = M33.fit_couceiro(t, ys, lm, M33.couceiro_points(t, ys, lm))
        out["ri_cou"] = float(r.get("ri_cou", NAN))
    except Exception:      # noqa: BLE001
        pass
    return out


def window_row(seg_p, seg_e, seg_a, t0: float) -> dict | None:
    """1 ウィンドウ → 指標＋平均血圧。研究1 と同じ採否（品質通過拍 8 以上・動脈圧 50% 以上）。"""
    try:
        beats = segment_beats(seg_p, FS, ecg=seg_e)
        good = [(s, e) for s, e in beats if sqi(seg_p[s:e], FS)["ok"]]
    except Exception:      # noqa: BLE001
        return None
    if len(good) < MIN_GOOD:
        return None
    a = seg_a[np.isfinite(seg_a) & (seg_a > 20) & (seg_a < 300)]
    if a.size < int(0.5 * WIN_S * FS):
        return None
    row = {"t0": float(t0), "n_good": len(good), "map": float(np.mean(a))}
    row.update(indices_on_beat(ensemble_average([seg_p[s:e] for s, e in good])))
    return row


def _task(args):
    t0, seg_p, seg_e, seg_a = args
    try:
        return window_row(seg_p, seg_e, seg_a, t0)
    except Exception:      # noqa: BLE001
        return None


# ════════════════════════════════════════════════ 症例の一覧と抽出
def build_case_list() -> pd.DataFrame:
    """VitalDB のトラック表から、波形3本と EV1000/SVR をすべて持つ症例を選ぶ。"""
    OUT.mkdir(parents=True, exist_ok=True)
    trk = DATA / "trks.csv"
    if not trk.exists():
        print("トラック表を取得中 …")
        DATA.mkdir(parents=True, exist_ok=True)
        pd.read_csv("https://api.vitaldb.net/trks").to_csv(trk, index=False)
    t = pd.read_csv(trk)
    ids = None
    for name in WAVES + [SVR_TRACK]:
        s = set(t.loc[t["tname"] == name, "caseid"].astype(int))
        ids = s if ids is None else (ids & s)
        print(f"  {name:18s} {len(s):5d} 例  → 累積 {len(ids)} 例")
    df = pd.DataFrame({"caseid": sorted(ids)})
    df.to_csv(OUT / "cases.csv", index=False)
    print(f"対象 {len(df)} 例 → {OUT / 'cases.csv'}")
    return df


def extract_case(caseid: int, jobs: int) -> int:
    from multiprocessing import Pool
    import vitaldb
    p = OUT / f"case_{caseid}.csv"
    if p.exists():
        return -1
    wav = vitaldb.load_case(caseid, WAVES, 1 / FS)
    pleth = np.nan_to_num(np.asarray(wav[:, 0], float))
    ecg = np.nan_to_num(np.asarray(wav[:, 1], float))
    art = np.asarray(wav[:, 2], float)
    dur = len(pleth) / FS
    tasks = []
    for t0 in np.arange(0, dur - WIN_S, WIN_S):
        i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
        if pleth[i0:i1].size < int(WIN_S * FS) * 0.9 or not np.any(pleth[i0:i1]):
            continue
        tasks.append((float(t0), pleth[i0:i1], ecg[i0:i1], art[i0:i1]))
    if not tasks:
        return 0
    with Pool(jobs) as pool:
        rows = [r for r in pool.map(_task, tasks) if r]
    if not rows:
        return 0
    pd.DataFrame(rows).to_csv(p, index=False)
    return len(rows)


def window_median(vals_1hz: np.ndarray, t0s: np.ndarray) -> np.ndarray:
    """1秒間隔の数値トラックを 60 秒ウィンドウの中央値に畳む（16番 `_window_median` と同一）。

    **点数の下限を置かない。**EV1000/SVR は 20 秒間隔程度でしか更新されないため、
    「60 秒に n 点以上」を課すとほぼ全ウィンドウが落ちる。有限値が 1 点でもあれば採る。
    """
    out = []
    for t0 in np.asarray(t0s, float):
        seg = vals_1hz[int(t0):int(t0 + WIN_S)]
        seg = seg[np.isfinite(seg)]
        out.append(float(np.median(seg)) if seg.size else NAN)
    return np.array(out, float)


def fetch_svr(caseid: int, force: bool = False) -> int:
    """数値トラック（1秒間隔）だけを取り直す。波形の再取得は要らないので安価。

    **16番の `_window_median` と完全に同じ**にしてある。ウィンドウ内の有限値の中央値を取り、
    点数の下限も値域の絞り込みも置かない。EV1000/SVR は 20 秒間隔程度でしか更新されないため、
    「60 秒に 5 点以上」のような条件を課すとほぼ全ウィンドウが落ちる。
    """
    import vitaldb
    q = OUT / f"svr_{caseid}.csv"
    if q.exists() and not force:
        return -1
    cp = OUT / f"case_{caseid}.csv"
    if not cp.exists():
        return 0
    t0s = pd.read_csv(cp)["t0"].to_numpy(float)
    svr = vitaldb.load_case(caseid, [SVR_TRACK], 1).ravel().astype(float)
    vals = window_median(svr, t0s)
    pd.DataFrame({"t0": t0s, "svr": vals}).to_csv(q, index=False)
    return int(np.isfinite(vals).sum())


def run(limit: int | None, jobs: int) -> None:
    cp = OUT / "cases.csv"
    ids = (pd.read_csv(cp) if cp.exists() else build_case_list())["caseid"].astype(int).tolist()
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
        try:
            ns = fetch_svr(cid)
        except Exception as e:      # noqa: BLE001
            ns = 0
            print(f"      SVR 取得に失敗 {str(e)[:50]}")
        tag = "既にある" if n < 0 else f"{n} ウィンドウ"
        stag = "SVR 既にある" if ns < 0 else f"SVR 有 {ns}"
        print(f"  [{k}/{len(ids)}] {cid}: {tag}・{stag}（{(time.time()-t)/60:.1f} 分）")


# ════════════════════════════════════════════════ 集計
def analyse_case(d: pd.DataFrame, col: str) -> dict | None:
    """1 症例を要約する。**相対変化の基準は「指標・MAP・SVR が3つとも揃う最初のウィンドウ」。**

    ここを取り違えると症例が丸ごと消える。EV1000 は記録開始と同時には繋がらない。
    実測（対象40例・数値トラックのみで確認）では **40例すべてで最初のウィンドウに SVR が無く**、
    初めて出るのは中央値で 21 番目のウィンドウ、最も遅い例で 337 番目（＝5時間半後）だった。
    生の列にそのまま `rel` を掛けると先頭が NaN で系列全体が NaN になり、解析できる症例が
    ほぼ消える。37番が svr の欠測行を先に落としているのと同じ処理を、3 列すべてに行う。
    """
    d = d.sort_values("t0")
    v0 = d[col].to_numpy(float)
    m0 = d["map"].to_numpy(float)
    s0 = d["svr"].to_numpy(float)
    ok = np.isfinite(v0) & np.isfinite(m0) & np.isfinite(s0)
    if ok.sum() < MIN_WIN:
        return None
    x, mp, sv = rel(v0[ok]), rel(m0[ok]), rel(s0[ok])
    # 3 つの集合は互いに素にする。MAP がほぼ動いていないウィンドウ（|ΔMAP%| < 2%）は、
    # 符号がどちらであっても「平坦」に入れる。0.5% の変化を「逆向き」と数えると
    # 雑音の符号を読むことになるため。**37番・38番はこの排除をしておらず、
    # 逆向きに平坦を含んでいた**（全ウィンドウの数%）ので、値がわずかに異なる。
    flat = (np.abs(mp) < FLAT) & (np.abs(sv) >= FLAT)         # MAP 平坦で SVR が動く
    opp = (np.sign(sv) * np.sign(mp) < 0) & ~flat             # 逆向き（厳格・排他）
    conc = (np.sign(sv) * np.sign(mp) > 0) & ~flat            # 一致（同上）
    sub = lambda m, a, b: spearman(a[m], b[m]) if m.sum() >= MIN_PAIR else NAN  # noqa: E731
    return {"n": int(ok.sum()), "n_opp": int(opp.sum()), "n_flat": int(flat.sum()),
            "n_conc": int(conc.sum()),
            "rho_svr": spearman(x, sv), "rho_map": spearman(x, mp),
            "rho_svr_map": spearman(sv, mp),
            "opp_svr": sub(opp, x, sv), "opp_map": sub(opp, x, mp),
            "flat_svr": sub(flat, x, sv), "conc_svr": sub(conc, x, sv)}


def load_frames() -> list[tuple[int, pd.DataFrame]]:
    """case_*.csv に svr_*.csv を結合して返す。集計と診断の両方が同じ経路を通る。"""
    frames = []
    for f in sorted(OUT.glob("case_*.csv")):
        cid = int(f.stem.split("_")[1])
        d = pd.read_csv(f)
        q = OUT / f"svr_{cid}.csv"
        if q.exists():                                   # 新しい取り方を優先
            d = d.drop(columns=[c for c in ("svr",) if c in d.columns])
            d = d.merge(pd.read_csv(q), on="t0", how="left")
        elif "svr" not in d.columns:
            continue
        frames.append((cid, d.sort_values("t0")))
    return frames


def diagnose() -> int:
    """**どこで症例が落ちたかを症例ごとに出す。**

    39番の初版はここが見えなかったために、二つの取り違えを続けて見逃した。
    (1) SVR ウィンドウ中央値に点数の下限を置いていた（EV1000 は 20 秒間隔なので大半が脱落）。
    (2) 相対変化の基準を「最初の行」に取っていた（EV1000 は記録開始と同時には繋がらないので、
        最初の行の SVR は原則 NaN。系列全体が NaN になり症例が丸ごと消える）。
    どちらも「解析できた症例が少ない」としか見えず、指標の性質の話に見えてしまう。
    この表があれば、脱落が指標側なのか SVR 側なのかが一目で分かる。
    """
    frames = load_frames()
    if not frames:
        print("先に --lists と --run を実行すること。")
        return 1
    print("=" * 96)
    print("【診断】症例ごとの脱落の内訳（39番）")
    print("=" * 96)
    print(f"{'caseid':>7s}{'全':>6s}{'MAP有':>7s}{'SVR有':>7s}{'SVR初出':>8s}"
          + "".join(f"{c:>9s}" for c in INDEX_COLS)
          + "".join(f"{'3揃 '+c:>11s}" for c in INDEX_COLS))
    rows = []
    for cid, d in frames:
        sv = d["svr"].to_numpy(float) if "svr" in d.columns else np.full(len(d), NAN)
        mp = d["map"].to_numpy(float)
        first = int(np.flatnonzero(np.isfinite(sv))[0]) if np.isfinite(sv).any() else -1
        rec = {"caseid": cid, "n": len(d), "n_map": int(np.isfinite(mp).sum()),
               "n_svr": int(np.isfinite(sv).sum()), "first_svr": first}
        for c in INDEX_COLS:
            v = d[c].to_numpy(float) if c in d.columns else np.full(len(d), NAN)
            rec[f"n_{c}"] = int(np.isfinite(v).sum())
            rec[f"ok_{c}"] = int((np.isfinite(v) & np.isfinite(mp) & np.isfinite(sv)).sum())
        rows.append(rec)
        print(f"{cid:>7d}{rec['n']:>6d}{rec['n_map']:>7d}{rec['n_svr']:>7d}{first:>8d}"
              + "".join(f"{rec[f'n_{c}']:>9d}" for c in INDEX_COLS)
              + "".join(f"{rec[f'ok_{c}']:>11d}" for c in INDEX_COLS))
    t = pd.DataFrame(rows)
    print("-" * 96)
    print(f"症例 {len(t)}・ウィンドウ計 {int(t['n'].sum()):,}")
    print(f"SVR が最初のウィンドウから出ている症例: {int((t['first_svr'] == 0).sum())} / {len(t)}"
          f"　（初出の中央値 {int(t.loc[t.first_svr >= 0, 'first_svr'].median())} 番目・"
          f"最遅 {int(t['first_svr'].max())} 番目）")
    for c in INDEX_COLS:
        n_ok = int((t[f"ok_{c}"] >= MIN_WIN).sum())
        print(f"  {INDEX_NAME[c]:24s} 3列そろうウィンドウ計 {int(t[f'ok_{c}'].sum()):>7,}"
              f"・{MIN_WIN} 以上ある症例 {n_ok:>3d} / {len(t)}")
    print("""
  【読み方】「SVR初出」が 0 でない症例は、生の列にそのまま相対変化を掛けると全 NaN になる。
  EV1000 は記録開始と同時には繋がらないので、これが普通である。`analyse_case` は
  3 列がそろう最初のウィンドウを基準に取り直しているので、この列が 0 でなくてよい。""")
    print("=" * 96)
    return 0


def line(out: list, name: str, v: np.ndarray) -> None:
    """1 行を組み立てる。**符号検定は観測された中央値の向きで数える。**

    常に「正の側」で数えると、中央値が負のときに p=1 と出て「関連なし」に見えてしまう。
    実際には負の向きに偏っている（例: 早期振幅比 × ΔMAP% は 39 例中 28 例が負で
    両側 p=0.0095 だが、正の側で数えると 11/39・p=1 と表示されていた）。
    符号は「一致」欄に + / − を付けて示す。
    """
    lo, hi = boot_ci(v)
    med = float(np.nanmedian(v)) if np.isfinite(v).any() else NAN
    pos = not (np.isfinite(med) and med < 0)
    k, n, p = sign_test(v, positive=pos)
    ci = f"[{lo:+.3f}, {hi:+.3f}]" if np.isfinite(lo) else "—"
    tag = f"{'+' if pos else '−'}{k}/{n}"
    out.append(f"{name:36s}{med:>+9.3f}{ci:>22s}{tag:>10s}{p:>10.2g}")


def stats() -> int:
    files = sorted(OUT.glob("case_*.csv"))
    out = ["=" * 84,
           "【単体・探索】RI 系は血管抵抗を追うか、血圧を追うか（39番）",
           "roadmap §9・§12 の判定は動かさない。仮説生成のための解析である。",
           "=" * 84,
           f"\n抽出済み症例ファイル: {len(files)}"]
    if not files:
        out.append("\n先に --lists と --run を実行すること。")
        print("\n".join(out))
        return 1
    pairs = load_frames()
    frames = [d for _cid, d in pairs]
    got = int(sum(np.isfinite(d["svr"]).sum() for d in frames))
    tot = int(sum(len(d) for d in frames))
    first0 = sum(1 for d in frames
                 if np.isfinite(d["svr"].to_numpy(float)[:1]).all() and len(d))
    out.append(f"SVR が取れたウィンドウ: {got:,} / {tot:,}（{got/max(tot,1):.1%}）"
               f"　うち最初のウィンドウから SVR がある症例 {first0} / {len(frames)}")
    if tot and got / tot < 0.5:
        out.append("  ★ SVR の被覆が半分未満である。`--refresh-svr` で数値トラックを取り直すこと。")
    for col in INDEX_COLS:
        rows, n_skip = [], 0
        for d in frames:
            if col not in d.columns:
                continue
            r = analyse_case(d, col)
            rows.append(r) if r else None
            n_skip += 0 if r else 1
        if not rows:
            out.append(f"\n■ {INDEX_NAME[col]}: 解析できる症例なし")
            continue
        df = pd.DataFrame(rows)
        out.append(f"\n■ {INDEX_NAME[col]}（{len(df)} 例・ウィンドウ計 {int(df['n'].sum()):,}"
                   + (f"・有効ウィンドウ {MIN_WIN} 未満で除外 {n_skip} 例）" if n_skip else "）"))
        out.append(f"{'量':36s}{'中央値':>9s}{'95%CI':>22s}{'符号一致':>10s}{'p':>10s}"
                   "\n  （符号一致は中央値の向きに揃えた症例数／全症例。p は両側符号検定）")
        line(out, "ρ(Δ指標%, ΔSVR%)  全ウィンドウ", df["rho_svr"].to_numpy(float))
        line(out, "ρ(Δ指標%, ΔMAP%)  全ウィンドウ", df["rho_map"].to_numpy(float))
        line(out, "ρ(ΔSVR%, ΔMAP%)   解離の程度", df["rho_svr_map"].to_numpy(float))
        out.append("")
        line(out, "★ ρ(Δ指標%, ΔSVR%)  逆向きのみ", df["opp_svr"].to_numpy(float))
        line(out, "★ ρ(Δ指標%, ΔMAP%)  逆向きのみ", df["opp_map"].to_numpy(float))
        line(out, "  ρ(Δ指標%, ΔSVR%)  MAP平坦", df["flat_svr"].to_numpy(float))
        line(out, "  ρ(Δ指標%, ΔSVR%)  一致のみ", df["conc_svr"].to_numpy(float))
        tot = int(df["n"].sum())
        out.append(f"  逆向き {int(df['n_opp'].sum()):,}（{df['n_opp'].sum()/tot:.1%}）"
                   f"・MAP平坦 {int(df['n_flat'].sum()):,}（{df['n_flat'].sum()/tot:.1%}）"
                   f"・一致 {int(df['n_conc'].sum()):,}（{df['n_conc'].sum()/tot:.1%}）")
    out.append("""
  【読み方】判別試験は ★ の2行である。血管抵抗と血圧が逆向きに動いたウィンドウで、
  指標がどちらを追うかを見る。SVR 側が 0 近傍で MAP 側が正なら、その指標は血圧を追っている。
  【37番・38番との差】本スクリプトは「逆向き」「MAP平坦」「一致」を互いに素にしている。
  |ΔMAP%| < 2% のウィンドウは符号によらず「平坦」に入れる。37番・38番は平坦を逆向きから
  排除しておらず、逆向きに数%の平坦ウィンドウを含んでいた。値がわずかに異なるのはこのためで、
  本スクリプトの定義のほうが厳格である。
  【限界】EV1000 の SVR は (MAP−CVP)×80/CO で MAP を分子に含み、CO も動脈圧波形由来である。
  逆向きウィンドウは定義上「FloTrac の CO が動いた」ウィンドウなので、そこでの相関は
  「指標は FloTrac の CO 推定を逆に追うか」に化ける。**陽性は証明にならない。**
  成分が独立に測られた抵抗（熱希釈CO＋実測MAP＋実測CVP）でしか決着しない。""")
    out.append("=" * 84)
    text = "\n".join(out)
    print(text)
    dst = ROOT.parent / "docs" / "research" / "results" / "39_ri_svr_standalone.txt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text + "\n", encoding="utf-8")
    print(f"\n書き出し: {dst}", file=sys.stderr)
    return 0


# ════════════════════════════════════════════════ 自己検査（ネットワーク不要）
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

    v = rel(np.array([2.0, 3.0, 4.0]))
    chk("rel 先頭は0・2→3 は +0.5", abs(v[0]) < 1e-12 and abs(v[1] - 0.5) < 1e-12)
    chk("rel 初回0近傍でも発散しない", np.all(np.isfinite(rel(np.array([1e-12, 1.0, 2.0])))))
    x = np.arange(50.0)
    chk("spearman 単調増加=+1", abs(spearman(x, 2 * x + 1) - 1) < 1e-9)
    chk("spearman 定数はNaN", not np.isfinite(spearman(x, np.ones(50))))
    k, n, p = sign_test(np.array([1.0, 1, 1, 1, 1]))
    chk("符号検定 5/5 で p=0.0625", k == 5 and abs(p - 0.0625) < 1e-9)

    fs, t = FS, np.arange(0, 1.0, 1 / FS)
    beat = (1.00 * np.exp(-((t - 0.20) / 0.055) ** 2)
            + 0.45 * np.exp(-((t - 0.33) / 0.070) ** 2)
            + 0.25 * np.exp(-((t - 0.50) / 0.090) ** 2))
    r = indices_on_beat(beat, fs)
    chk("合成拍で R1_d が有限", np.isfinite(r["ri_cou"]))
    chk("合成拍で早期振幅比が有限", np.isfinite(r["amb"]))
    r2 = indices_on_beat(2.0 * beat, fs)
    chk("R1_d は振幅倍率に不変",
        np.isfinite(r["ri_cou"]) and abs(r["ri_cou"] - r2["ri_cou"]) < 0.02)
    chk("平坦な信号は R1_d が NaN", not np.isfinite(indices_on_beat(np.ones(500), fs)["ri_cou"]))

    # 判別試験の陽性・陰性統制（指標が SVR にのみ従う／MAP にのみ従う）
    rng = np.random.default_rng(0)
    n_w = 200
    base_map = 80 * (1 + np.cumsum(rng.normal(0, 0.01, n_w)))
    base_svr = 1000 * (1 + np.cumsum(rng.normal(0, 0.01, n_w)))
    d_svr = pd.DataFrame({"t0": np.arange(n_w) * WIN_S, "map": base_map, "svr": base_svr,
                          "ri_v1": 0.3 * (1 + 0.5 * rel(base_svr))})
    d_map = d_svr.copy()
    d_map["ri_v1"] = 0.3 * (1 + 0.5 * rel(base_map))
    a, b = analyse_case(d_svr, "ri_v1"), analyse_case(d_map, "ri_v1")
    chk("陽性統制: SVR に従う指標は逆向きで SVR 側",
        a is not None and a["n_opp"] >= MIN_PAIR and a["opp_svr"] > 0.5 and a["opp_map"] < 0)
    chk("陰性統制: MAP に従う指標は逆向きで MAP 側",
        b is not None and b["n_opp"] >= MIN_PAIR and b["opp_map"] > 0.5 and b["opp_svr"] < 0)
    chk("ウィンドウ不足は None", analyse_case(d_svr.head(5), "ri_v1") is None)

    # ★ 疎な数値トラックでも値が取れること（39番 初版はここで全ウィンドウを落としていた）
    sparse = np.full(600, NAN)
    sparse[::20] = 1200.0                       # 20 秒間隔＝60秒ウィンドウに 3 点
    wm = window_median(sparse, np.arange(0, 540, WIN_S))
    chk("20秒間隔のSVRでも全ウィンドウで値が取れる",
        np.all(np.isfinite(wm)) and abs(wm[0] - 1200.0) < 1e-9)
    chk("有限値ゼロのウィンドウは NaN",
        not np.isfinite(window_median(np.full(600, NAN), np.array([0.0]))[0]))
    chk("窓中央値は該当区間だけを見る",
        abs(window_median(np.r_[np.full(60, 900.0), np.full(60, 1500.0)],
                          np.array([0.0, 60.0]))[1] - 1500.0) < 1e-9)
    chk("逆向き・一致・平坦が重ならない",
        a is not None and a["n_opp"] + a["n_conc"] + a["n_flat"] <= a["n"])

    # ★ SVR が途中から始まる症例（39番 第2版はここで症例をほぼ全部落としていた）
    # EV1000 は記録開始と同時には繋がらない。実測では対象40例すべてで最初のウィンドウに
    # SVR が無く、初出は中央値 21 番目・最遅 337 番目だった。したがって「最初の行を基準に
    # 相対変化を取る」実装は、この母集団では原則として全症例を落とす。
    LATE = 30
    d_late = d_svr.copy()
    d_late.loc[d_late.index[:LATE], "svr"] = NAN
    c = analyse_case(d_late, "ri_v1")
    chk("SVR が 31 番目から始まる症例でも解析できる", c is not None)
    chk("その症例の有効ウィンドウ数は残りと一致", c is not None and c["n"] == n_w - LATE)
    ref = analyse_case(d_svr.iloc[LATE:].reset_index(drop=True), "ri_v1")
    chk("欠測の前置きは結果を変えない（基準は3列そろう最初のウィンドウ）",
        c is not None and ref is not None
        and abs(c["rho_svr"] - ref["rho_svr"]) < 1e-9
        and abs(c["rho_svr_map"] - ref["rho_svr_map"]) < 1e-9)
    d_lidx = d_svr.copy()
    d_lidx.loc[d_lidx.index[:LATE], "ri_v1"] = NAN
    chk("指標が途中から始まる症例でも解析できる", analyse_case(d_lidx, "ri_v1") is not None)
    chk("先頭が欠測でも ρ(ΔSVR%,ΔMAP%) が NaN にならない",
        c is not None and np.isfinite(c["rho_svr_map"]))

    print(f"\n  {ok}/{ok + len(ng)} PASS" + ("  ALL PASS" if not ng else f"  FAIL: {ng}"))
    return 0 if not ng else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lists", action="store_true", help="症例の一覧を作る（初回のみ）")
    ap.add_argument("--run", action="store_true", help="波形を取得して指標を抽出する")
    ap.add_argument("--stats", action="store_true", help="集計だけ行う")
    ap.add_argument("--refresh-svr", action="store_true",
                    help="波形は再取得せず、SVR の数値トラックだけ取り直す（安価）")
    ap.add_argument("--diag", action="store_true",
                    help="症例ごとの脱落の内訳を出す（どこで落ちたかを見る）")
    ap.add_argument("--selftest", action="store_true", help="ネットワーク不要の自己検査")
    ap.add_argument("--limit", type=int, default=None, help="症例数を絞る（seed 0 で無作為）")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.diag:
        sys.exit(diagnose())
    if a.refresh_svr:
        ids = sorted(int(f.stem.split("_")[1]) for f in OUT.glob("case_*.csv"))
        print(f"SVR を取り直す {len(ids)} 例")
        for k, cid in enumerate(ids, 1):
            try:
                n = fetch_svr(cid, force=True)
                print(f"  [{k}/{len(ids)}] {cid}: SVR 有 {n}")
            except Exception as e:      # noqa: BLE001
                print(f"  [{k}/{len(ids)}] {cid}: 失敗 {str(e)[:50]}")
        sys.exit(stats())
    if a.lists:
        build_case_list()
        if not a.run:
            sys.exit(0)
    if a.run:
        run(a.limit, a.jobs)
        sys.exit(stats())
    if a.stats:
        sys.exit(stats())
    ap.print_help()


if __name__ == "__main__":
    main()
