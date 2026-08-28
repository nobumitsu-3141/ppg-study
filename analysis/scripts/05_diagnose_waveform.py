# -*- coding: utf-8 -*-
"""実波形の素性を調べる診断スクリプト（合成データの想定と食い違う点を洗い出す）。

実行:  python scripts/05_diagnose_waveform.py 1

出力:
 1. 脈波・心電図の値の分布（スケール・極性・飽和の有無）
 2. R波に揃えた平均脈波テンプレート（波形の形そのものを数値で表示）
 3. 拍長・PWTT・ノイズの分布
 4. data/excerpt_case{id}.csv に30秒の抜粋を保存（詳細解析用・公開データなので共有可）
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.beats import segment_beats, estimate_noise  # noqa: E402
from src.indices import detect_r_peaks  # noqa: E402

FS = 500.0
TRACKS = ["SNUADC/PLETH", "SNUADC/ECG_II"]
T0_MIN, DUR_MIN = 10.0, 5.0        # 解析に使う区間（02 と同じ）


def describe(name: str, x: np.ndarray) -> None:
    q = np.nanpercentile(x, [0, 1, 25, 50, 75, 99, 100])
    print(f"  {name:8s} min {q[0]:9.3f} | 1% {q[1]:8.3f} | 中央 {q[3]:8.3f} | "
          f"99% {q[5]:8.3f} | max {q[6]:9.3f}")
    d = np.diff(x)
    flat = int(np.max(np.diff(np.flatnonzero(np.concatenate(([True], d != 0, [True]))))))
    print(f"           NaN {np.mean(np.isnan(x)):.1%} / 同一値の最長連続 {flat} サンプル "
          f"({flat/FS*1000:.0f} ms) / 値の種類 {len(np.unique(np.round(x,4))):,}")


def main() -> None:
    caseid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    import vitaldb
    print(f"caseid={caseid} を取得中 …")
    v = vitaldb.load_case(caseid, TRACKS, 1 / FS)
    i0 = int(T0_MIN * 60 * FS)
    pleth = np.nan_to_num(v[i0:i0 + int(DUR_MIN * 60 * FS), 0])
    ecg = np.nan_to_num(v[i0:i0 + int(DUR_MIN * 60 * FS), 1])
    print(f"解析区間: {T0_MIN:.0f}分目から{DUR_MIN:.0f}分  ({len(pleth):,} サンプル)\n")

    print("[1. 値の分布]")
    describe("PLETH", pleth)
    describe("ECG", ecg)

    r = detect_r_peaks(ecg, FS)
    rr = np.diff(r) / FS
    rr = rr[(rr > 0.3) & (rr < 2.0)]
    print(f"\n[2. 心電図] R波 {len(r)} 個, HR 中央値 {60/np.median(rr):.0f} 拍/分 "
          f"(RR {np.median(rr)*1000:.0f} ms, IQR {np.percentile(rr,25)*1000:.0f}–"
          f"{np.percentile(rr,75)*1000:.0f})")

    # --- R波に揃えた平均脈波テンプレート（波形の形を数値で見る） ---
    pre, post = int(0.1 * FS), int(1.0 * FS)
    segs = [pleth[i - pre:i + post] for i in r
            if i - pre >= 0 and i + post <= len(pleth)]
    print(f"\n[3. R波に揃えた平均脈波テンプレート]  n={len(segs)} 拍")
    if segs:
        tpl = np.median(np.vstack(segs), axis=0)
        tpl = tpl - tpl.min()
        step = int(0.025 * FS)
        print("   R波からの時間[ms] : 値（最小値を0に揃え、最大値で正規化）")
        norm = tpl / max(tpl.max(), 1e-12)
        for row0 in range(0, len(tpl), step * 8):
            cells = []
            for k in range(row0, min(row0 + step * 8, len(tpl)), step):
                cells.append(f"{(k-pre)/FS*1000:+5.0f}:{norm[k]:.2f}")
            print("   " + "  ".join(cells))
        i_pk = int(np.argmax(tpl))
        print(f"   → 最大値の位置: R波から {(i_pk-pre)/FS*1000:+.0f} ms"
              f"  （正常な脈波なら +200〜+400 ms 付近）")
        d1 = np.gradient(tpl)
        i_up = int(np.argmax(d1[:i_pk + 1])) if i_pk > 0 else 0
        print(f"   → 最大立ち上がりの位置: R波から {(i_up-pre)/FS*1000:+.0f} ms")
        rr_med = float(np.median(rr)) if len(rr) else float("nan")
        print(f"   ※ RR={rr_med*1000:.0f} ms なので、R波から {rr_med*1000:.0f} ms 以降の山は"
              f"【次の心拍】であって反射波ではない")

        # --- テンプレート1拍にPDAを当てて、この症例が分解可能かを判定する ---
        from src.pda import fit_beat
        from src.indices import si_ri_from_fit
        # 拍頭（収縮期ピーク手前の谷）から次拍の直前までを1拍として切り出す。
        # 立ち上がり点から切ると先頭が非ゼロになり、定数項の無いモデルが破綻する。
        i_end = min(pre + int(rr_med * FS), len(tpl)) if np.isfinite(rr_med) else len(tpl)
        i_foot = int(np.argmin(tpl[:i_pk + 1])) if i_pk > 0 else 0
        seg = tpl[i_foot:i_end]
        print(f"   （1拍の切り出し: R波から {(i_foot-pre)/FS*1000:+.0f} ms 〜 "
              f"{(i_end-pre)/FS*1000:+.0f} ms）")
        if seg.size > int(0.2 * FS):
            try:
                f = fit_beat(np.arange(len(seg)) / FS, seg, compute_valley=True)
                m = si_ri_from_fit(f)
                c = f["components"]
                print(f"\n[3b. テンプレート1拍へのPDA当てはめ]（この症例が分解可能かの判定）")
                print(f"   成分1 ピーク {c[0]['t_peak']*1000:5.0f} ms 高さ {c[0]['height']:.3f}  /  "
                      f"成分2 ピーク {c[1]['t_peak']*1000:5.0f} ms 高さ {c[1]['height']:.3f}")
                print(f"   ΔT={m['dt_s']*1000:.0f} ms  RI={m['ri']:.2f}  nrmse={f['nrmse']:.4f}  "
                      f"収束検算 ok={f['ok']}")
                vw = f["checks"]["valley_width_s"] * 1000
                print(f"   谷の幅 {vw:.0f} ms（ΔT {m['dt_s']*1000:.0f} ms に対し十分狭ければ"
                      f"位置が定まっている）")
                if f["ok"] and 0.1 <= m["ri"] <= 1.0:
                    print("   → この症例は解析可能。個々のウィンドウで異常が出るなら前処理側の問題")
                else:
                    print("   → 平均波形ですら分解できない。この症例は解析対象から外す候補")
            except Exception as e:
                print(f"\n[3b] テンプレートの当てはめ失敗: {e}")

    # --- 拍とノイズ ---
    b = segment_beats(pleth, FS, ecg=ecg)
    dur_min = len(pleth) / FS / 60
    print(f"\n[4. 拍の切り出し] {len(b)} 拍 ({len(b)/dur_min:.0f} 拍/分), "
          f"R波比 {len(b)/max(len(r),1):.2f}")
    if b:
        L = np.array([e - s for s, e in b]) / FS
        print(f"   拍長 中央値 {np.median(L)*1000:.0f} ms "
              f"(IQR {np.percentile(L,25)*1000:.0f}–{np.percentile(L,75)*1000:.0f}, "
              f"範囲 {L.min()*1000:.0f}–{L.max()*1000:.0f})")
        sg = np.array([estimate_noise(pleth[s:e]) for s, e in b])
        print(f"   相対ノイズ 中央値 {np.median(sg):.4f} "
              f"(IQR {np.percentile(sg,25):.4f}–{np.percentile(sg,75):.4f})")

    out = Path(__file__).resolve().parent.parent / "data" / f"excerpt_case{caseid}.csv"
    n = int(30 * FS)
    np.savetxt(out, np.column_stack([np.arange(n) / FS, pleth[:n], ecg[:n]]),
               delimiter=",", header="t_s,pleth,ecg", comments="", fmt="%.4f")
    print(f"\n[5. 抜粋を保存] {out}  (30秒, {out.stat().st_size/1e3:.0f} KB)")
    print("   ← このファイルをチャットに添付してください（公開データなので共有可）")


if __name__ == "__main__":
    main()
