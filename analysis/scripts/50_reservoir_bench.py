#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・事後】論文2: 当てはめの型を変えると真の反射波の到達と大きさを追えるか
（節A・節A-2・合成）と、凍結版 ΔT・RI の崩れ方は実データにも出るか（節B・PWDB）。

**これは事後の探索であり、論文2 の事前規準による判定（26番）は動かさない。**
26番（`26_pwdb_compare.py`）で下した判定はそのまま有効で、この台本の出力はすべて
「探索的（事後）」として読む。この台本は成立・不成立の判定を出さない。

なぜ必要か
----------
48番 節4（`48_pwdb_by_waveform_type.py`）で、凍結版 PDA の第2成分のピークは特徴点法の
拡張期側の点より、型1 で +36.9 ms・型3 で +98.5 ms 遅かった（lab_log 2026-09-14 追記140）。
なぜそうなるかを合成脈波で調べたところ、**凍結版の ΔT は真の反射波の到達が約 150 ms を
下回ると下限で詰まり、真値が違っても同じ値を返す。**貯留槽の時定数 0.45 s のとき、
真の ΔT → 凍結版が返した ΔT [ms] は次のとおりであった。

    332→332・300→298・268→264・234→228・158→162・138→142・118→134・98→132・78→174・58→174

最後の 2 拍は真値が 20 ms 違うのに返り値が同じ 174 ms である。長い側（真値 230 ms 以上）の
誤差は 0〜6 ms なので、失敗は精度ではなく**短い側で順位が消えること**である。26番・48番は
年齢層内の順位相関で判定するので、この詰まりはそのまま ρ の低下になる。

同じ拍での順位相関 ρ（時定数 0.45 s ／ 0.30 s）は、凍結版 0.71／0.81、Δμ の下限を 0.01 s に
緩めると 0.89／0.95、貯留槽を前進波の畳み込みで持つと 1.00／1.00、0.65T までで当てはめると
0.95／0.99、参考の特徴点法 1.00／1.00 であった（監督者が合成脈波で実測した値。
lab_log 2026-09-15 追記141。この台本の節A はこの実測を台本の流儀で作り直したものである）。

この台本は 3 つの節を持つ。節A は反射波の**到達**（ΔT）、節A-2 は反射波の**大きさ**（RI）を
同じ合成脈波で振る。節B は実データ（PWDB）の既存列だけで、合成から立てた予測を確かめる。
**節A-2 のほうが所見は強い**: 反射波が収縮期に重なる条件（型3 相当）では、凍結版の RI は
真の反射が大きいほど小さくなる（ρ −0.89。符号が反転する）。

節A（合成・既定で走る）
-----------------------
当てはめの型を並べ、真の反射波の到達を追えるかを測る（(5)(6) には Δμ の下限だけを凍結版の
ままにした版 (5b)(6b)、(4) には Δμ の下限を 0.01 s に緩めた版 (4b) を足し、先頭に凍結版
そのものを呼ぶ (0) を置いたので、表は 10 行になる）。

  合成脈波   前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）。反射波は
             早く到達するほど幅が広くなり歪みが消える（硬い血管の波形）。雑音は標準偏差
             0.002。**真値は反射波のピーク − 前進波のピーク**（母数の差ではない）
  当てはめ   (0) 凍結版そのもの（`src/pda.py` の `fit_beat` を既定の引数で呼ぶ。起点 8 点・
                 特徴点近傍の解を優先する規則・max_nfev 4000）
             (1) 凍結版 2 カーネル（`src/pda.py` の探索範囲と同じ。Δμ の下限 0.08 s）
             (2) Δμ の下限を 0.01 s に緩める
             (3) 自由な指数減衰を足す（24番 の A1 と同じ形。d·exp(−(t−t0)/τ)）
             (4) 貯留槽を前進波の畳み込みで持つ（res(t) = g·∫g1(s)·e^{−(t−s)/τ}ds。母数は
                 g と τ の 2 つ）
             (4b) 同じ畳み込みで Δμ の下限を 0.01 s に緩める（(2) と (4) の同時適用）
             (5) 第2成分の形を第1成分に縛る（σ2 = c·σ1・α2 = α1）＋ Δμ の下限 0.01 s
             (5b) 同じ形の拘束で、Δμ の下限は凍結版のまま 0.08 s
             (6) 0.65T までで当てはめる ＋ Δμ の下限 0.01 s
             (6b) 同じ打ち切りで、Δμ の下限は凍結版のまま 0.08 s
             (1) 以降は `scipy.optimize.least_squares`（trf・起点 4 点・max_nfev 3000）で、
             **収束検算は課さない**（この節が見たいのは下限で詰まるかどうかで、採否ではない）。
             (0) は `fit_beat` そのものなので収束検算を計算するが、**採否には使わず**、
             通過した拍数を表の下に印字するだけである

             (5)(6) は試作と同じ設定で、形の拘束（打ち切り）と Δμ の下限の**2 つ**が凍結版
             から変わっている。これでは効き目の出どころが読めないので、**一度に 1 つだけ
             変えた** (5b)(6b) を 2026-09-15 に足した。(5)(6) の行は試作と数値が一致する
             ことの記録なので消していない。

             (4b) と (0) も 2026-09-15 に足した。(4b) は「Δμ を緩める・貯留槽を畳み込みで
             持つ、の 2 つをそれぞれと同時に適用したときの結果を出すのか」に答えるための行
             である（(2) と (4) の同時適用）。(0) は凍結版そのものを呼ぶ行で、起点 4 点で
             写した複製 (1) が本体と同じ振る舞いをすることの照合である。
  掃引       貯留槽の時定数 3 通り（0.45・0.35・0.25 s）× 反射波の到達 10 通り（0.30〜0.08 s）。
             時定数を年齢層に見立て、層の中で到達だけを振る（26番の年齢層内 Spearman を模す）
  出す表     型ごとに、時定数の層ごとの 順位相関 ρ・|誤差| の中央値・全拍の最小・
             下限の詰まり（新旧 2 つの規準。下記）、および
             1 拍ずつの表（真値・型・各当てはめの返り値と誤差・特徴点法）

**下限の詰まりの規準（2026-09-15 に差し替えた）**: 真値の小さいほうから 3 拍で、
**返り値の最小がその 3 拍の真値の最大より 30 ms 以上大きい**とき「あり」と印字する。

最初に置いた規準は「その 3 拍の返り値の範囲が 20 ms 未満なら『あり』」であった。これは
**凍結版を取り逃がす**。凍結版の返り値は真値 98 ms で 132 ms と最小になり、さらに短い
真値（78・58 ms）では逆に 174 ms へ増えるので、下位 3 拍の範囲は 42 ms と広く出る。
範囲は「返り値が下に行けないこと」を測っていない（名前どおりの量になっていない）ので、
規準そのものを差し替えた。**結果を見て閾値を緩めたのではなく、測り方の誤りを直した。**
差し替える前の規準も「（参考）下位 3 拍の範囲」として同じ表に残し、表の下に両方の定義を
書く。あわせて**掃引の全拍を通した返り値の最小**も並べる（真値の最小との差が、追えなく
なった大きさである）。

**この節は探索・記述であり、26番の事前規準による判定には一切関与しない。**下限の詰まりの
規準は、この節の表に印を付けるためだけのもので、成立・不成立の判定には使わない。

参考として `pda2.preprocess` → `find_landmarks` の特徴点法（dia_t − sys_t）も同じ拍で出す。

節A-2（合成・既定で走る）
-------------------------
同じ合成脈波で、振るものを反射波の**大きさ**（母数 a_ref）に変え、当てはめが返す RI
（第2成分／第1成分のピーク高さの比 h2/h1）が順位を追うかを測る。

  掃引       反射波の大きさ 7 通り（0.20・0.28・0.35・0.42・0.50・0.58・0.65）× 条件 2 つ。
             条件は**型1 相当**（反射波の到達 0.28 s。遅く分離する）と**型3 相当**
             （到達 0.10 s。収縮期に重なる）で、貯留槽の時定数は 0.35 s に固定する
  当てはめ   節A と同じ 10 行。参考の特徴点法の RI は `dia_v / sys_v`
  真値       2 つ出す。「真の RI」は振った母数 a_ref、「真の比」は合成した成分のピーク
             高さの比（当てはめの h2/h1 と同じ定義）。条件の中では前進波が変わらないので
             両者は比例し、**順位は同じ**である。ρ は母数に対して、|誤差| は比に対して出す
  出す表     条件ごとに 順位相関 ρ・|誤差| の中央値・返り値の範囲・**符号の反転**、
             および 1 拍ずつの表（真の RI・真の比・波形の型・各当てはめの返り値・特徴点法）

**符号の反転の規準（2026-09-15 に、実装の前に決めた）**: ρ が −0.30 より小さいとき
「反転」と印字する。大きさは 20番の `CRIT_RHO`（0.30）と同じで、符号を負にしたものである。
**この印も探索・記述のためだけのもので、26番の事前規準による判定には関与しない。**

監督者が試作で測った値（一致の目安。貯留槽 0.35 s）

    型1 相当  凍結版・Δμ0.01・畳み込み・0.65T・特徴点法のすべてで ρ +1.00。凍結版の
              返り値は真の RI 0.20〜0.65 に対し 0.382・0.442・0.496・0.551・0.614・
              0.679・0.736
    型3 相当  **凍結版 ρ −0.89**（返り値 0.266・0.278・0.268・0.262・0.252・0.239・0.226
              と、真の反射波が大きくなるほど小さくなる）。Δμ0.01 +1.00（0.351〜0.564）、
              畳み込み +1.00（0.151〜0.277）、0.65T +1.00（0.396〜0.714）、
              特徴点法 +1.00（0.304〜0.441）

機構: 型3 相当では反射波が前進波に融合するので、真の反射が大きいほど**第1成分が高く
なる**。一方、第2成分は貯留槽の下降の上に固定されて高さが変わらない。したがって比
h2/h1 は**下がる**。

節B（実データ・`--csv` があれば走る）
-------------------------------------
既存の `data/pwdb/pwdb_compare.csv`（26番の出力・確認的解析を回した機械では 4,374 行）の
**列だけを読む。新しい当てはめはしない**（数秒で終わる）。読む列は `age`・`klass_own`・
`dt_v1_ms`（凍結版 ΔT）・`dt_lm_ms`（特徴点法 ΔT・Charlton 同梱）・`ok_v1`（26番の A 段）と、
B4 で `ri_v1`（凍結版 RI）・`digital_ri`（特徴点法 RI・Charlton 同梱）。

  B1  型（`klass_own`）ごとに、凍結版 ΔT と特徴点法 ΔT の分布（5・10・25・50・75・90・95
      パーセンタイルと最小・最大）
  B2  下限の検査。特徴点法 ΔT を 20 ms 刻みの区間に分け、区間ごとに凍結版 ΔT の中央値・
      四分位範囲・人数を出す（特徴点法が短い区間でも凍結版が下がらなければ、下限で詰まって
      いる）。あわせて凍結版 ΔT の最小値・下位 5% と、探索範囲の下限（Δμ 0.08 s ＝ 80 ms）
      との差を印字する
  B3  型ごとに ρ(dt_v1_ms, dt_lm_ms)（年齢層内 Spearman の中央値。**符号つき**。同じ量を
      測っているなら正になるはずで、|ρ| では順位が壊れて負に振れたときに見えなくなる）と、
      特徴点法 ΔT が短い側の半数・長い側の半数に分けたときのそれぞれの ρ
  B4  型ごとに ρ(ri_v1, digital_ri) を**年齢層ごとに 1 行ずつ**並べる（節A-2 の所見を
      実データで見るため。規約は B3・48番 と同じ。A 段を主とし C 段を同じ行に並べる）。
      `ri_v1`・`digital_ri` の列が無い CSV では B4 と P4・P5 だけを飛ばす
  B5  予測との照合（下記 P1〜P5）。**判定は付けない**（事後・記述）

凍結版の列は 26番の A 段（`ok_v1 == 1`。その手法が自分で採用した例だけ）で計算し、C 段
（採否を無視した全例）は参考として添える。48番 節4 の +36.9 ms・+98.5 ms が A 段の値だから
である。年齢層内 Spearman の規約は 26番・48番と共有する（`20_pwdb_validity.py` の
`_spearman`・`_judge` をそのまま読み込む。層は `age` の相異なる値、1 層 8 名以上）。
短い側・長い側は**年齢層ごとに**その層の `dt_lm_ms` の中央値で二分する（層をまたいだ
中央値で切ると、年齢と混ざる）。半数それぞれにも 1 層 8 名以上を要求する。

予測（2026-09-15、実データを見る前に固定した）
----------------------------------------------
(P1) 実データでも凍結版 ΔT には下限の詰まりがある: 型3 で、特徴点法 ΔT が最も短い区間
     （下から 2 区間）でも凍結版 ΔT の中央値は 140 ms を下回らない。根拠: 合成では 150 ms を
     下回る真値に対して返り値が下がらなかった。
(P2) 型3 では、特徴点法 ΔT が短い側の半数の ρ(dt_v1_ms, dt_lm_ms) が、長い側の半数より
     0.15 以上小さい。根拠: 下限で詰まるのは短い側だけなので、順位が壊れるのも短い側である。
(P3) 型1 では (P2) の差が 0.15 未満。根拠: 型1 は真の到達が長く、下限で詰まる範囲に入らない。
(P4) 型3 では、年齢層内の ρ(ri_v1, digital_ri) の中央値が 0.30 未満で、かつ高齢の層ほど
     小さい（75 歳層で 0.20 未満）。根拠: 節A-2 で、型3 相当の条件では凍結版の RI が
     真の反射の大きさと逆に動いた（ρ −0.89）。加齢で切痕が消えるほど型3 の波形に近づく。
(P5) 型1 ではその ρ の中央値が 0.60 以上で、年齢層による傾きがない。根拠: 節A-2 の
     型1 相当では凍結版・特徴点法とも ρ +1.00 で、両者は同じ順位を返した。

P4・P5 も 2026-09-15 に、**実データを見る前に**固定した（節A-2 の合成の結果だけを見て
立てた予測である）。P5 の「年齢層による傾きがない」は、**最も若い層と最も高齢の層の ρ の
差が 0.15 未満**と読む（P2・P3 と同じ 0.15 を使う）。P4 の「高齢の層ほど小さい」は括弧の
とおり **75 歳層の ρ が 0.20 未満**で判定し、年齢と層ごとの ρ の順位相関は記述として
添えるだけにする（規準には使わない）。

予測の本文と数値の規準（140 ms・0.15・下から 2 区間・0.30・0.20・0.60）は 2026-09-15 に
固定したものから変えていない。語だけは用語の決まり（`docs/research/terminology.md`）に
従い「下限で詰まる」と書く。

前提と限界
----------
合成脈波は監督者が作ったもので PWDB ではない。反射波の幅と到達の結び付け方は仮定である。
1 層 10 拍なので ρ の差（0.71 対 0.89）は 1〜2 組の入れ替わりに当たる。RI は測っていない。
節B の CSV が抜粋（この環境の複製は 24 行）だと 1 層 8 名に満たず、どの ρ も計算できない。
その場合も落ちずに「—」と人数不足を印字するが、**その数値は読んではいけない。**

版は確認的解析と同じにそろえる（Python 3.9.6・NumPy 2.0.2・SciPy 1.13.1・pandas 2.3.3）。

使い方
------
    python3 scripts/50_reservoir_bench.py --selftest
    python3 scripts/50_reservoir_bench.py
    python3 scripts/50_reservoir_bench.py --csv data/pwdb/pwdb_compare.csv
    python3 scripts/50_reservoir_bench.py --section B --csv data/pwdb/pwdb_compare.csv

`--section A|B|AB`（既定 AB。CSV が無ければ A だけ）。`--fast` は節A の掃引を 2 層 × 5 拍に
減らす（自己検査と同じ掃引。本番の表ではない）。自己検査は合成だけで走る（CSV もネット
ワークも要らない）。節A（3 層 × 10 拍）＋ 節A-2（2 条件 × 7 拍）の本番は、当てはめ 10 行で
この環境では約 40 秒である（`--section A` を 3 回計った実測は 42・44・38 秒。CSV は要らない）。
結果は print するので、残すときは tee で `docs/research/results/50_reservoir_bench.txt` に
落とす。

終了コード 0 = 通常、2 = 節B を頼まれたのに CSV が無い・要る列が無い。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import sys
import unicodedata
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import pda                       # noqa: E402  (0) が呼ぶ凍結版本体（fit_beat）
from src import pda2                      # noqa: E402  ROOT を通してから読む
from src.pda import skew_gaussian         # noqa: E402  凍結版と同じ歪みガウス


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。45番・48番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 順位相関の規約は 20番のものをそのまま使う（自前で書き直さない。26番・45番・48番と同じ）
M = _load("20_pwdb_validity.py", "m20")

DATA = ROOT / "data"
DEFAULT_CSV = DATA / "pwdb" / "pwdb_compare.csv"

MIN_PER_AGE = 8        # 1 年齢層に要る人数。26番・45番・48番の MIN_PER_AGE と同じ
N_AGES_FULL = 6        # PWDB の年齢層（25・35・45・55・65・75 歳）


# ---------------------------------------------------------------- 表示の部品
def _pad(s, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。"""
    used = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))
    fill = " " * max(0, w - used)
    return (fill + str(s)) if right else (str(s) + fill)


def _f(v: float, w: int = 9, prec: int = 3, sign: bool = False) -> str:
    if not np.isfinite(v):
        return _pad("—", w, right=True)
    return f"{v:>+{w}.{prec}f}" if sign else f"{v:>{w}.{prec}f}"


def _n(v: float, prec: int = 3, sign: bool = False) -> str:
    """文中に埋める数値（桁揃えをしない）。"""
    if not np.isfinite(v):
        return "—"
    return f"{v:+.{prec}f}" if sign else f"{v:.{prec}f}"


def _yn(b: bool) -> str:
    return "はい" if b else "いいえ"


def _ari(b: bool) -> str:
    return "あり" if b else "なし"


# ================================================================ 節A（合成）
# 合成脈波の母数。監督者の試作（scratchpad/bench.py）と同じ値で、変えると節A の数値が変わる。
FS = 500.0                 # 標本化周波数 [Hz]
HR_SYN = 70.0              # 心拍数 [1/min]。拍長 T = 60 / HR
TP_F = 0.12                # 前進波のピークの目安 [s]
A_FWD, SIG_FWD, AL_FWD = 1.0, 0.045, 2.5     # 前進波（歪みガウス）の高さ・幅・歪度
A_REF = 0.45               # 反射波の高さ
W_REF_A, W_REF_B = 0.055, 0.16   # 反射波の幅 = W_REF_A + W_REF_B × 到達 [s]
AL_REF = 1.2               # 反射波の歪度（早く到達する拍では 0 にする）
DT_SKEW = 0.18             # 到達がこれ以下なら歪度 0（硬い血管の、幅が広く対称な反射波）
D_RES = 0.45               # 貯留槽の大きさ
RES_PEAK_LAG = 0.05        # 貯留槽が減衰に入る時刻 = 前進波のピーク + 到達 + これ [s]
RES_MAX_FRAC = 0.55        # ただし拍長のこの割合を超えない
NOISE_SD = 0.002           # 雑音の標準偏差

# 当てはめの型。(鍵, 番号, 表の見出し, 説明)
# 番号は波形の型（klass_own）と混ざらないよう括弧付きで書く。(5)(6) は試作と同じ設定で、
# 形の拘束・打ち切りに加えて Δμ の下限も 0.01 s に緩めてある（2 つ変わっている）。
# (5b)(6b) は同じ拘束・打ち切りで Δμ の下限を凍結版のまま 0.08 s にした版で、
# **一度に 1 つだけ変えたときの効き**を読むために 2026-09-15 に足した。
# (4b) と (0) も 2026-09-15 に足した。(4b) は「Δμ を緩める・貯留槽を畳み込みで持つ、の
# 2 つをそれぞれと同時に適用したときの結果を出すのか」に答えるための行で、(2) と (4) を
# 同時に適用したものである。(0) は `src/pda.py` の `fit_beat` をそのまま呼ぶ行で、
# 起点 4 点で写した複製 (1) が本体と同じ振る舞いをすることの照合である。
KINDS = [
    ("fb", "(0)", "凍結版本体",
     "凍結版そのもの（`src/pda.py` の `fit_beat` を既定の引数で呼ぶ。起点 8 点・"
     "特徴点近傍の解を優先する規則・max_nfev 4000）。(1) はこれを起点 4 点で写した複製で、"
     "(0) は複製が本体と同じ振る舞いをすることの照合（2026-09-15 に足した）"),
    ("frozen", "(1)", "凍結版", "凍結版 2 カーネル（src/pda.py と同じ探索範囲・Δμ の下限 0.08 s）"),
    ("relax", "(2)", "Δμ0.01", "Δμ の下限を 0.01 s に緩める（ほかは凍結版のまま）"),
    ("decay", "(3)", "減衰項", "自由な指数減衰を足す（24番 A1 と同じ形・d·exp(−(t−t0)/τ)）"),
    ("conv", "(4)", "畳み込み", "貯留槽を前進波の畳み込みで持つ（res = g·∫g1(s)·e^{−(t−s)/τ}ds）"),
    ("conv01", "(4b)", "畳み込み",
     "同じ畳み込みで Δμ の下限を 0.01 s に緩める（(2) と (4) の同時適用。2026-09-15 に足した）"),
    ("tied", "(5)", "形を縛る", "第2成分の形を第1成分に縛る（σ2 = c·σ1・α2 = α1）＋ Δμ の下限 0.01 s"),
    ("tied08", "(5b)", "形を縛る", "同じ形の拘束で、Δμ の下限は凍結版のまま 0.08 s"),
    ("trunc", "(6)", "0.65T", "0.65T までで当てはめる ＋ Δμ の下限 0.01 s"),
    ("trunc08", "(6b)", "0.65T", "同じ打ち切りで、Δμ の下限は凍結版のまま 0.08 s"),
]
KIND_KEYS = [k for k, _no, _h, _l in KINDS]
KIND_NO = {k: no for k, no, _h, _l in KINDS}
KIND_HEAD = {k: h for k, _no, h, _l in KINDS}
KIND_LABEL = {k: l for k, _no, _h, l in KINDS}

# 模型の形（母数の並び）と、当てはめに使う範囲。(5b) は (5) と、(6b) は (6) と、
# (4b) は (4) と同じ形で、違うのは Δμ の下限だけである。(0) の形「fb」はこの台本の模型を
# 使わないという印で、`_bounds`・`_starts`・`_model` は (0) では呼ばない。
KIND_SHAPE = {"fb": "fb", "frozen": "plain", "relax": "plain", "decay": "decay",
              "conv": "conv", "conv01": "conv",
              "tied": "tied", "tied08": "tied", "trunc": "plain", "trunc08": "plain"}
KIND_TRUNC = ("trunc", "trunc08")

# 当てはめの設定。凍結版と同じ探索範囲を使う型と、Δμ の下限を緩める型を分ける。
DMU_LO_FROZEN = 0.08       # `src/pda.py` の dmu_bounds の下限 [s]
DMU_LO_RELAX = 0.01
# (0) の Δμ の下限も凍結版と同じ 0.08 s（`fit_beat` の既定）だが、下限は `fit_beat` の側に
# あり、この台本の `_bounds` は (0) では使わない。(4b) は下限だけを DMU_LO_RELAX にする。
KIND_DMU_FROZEN = ("fb", "frozen", "decay", "conv", "tied08", "trunc08")
N_STARTS = 4               # 起点の数（試作と同じ）
MAX_NFEV = 3000
TRUNC_FRAC = 0.65          # (6)(6b) が当てはめに使う範囲（拍長に対する割合）

# 掃引
TAUS_FULL = (0.45, 0.35, 0.25)
DTS_FULL = (0.30, 0.27, 0.24, 0.21, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08)
TAUS_FAST = (0.45, 0.35)
# 自己検査の掃引。下位 3 拍を本番と同じ到達（0.12・0.10・0.08 s）にそろえてある。
# 下限の詰まりは下位 3 拍で測るので、ここが本番と違うと同じものを検査できない。
DTS_FAST = (0.24, 0.18, 0.12, 0.10, 0.08)
SEED_A = 0                 # 雑音の乱数種。拍ごとに同じ種を使う（試作と同じ）

MIN_BEATS_A = 3            # 節A の ρ を計算するのに要る拍数（節B の 8 名以上とは別）
FLOOR_N = 3                # 下限の詰まりを見る拍数（真値の小さいほうから）
# いま使う規準（2026-09-15 に差し替えた）: その 3 拍の**返り値の最小**が、その 3 拍の
# **真値の最大**より FLOOR_GAP_MS 以上大きいとき「あり」。
FLOOR_GAP_MS = 30.0
# 差し替える前の規準（参考として表に残す）: その 3 拍の返り値の範囲が FLOOR_RANGE_MS
# 未満なら「あり」。凍結版は返り値が下限の手前で折り返すので、範囲では取り逃がす。
FLOOR_RANGE_MS = 20.0


def synth_beat(dt_true: float, tau: float, seed: int = SEED_A, hr: float = HR_SYN,
               a_ref: float = A_REF):
    """前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）の 1 拍を作る。

    反射波は早く到達するほど幅が広くなり歪みが消える（硬い血管の波形）。
    ΔT の真値は**反射波のピーク − 前進波のピーク**で、母数（μ）の差ではない。幅と歪度が
    到達によって変わるので、両者は一致しない。`a_ref` は反射波の大きさの母数で、節A-2 が
    これを振る（既定は A_REF で、節A の掃引はこれまでと同じ波形になる）。RI の真値として
    成分のピーク高さの比 `ri_peak` も返す（当てはめが返す h2/h1 と同じ定義）。
    """
    T = 60.0 / hr
    t = np.arange(0.0, T, 1.0 / FS)
    w_ref = W_REF_A + W_REF_B * dt_true
    al_ref = AL_REF if dt_true > DT_SKEW else 0.0
    fwd = skew_gaussian(t, A_FWD, TP_F - 0.02, SIG_FWD, AL_FWD)
    ref = skew_gaussian(t, a_ref, TP_F + dt_true - 0.02, w_ref, al_ref)
    t_a = min(RES_MAX_FRAC * T, TP_F + dt_true + RES_PEAK_LAG)
    rise = np.clip(t / max(t_a, 1e-6), 0.0, 1.0) ** 2
    res = D_RES * rise * np.exp(-np.maximum(t - t_a, 0.0) / tau)
    y = fwd + ref + res
    y = y + NOISE_SD * np.random.default_rng(seed).standard_normal(y.size)
    i_ref, i_fwd = int(np.argmax(ref)), int(np.argmax(fwd))
    t_ref, t_fwd = float(t[i_ref]), float(t[i_fwd])
    h_ref, h_fwd = float(ref[i_ref]), float(fwd[i_fwd])
    return t, y, {"dt_s": t_ref - t_fwd, "t_ref": t_ref, "t_fwd": t_fwd,
                  "tau": tau, "dt_set": dt_true, "a_ref": a_ref,
                  "h_ref": h_ref, "h_fwd": h_fwd,
                  "ri_peak": h_ref / max(h_fwd, 1e-12)}


def _norm(y: np.ndarray) -> np.ndarray:
    """当てはめの前に 0〜1 に正規化する（凍結版 `fit_beat` と同じ扱い）。"""
    y = np.asarray(y, float)
    y = y - float(np.min(y))
    return y / max(float(np.max(y)), 1e-12)


def _peak_on(comp, t: np.ndarray):
    """成分のピーク時刻と高さ（歪みがあるので μ とは違う。拍の標本の上で探す）。"""
    g = skew_gaussian(t, *comp)
    i = int(np.argmax(g))
    return float(t[i]), float(g[i])


def _reject_fb(kind: str) -> None:
    """(0) は `src/pda.py` の `fit_beat` をそのまま呼ぶ型なので、この台本の探索範囲・
    起点・模型は使わない。取り違えたときに黙って別の当てはめにならないよう、ここで止める。
    """
    if kind == "fb":
        raise ValueError("型 fb（(0) 凍結版本体）は src/pda.py の fit_beat を直接呼ぶ。"
                         "_bounds・_starts・_model は使えない")


def _bounds(t: np.ndarray, ys: np.ndarray, kind: str):
    """型ごとの探索範囲。8 母数の並びは `src/pda.py` と同じ

    (a1, mu1, sigma1, alpha1, a2, Δμ, sigma2, alpha2)。型5 は末尾 2 つを σ の比 c に
    置き換え（7 母数）、型3・型4 は減衰の (g, τ) を足す（10 母数）。(0) はこの探索範囲を
    使わないので、呼ばれたら ValueError で止める。
    """
    _reject_fb(kind)
    T = float(t[-1] - t[0])
    t_pk = float(t[int(np.argmax(ys))])
    shape = KIND_SHAPE[kind]
    dmu_lo = DMU_LO_FROZEN if kind in KIND_DMU_FROZEN else DMU_LO_RELAX
    lo = [0.05, 0.02, 0.015, 0.0, 0.02, dmu_lo, 0.015, 0.0]
    hi = [2.50, max(0.60 * T, t_pk + 0.05), 0.30, 8.0,
          2.00, min(0.60, 0.85 * T), 0.35, 8.0]
    if shape == "tied":
        lo, hi = lo[:6] + [0.5], hi[:6] + [4.0]
    elif shape == "decay":
        lo, hi = lo + [0.0, 0.05], hi + [1.0, 1.50]
    elif shape == "conv":
        lo, hi = lo + [0.0, 0.05], hi + [3.0, 1.50]
    return lo, hi, dmu_lo


def _components(p, kind: str):
    """母数から 2 成分（歪みガウス 4 母数ずつ）を取り出す。"""
    c1 = (p[0], p[1], p[2], p[3])
    if KIND_SHAPE[kind] == "tied":
        c2 = (p[4], p[1] + p[5], p[2] * p[6], p[3])
    else:
        c2 = (p[4], p[1] + p[5], p[6], p[7])
    return c1, c2


def _model(p, tt: np.ndarray, kind: str) -> np.ndarray:
    _reject_fb(kind)
    c1, c2 = _components(p, kind)
    out = skew_gaussian(tt, *c1) + skew_gaussian(tt, *c2)
    shape = KIND_SHAPE[kind]
    if shape == "decay":
        out = out + p[8] * np.exp(-(tt - tt[0]) / max(p[9], 1e-3))
    elif shape == "conv":
        g1 = skew_gaussian(tt, *c1)
        dt = float(tt[1] - tt[0])
        kern = np.exp(-(tt - tt[0]) / max(p[9], 1e-3)) * dt
        out = out + p[8] * np.convolve(g1, kern)[:tt.size]
    return out


def _starts(kind: str, dmu_lo: float, lo, hi):
    """起点 4 点（試作と同じ。Δμ を 0.05 s ずつずらして別の解も探す）。

    (0) は `fit_beat` が自分で起点 8 点を作るので、ここには来ない。
    """
    _reject_fb(kind)
    out = []
    shape = KIND_SHAPE[kind]
    for s in range(N_STARTS):
        x0 = [0.9, 0.10 + 0.01 * s, 0.05, 2.0, 0.4,
              max(dmu_lo, 0.10 + 0.05 * s), 0.08, 1.0]
        if shape == "tied":
            x0 = x0[:6] + [1.6]
        elif shape in ("decay", "conv"):
            x0 = x0 + [0.3, 0.35]
        out.append([min(max(v, l), h) for v, l, h in zip(x0, lo, hi)])
    return out


def fit_kind(t: np.ndarray, y: np.ndarray, kind: str) -> dict:
    """1 拍を型 `kind` で当てはめ、ΔT [s]・RI・残差を返す。

    **収束検算（境界張り付き・別解の有無）は課さない。**この節が見たいのは真値の順位を
    追えるかどうかで、採否ではない（凍結版の採否は 26番の A 段が決めている）。

    型 `fb`（(0) 凍結版本体）だけは `src/pda.py` の `fit_beat` を既定の引数でそのまま
    呼ぶ（起点 8 点・特徴点近傍の解を優先する規則・max_nfev 4000）。正規化は `fit_beat`
    が中で行うので生の y を渡す（`_norm` と同じ扱いである）。`fit_beat` が返す収束検算の
    結果は `ok` に入れて記録するが、**この節では採否に使わない。**
    """
    if kind == "fb":
        try:
            r = pda.fit_beat(t, y)
            c1, c2 = r["components"][0], r["components"][1]
            return {"dt_s": float(c2["t_peak"] - c1["t_peak"]),
                    "ri": float(c2["height"]) / max(float(c1["height"]), 1e-9),
                    "ok": bool(r["ok"]), "cost": float(r["rss"]) / 2.0}
        except Exception:
            return {"dt_s": float("nan"), "ri": float("nan"), "ok": False,
                    "cost": float("nan")}
    ys = _norm(y)
    lo, hi, dmu_lo = _bounds(t, ys, kind)
    if kind in KIND_TRUNC:
        keep = t <= t[0] + TRUNC_FRAC * (t[-1] - t[0])
        tfit, yfit = t[keep], ys[keep]
    else:
        tfit, yfit = t, ys
    best = None
    for x0 in _starts(kind, dmu_lo, lo, hi):
        try:
            r = least_squares(lambda p: _model(p, tfit, kind) - yfit, x0,
                              bounds=(lo, hi), method="trf", max_nfev=MAX_NFEV)
        except Exception:
            continue
        if best is None or r.cost < best.cost:
            best = r
    if best is None:
        return {"dt_s": float("nan"), "ri": float("nan"), "ok": False,
                "cost": float("nan")}
    c1, c2 = _components(best.x, kind)
    t1, h1 = _peak_on(c1, t)
    t2, h2 = _peak_on(c2, t)
    return {"dt_s": t2 - t1, "ri": h2 / max(h1, 1e-9), "ok": True,
            "cost": float(best.cost)}


def fiducial_dt(t: np.ndarray, y: np.ndarray) -> dict:
    """参考: 特徴点法（`pda2.preprocess` → `find_landmarks`）の ΔT = dia_t − sys_t。"""
    ys, _amp = pda2.preprocess(t, y, FS)
    if ys is None:
        return {"dt_s": float("nan"), "ri": float("nan"), "klass": -1}
    lm = pda2.find_landmarks(t, ys)
    klass = int(lm["klass"])
    if not (np.isfinite(lm["dia_t"]) and np.isfinite(lm["sys_t"])):
        return {"dt_s": float("nan"), "ri": float("nan"), "klass": klass}
    return {"dt_s": float(lm["dia_t"] - lm["sys_t"]),
            "ri": float(lm["dia_v"] / max(lm["sys_v"], 1e-12)), "klass": klass}


def sweep(taus, dts, seed: int = SEED_A, kinds=None) -> dict:
    """時定数 × 到達の掃引。返り値は時定数ごとの真値・返り値・型（すべて ms）。

    `ok_fb` は (0) 凍結版本体の収束検算（`fit_beat` の `ok`）を拍ごとに並べたもので、
    記録するだけである（この節は採否を課さない）。
    """
    kinds = list(KIND_KEYS) if kinds is None else list(kinds)
    out = {}
    for tau in taus:
        rec = {"tau": float(tau), "dt_set": [], "truth": [], "klass": [], "fid": [],
               "ok_fb": [], "got": dict((k, []) for k in kinds)}
        for dt in dts:
            t, y, tr = synth_beat(dt, tau, seed=seed)
            rec["dt_set"].append(1000.0 * dt)
            rec["truth"].append(1000.0 * tr["dt_s"])
            for k in kinds:
                r = fit_kind(t, y, k)
                if k == "fb":
                    rec["ok_fb"].append(bool(r["ok"]))
                rec["got"][k].append(1000.0 * r["dt_s"] if np.isfinite(r["dt_s"])
                                     else float("nan"))
            f = fiducial_dt(t, y)
            rec["fid"].append(1000.0 * f["dt_s"] if np.isfinite(f["dt_s"])
                              else float("nan"))
            rec["klass"].append(f["klass"])
        out[float(tau)] = rec
    return out


def floor_check(truth_ms, got_ms) -> dict:
    """下限の詰まり。真値の小さいほうから FLOOR_N 拍を取って 2 通りの規準で測る。

    いま使う規準（`flag_gap`。2026-09-15 に差し替えた）
        その 3 拍の**返り値の最小**が、その 3 拍の**真値の最大**より FLOOR_GAP_MS 以上
        大きいとき「あり」。返り値がどれだけ下に行けないかを直接測る。
    差し替える前の規準（`flag_range`。参考として表に残す）
        その 3 拍の返り値の範囲が FLOOR_RANGE_MS 未満なら「あり」。凍結版は返り値が
        下限の手前で折り返すので（真値 98 ms で 132 ms、78・58 ms で 174 ms）、
        範囲は広く出て取り逃がす。

    `got_min` は掃引の全拍を通した返り値の最小で、真値の最小と並べて読む。
    """
    truth = np.asarray(truth_ms, float)
    got = np.asarray(got_ms, float)
    order = np.argsort(truth)[:FLOOR_N]
    v = got[order]
    tv = truth[order]
    fin = v[np.isfinite(v)]
    all_fin = got[np.isfinite(got)]
    out = {"n": int(fin.size), "lo": float("nan"), "hi": float("nan"),
           "rng": float("nan"), "gap": float("nan"),
           "truth_rng": float(np.max(tv) - np.min(tv)),
           "truth_max": float(np.max(tv)), "flag_gap": False, "flag_range": False,
           "got_min": float("nan"),
           "truth_min": float(np.min(truth)) if truth.size else float("nan")}
    if all_fin.size:
        out["got_min"] = float(np.min(all_fin))
    if fin.size >= 2:
        out["lo"], out["hi"] = float(np.min(fin)), float(np.max(fin))
        out["rng"] = out["hi"] - out["lo"]
        out["gap"] = out["lo"] - out["truth_max"]
        out["flag_gap"] = bool(out["gap"] >= FLOOR_GAP_MS)
        out["flag_range"] = bool(out["rng"] < FLOOR_RANGE_MS)
    return out


def summarise_a(res: dict) -> dict:
    """型 × 時定数の (ρ, |誤差| 中央値, 下限の詰まり)。ρ は 20番の `_spearman`。"""
    out = {}
    for tau, rec in res.items():
        truth = np.asarray(rec["truth"], float)
        series = [(k, np.asarray(rec["got"][k], float)) for k in rec["got"]]
        series.append(("fid", np.asarray(rec["fid"], float)))
        for key, got in series:
            rho, n = M._spearman(truth, got, min_n=MIN_BEATS_A)
            err = got - truth
            out[(key, tau)] = {
                "rho": rho, "n": int(n),
                "mae": float(np.nanmedian(np.abs(err))) if np.any(np.isfinite(err))
                else float("nan"),
                "bias": float(np.nanmedian(err)) if np.any(np.isfinite(err))
                else float("nan"),
                "floor": floor_check(truth, got)}
    return out


def _kind_no(key: str) -> str:
    """当てはめの型の番号（波形の型 klass_own と混ざらないよう括弧付きで書く）。"""
    return KIND_NO.get(key, "（参考）")


def print_a_legend(taus, dts, seed: int) -> None:
    print("\n" + "-" * 100)
    print("A0. 合成脈波と当てはめの型")
    print("-" * 100)
    print("  合成脈波 = 前進波（歪みガウス）＋ 反射波（歪みガウス）＋ 貯留槽（指数減衰）。")
    print(f"  反射波は早く到達するほど幅が広くなり歪みが消える（幅 = {W_REF_A} + "
          f"{W_REF_B} × 到達 [s]、到達 {DT_SKEW} s 以下で歪度 0）。")
    print(f"  雑音は標準偏差 {NOISE_SD}（乱数種 {seed}・拍ごとに同じ種）。"
          f"標本化 {FS:.0f} Hz・心拍数 {HR_SYN:.0f}/min。")
    print("  **真値は反射波のピーク − 前進波のピーク**（母数 μ の差ではない。幅と歪度が")
    print("  到達で変わるので両者は一致しない）。")
    print(f"  掃引: 貯留槽の時定数 {list(taus)} s（{len(list(taus))} 層）")
    print(f"        × 反射波の到達 {list(dts)} s（{len(list(dts))} 拍）。")
    print("  時定数を年齢層に見立て、層の中で到達だけを振る（26番の年齢層内 Spearman を模す）。")
    print("  時定数が小さいほど高齢に相当する（PWDB は加齢で末梢血管コンプライアンスを減らす）。")
    print("\n  当てはめの型（**波形の型 klass_own とは別のもの**。番号は括弧付きで書く）:")
    for k in KIND_KEYS:
        print("    " + _pad(_kind_no(k), 8) + _pad(KIND_HEAD[k], 11) + KIND_LABEL[k])
    print("    " + _pad("（参考）", 8) + _pad("特徴点法", 11)
          + "pda2.preprocess → find_landmarks の dia_t − sys_t")
    print("    (5)(6) は形の拘束・打ち切りに加えて Δμ の下限も 0.01 s に緩めた版、"
          "(5b)(6b) は")
    print("    凍結版の 0.08 s のままの版である（一度に 1 つだけ変えたときの効きを読むため）。")
    print("    (4b) は (2) と (4) を同時に適用した版、(0) は複製 (1) の照合で、"
          "いずれも 2026-09-15 に足した。")
    print(f"  (1) 以降の当てはめは least_squares（trf・起点 {N_STARTS} 点・"
          f"max_nfev {MAX_NFEV}）。**収束検算は課さない。**")
    print("  (0) は `src/pda.py` の `fit_beat` そのもの（起点 8 点・max_nfev 4000）で、"
          "収束検算は計算するが")
    print("  採否には使わず、通過した拍数を層ごとの表の下に印字するだけである。")


def print_a_matrix(summ: dict, taus) -> None:
    """型 × 時定数の順位相関 ρ だけを 1 枚にまとめる。"""
    print("\n" + "-" * 100)
    print("A1. 順位相関 ρ（真の ΔT と、当てはめが返した ΔT。20番の `_spearman`・層ごとに"
          f" {len(list(taus))} 通りの時定数）")
    print("-" * 100)
    head = "  " + _pad("当てはめの型", 32)
    for tau in taus:
        head += _pad(f"時定数 {tau:.2f} s", 15, right=True)
    print(head)
    for k in KIND_KEYS + ["fid"]:
        lab = (f"{_kind_no(k)} {KIND_HEAD[k]}" if k in KIND_HEAD else "（参考）特徴点法")
        line = "  " + _pad(lab, 32)
        for tau in taus:
            line += _f(summ[(k, float(tau))]["rho"], 15, prec=2, sign=True)
        print(line)
    print("  ρ が 1.00 なら真値の順位を完全に追えている。1 層の拍数が少ないので、")
    print("  0.71 と 0.89 の差は 1〜2 組の入れ替わりに当たる。")


def print_a_layer(rec: dict, summ: dict, tau: float) -> None:
    """時定数 1 層ぶんの表（まとめ → 1 拍ずつ）。"""
    truth = np.asarray(rec["truth"], float)
    print(f"\n  --- 貯留槽の時定数 {tau:.2f} s（{truth.size} 拍・真値 "
          f"{np.min(truth):.0f}〜{np.max(truth):.0f} ms）---")
    print("    " + _pad("当てはめの型", 18) + _pad("ρ", 8, right=True)
          + _pad("|誤差|中央値", 13, right=True) + _pad("全拍の最小", 13, right=True)
          + _pad("下限の詰まり", 15, right=True)
          + _pad("（参考）下位3拍の範囲", 24, right=True))
    for k in KIND_KEYS + ["fid"]:
        s = summ[(k, tau)]
        fl = s["floor"]
        lab = (f"{_kind_no(k)} {KIND_HEAD[k]}" if k in KIND_HEAD else "（参考）特徴点法")
        rngs = ("—" if not np.isfinite(fl["rng"])
                else f"{fl['lo']:.0f}〜{fl['hi']:.0f}（{fl['rng']:.0f}）"
                     f" {_ari(fl['flag_range'])}")
        gaps = ("—" if not np.isfinite(fl["gap"])
                else f"{_ari(fl['flag_gap'])}（{fl['gap']:+.0f}）")
        print("    " + _pad(lab, 18) + _f(s["rho"], 8, prec=2, sign=True)
              + _pad(f"{s['mae']:.0f} ms" if np.isfinite(s["mae"]) else "—", 13, right=True)
              + _pad(f"{fl['got_min']:.0f} ms" if np.isfinite(fl["got_min"]) else "—",
                     13, right=True)
              + _pad(gaps, 15, right=True)
              + _pad(rngs, 24, right=True))
    f0 = summ[(KIND_KEYS[0], tau)]["floor"]
    print(f"    「下限の詰まり」は、真値の小さいほうから {FLOOR_N} 拍の**返り値の最小**が、"
          f"その {FLOOR_N} 拍の**真値の最大**（{f0['truth_max']:.0f} ms）より")
    print(f"    {FLOOR_GAP_MS:.0f} ms 以上大きいとき「あり」（括弧内はその差）。"
          "2026-09-15 に差し替えた規準である。")
    print(f"    「（参考）下位3拍の範囲」は差し替える前の規準で、その {FLOOR_N} 拍の返り値の"
          f"範囲が {FLOOR_RANGE_MS:.0f} ms 未満のとき「あり」。")
    print("    凍結版は返り値が下限の手前で折り返すので範囲は広く出る。取り逃がすことが")
    print("    分かったので、参考として残してある。")
    print(f"    その {FLOOR_N} 拍の真値の範囲は {f0['truth_rng']:.0f} ms、真値の最小は "
          f"{f0['truth_min']:.0f} ms である。")
    print("    「全拍の最小」は掃引の全拍を通した返り値の最小で、これが真値の最小より"
          "大きいほど")
    print("    短い側を追えていない（下限で詰まっている）。")
    ok_fb = list(rec.get("ok_fb", []))
    if ok_fb:
        n_ok, n = int(sum(1 for v in ok_fb if v)), len(ok_fb)
        print(f"    (0) の収束検算（境界張り付き・高さ・別解）の通過は {n_ok}/{n} 拍。"
              "この節は採否を課さないので表の値は全拍のものである。")

    print("\n    1 拍ずつ（返り値 [ms] と、括弧内は 返り値 − 真値。列の番号は上の表と同じ）")
    head = _pad("真値[ms]", 9, right=True) + _pad("波形の型", 9, right=True)
    for k in KIND_KEYS:
        head += _pad(_kind_no(k), 10, right=True)
    head += _pad("特徴点法", 10, right=True)
    print("  " + head)
    for i, tv in enumerate(rec["truth"]):
        line = _pad(f"{tv:.0f}", 9, right=True) + _pad(str(rec["klass"][i]), 9, right=True)
        for k in KIND_KEYS + ["fid"]:
            v = rec["got"][k][i] if k in rec["got"] else rec["fid"][i]
            line += (_pad("—", 10, right=True) if not np.isfinite(v)
                     else f"{v:>4.0f}({v - tv:+4.0f})")
        print("  " + line)
    print("    「波形の型」は特徴点法（pda2.find_landmarks）が付けた klass_own である"
          "（1 = 極値あり、3 = 変曲点で代用）。")


def section_a(taus=TAUS_FULL, dts=DTS_FULL, seed: int = SEED_A) -> dict:
    """節A: 当てはめの型を並べ、真の反射波の到達を追えるかを測る（合成・表は 10 行）。"""
    print("\n" + "=" * 100)
    print("節A 合成脈波: 当てはめの型を変えると、真の反射波の到達を追えるか")
    print("=" * 100)
    print_a_legend(taus, dts, seed)
    res = sweep(taus, dts, seed=seed)
    summ = summarise_a(res)
    print_a_matrix(summ, taus)
    print("\n" + "-" * 100)
    print("A2. 時定数の層ごとの表")
    print("-" * 100)
    for tau in taus:
        print_a_layer(res[float(tau)], summ, float(tau))
    print("\n  出典: この台本（50番）の節A が合成脈波から計算した値")
    print(f"        （時定数 {len(list(taus))} 通り × 到達 {len(list(dts))} 通り × "
          f"当てはめ {len(KIND_KEYS)} 型・乱数種 {seed}）。")
    return {"res": res, "summ": summ, "taus": tuple(float(v) for v in taus),
            "dts": tuple(dts), "seed": seed}


# ============================================================== 節A-2（合成・RI）
# 反射波の大きさ a_ref を振り、当てはめが返す RI（h2/h1）が順位を追うかを見る。
# 条件は 2 つ。反射波が遅く分離する拍（型1 相当）と、収縮期に重なる拍（型3 相当）。
RIS_FULL = (0.20, 0.28, 0.35, 0.42, 0.50, 0.58, 0.65)
RIS_FAST = (0.20, 0.35, 0.50, 0.65)      # 自己検査の掃引
RI_TAU = 0.35                            # 貯留槽の時定数は固定する
RI_CONDS = ((0.28, "型1 相当", "反射波が遅く分離する（到達 280 ms）"),
            (0.10, "型3 相当", "反射波が収縮期に重なる（到達 100 ms）"))
# 符号の反転の規準（2026-09-15 に、実装の前に決めた）: ρ がこれより小さいとき「反転」。
# 大きさは 20番の CRIT_RHO（0.30）と同じで、符号を負にしたものである。
RHO_FLIP = -0.30


def sweep_ri(conds=RI_CONDS, ris=RIS_FULL, tau: float = RI_TAU, seed: int = SEED_A,
             kinds=None) -> dict:
    """条件 × 反射波の大きさの掃引。返り値は条件ごとの真値・返り値・波形の型。

    真値は 2 つ返す。`truth` は振った母数 a_ref、`ri_peak` は成分のピーク高さの比
    （当てはめが返す h2/h1 と同じ定義）である。条件の中では前進波が変わらないので
    両者は比例し、**順位は同じ**である。ρ は母数（試作と同じ）、|誤差| は比に対して出す。
    `ok_fb` は (0) 凍結版本体の収束検算（`fit_beat` の `ok`）を拍ごとに並べたもので、
    記録するだけである（この節は採否を課さない）。
    """
    kinds = list(KIND_KEYS) if kinds is None else list(kinds)
    out = {}
    for dt, lab, note in conds:
        rec = {"dt": float(dt), "label": lab, "note": note, "tau": float(tau),
               "truth": [], "ri_peak": [], "klass": [], "fid": [], "ok_fb": [],
               "got": dict((k, []) for k in kinds)}
        for ri in ris:
            t, y, tr = synth_beat(dt, tau, seed=seed, a_ref=ri)
            rec["truth"].append(float(ri))
            rec["ri_peak"].append(tr["ri_peak"])
            for k in kinds:
                r = fit_kind(t, y, k)
                if k == "fb":
                    rec["ok_fb"].append(bool(r["ok"]))
                rec["got"][k].append(r["ri"])
            f = fiducial_dt(t, y)
            rec["fid"].append(f["ri"])
            rec["klass"].append(f["klass"])
        out[lab] = rec
    return out


def summarise_a2(res: dict) -> dict:
    """型 × 条件の (ρ, |誤差| 中央値, 符号の反転)。ρ は 20番の `_spearman`。"""
    out = {}
    for lab, rec in res.items():
        truth = np.asarray(rec["truth"], float)
        peak = np.asarray(rec["ri_peak"], float)
        series = [(k, np.asarray(rec["got"][k], float)) for k in rec["got"]]
        series.append(("fid", np.asarray(rec["fid"], float)))
        for key, got in series:
            rho, n = M._spearman(truth, got, min_n=MIN_BEATS_A)
            err = got - peak
            fin = got[np.isfinite(got)]
            out[(key, lab)] = {
                "rho": rho, "n": int(n),
                "mae": float(np.nanmedian(np.abs(err))) if np.any(np.isfinite(err))
                else float("nan"),
                "lo": float(np.min(fin)) if fin.size else float("nan"),
                "hi": float(np.max(fin)) if fin.size else float("nan"),
                "flip": bool(np.isfinite(rho) and rho < RHO_FLIP)}
    return out


def print_a2_legend(ris, tau: float) -> None:
    print("\n" + "-" * 100)
    print("A2-0. RI の掃引（当てはめの型は節A と同じ 10 行＋参考の特徴点法）")
    print("-" * 100)
    print(f"  反射波の大きさ（母数 a_ref）を {list(ris)} の "
          f"{len(list(ris))} 通りに振る。")
    print(f"  条件は 2 つ。貯留槽の時定数は {tau} s に固定し、反射波の到達だけを変える。")
    for dt, lab, note in RI_CONDS:
        print(f"    {lab}  {note}")
    print("  当てはめが返す RI は第2成分／第1成分の**ピーク高さの比** h2/h1、特徴点法の RI は")
    print("  `dia_v / sys_v` である。真値は 2 つ出す。「真の RI」は振った母数 a_ref、")
    print("  「真の比」は合成した成分のピーク高さの比で、当てはめの h2/h1 と同じ定義である。")
    print("  条件の中では前進波が変わらないので両者は比例し、順位は同じになる。")
    print(f"  **符号の反転**は ρ < {RHO_FLIP:+.2f} のとき「反転」と印字する"
          "（2026-09-15 に実装の前に決めた規準）。")


def print_a2_cond(rec: dict, summ: dict, lab: str) -> None:
    truth = np.asarray(rec["truth"], float)
    print(f"\n  --- {lab}: {rec['note']}・貯留槽の時定数 {rec['tau']:.2f} s"
          f"（{truth.size} 拍・真の RI {np.min(truth):.2f}〜{np.max(truth):.2f}）---")
    print("    " + _pad("当てはめの型", 18) + _pad("ρ", 8, right=True)
          + _pad("|誤差|中央値", 13, right=True) + _pad("返り値の範囲", 18, right=True)
          + _pad("符号の反転", 12, right=True))
    for k in KIND_KEYS + ["fid"]:
        s = summ[(k, lab)]
        name = (f"{_kind_no(k)} {KIND_HEAD[k]}" if k in KIND_HEAD else "（参考）特徴点法")
        rng = ("—" if not np.isfinite(s["lo"])
               else f"{s['lo']:.3f}〜{s['hi']:.3f}")
        print("    " + _pad(name, 18) + _f(s["rho"], 8, prec=2, sign=True)
              + _f(s["mae"], 13, prec=3)
              + _pad(rng, 18, right=True)
              + _pad("反転" if s["flip"] else "—", 12, right=True))
    print(f"    「|誤差|中央値」は**真の比**（成分のピーク高さの比）に対する差の中央値。")
    print(f"    「符号の反転」は ρ < {RHO_FLIP:+.2f} のとき印字する"
          "（2026-09-15 に実装の前に決めた規準）。")
    ok_fb = list(rec.get("ok_fb", []))
    if ok_fb:
        n_ok, n = int(sum(1 for v in ok_fb if v)), len(ok_fb)
        print(f"    (0) の収束検算（境界張り付き・高さ・別解）の通過は {n_ok}/{n} 拍。"
              "この節は採否を課さないので表の値は全拍のものである。")

    print("\n    1 拍ずつ（当てはめが返した RI。列の番号は上の表と同じ）")
    head = (_pad("真のRI", 8, right=True) + _pad("真の比", 8, right=True)
            + _pad("波形の型", 9, right=True))
    for k in KIND_KEYS:
        head += _pad(_kind_no(k), 9, right=True)
    head += _pad("特徴点法", 9, right=True)
    print("  " + head)
    for i, tv in enumerate(rec["truth"]):
        line = (_pad(f"{tv:.2f}", 8, right=True)
                + _pad(f"{rec['ri_peak'][i]:.3f}", 8, right=True)
                + _pad(str(rec["klass"][i]), 9, right=True))
        for k in KIND_KEYS + ["fid"]:
            v = rec["got"][k][i] if k in rec["got"] else rec["fid"][i]
            line += (_pad("—", 9, right=True) if not np.isfinite(v)
                     else f"{v:>9.3f}")
        print("  " + line)
    print("    「波形の型」は特徴点法（pda2.find_landmarks）が付けた klass_own である。")


def section_a2(conds=RI_CONDS, ris=RIS_FULL, tau: float = RI_TAU,
               seed: int = SEED_A) -> dict:
    """節A-2: 反射波の大きさを振り、返り値の RI が順位を追うかを測る（合成）。"""
    print("\n" + "=" * 100)
    print("節A-2 合成脈波: 反射波の大きさを振ると、返り値の RI は順位を追うか")
    print("=" * 100)
    print("  節A と同じ合成脈波で、振るものだけを反射波の大きさに変える。")
    print("  型3 相当で何が起きるか（機構）: 反射波が前進波に融合するので、真の反射が")
    print("  大きいほど**第1成分が高くなる**。一方、第2成分は貯留槽の下降の上に固定されて")
    print("  高さが変わらない。したがって比 h2/h1 は**下がる**。")
    print_a2_legend(ris, tau)
    res = sweep_ri(conds, ris, tau=tau, seed=seed)
    summ = summarise_a2(res)
    print("\n" + "-" * 100)
    print("A2-1. 条件ごとの表")
    print("-" * 100)
    for _dt, lab, _note in conds:
        print_a2_cond(res[lab], summ, lab)
    print("\n  出典: この台本（50番）の節A-2 が合成脈波から計算した値")
    print(f"        （条件 {len(list(conds))} 通り × 反射波の大きさ {len(list(ris))} 通り × "
          f"当てはめ {len(KIND_KEYS)} 型・乱数種 {seed}）。")
    return {"res": res, "summ": summ, "ris": tuple(ris), "tau": float(tau),
            "conds": tuple(lab for _d, lab, _n in conds)}


# ================================================================ 節B（実データ）
KLASS_COL = "klass_own"
KLASSES = (1, 3, 4, 5)
KLASS_LABEL = {
    1: "型1 明瞭な重複切痕と拡張期ピーク（極値）",
    3: "型3 極値は無いが下降の緩む変曲点",
    4: "型4 変曲点が見つからない",
    5: "型5 収縮期ピークが拍の末尾（波形が不正）",
}
KLASS_SHORT = {1: "型1 極値あり", 3: "型3 変曲点で代用", 4: "型4 変曲点なし",
               5: "型5 波形が不正"}
COL_V1 = "dt_v1_ms"        # 凍結版 2 カーネルの ΔT（26番の出力）
COL_LM = "dt_lm_ms"        # 特徴点法の ΔT（Charlton 同梱）
COL_OK = "ok_v1"           # 26番の A 段（その手法が自分で採用した例）
COL_RI_V1 = "ri_v1"        # 凍結版 2 カーネルの RI（26番の出力）
COL_RI_LM = "digital_ri"   # 特徴点法の RI（Charlton 同梱）
NEED_B = ("age", KLASS_COL, COL_V1, COL_LM)
NEED_B4 = (COL_RI_V1, COL_RI_LM)   # B4（RI）に要る列。無ければ B4 だけを飛ばす

BIN_MS = 20.0              # B2 の区間の幅
PCTS = (5, 10, 25, 50, 75, 90, 95)
DMU_LO_MS = 1000.0 * DMU_LO_FROZEN   # 凍結版の探索範囲の下限 Δμ 0.08 s ＝ 80 ms

# 予測の規準（docstring の P1〜P3。2026-09-15 に、実データを見る前に固定した）
PRED_P1_FLOOR_MS = 140.0   # P1 型3: 下から 2 区間でも凍結版 ΔT の中央値がこれを下回らない
PRED_P1_N_BINS = 2         # P1 で見る区間の数（下から）
PRED_RHO_GAP = 0.15        # P2 型3: 短い側の ρ が長い側より これ以上小さい／P3 型1: 未満
# P4・P5（RI。2026-09-15 に、実データを見る前に固定した）
PRED_P4_MED = 0.30         # P4 型3: ρ(ri_v1, digital_ri) の中央値がこれ未満
PRED_P4_OLD = 0.20         # P4 型3: 最も高齢の層（75 歳）の ρ がこれ未満
PRED_P5_MED = 0.60         # P5 型1: ρ の中央値がこれ以上
PRED_P5_SLOPE = 0.15       # P5 型1: 最も若い層と最も高齢の層の ρ の差がこれ未満（傾きがない）
AGE_OLD = 75.0             # PWDB の最も高齢の層


def _colv(d: pd.DataFrame, c: str) -> np.ndarray:
    if c not in d.columns:
        return np.full(len(d), np.nan)
    return pd.to_numeric(d[c], errors="coerce").to_numpy(dtype=float)


def stage_a(d: pd.DataFrame) -> pd.DataFrame:
    """26番の A 段（ok_v1 == 1）。列が無ければそのまま返す（C 段と同じになる）。"""
    if COL_OK not in d.columns:
        return d
    return d[pd.to_numeric(d[COL_OK], errors="coerce") == 1]


def subset(d: pd.DataFrame, k: int) -> pd.DataFrame:
    return d[_colv(d, KLASS_COL) == float(k)]


def missing_cols(d: pd.DataFrame) -> list:
    return [c for c in NEED_B if c not in d.columns]


def dist_of(d: pd.DataFrame, col: str) -> dict:
    """1 列の分布（人数・最小・パーセンタイル・最大）。"""
    v = _colv(d, col)
    v = v[np.isfinite(v)]
    out = {"n": int(v.size), "min": float("nan"), "max": float("nan"),
           "p": dict((q, float("nan")) for q in PCTS)}
    if v.size:
        out["min"], out["max"] = float(np.min(v)), float(np.max(v))
        out["p"] = dict((q, float(np.percentile(v, q))) for q in PCTS)
    return out


def floor_bins(d: pd.DataFrame) -> dict:
    """特徴点法 ΔT を BIN_MS 刻みの区間に分け、区間ごとの凍結版 ΔT を要約する。

    対応のある行（両方が有限）だけを使う。返り値の `bins` は区間の下端をキーにした
    辞書で、下端の小さい順に並べれば「特徴点法が短い区間で凍結版が下がるか」が読める。
    """
    x, y = _colv(d, COL_LM), _colv(d, COL_V1)
    g = np.isfinite(x) & np.isfinite(y)
    x, y = x[g], y[g]
    out = {"n": int(x.size), "bins": [], "v1_min": float("nan"),
           "v1_p5": float("nan"), "lm_min": float("nan")}
    if x.size == 0:
        return out
    out["v1_min"] = float(np.min(y))
    out["v1_p5"] = float(np.percentile(y, 5))
    out["lm_min"] = float(np.min(x))
    idx = np.floor(x / BIN_MS).astype(int)
    for b in np.unique(idx):
        sel = idx == b
        v = y[sel]
        q1, q3 = (float(q) for q in np.percentile(v, [25, 75]))
        out["bins"].append({"lo": float(b) * BIN_MS, "hi": float(b + 1) * BIN_MS,
                            "n": int(sel.sum()), "med": float(np.median(v)),
                            "q1": q1, "q3": q3,
                            "lm_med": float(np.median(x[sel]))})
    return out


def rho_rows(d: pd.DataFrame, half=None, xcol: str = COL_V1, ycol: str = COL_LM) -> list:
    """年齢層ごとの (年齢, ρ(xcol, ycol), n)。既定は ΔT（dt_v1_ms・dt_lm_ms）。

    `half` が "short"／"long" のときは、**その年齢層の** `ycol` の中央値で二分した
    片側だけを使う（層をまたいだ中央値で切ると年齢と混ざる）。ρ は 20番の `_spearman`
    （対応のある行だけ・1 層 MIN_PER_AGE 名以上）。B4 は xcol・ycol に RI の列を渡す。
    """
    out = []
    if "age" not in d.columns or len(d) == 0:
        return out
    for age, g in d.groupby("age", sort=True):
        x, y = _colv(g, xcol), _colv(g, ycol)
        keep = np.isfinite(x) & np.isfinite(y)
        if half is not None and int(keep.sum()) >= 2:
            thr = float(np.median(y[keep]))
            keep = keep & ((y <= thr) if half == "short" else (y > thr))
        r, n = M._spearman(x[keep], y[keep], min_n=MIN_PER_AGE)
        out.append((float(age), r, int(n)))
    return out


def strat(rows: list, sign: int = 1) -> dict:
    """年齢層をまたいだまとめ。中央値・向きの層数は 20番の `_judge` に任せる。"""
    fin = [(a, r, n) for a, r, n in rows if np.isfinite(r)]
    j = M._judge(rows, sign) if rows else None
    return {"rows": rows,
            "med": float(np.median([r for _a, r, _n in fin])) if fin else float("nan"),
            "med_abs": j["med_abs"] if j else float("nan"),
            "n_ok": j["n_ok"] if j else 0,
            "n_ages": j["n_ages"] if j else 0,
            "min_n": min(n for _a, _r, n in fin) if fin else 0,
            "n_tot": int(sum(n for _a, _r, n in fin))}


def print_b1(d: pd.DataFrame, klasses) -> dict:
    """B1 型ごとの ΔT の分布。"""
    print("\n" + "-" * 100)
    print("B1. 型ごとの ΔT の分布（凍結版と特徴点法。単位 ms）")
    print("-" * 100)
    print("  段 A は 26番の A 段（ok_v1 == 1。凍結版が自分で採用した例）、段 C は採否を"
          "無視した全例。")
    out = {}
    for k in klasses:
        g = subset(d, k)
        ga = stage_a(g)
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  n = {len(g)} 名（A 段 {len(ga)} 名）")
        if len(g) == 0:
            print("    該当なし")
            continue
        print("    " + _pad("列", 12) + _pad("段", 4) + _pad("n", 7, right=True)
              + _pad("最小", 8, right=True)
              + "".join(_pad(f"p{q}", 8, right=True) for q in PCTS)
              + _pad("最大", 8, right=True))
        for col in (COL_V1, COL_LM):
            for stg, gg in (("A", ga), ("C", g)):
                s = dist_of(gg, col)
                out[(k, col, stg)] = s
                print("    " + _pad(col, 12) + _pad(stg, 4) + _pad(s["n"], 7, right=True)
                      + _f(s["min"], 8, prec=1)
                      + "".join(_f(s["p"][q], 8, prec=1) for q in PCTS)
                      + _f(s["max"], 8, prec=1))
    print("\n  出典: この台本（50番）の節B が CSV の既存列から計算した値。"
          "**新しい当てはめはしていない。**")
    return out


def print_b2(d: pd.DataFrame, klasses) -> dict:
    """B2 下限の検査（特徴点法 ΔT の区間ごとに凍結版 ΔT を並べる）。"""
    print("\n" + "-" * 100)
    print(f"B2. 下限の検査: 特徴点法 ΔT を {BIN_MS:.0f} ms 刻みの区間に分け、区間ごとの"
          " 凍結版 ΔT（A 段）")
    print("-" * 100)
    print("  特徴点法 ΔT が短い区間でも凍結版 ΔT の中央値が下がらなければ、凍結版は下限で"
          "詰まっている。")
    print("  対応のある行（両方が有限）だけを使う。")
    out = {}
    for k in klasses:
        g = stage_a(subset(d, k))
        res = floor_bins(g)
        out[k] = res
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  対応のある行 {res['n']} 名（A 段）")
        if res["n"] == 0:
            print("    対応のある行が無い")
            continue
        print("    " + _pad("特徴点法 ΔT の区間", 22) + _pad("人数", 7, right=True)
              + _pad("凍結版 ΔT 中央値", 18, right=True)
              + _pad("四分位範囲", 22, right=True)
              + _pad("特徴点法 ΔT 中央値", 20, right=True))
        for b in res["bins"]:
            iqr = f"[{b['q1']:.1f}〜{b['q3']:.1f}]"
            print("    " + _pad(f"[{b['lo']:.0f}, {b['hi']:.0f})", 22)
                  + _pad(b["n"], 7, right=True) + _f(b["med"], 18, prec=1)
                  + _pad(iqr, 22, right=True) + _f(b["lm_med"], 20, prec=1))
        print(f"    凍結版 ΔT の最小 {_n(res['v1_min'], 1)} ms・下位 5% "
              f"{_n(res['v1_p5'], 1)} ms（特徴点法 ΔT の最小は "
              f"{_n(res['lm_min'], 1)} ms）。")
        print(f"    探索範囲の下限 Δμ {DMU_LO_FROZEN} s（＝ {DMU_LO_MS:.0f} ms）との差は "
              f"{_n(res['v1_min'] - DMU_LO_MS, 1, sign=True)} ms・"
              f"{_n(res['v1_p5'] - DMU_LO_MS, 1, sign=True)} ms。")
    print("\n  Δμ は母数（μ2 − μ1）の下限で、ΔT は成分のピーク間隔である。歪みがあると")
    print("  ピークは μ からずれるので、ΔT が 80 ms を下回ることはありうる。80 ms は")
    print("  それでも目安になる（下限より下には母数を動かせない）。")
    print("  出典: この台本（50番）の節B が CSV の既存列から計算した値。")
    return out


def print_b3(d: pd.DataFrame, klasses) -> dict:
    """B3 型ごとの ρ(dt_v1_ms, dt_lm_ms) と、特徴点法 ΔT の短い側・長い側。"""
    print("\n" + "-" * 100)
    print("B3. 型ごとの ρ(dt_v1_ms, dt_lm_ms)（年齢層内 Spearman の中央値。符号つき）")
    print("-" * 100)
    print(f"  層は `age` の相異なる値、1 層 {MIN_PER_AGE} 名以上（20番の `_spearman`）。")
    print("  短い側・長い側は**年齢層ごとに**その層の dt_lm_ms の中央値で二分した半数で、")
    print("  半数それぞれにも 1 層 8 名以上を要求する（足りない層は数えない）。")
    print("  下限で詰まっているなら、短い側で ρ が落ちる。")
    print("    " + _pad("型", 20) + _pad("段", 4) + _pad("ρ 全体", 13, right=True)
          + _pad("ρ 短い側", 13, right=True) + _pad("ρ 長い側", 13, right=True)
          + _pad("差 長−短", 11, right=True) + _pad("層", 5, right=True)
          + _pad("最小n", 8, right=True))
    out = {}
    for k in klasses:
        g = subset(d, k)
        for stg, gg in (("A", stage_a(g)), ("C", g)):
            s_all = strat(rho_rows(gg))
            s_sh = strat(rho_rows(gg, half="short"))
            s_lg = strat(rho_rows(gg, half="long"))
            gap = s_lg["med"] - s_sh["med"]
            out[(k, stg)] = {"all": s_all, "short": s_sh, "long": s_lg, "gap": gap}
            lab = KLASS_SHORT.get(k, f"型{k}")
            print("    " + _pad(lab, 20) + _pad(stg, 4)
                  + _f(s_all["med"], 13, prec=3, sign=True)
                  + _f(s_sh["med"], 13, prec=3, sign=True)
                  + _f(s_lg["med"], 13, prec=3, sign=True)
                  + _f(gap, 11, prec=3, sign=True)
                  + _pad(s_all["n_ages"], 5, right=True)
                  + _pad(s_all["min_n"] or "—", 8, right=True))
    print("  「層」「最小n」は ρ 全体のもの。短い側・長い側は人数が半分になるので、"
          "層が減ることがある。")
    print("  出典: この台本（50番）の節B が CSV の既存列から計算した値。")
    return out


def print_b4_ri(d: pd.DataFrame, klasses) -> dict:
    """B4 型ごとの ρ(ri_v1, digital_ri) を年齢層ごとに 1 行ずつ。

    規約は 48番・B3 と同じ（20番の `_spearman`・1 層 MIN_PER_AGE 名以上・層は `age` の
    相異なる値）。凍結版の RI は A 段（ok_v1 == 1）を主とし、C 段（採否を無視した全例）を
    同じ行に並べる。**新しい当てはめはしない**（既存列を読むだけ）。
    """
    print("\n" + "-" * 100)
    print("B4. 型ごとの ρ(ri_v1, digital_ri)（年齢層ごとに 1 行。符号つき）")
    print("-" * 100)
    miss = [c for c in NEED_B4 if c not in d.columns]
    if miss:
        print(f"  ★ 列が無い: {miss}。B4 と予測 P4・P5 は計算できない。")
        return {}
    print(f"  層は `age` の相異なる値、1 層 {MIN_PER_AGE} 名以上。A 段は ok_v1 == 1、")
    print("  C 段は採否を無視した全例。対応のある行（両方が有限）だけを使う。")
    out = {}
    for k in klasses:
        g = subset(d, k)
        rows_a = rho_rows(stage_a(g), xcol=COL_RI_V1, ycol=COL_RI_LM)
        rows_c = rho_rows(g, xcol=COL_RI_V1, ycol=COL_RI_LM)
        s_a, s_c = strat(rows_a), strat(rows_c)
        out[k] = {"A": s_a, "C": s_c}
        print(f"\n  {KLASS_LABEL.get(k, f'型{k}')}  n = {len(g)} 名（A 段 {len(stage_a(g))} 名）")
        if not rows_c:
            print("    該当なし")
            continue
        print("    " + _pad("年齢層", 10, right=True) + _pad("A段 n", 10, right=True)
              + _pad("A段 ρ", 12, right=True) + _pad("C段 n", 10, right=True)
              + _pad("C段 ρ", 12, right=True))
        d_a = dict((a, (r, n)) for a, r, n in rows_a)
        for age, r_c, n_c in rows_c:
            r_a, n_a = d_a.get(age, (float("nan"), 0))
            print("    " + _pad(f"{age:.0f}", 10, right=True)
                  + _pad(n_a or "—", 10, right=True) + _f(r_a, 12, prec=3, sign=True)
                  + _pad(n_c or "—", 10, right=True) + _f(r_c, 12, prec=3, sign=True))
        print("    " + _pad("中央値", 10, right=True) + _pad("", 10)
              + _f(s_a["med"], 12, prec=3, sign=True) + _pad("", 10)
              + _f(s_c["med"], 12, prec=3, sign=True)
              + f"  （評価できた層 A {s_a['n_ages']}・C {s_c['n_ages']}）")
    print("\n  出典: この台本（50番）の節B が CSV の既存列から計算した値。"
          "**新しい当てはめはしていない。**")
    return out


def print_b5(b2: dict, b3: dict, b4: dict) -> dict:
    """B5 予測との照合（P1〜P5）。**判定は付けない**（事後・記述）。"""
    print("\n" + "-" * 100)
    print("B5. 予測との照合（予測は 2026-09-15 に、実データを見る前に固定した。docstring と同文）")
    print("-" * 100)
    print("  (P1) 型3 で、特徴点法 ΔT が最も短い区間（下から 2 区間）でも凍結版 ΔT の")
    print(f"       中央値は {PRED_P1_FLOOR_MS:.0f} ms を下回らない。")
    print(f"  (P2) 型3 では、特徴点法 ΔT が短い側の半数の ρ が長い側の半数より "
          f"{PRED_RHO_GAP:.2f} 以上小さい。")
    print(f"  (P3) 型1 では (P2) の差が {PRED_RHO_GAP:.2f} 未満。")
    print(f"  (P4) 型3 では、年齢層内の ρ(ri_v1, digital_ri) の中央値が "
          f"{PRED_P4_MED:.2f} 未満で、かつ高齢の層ほど")
    print(f"       小さい（{AGE_OLD:.0f} 歳層で {PRED_P4_OLD:.2f} 未満）。")
    print(f"  (P5) 型1 ではその ρ の中央値が {PRED_P5_MED:.2f} 以上で、年齢層による傾きが")
    print(f"       ない（最も若い層と最も高齢の層の差が {PRED_P5_SLOPE:.2f} 未満）。")

    res3 = b2.get(3, {"bins": [], "n": 0})
    low = res3["bins"][:PRED_P1_N_BINS]
    ev1 = len(low) == PRED_P1_N_BINS
    p1 = ev1 and all(np.isfinite(b["med"]) and b["med"] >= PRED_P1_FLOOR_MS for b in low)
    print(f"\n  P1 型3・特徴点法 ΔT が下から {PRED_P1_N_BINS} 区間の凍結版 ΔT 中央値:")
    for b in low:
        print(f"     [{b['lo']:.0f}, {b['hi']:.0f}) ms  n = {b['n']}  "
              f"凍結版 ΔT の中央値 {_n(b['med'], 1)} ms"
              + ("  ★ この区間は 8 名未満で、中央値は不安定である"
                 if b["n"] < MIN_PER_AGE else ""))
    if ev1:
        print(f"     → {PRED_P1_FLOOR_MS:.0f} ms を下回らない: {_yn(p1)}")
    else:
        print(f"     → 照合できない（対応のある行の区間が {len(low)} しかない）")

    g3 = b3.get((3, "A"), {})
    g1 = b3.get((1, "A"), {})
    gap3 = g3.get("gap", float("nan"))
    gap1 = g1.get("gap", float("nan"))
    p2 = bool(np.isfinite(gap3) and gap3 >= PRED_RHO_GAP)
    p3 = bool(np.isfinite(gap1) and gap1 < PRED_RHO_GAP)
    print(f"\n  P2 型3（A 段）  ρ 短い側 {_n(g3.get('short', {}).get('med', float('nan')), 3, sign=True)}"
          f"・長い側 {_n(g3.get('long', {}).get('med', float('nan')), 3, sign=True)}"
          f"・差 {_n(gap3, 3, sign=True)}")
    print(f"     → 差が {PRED_RHO_GAP:.2f} 以上: "
          + (_yn(p2) if np.isfinite(gap3) else "照合できない（層の人数が足りない）"))
    print(f"\n  P3 型1（A 段）  ρ 短い側 {_n(g1.get('short', {}).get('med', float('nan')), 3, sign=True)}"
          f"・長い側 {_n(g1.get('long', {}).get('med', float('nan')), 3, sign=True)}"
          f"・差 {_n(gap1, 3, sign=True)}")
    print(f"     → 差が {PRED_RHO_GAP:.2f} 未満: "
          + (_yn(p3) if np.isfinite(gap1) else "照合できない（層の人数が足りない）"))

    r4 = _ri_stats(b4, 3)
    r5 = _ri_stats(b4, 1)
    p4 = bool(np.isfinite(r4["med"]) and np.isfinite(r4["old"])
              and r4["med"] < PRED_P4_MED and r4["old"] < PRED_P4_OLD)
    p5 = bool(np.isfinite(r5["med"]) and np.isfinite(r5["span"])
              and r5["med"] >= PRED_P5_MED and r5["span"] < PRED_P5_SLOPE)
    print(f"\n  P4 型3（A 段）  ρ(ri_v1, digital_ri) の中央値 {_n(r4['med'], 3, sign=True)}"
          f"・{AGE_OLD:.0f} 歳層 {_n(r4['old'], 3, sign=True)}"
          f"（評価できた層 {r4['n_ages']}）")
    print(f"     層ごと: {r4['line']}")
    print(f"     → 中央値が {PRED_P4_MED:.2f} 未満、かつ {AGE_OLD:.0f} 歳層が "
          f"{PRED_P4_OLD:.2f} 未満: "
          + (_yn(p4) if np.isfinite(r4["med"]) and np.isfinite(r4["old"])
             else "照合できない（層の人数が足りない）"))
    print(f"     参考: 年齢と層ごとの ρ の順位相関 {_n(r4['trend'], 2, sign=True)}"
          "（負なら高齢の層ほど小さい。記述のみで、規準には使わない）")
    print(f"\n  P5 型1（A 段）  ρ(ri_v1, digital_ri) の中央値 {_n(r5['med'], 3, sign=True)}"
          f"・最も若い層 {_n(r5['young'], 3, sign=True)}"
          f"・最も高齢の層 {_n(r5['old'], 3, sign=True)}"
          f"・差 {_n(r5['span'], 3)}")
    print(f"     層ごと: {r5['line']}")
    print(f"     → 中央値が {PRED_P5_MED:.2f} 以上、かつ層による差が "
          f"{PRED_P5_SLOPE:.2f} 未満: "
          + (_yn(p5) if np.isfinite(r5["med"]) and np.isfinite(r5["span"])
             else "照合できない（層の人数が足りない）"))

    ev4 = bool(np.isfinite(r4["med"]) and np.isfinite(r4["old"]))
    ev5 = bool(np.isfinite(r5["med"]) and np.isfinite(r5["span"]))
    hit = sum(1 for v in (p1, p2, p3, p4, p5) if v)
    ev = sum(1 for v in (ev1, np.isfinite(gap3), np.isfinite(gap1), ev4, ev5) if v)
    print(f"\n  まとめ: 予測 5 条のうち照合できたのは {ev} 条、そのうち「はい」は {hit} 条。")
    if ev < 5:
        print("  照合できなかった条は、人数が足りないか対応のある行・列が無いためである。")
        print("  この CSV が抜粋なら、確認的解析の機械（4,374 行）で走らせ直す。")
    print("  **この節は事後の記述であり、判定（成立・不成立）は付けない。**"
          "26番の事前規準による判定は動かない。")
    return {"P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "hit": hit, "n_eval": ev,
            "p1_bins": low, "gap3": gap3, "gap1": gap1, "ri3": r4, "ri1": r5}


def _ri_stats(b4: dict, klass: int) -> dict:
    """B4 の A 段から、P4・P5 に要る値を取り出す（中央値・最若層・最高齢層・傾き）。

    「年齢層による傾き」は記述として年齢と ρ の順位相関も出すが、**規準に使うのは
    最も若い層と最も高齢の層の差**（P5）と、最も高齢の層の値（P4）である。
    """
    s = b4.get(klass, {}).get("A", {})
    rows = [(a, r) for a, r, _n in s.get("rows", []) if np.isfinite(r)]
    out = {"med": s.get("med", float("nan")), "n_ages": s.get("n_ages", 0),
           "young": float("nan"), "old": float("nan"), "span": float("nan"),
           "trend": float("nan"), "line": "—"}
    if not rows:
        return out
    rows.sort()
    out["young"], out["old"] = rows[0][1], rows[-1][1]
    out["span"] = abs(out["old"] - out["young"])
    if len(rows) >= MIN_BEATS_A:
        out["trend"] = M._spearman(np.array([a for a, _r in rows], float),
                                   np.array([r for _a, r in rows], float),
                                   min_n=MIN_BEATS_A)[0]
    out["line"] = "・".join(f"{a:.0f}歳 {r:+.3f}" for a, r in rows)
    # P4 は「75 歳層」を見る。その層が評価できていなければ最も高齢の層で代える
    for a, r in rows:
        if abs(a - AGE_OLD) < 1e-9:
            out["old"] = r
    return out


def section_b(d: pd.DataFrame, src: str) -> dict:
    """節B: 凍結版 ΔT が下限で詰まる性質は実データにも出るか（既存列だけを読む）。"""
    print("\n" + "=" * 100)
    print("節B 実データ（PWDB）: 凍結版 ΔT は下限で詰まっているか")
    print("=" * 100)
    miss = missing_cols(d)
    if miss:
        print(f"  入力 {src}")
        print(f"  ★ 列が無い: {miss}。節B は計算できない（26番 `26_pwdb_compare.py` の"
              "出力が要る）。")
        return {"state": 2, "missing": miss}
    ages = sorted(pd.to_numeric(d["age"], errors="coerce").dropna().unique().tolist())
    kl = _colv(d, KLASS_COL)
    seen = sorted(set(int(v) for v in kl[np.isfinite(kl)]))
    n_ok = int(np.sum(pd.to_numeric(d[COL_OK], errors="coerce") == 1)) \
        if COL_OK in d.columns else -1
    print(f"  入力 {src}")
    print("  （26番の出力。**既存列だけを読み、新しい当てはめはしない**）")
    print(f"  行数 {len(d)} 名（確認的解析を回した機械では 4,374 名）"
          f"・年齢層 {[int(a) for a in ages]}・型の値 {seen}")
    print(f"  A 段（{COL_OK} == 1）{n_ok} 名"
          if n_ok >= 0 else f"  {COL_OK} の列が無いので A 段と C 段は同じになる")
    short = [int(a) for a in ages
             if int((pd.to_numeric(d["age"], errors="coerce") == a).sum()) < MIN_PER_AGE]
    if len(d) < 100:
        print(f"  ★ この CSV は {len(d)} 行の抜粋である（1 層 "
              f"{len(d) // max(len(ages), 1)} 名）。**ここから出る数値は読んではいけない。**")
    elif short:
        print(f"  ★ {MIN_PER_AGE} 名に満たない年齢層がある: {short}")
    klasses = list(KLASSES) + sorted(set(seen) - set(KLASSES))
    out = {"state": 0}
    out["b1"] = print_b1(d, klasses)
    out["b2"] = print_b2(d, klasses)
    out["b3"] = print_b3(d, klasses)
    out["b4"] = print_b4_ri(d, klasses)
    out["b5"] = print_b5(out["b2"], out["b3"], out["b4"])
    return out


# ---------------------------------------------------------------- まとめ
def report(section: str, d=None, src: str = "", taus=TAUS_FULL, dts=DTS_FULL,
           ris=RIS_FULL, seed: int = SEED_A) -> dict:
    """節A（ΔT）・節A-2（RI）・節B を印字する。返り値は計算した値と終了コード。"""
    print("\n" + "=" * 100)
    print("50番 探索的（事後）: 当てはめの型と、凍結版 ΔT が下限で詰まること")
    print("=" * 100)
    print("  論文2・探索的（事後）。**判定（成立・不成立）は付けない。**事前規準による")
    print("  判定は 26番のものが有効で、この台本の出力は事後の記述である。")
    out = {"code": 0}
    if "A" in section:
        out["A"] = section_a(taus, dts, seed=seed)
        out["A2"] = section_a2(RI_CONDS, ris, seed=seed)
    if "B" in section:
        if d is None:
            print("\n  節B は CSV が無いので走らせない（--csv で 26番の出力を渡す）。")
            out["code"] = 2
        else:
            out["B"] = section_b(d, src)
            if out["B"]["state"] != 0:
                out["code"] = 2
    print("\n" + "-" * 100)
    a_txt = (f"節A 合成脈波（時定数 {len(list(taus))} 通り × 到達 {len(list(dts))} 通り）"
             f"＋ 節A-2（条件 {len(RI_CONDS)} 通り × 大きさ {len(list(ris))} 通り）"
             if "A" in section else "節A・節A-2 なし")
    a_txt2 = (f"当てはめ {len(KIND_KEYS)} 型・雑音 SD {NOISE_SD}・乱数種 {seed}"
              if "A" in section else "")
    b_txt = (f"節B {src}（{len(d)} 名・型の列 {KLASS_COL}・A 段 {COL_OK} == 1）"
             if ("B" in section and d is not None) else "節B なし")
    print("  出典: analysis/scripts/50_reservoir_bench.py")
    print(f"        / {a_txt}")
    if a_txt2:
        print(f"          （{a_txt2}）")
    print(f"        / {b_txt}")
    print("  年齢層内 Spearman の規約は 20番 `20_pwdb_validity.py` の `_spearman`・`_judge`")
    print(f"  をそのまま使う（1 層 {MIN_PER_AGE} 名以上・層は `age` の相異なる値）。")
    return out


# ---------------------------------------------------------------- 自己検査
# 節B の部品を試す合成データ。型3 だけ凍結版 ΔT を FLOOR_SYN_MS で止め、型1 は特徴点法に
# 載せる。これで P1・P2 が「はい」、P3 も「はい」になるはずである。
AGES_SYN = (25, 35, 45, 55, 65, 75)
N_PER_AGE_SYN = 300
LM_LO_SYN, LM_HI_SYN = 60.0, 260.0     # 特徴点法 ΔT の範囲 [ms]
FLOOR_SYN_MS = 150.0                   # 型3 に仕込む下限 [ms]
JIT_SYN_MS = 4.0                       # 当てはめの雑音 [ms]
P_KLASS1_SYN = 0.35
# RI の仕込み（B4・P4・P5 の部品を試すため）。型1 は特徴点法に載せ、型3 は年齢層ごとに
# 関係の強さを変えて、高齢の層ほど逆向きにする。
RI_LO_SYN, RI_HI_SYN = 0.20, 0.70      # 特徴点法 RI の範囲
RI_JIT_SYN = 0.05                      # 当てはめの雑音
RI_SLOPE_SYN = (0.6, 0.4, 0.2, 0.0, -0.3, -0.6)     # 型3 の傾き（25〜75 歳層）
RI_SLOPE_FLAT = 1.0                    # 型1 の傾き（年齢層によらない）


def synth_b(seed: int = 0) -> pd.DataFrame:
    """節B の部品を試す合成データ。

    ΔT: 型3 は下限（FLOOR_SYN_MS）で詰まり、型1 は詰まらない。
    RI: 型1 は特徴点法に載る（ρ ≈ +1・年齢層による差なし）。型3 は年齢層ごとに傾きを
        変え、高齢の層ほど逆向きにする（P4 の仕込み）。
    """
    rng = np.random.default_rng(seed)
    frames = []
    for k_age, age in enumerate(AGES_SYN):
        n = N_PER_AGE_SYN
        lm = rng.uniform(LM_LO_SYN, LM_HI_SYN, n)
        klass = np.where(rng.random(n) < P_KLASS1_SYN, 1.0, 3.0)
        jit = rng.normal(0.0, JIT_SYN_MS, n)
        v1 = np.where(klass == 1.0, lm + jit, np.maximum(lm, FLOOR_SYN_MS) + jit)
        ri_lm = rng.uniform(RI_LO_SYN, RI_HI_SYN, n)
        ri_jit = rng.normal(0.0, RI_JIT_SYN, n)
        slope = np.where(klass == 1.0, RI_SLOPE_FLAT, RI_SLOPE_SYN[k_age])
        ri_v1 = 0.30 + slope * (ri_lm - 0.45) + ri_jit
        frames.append(pd.DataFrame({"age": age, KLASS_COL: klass, COL_LM: lm,
                                    COL_V1: v1, COL_RI_LM: ri_lm, COL_RI_V1: ri_v1,
                                    COL_OK: 1}))
    return pd.concat(frames, ignore_index=True)


def selftest() -> int:
    n_fail = 0

    def rep(name, cond, detail=""):
        nonlocal n_fail
        cond = bool(cond)
        if not cond:
            n_fail += 1
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("50番 自己検査（合成だけで走る。CSV もネットワークも要らない）")
    print(f"  節A の掃引は {len(TAUS_FAST)} 層 × {len(DTS_FAST)} 拍に減らす"
          f"（本番は {len(TAUS_FULL)} 層 × {len(DTS_FULL)} 拍）。")
    print(f"  節A-2 は {len(RI_CONDS)} 条件 × {len(RIS_FAST)} 拍に減らす"
          f"（本番は {len(RI_CONDS)} 条件 × {len(RIS_FULL)} 拍）。")

    import inspect
    rep("順位相関の規約を 20番と共有している（_spearman・_judge・層の人数）",
        M.CRIT_RHO == 0.30
        and inspect.signature(M._by_age).parameters["min_n"].default == MIN_PER_AGE,
        f"CRIT_RHO {M.CRIT_RHO} / 層の人数 {MIN_PER_AGE}")

    # --- 合成脈波そのもの
    t, y, tr = synth_beat(0.20, 0.45)
    rep("合成脈波を作れる（真値は成分のピークの差で、母数の差とは違う）",
        t.size == int(round(FS * 60.0 / HR_SYN)) and np.isfinite(tr["dt_s"])
        and abs(tr["dt_s"] - 0.20) > 0.005,
        f"{t.size} 標本・真値 {1000 * tr['dt_s']:.0f} ms（設定 200 ms）")

    # --- (a-1) 下限の詰まりの検出器そのもの（いま使う規準と、差し替える前の規準）
    truth5 = np.array([250.0, 200.0, 150.0, 100.0, 50.0])
    stuck = np.array([250.0, 200.0, 190.0, 187.0, 185.0])   # 下限 185 ms で止めた列
    prop = np.array([255.0, 205.0, 155.0, 105.0, 55.0])     # 真値に比例する列
    f_stuck, f_prop = floor_check(truth5, stuck), floor_check(truth5, prop)
    rep("(a) 検出器: 人工的に下限で止めた列で「あり」（新しい規準・差し替える前の規準とも）",
        f_stuck["flag_gap"] and f_stuck["flag_range"],
        f"返り値の最小 − 真値の最大 {f_stuck['gap']:+.0f} ms"
        f"（要 {FLOOR_GAP_MS:.0f} 以上）・下位 {FLOOR_N} 拍の範囲 {f_stuck['rng']:.0f} ms")
    rep("(a) 検出器: 真値に比例する列では「なし」（同上）",
        (not f_prop["flag_gap"]) and (not f_prop["flag_range"]),
        f"返り値の最小 − 真値の最大 {f_prop['gap']:+.0f} ms・"
        f"下位 {FLOOR_N} 拍の範囲 {f_prop['rng']:.0f} ms")

    # --- 節A を減らした掃引で 1 回走らせる（(a-2)・(b)・(e) で使い回す）
    buf = io.StringIO()
    with redirect_stdout(buf):
        a0 = section_a(TAUS_FAST, DTS_FAST, seed=SEED_A)
    txt_a0 = buf.getvalue()
    summ, res = a0["summ"], a0["res"]
    rep("節A が減らした掃引で最後まで印字される",
        "A2. 時定数の層ごとの表" in txt_a0 and len(txt_a0) > 1000,
        f"{len(txt_a0)} 文字・{len(TAUS_FAST)} 層 × {len(DTS_FAST)} 拍")

    # --- (a-2) 凍結版が短い側で下限に詰まる（本文の所見そのもの）
    det = []
    for tau in TAUS_FAST:
        rec = res[float(tau)]
        truth = np.asarray(rec["truth"], float)
        got = np.asarray(rec["got"]["frozen"], float)
        order = np.argsort(truth)
        d2 = abs(got[order[0]] - got[order[1]])          # 真値が 20 ms 違う 2 拍
        fl = summ[("frozen", float(tau))]["floor"]
        det.append((tau, d2, fl["got_min"] - float(np.min(truth)), fl))
    rep("(a) 凍結版は短い側で下限に詰まる（真値が 20 ms 違う 2 拍で返り値の差 1 ms 未満）",
        all(dd < 1.0 for _t, dd, _g, _fl in det),
        "・".join(f"時定数 {t_:.2f}s 差 {dd:.1f} ms" for t_, dd, _g, _fl in det))
    rep("(a) 凍結版の返り値の最小は真値の最小より 60 ms 以上大きい（短い側を追えない）",
        all(g >= 60.0 for _t, _d, g, _fl in det),
        "・".join(f"時定数 {t_:.2f}s +{g:.0f} ms" for t_, _d, g, _fl in det))

    # 新しい規準（2026-09-15 差し替え）の検算。時定数 0.45 s の層で、凍結版だけが「あり」
    tau0 = float(TAUS_FAST[0])
    fl_fz = summ[("frozen", tau0)]["floor"]
    rep(f"(a) 新しい規準で凍結版が「あり」（時定数 {tau0:.2f} s の層）",
        fl_fz["flag_gap"],
        f"下位 {FLOOR_N} 拍の返り値の最小 {fl_fz['lo']:.0f} ms − 真値の最大 "
        f"{fl_fz['truth_max']:.0f} ms = {fl_fz['gap']:+.0f} ms（要 {FLOOR_GAP_MS:.0f} 以上）")
    none_keys = ("relax", "conv", "conv01", "trunc")
    rep("(a) 新しい規準で Δμ0.01・畳み込み・(4b) 畳み込み＋Δμ0.01・0.65T は「なし」"
        f"（時定数 {tau0:.2f} s の層）",
        all(not summ[(k, tau0)]["floor"]["flag_gap"] for k in none_keys),
        "・".join(f"{_kind_no(k)}{KIND_HEAD[k]} {summ[(k, tau0)]['floor']['gap']:+.0f} ms"
                  for k in none_keys))

    # (0) 凍結版本体も、複製 (1) と同じように短い側で下限に詰まるか。閾値 60 ms は上の
    # (1) の検査と同じものを使う。ここが落ちたら、複製が本体と同じ振る舞いをしていない。
    det_fb = []
    for tau in TAUS_FAST:
        tmin = float(np.min(np.asarray(res[float(tau)]["truth"], float)))
        det_fb.append((float(tau),
                       summ[("fb", float(tau))]["floor"]["got_min"] - tmin,
                       summ[("frozen", float(tau))]["floor"]["got_min"] - tmin))
    rep("(0) 凍結版本体も短い側で下限に詰まる（複製 (1) と同じ印）",
        summ[("fb", tau0)]["floor"]["flag_gap"]
        and all(np.isfinite(g0) and g0 >= 60.0 for _t, g0, _g1 in det_fb),
        "返り値の最小 − 真値の最小: "
        + "・".join(f"時定数 {t_:.2f}s (0) {g0:+.0f} ms / (1) {g1:+.0f} ms"
                    for t_, g0, g1 in det_fb))
    print("    参考: 差し替える前の規準（下位 3 拍の返り値の範囲 < "
          f"{FLOOR_RANGE_MS:.0f} ms）での凍結版の印字は "
          + "・".join(f"時定数 {t_:.2f}s {_ari(fl['flag_range'])}"
                      f"（範囲 {fl['rng']:.0f} ms）" for t_, _d, _g, fl in det)
          + "。これが取り逃がしである。")

    # (0)(4b)(5b)(6b): 凍結版本体が先頭にあり、一度に 1 つだけ変える版が並んでいるか
    rep("当てはめの型が 10 行あり、先頭が (0) 凍結版本体・(4b) は (2) と (4) の同時適用・"
        "(5b)(6b) は Δμ の下限だけが (5)(6) と違う",
        len(KIND_KEYS) == 10 and KIND_KEYS[0] == "fb"
        and KIND_NO["fb"] == "(0)" and KIND_NO["conv01"] == "(4b)"
        and KIND_SHAPE["conv01"] == "conv"
        and ("conv01" not in KIND_DMU_FROZEN) and ("fb" in KIND_DMU_FROZEN)
        and KIND_NO["tied08"] == "(5b)" and KIND_NO["trunc08"] == "(6b)"
        and KIND_SHAPE["tied08"] == KIND_SHAPE["tied"]
        and KIND_SHAPE["trunc08"] == KIND_SHAPE["trunc"]
        and ("tied08" in KIND_DMU_FROZEN) and ("trunc08" in KIND_DMU_FROZEN)
        and ("tied" not in KIND_DMU_FROZEN) and ("trunc" not in KIND_DMU_FROZEN)
        and all(np.isfinite(res[tau0]["got"][k]).all()
                for k in ("fb", "conv01", "tied08", "trunc08")),
        "・".join(f"{_kind_no(k)} ρ {summ[(k, tau0)]['rho']:+.2f}"
                  for k in ("fb", "frozen", "conv", "conv01",
                            "tied", "tied08", "trunc", "trunc08")))

    # --- (b) 畳み込み貯留槽の ρ が凍結版より大きい
    pairs = [(tau, summ[("frozen", float(tau))]["rho"], summ[("conv", float(tau))]["rho"])
             for tau in TAUS_FAST]
    rep("(b) 畳み込み貯留槽の ρ が凍結版より大きい（両層）",
        all(np.isfinite(a) and np.isfinite(b) and b > a for _t, a, b in pairs),
        "・".join(f"時定数 {t_:.2f}s 凍結版 {a:+.2f} → 畳み込み {b:+.2f}"
                  for t_, a, b in pairs))

    # --- 節A-2（RI）を減らした掃引で走らせる
    bufr = io.StringIO()
    with redirect_stdout(bufr):
        a2 = section_a2(RI_CONDS, RIS_FAST, seed=SEED_A)
    txt_a2 = bufr.getvalue()
    s2 = a2["summ"]
    rep("節A-2 が減らした掃引で最後まで印字される",
        "A2-1. 条件ごとの表" in txt_a2 and len(txt_a2) > 1000,
        f"{len(txt_a2)} 文字・条件 {len(RI_CONDS)} 通り × 大きさ {len(RIS_FAST)} 通り")
    rho_fz3 = s2[("frozen", "型3 相当")]["rho"]
    rho_rx3 = s2[("relax", "型3 相当")]["rho"]
    rho_fz1 = s2[("frozen", "型1 相当")]["rho"]
    rep("(a2) 型3 相当で凍結版の RI の ρ が負（符号の反転）",
        s2[("frozen", "型3 相当")]["flip"] and rho_fz3 < RHO_FLIP,
        f"ρ {rho_fz3:+.2f}（規準 {RHO_FLIP:+.2f} より小さいとき反転）")
    rho_fb3 = s2[("fb", "型3 相当")]["rho"]
    rep("(a2) (0) 凍結版本体も型3 相当で反転（複製と同じ）",
        s2[("fb", "型3 相当")]["flip"],
        f"(0) ρ {rho_fb3:+.2f}・(1) ρ {rho_fz3:+.2f}"
        f"（規準 {RHO_FLIP:+.2f} より小さいとき反転）")
    rep("(a2) 同じ条件で Δμ0.01 は正（下限を緩めると反転が消える）",
        np.isfinite(rho_rx3) and rho_rx3 > 0
        and not s2[("relax", "型3 相当")]["flip"],
        f"Δμ0.01 ρ {rho_rx3:+.2f}・凍結版 ρ {rho_fz3:+.2f}")
    rho_cv01_3 = s2[("conv01", "型3 相当")]["rho"]
    rep("(a2) (4b) 畳み込み＋Δμ0.01 は型3 相当で正",
        np.isfinite(rho_cv01_3) and rho_cv01_3 > 0
        and not s2[("conv01", "型3 相当")]["flip"],
        f"(4b) ρ {rho_cv01_3:+.2f}・(1) ρ {rho_fz3:+.2f}")
    rep("(a2) 型1 相当では凍結版も反転しない",
        np.isfinite(rho_fz1) and rho_fz1 > 0 and not s2[("frozen", "型1 相当")]["flip"],
        f"ρ {rho_fz1:+.2f}")
    rep("(a2) RI の真値は 2 通りとも順位が同じ（母数 a_ref と成分のピーク高さの比）",
        all(np.array_equal(np.argsort(np.asarray(r["truth"], float)),
                           np.argsort(np.asarray(r["ri_peak"], float)))
            for r in a2["res"].values()),
        "母数で計算した ρ と比で計算した ρ は同じ順位になる")

    # --- (c) 節B の計算部品を、下限で詰まる列を人工的に作った表で確かめる
    db = synth_b(seed=0)
    bufb = io.StringIO()
    with redirect_stdout(bufb):
        sb = section_b(db, "合成データ（自己検査）")
    txt_b = bufb.getvalue()
    rep("(c) 節B が合成の表で最後まで印字される",
        sb["state"] == 0 and "B5. 予測との照合" in txt_b,
        f"{len(db)} 行・{len(txt_b)} 文字")
    b2, bp = sb["b2"], sb["b5"]
    low3 = b2[3]["bins"][:PRED_P1_N_BINS]
    rep("(c) P1: 型3 は下から 2 区間でも凍結版 ΔT の中央値が下がらない",
        bp["P1"] and all(abs(b["med"] - FLOOR_SYN_MS) < 3.0 for b in low3),
        "・".join(f"[{b['lo']:.0f},{b['hi']:.0f}) 中央値 {b['med']:.1f} ms" for b in low3)
        + f"（仕込んだ下限 {FLOOR_SYN_MS:.0f} ms）")
    rep("(c) P2: 型3 は短い側の ρ が長い側より 0.15 以上小さい",
        bp["P2"], f"差 {_n(bp['gap3'], 3, sign=True)}")
    rep("(c) P3: 型1（下限を仕込んでいない）は差が 0.15 未満",
        bp["P3"], f"差 {_n(bp['gap1'], 3, sign=True)}")
    rep("(c) 型1 の凍結版 ΔT の最小は特徴点法に追随する（下限を仕込んでいない）",
        b2[1]["v1_min"] < FLOOR_SYN_MS - 40.0,
        f"型1 の最小 {b2[1]['v1_min']:.1f} ms・型3 の最小 {b2[3]['v1_min']:.1f} ms")
    rep("(c) 下限を仕込まない表では P1 が「いいえ」になる（検査が効いている）",
        not _p1_of(synth_b_nofloor(seed=0)),
        "型3 にも下限を仕込まない合成データで照合した")
    b4 = sb["b4"]
    r3, r1 = bp["ri3"], bp["ri1"]
    rep("(c) P4: 型3 の ρ(ri_v1, digital_ri) は中央値 0.30 未満・75 歳層 0.20 未満",
        bp["P4"],
        f"中央値 {_n(r3['med'], 3, sign=True)}・75 歳層 {_n(r3['old'], 3, sign=True)}"
        f"・年齢との順位相関 {_n(r3['trend'], 2, sign=True)}")
    rep("(c) P5: 型1 は中央値 0.60 以上で年齢層による差が 0.15 未満",
        bp["P5"],
        f"中央値 {_n(r1['med'], 3, sign=True)}・最若層 {_n(r1['young'], 3, sign=True)}"
        f"・最高齢層 {_n(r1['old'], 3, sign=True)}・差 {_n(r1['span'], 3)}")
    rep("(c) B4 の表が型ごと・年齢層ごとに並ぶ（A 段と C 段）",
        set(b4.keys()) >= {1, 3} and b4[3]["A"]["n_ages"] == len(AGES_SYN)
        and b4[1]["C"]["n_ages"] == len(AGES_SYN),
        f"型3 の層 {b4[3]['A']['n_ages']}・型1 の層 {b4[1]['A']['n_ages']}")
    rep("(c) 型3 も特徴点法に追随する表では P4 が「いいえ」になる（検査が効いている）",
        not _p4_of(synth_b_ri_flat(seed=0)),
        "型3 の傾きを型1 と同じにした合成データで照合した")

    # --- (d) 列が無い CSV
    d_miss = db.drop(columns=[COL_V1])
    bufm = io.StringIO()
    with redirect_stdout(bufm):
        out_m = report("B", d_miss, "合成データ（列を抜いた）")
    txt_m = bufm.getvalue()
    rep("(d) 列が無い CSV で落ちずに「列が無い」と印字し、終了コード 2 になる",
        out_m["code"] == 2 and "列が無い" in txt_m and COL_V1 in txt_m,
        f"終了コード {out_m['code']}")

    # --- (e) 同じ乱数種なら出力が同一
    def render(seed):
        b = io.StringIO()
        with redirect_stdout(b):
            section_a(TAUS_FAST, DTS_FAST, seed=seed)
        return b.getvalue()

    t_same, t_other = render(SEED_A), render(SEED_A + 1)
    rep("(e) 同じ乱数種なら出力が同一", t_same == txt_a0, f"{len(t_same)} 文字")
    rep("(e) 乱数種を変えれば値は変わる（比較が効いている）", t_other != txt_a0)

    # --- 既定の CSV があれば節B を走らせる（動くことの確認だけ）
    print("\n  --- 既定の CSV で節B を走らせる（動くことの確認だけ）---")
    if DEFAULT_CSV.exists():
        d_real = pd.read_csv(DEFAULT_CSV)
        bufr = io.StringIO()
        with redirect_stdout(bufr):
            out_r = report("B", d_real, str(DEFAULT_CSV))
        txt_r = bufr.getvalue()
        rep("既定の CSV で節B が例外なく最後まで印字される",
            out_r["code"] == 0 and "B5. 予測との照合" in txt_r,
            f"{len(d_real)} 行・終了コード {out_r['code']}・{len(txt_r)} 文字")
        if len(d_real) < 100:
            rows = out_r["B"]["b3"].get((3, "A"), {}).get("all", {})
            rep("抜粋では 8 名以上の年齢層が無く、ρ が計算できないことが表に出る",
                rows.get("n_ages", 0) == 0,
                f"評価できた層 {rows.get('n_ages', 0)}")
            print(f"  ★ この機械の {DEFAULT_CSV.name} は {len(d_real)} 行の抜粋である。")
            print("  ★ **ここから出る数値は読んではいけない。**確認的解析の機械の"
                  " 4,374 行で走らせること。")
    else:
        rep("既定の CSV が無い機械でも自己検査は通る", True, f"{DEFAULT_CSV} が無い")

    print("\n" + ("自己検証: 通過" if n_fail == 0 else f"自己検証: 失敗 {n_fail} 件"))
    return 0 if n_fail == 0 else 1


def synth_b_nofloor(seed: int = 0) -> pd.DataFrame:
    """(c) の対照。型3 にも下限を仕込まない（P1 が「いいえ」になるはず）。"""
    d = synth_b(seed=seed)
    rng = np.random.default_rng(seed + 1)
    d[COL_V1] = _colv(d, COL_LM) + rng.normal(0.0, JIT_SYN_MS, len(d))
    return d


def _p1_of(d: pd.DataFrame) -> bool:
    """P1 だけを静かに計算する（自己検査の対照用）。"""
    b = floor_bins(stage_a(subset(d, 3)))
    low = b["bins"][:PRED_P1_N_BINS]
    return bool(low) and len(low) == PRED_P1_N_BINS and all(
        np.isfinite(x["med"]) and x["med"] >= PRED_P1_FLOOR_MS for x in low)


def synth_b_ri_flat(seed: int = 0) -> pd.DataFrame:
    """(c) の対照。型3 の RI も型1 と同じ傾きにする（P4 が「いいえ」になるはず）。"""
    d = synth_b(seed=seed)
    rng = np.random.default_rng(seed + 2)
    d[COL_RI_V1] = (0.30 + RI_SLOPE_FLAT * (_colv(d, COL_RI_LM) - 0.45)
                    + rng.normal(0.0, RI_JIT_SYN, len(d)))
    return d


def _p4_of(d: pd.DataFrame) -> bool:
    """P4 だけを静かに計算する（自己検査の対照用）。"""
    s = strat(rho_rows(stage_a(subset(d, 3)), xcol=COL_RI_V1, ycol=COL_RI_LM))
    rows = [(a, r) for a, r, _n in s["rows"] if np.isfinite(r)]
    if not rows:
        return False
    old = [r for a, r in rows if abs(a - AGE_OLD) < 1e-9]
    old_v = old[0] if old else sorted(rows)[-1][1]
    return bool(np.isfinite(s["med"]) and s["med"] < PRED_P4_MED
                and old_v < PRED_P4_OLD)


# ---------------------------------------------------------------- 入口
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=None,
                    help="26番の出力（既定 data/pwdb/pwdb_compare.csv があれば使う）")
    ap.add_argument("--section", type=str, default="AB", choices=("A", "B", "AB"),
                    help="走らせる節（既定 AB。CSV が無ければ A だけ）")
    ap.add_argument("--fast", action="store_true",
                    help="節A・節A-2 の掃引を減らす（自己検査と同じ。本番の表ではない）")
    ap.add_argument("--seed", type=int, default=SEED_A,
                    help="節A・節A-2 の雑音の乱数種")
    ap.add_argument("--selftest", action="store_true",
                    help="合成だけで計算の筋道を検算する（CSV もネットワークも要らない）")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    d, src = None, ""
    want_b = "B" in args.section
    if want_b:
        p = Path(args.csv) if args.csv else DEFAULT_CSV
        if not p.exists() and not p.is_absolute():
            p = ROOT / str(args.csv)
        if p.exists():
            d, src = pd.read_csv(p), str(p)
        elif args.csv:
            print(f"\n{args.csv} が無い。26番（26_pwdb_compare.py）の出力が要る。")
            print("確認的解析を回した機械には data/pwdb/pwdb_compare.csv がある（4,374 行）。")
            sys.exit(2)
        else:
            print(f"\n{DEFAULT_CSV} が無いので節A だけを走らせる"
                  "（節B は --csv で 26番の出力を渡す）。")
            args.section = args.section.replace("B", "") or "A"

    taus = TAUS_FAST if args.fast else TAUS_FULL
    dts = DTS_FAST if args.fast else DTS_FULL
    ris = RIS_FAST if args.fast else RIS_FULL
    if args.fast:
        print("\n  ★ --fast: 節A・節A-2 の掃引を減らしている。**本番の表ではない。**")
    out = report(args.section, d, src, taus=taus, dts=dts, ris=ris, seed=args.seed)
    sys.exit(out["code"])


if __name__ == "__main__":
    main()
