"""観血的動脈圧 講義スライド 図版生成（川副式・白背景版）。
医学的に正しい形の動脈圧波形を「前進波＋反射波」合成で作り、透過PNGで出力。
各図 fig_*(path) 。__main__ で全図＋コンタクトシート生成。
背景は元々 fig.patch/ax.patch とも alpha=0（完全透過）で、濃紺スライド向けの塗り背景は
一度も使っていなかった（NAVY定数は未使用のため削除）。今回はアクセント色を decklib.py の
川副式ゴールド #BF9000（GOLD_D）に統一し、白背景（decklib版デック）でもそのまま使い回せる
ようにしている。波形の形状・数値・軸ラベルは一切変更していない。
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Polygon, Circle, FancyBboxPatch

# ---- palette（白背景版; GOLD_D は decklib.py の川副式ゴールド #BF9000 に統一） ----
GOLD="#D8AE3C"; GOLD_D="#BF9000"; INK="#262626"
SLATE="#8A94A0"; SLATE2="#6B7480"; HAIR="#C7CED6"; GRAY="#808080"
BLUE="#2E6FBF"; BLUE_F="#DCE6F5"; ORANGE="#D8702B"; ORANGE_F="#FBE3D0"
RED="#C00000"; TEAL="#00A0A2"; GREEN="#5E9E3E"; GRAYF="#EFEFEF"
TEAL_F="#D8F0F0"; GREEN_F="#E4F0DA"; RED_F="#F8D9D9"; GOLD_F="#F7ECCF"  # 追加7図のカード塗り（既存の淡色トーンに合わせる）
JP="Hiragino Sans"
plt.rcParams.update({"font.family":JP,"font.size":15,"svg.fonttype":"none"})

def _ax(w=9.2,h=4.3):
    fig,ax=plt.subplots(figsize=(w,h)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([]); return fig,ax
def _save(fig,path):
    fig.savefig(path,dpi=200,transparent=True,bbox_inches="tight",pad_inches=0.10); plt.close(fig)
def _g(x,mu,sg): return np.exp(-0.5*((x-mu)/sg)**2)

def components(x, peak=0.15, refl_mu=0.40, refl_amp=0.36, sharp=1.0, refl_w=0.088):
    """正規化(0..~1)の前進波・反射波・和を返す。"""
    fwd = _g(x,peak,0.052/sharp) + 0.16*_g(x,peak+0.09,0.075)
    refl = refl_amp*_g(x,refl_mu,refl_w)
    s = fwd+refl
    return fwd,refl,s

def beat(x, sbp=120,dbp=72, **kw):
    fwd,refl,s = components(x,**kw)
    sc=(sbp-dbp)/s.max()
    return dbp+sc*s
def train(nb=2,npts=600,**kw):
    xs=np.linspace(0,1,npts,endpoint=False); one=beat(xs,**kw)
    X=np.concatenate([xs+i for i in range(nb)]); Y=np.tile(one,nb); return X,Y

# ===================== 図 =====================

def fig_anatomy(path):
    fig,ax=_ax(9.4,4.6)
    x=np.linspace(0,1,700); y=beat(x,120,72)
    ax.plot(x,y,color=INK,lw=3.4,solid_capstyle="round")
    sbp=y.max(); ipk=y.argmax(); xpk=x[ipk]
    # notch位置 (収縮期後の局所最小)
    seg=(x>0.24)&(x<0.40); iN=np.where(seg)[0][y[seg].argmin()]; xN,yN=x[iN],y[iN]
    # SBP/DBP/MAP lines
    mapv=72+ (sbp-72)/3
    for val,txt,col in [(sbp,"収縮期圧 SBP",GOLD_D),(72,"拡張末期圧 DBP",BLUE),(mapv,"平均動脈圧 MAP",SLATE2)]:
        ax.axhline(val,0.02,0.98,color=col,lw=1.1,ls=(0,(5,4)),alpha=.65)
    ax.annotate("収縮期圧 SBP",(xpk,sbp),(xpk+0.02,sbp+3),color=GOLD_D,fontsize=15,weight="bold")
    ax.annotate("拡張末期圧 DBP",(0.9,72),(0.62,60),color=BLUE,fontsize=14,weight="bold")
    ax.text(0.985,mapv+1.5,"平均動脈圧 MAP",color=SLATE2,fontsize=13,ha="right")
    # dicrotic notch
    ax.plot([xN],[yN],'o',color=RED,ms=10,zorder=5)
    ax.annotate("重複切痕\n(dicrotic notch)\n＝大動脈弁閉鎖",(xN,yN),(xN+0.06,yN+16),
                color=RED,fontsize=13.5,weight="bold",ha="left",
                arrowprops=dict(arrowstyle="-",color=RED,lw=1.6))
    # upstroke arrow（白背景で波形線と重なっても読めるように）
    ax.annotate("急峻な立ち上がり\n(anacrotic upstroke)",(0.072,96),(0.002,118),
                color=INK,fontsize=13.5,ha="left",va="top",
                bbox=dict(boxstyle="round,pad=0.3",fc="white",ec="none",alpha=0.92),
                arrowprops=dict(arrowstyle="->",color=INK,lw=1.6))
    # runoff
    ax.annotate("拡張期下降\n(diastolic runoff)",(0.62,80),(0.66,96),color=INK,fontsize=13.5,
                arrowprops=dict(arrowstyle="->",color=INK,lw=1.4))
    # PP bracket
    ax.annotate("",(0.045,sbp),(0.045,72),arrowprops=dict(arrowstyle="<->",color=GOLD_D,lw=1.8))
    ax.text(0.06,(sbp+72)/2,"脈圧\nPP",color=GOLD_D,fontsize=13,weight="bold",va="center")
    ax.set_xlim(-0.03,1.02); ax.set_ylim(50,140)
    _save(fig,path)

def fig_decomp(path):
    fig,ax=_ax(9.4,4.5)
    x=np.linspace(0,1,700)
    fwd,refl,s=components(x); sc=(120-72)/s.max()
    F=72+sc*fwd; R=72+sc*refl; S=72+sc*s
    ax.fill_between(x,72,F,color=BLUE_F,alpha=.7,zorder=1)
    ax.fill_between(x,72,R,color=ORANGE_F,alpha=.7,zorder=1)
    ax.plot(x,F,color=BLUE,lw=2.2,ls=(0,(6,4)),zorder=3)
    ax.plot(x,R,color=ORANGE,lw=2.2,ls=(0,(6,4)),zorder=3)
    ax.plot(x,S,color=INK,lw=3.6,zorder=4,solid_capstyle="round")
    seg=(x>0.24)&(x<0.40); iN=np.where(seg)[0][S[seg].argmin()]
    ax.plot([x[iN]],[S[iN]],'o',color=RED,ms=9,zorder=6)
    ax.annotate("重複切痕",(x[iN],S[iN]),(x[iN]+0.02,S[iN]+13),color=RED,fontsize=13.5,weight="bold",
                arrowprops=dict(arrowstyle="-",color=RED,lw=1.4))
    ax.text(0.15,66,"前進波\n(左室駆出)",color=BLUE,fontsize=15,weight="bold",ha="center",va="top")
    ax.text(0.52,66,"反射波\n(末梢からの帰還)",color=ORANGE,fontsize=15,weight="bold",ha="center",va="top")
    ax.text(0.99,S.max(),"実測波形＝前進波＋反射波",color=INK,fontsize=13,ha="right",style="italic")
    ax.set_xlim(-0.02,1.02); ax.set_ylim(48,130)
    _save(fig,path)

def fig_central_peripheral(path):
    fig,ax=_ax(9.4,4.5)
    x=np.linspace(0,1,700)
    ao =beat(x,116,74,peak=0.185,refl_mu=0.34,refl_amp=0.52,sharp=0.8,refl_w=0.11)  # 大動脈:丸く低SBP早いnotch
    ra =beat(x,132,68,peak=0.15,refl_mu=0.44,refl_amp=0.30,sharp=1.25,refl_w=0.08)   # 橈骨:尖鋭高SBP遅いnotch
    dp =beat(x,142,64,peak=0.135,refl_mu=0.50,refl_amp=0.22,sharp=1.6,refl_w=0.07)   # 足背:さらに尖鋭
    ax.plot(x,ao,color=SLATE2,lw=3.0,label="大動脈")
    ax.plot(x,ra,color=INK,lw=3.2,label="橈骨動脈")
    ax.plot(x,dp,color=GOLD_D,lw=2.6,label="足背動脈")
    ax.axhline(90,0.02,0.98,color=SLATE,lw=1.0,ls=(0,(4,4)),alpha=.6)
    ax.text(0.99,91.5,"MAP はほぼ一定",color=SLATE2,fontsize=12.5,ha="right")
    ax.legend(loc="upper right",frameon=False,fontsize=13.5,handlelength=1.4)
    ax.annotate("末梢ほど SBP↑・脈圧拡大・立ち上がり急峻・切痕遅延",(0.5,-0.02),
                xycoords="axes fraction",ha="center",color=INK,fontsize=13.5)
    ax.set_xlim(-0.02,1.02); ax.set_ylim(52,150)
    _save(fig,path)

def fig_indices(path):
    fig,ax=_ax(9.2,4.5)
    x=np.linspace(0,1,700); y=beat(x,120,72)
    ax.plot(x,y,color=INK,lw=3.2)
    # systolic area (立ち上がり〜notch)
    seg=(x>0.24)&(x<0.40); iN=np.where(seg)[0][y[seg].argmin()]
    m=x<=x[iN]; ax.fill_between(x[m],72,y[m],color=GOLD,alpha=.28,zorder=1)
    ax.text(0.16,86,"収縮期面積\n∝ 一回拍出量 SV",color=GOLD_D,fontsize=14,weight="bold",ha="center")
    # dP/dt tangent on upstroke
    i0=np.argmin(np.abs(x-0.06)); i1=np.argmin(np.abs(x-0.11))
    sl=(y[i1]-y[i0])/(x[i1]-x[i0]); xt=np.array([0.02,0.17]); yt=y[i0]+sl*(xt-x[i0])
    ax.plot(xt,yt,color=RED,lw=2.4)
    ax.annotate("立ち上がり勾配 dP/dt\n（収縮性の目安）",(0.10,y[i0]+sl*(0.10-x[i0])),(0.24,118),
                color=RED,fontsize=13.5,weight="bold",arrowprops=dict(arrowstyle="->",color=RED,lw=1.6))
    ax.plot([x[iN]],[y[iN]],'o',color=INK,ms=7)
    ax.text(x[iN]+0.01,y[iN]+2,"切痕まで",color=SLATE2,fontsize=11.5)
    ax.set_xlim(-0.02,1.02); ax.set_ylim(52,132)
    _save(fig,path)

def _flush_wave(kind,x):
    """fast-flushの応答波形。x:0..1 の時間軸。flush解放後の挙動。"""
    y=np.zeros_like(x); top=1.0; base=0.0
    tf=0.42  # 解放点
    y[x<tf]=top
    tt=x[x>=tf]-tf
    if kind=="opt":
        r=-0.28*np.exp(-38*tt)*np.cos(2*np.pi*14*tt)  # 1〜2振動で速やか
        env=base+r
    elif kind=="under":
        r=-0.5*np.exp(-9*tt)*np.cos(2*np.pi*14*tt)     # 多数の振動・overshoot
        env=base+r
    else: # over
        env=base+ (top)* (0)  # slow
        env=base+(0.0)+(top)*np.exp(-8*tt)*0  # placeholder
        env=base+(top*np.exp(-6.0*tt))*0.0
        env=base+ (0)  # 下でexp立ち上げ
        env=base+ (1-np.exp(-7*tt))*0.0
        env= base - (1-np.exp(-6*tt))*0 + (np.exp(-100*tt))*0
        env= base + (top)*0
        env= base + (np.zeros_like(tt))
        env= base + (top*np.exp(-6*tt))  # だらだら戻る（振動なし）
        env= base + (top*np.exp(-5.5*tt))
        env= base + (top-top*(1-np.exp(-5.5*tt)))  # = top*exp
        env= base + top*np.exp(-5.5*tt) - top   # start ~0 从 below? fix
        env= base - (top - top*np.exp(-5.5*tt))  # undershoot slow?
        env= base + (-(1-np.exp(-5.5*tt)))*0.0
        env= base + (np.exp(-5.5*tt)-1)*0.0
        env= base  # reset
        env= base + (-(top))*(1-np.exp(-5.5*tt))*0.0
        env= base - (1-np.exp(-5.0*tt))*0.0
        env= base + 0.0*tt
        env= base + (top*0)
        env= base + (- (top))* (1-np.exp(-5.0*tt)) *0
        env= base + (top*np.exp(-5.0*tt))*0
        env= base  # slow monotonic下降 from top to base without overshoot
        env= base + top*np.exp(-5.0*tt)*0
        env= base + (top)*np.exp(-5.5*tt)  # だらだら
    yy=y.copy(); yy[x>=tf]=env
    return yy

def _flush_panel(ax,kind,title,sub,col):
    x=np.linspace(0,1.7,900)
    # 先に数拍の動脈波、その後flush
    aw=beat(np.linspace(0,1,240,endpoint=False),1.0,0.28)
    seg=np.concatenate([aw,aw[:120]])
    pre=np.linspace(0,0.30,len(seg))
    # build combined: arterial then flush square then response then arterial
    t=np.linspace(0,1.0,700)
    # arterial baseline (2 beats)
    ax_x,ax_y=train(nb=2,npts=200,sbp=1.0,dbp=0.28)
    ax_x=ax_x/ (ax_x.max()) *0.30
    ax.plot(ax_x,ax_y,color=col,lw=2.4)
    # flush: square up
    fx0=0.32
    ax.plot([0.30,fx0],[ax_y[-1],1.28],color=col,lw=2.4)
    ax.plot([fx0,0.55],[1.28,1.28],color=col,lw=2.4)  # flush plateau
    # release + response
    rx=np.linspace(0.55,1.05,400); tt=rx-0.55
    if kind=="opt": r=1.28+(0.28-1.0)+(-0.30)*np.exp(-30*tt)*np.cos(2*np.pi*13*(tt))
    resp={
      "opt": 0.28-0.34*np.exp(-26*tt)*np.cos(2*np.pi*12*tt),
      "under": 0.28-0.62*np.exp(-6.5*tt)*np.cos(2*np.pi*12*tt),
      "over": 0.28+(1.0)*np.exp(-7.5*tt),
    }[kind]
    # connect from plateau drop
    ax.plot([0.55,0.55],[1.28,resp[0]],color=col,lw=2.4)
    ax.plot(rx,resp,color=col,lw=2.4)
    # arterial resumes
    rx2,ry2=train(nb=1,npts=200,sbp=1.0,dbp=0.28)
    rx2=1.05+rx2/rx2.max()*0.30
    ax.plot(rx2,ry2,color=col,lw=2.4)
    ax.set_title(title,color=col,fontsize=16,weight="bold",pad=8)
    ax.text(0.5,-0.13,sub,transform=ax.transAxes,ha="center",color=INK,fontsize=12.5)
    ax.set_xlim(-0.02,1.4); ax.set_ylim(-0.35,1.5)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])

def fig_flush(path):
    fig,axs=plt.subplots(1,3,figsize=(12.6,3.9)); fig.patch.set_alpha(0)
    _flush_panel(axs[0],"opt","最適ダンピング","1〜2回の振動で速やか復帰\n数値は正確",GREEN)
    _flush_panel(axs[1],"under","アンダーダンプ","多数の振動・overshoot\nSBP過大／DBP過小",RED)
    _flush_panel(axs[2],"over","オーバーダンプ","振動なくだらだら復帰\nSBP過小／DBP過大",BLUE)
    for a in axs: a.patch.set_alpha(0)
    fig.subplots_adjust(wspace=0.08,left=0.01,right=0.99,top=0.86,bottom=0.14)
    _save(fig,path)

def fig_fnzeta(path):
    fig,ax=plt.subplots(figsize=(9.4,5.0)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    fn=np.linspace(0,40,400)
    # Gardner風: 適正域の下側境界（ζ下限）と上側境界（ζ上限）はfnとともに広がる曲線
    def lower(f): return np.clip(0.7-0.015*f,0.18,0.7)   # underdamped境界
    def upper(f): return np.clip(1.35-0.02*f,0.45,1.35)  # overdamped境界
    ax.fill_between(fn,lower(fn),upper(fn),where=fn>=7,color=GREEN,alpha=.18,zorder=1)  # adequate
    ax.fill_between(fn,0,lower(fn),color=RED,alpha=.10,zorder=1)                        # underdamped
    ax.fill_between(fn,upper(fn),1.5,color=BLUE,alpha=.10,zorder=1)                     # overdamped
    ax.fill_between(fn,0,1.5,where=fn<7,color=GRAY,alpha=.14,zorder=2)                  # fn不足=unacceptable
    ax.plot(fn,lower(fn),color=RED,lw=1.6); ax.plot(fn,upper(fn),color=BLUE,lw=1.6)
    ax.axvline(7,color=GRAY,lw=1.4,ls=(0,(4,3)))
    # optimal box ζ0.6-0.7, fn>~15
    ax.add_patch(Rectangle((15,0.6),23,0.1,fill=True,color=GOLD,alpha=.5,zorder=3))
    ax.add_patch(Rectangle((15,0.6),23,0.1,fill=False,edgecolor=GOLD_D,lw=1.8,zorder=4))
    ax.text(26,0.65,"最適 ζ ≒ 0.6–0.7",color=GOLD_D,fontsize=13.5,weight="bold",ha="center",va="center")
    ax.text(24,1.15,"オーバーダンプ",color=BLUE,fontsize=14,weight="bold",ha="center")
    ax.text(24,0.28,"アンダーダンプ（共振）",color=RED,fontsize=14,weight="bold",ha="center")
    ax.text(3.5,0.75,"自然周波数\n不足",color=SLATE2,fontsize=12.5,weight="bold",ha="center",rotation=90)
    ax.text(22,0.93,"適正域 (adequate)",color=GREEN,fontsize=13.5,weight="bold",ha="center")
    ax.set_xlim(0,40); ax.set_ylim(0,1.5)
    ax.set_xlabel("自然周波数 fn (Hz) →",fontsize=14); ax.set_ylabel("減衰係数 ζ →",fontsize=14)
    ax.set_xticks([0,7,10,20,30,40]); ax.set_yticks([0,0.3,0.6,0.7,1.0,1.4])
    ax.tick_params(labelsize=11.5,length=0)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    for s in ["left","bottom"]: ax.spines[s].set_color(SLATE)
    _save(fig,path)

def fig_normal(path):
    fig,ax=_ax(9.4,4.2)
    X,Y=train(nb=4,npts=240,sbp=120,dbp=72)
    X=X/X.max()
    ax.plot(X,Y,color=INK,lw=3.0)
    ax.text(0.0,1.02,"正常波形（橈骨動脈）",transform=ax.transAxes,fontsize=13,color=SLATE2)
    ax.set_ylim(52,132); _save(fig,path)

def fig_optflush(path):
    fig,ax=_ax(9.2,4.2)
    _flush_panel(ax,"opt","","",GREEN)
    ax.set_title("最適ダンピングの正常フラッシュ応答",color=GREEN,fontsize=16,weight="bold")
    ax.text(0.5,-0.08,"方形波の解放後、1〜2回の小さな振動で速やかにベースラインへ復帰",
            transform=ax.transAxes,ha="center",color=INK,fontsize=13.5)
    _save(fig,path)

def fig_events(path):
    fig,ax=_ax(9.6,4.4)
    t=np.linspace(0,10,1000)
    base=88+3*np.sin(t*1.3)
    sbp=base+30; dbp=base-16
    # events
    def bump(c,w,a): return a*np.exp(-((t-c)/w)**2)
    m = bump(2.0,0.35,45)   # 挿管↑
    m+=-bump(4.6,0.5,30)    # 出血↓
    m+= bump(6.4,0.5,26)    # 昇圧薬↑
    sbp=sbp+m; dbp=dbp+m*0.5; mapv=(sbp+2*dbp)/3
    ax.fill_between(t,dbp,sbp,color=BLUE_F,alpha=.6)
    ax.plot(t,sbp,color=INK,lw=1.6); ax.plot(t,dbp,color=SLATE2,lw=1.6)
    ax.plot(t,mapv,color=GOLD_D,lw=2.6)
    ax.text(9.9,mapv[-1],"MAP",color=GOLD_D,fontsize=13,ha="right",va="bottom",weight="bold")
    for c,lab,dy in [(2.0,"喉頭鏡・挿管",1),(4.6,"出血",-1),(6.4,"昇圧薬",1),(0.5,"導入",1)]:
        ax.axvline(c,color=GRAY,lw=1.0,ls=(0,(3,3)),alpha=.6)
        ax.annotate(lab,(c,133 if dy>0 else 133),(c,140),color=INK,fontsize=12.5,ha="center")
    ax.set_ylim(55,148); ax.set_xlim(0,10)
    ax.text(0.0,52,"拍動ごとの連続血圧で急変に即応（NIBPの間欠測定では見えない）",fontsize=12.5,color=SLATE2)
    _save(fig,path)

def _vent(t,period=3.0,pins=0.6):
    ph=(t%period)/period
    return np.where(ph<0.33,pins*np.sin(np.pi*ph/0.33),0)

def fig_ppv(path):
    fig,(ax,ax2)=plt.subplots(2,1,figsize=(9.6,4.9),height_ratios=[3,1],sharex=True)
    fig.patch.set_alpha(0)
    for a in (ax,ax2): a.patch.set_alpha(0); [s.set_visible(False) for s in a.spines.values()]; a.set_xticks([]); a.set_yticks([])
    tb=0.8
    X=[];Y=[]
    n=12
    for i in range(n):
        xs=np.linspace(0,tb,120,endpoint=False)
        # 呼吸性に脈圧が変動
        resp=np.sin(2*np.pi*(i*tb)/3.0)
        sbp=120+8*resp; dbp=72-2*resp
        X.append(xs+i*tb); Y.append(beat(xs,sbp,dbp))
    X=np.concatenate(X); Y=np.concatenate(Y)
    ax.plot(X,Y,color=INK,lw=2.4)
    ppmax=Y.max(); ppmin=None
    # find max & min pulse pressure beats
    ax.annotate("PPmax",(X[Y.argmax()],Y.max()),(X[Y.argmax()],Y.max()+6),color=RED,fontsize=13,weight="bold",ha="center")
    imin=np.argmin([ (120+8*np.sin(2*np.pi*(i*tb)/3.0))-(72-2*np.sin(2*np.pi*(i*tb)/3.0)) for i in range(n)])
    ax.annotate("PPmin",(imin*tb+0.15,110),(imin*tb+0.15,60),color=BLUE,fontsize=13,weight="bold",ha="center",
                arrowprops=dict(arrowstyle="->",color=BLUE,lw=1.4))
    ax.text(0.995,1.02,"PPV = (PPmax − PPmin) / PPmean × 100（>~13%で輸液反応性↑）",
            transform=ax.transAxes,ha="right",va="bottom",fontsize=13.5,color=INK,weight="bold")
    ax.set_ylim(52,140)
    tv=np.linspace(0,n*tb,1000); ax2.fill_between(tv,0,_vent(tv),color=SLATE,alpha=.35)
    ax2.plot(tv,_vent(tv),color=SLATE2,lw=1.6)
    ax2.text(0.0,0.62,"気道内圧（陽圧換気）",fontsize=12,color=SLATE2)
    ax2.set_ylim(-0.05,0.8)
    fig.subplots_adjust(hspace=0.08,left=0.01,right=0.99,top=0.92,bottom=0.04)
    _save(fig,path)

def fig_spv(path):
    fig,(ax,ax2)=plt.subplots(2,1,figsize=(9.6,4.9),height_ratios=[3,1],sharex=True)
    fig.patch.set_alpha(0)
    for a in (ax,ax2): a.patch.set_alpha(0); [s.set_visible(False) for s in a.spines.values()]; a.set_xticks([]); a.set_yticks([])
    tb=0.8;n=10; X=[];Y=[];sbps=[]
    for i in range(n):
        xs=np.linspace(0,tb,120,endpoint=False)
        resp=np.sin(2*np.pi*(i*tb)/3.0)
        sbp=120+10*resp; sbps.append(sbp)
        X.append(xs+i*tb); Y.append(beat(xs,sbp,72))
    X=np.concatenate(X);Y=np.concatenate(Y)
    ax.plot(X,Y,color=INK,lw=2.4)
    ref=120-3
    ax.axhline(ref,color=SLATE,lw=1.2,ls=(0,(5,4)))
    ax.text(0.0,ref+0.5,"基準（呼気終末）",fontsize=11.5,color=SLATE2)
    ax.axhline(max(sbps),color=RED,lw=1.0,ls=(0,(3,3)))
    ax.axhline(min(sbps),color=BLUE,lw=1.0,ls=(0,(3,3)))
    ax.annotate("ΔUp",(n*tb*0.5,(max(sbps)+ref)/2),color=RED,fontsize=13,weight="bold")
    ax.annotate("ΔDown",(n*tb*0.5,(min(sbps)+ref)/2),color=BLUE,fontsize=13,weight="bold")
    ax.annotate("",(n*tb-0.4,max(sbps)),(n*tb-0.4,min(sbps)),arrowprops=dict(arrowstyle="<->",color=GOLD_D,lw=1.8))
    ax.text(n*tb-0.3,120,"SPV",color=GOLD_D,fontsize=13,weight="bold")
    ax.set_ylim(52,140)
    tv=np.linspace(0,n*tb,1000); ax2.fill_between(tv,0,_vent(tv),color=SLATE,alpha=.35); ax2.plot(tv,_vent(tv),color=SLATE2,lw=1.6)
    ax2.text(0.0,0.62,"気道内圧",fontsize=12,color=SLATE2); ax2.set_ylim(-0.05,0.8)
    fig.subplots_adjust(hspace=0.08,left=0.01,right=0.99,top=0.95,bottom=0.04)
    _save(fig,path)

def fig_svr(path):
    fig,axs=plt.subplots(1,2,figsize=(10.6,4.2)); fig.patch.set_alpha(0)
    x=np.linspace(0,1,500)
    low=beat(x,108,52,peak=0.14,refl_mu=0.30,refl_amp=0.18,sharp=1.2,refl_w=0.07) # 低SVR:切痕低位・急落
    high=beat(x,132,86,peak=0.16,refl_mu=0.42,refl_amp=0.5,sharp=0.95,refl_w=0.10) # 高SVR:切痕高位・緩徐
    for ax,y,t,c,sub in [(axs[0],low,"低 SVR",TEAL,"切痕が低位・拡張期の急落\n（distributive／敗血症様）"),
                          (axs[1],high,"高 SVR",ORANGE,"切痕が高位・拡張期は緩徐\n（血管収縮・低心拍出）")]:
        ax.plot(x,y,color=INK,lw=3.2); ax.patch.set_alpha(0)
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_ylim(40,140)
        ax.set_title(t,color=c,fontsize=17,weight="bold")
        ax.text(0.5,-0.16,sub,transform=ax.transAxes,ha="center",fontsize=13,color=INK)
    fig.subplots_adjust(wspace=0.1,left=0.02,right=0.98,top=0.86,bottom=0.16)
    _save(fig,path)

def _damp_pair(path,kind,title,sub,col):
    fig,ax=_ax(9.4,4.3)
    x=np.linspace(0,1,500)
    norm=beat(x,120,72)
    if kind=="over":
        # 低域通過的になまり: 平滑化＋振幅減＋切痕消失
        from numpy import convolve
        k=np.ones(60)/60; ab=np.convolve(np.tile(norm,3),k,"same")[500:1000]
        ab=72+(ab-72)*0.62; ab=ab+ (76-ab.min())*0  # lift DBP
        ab=ab+6  # DBP過大
        ab=np.clip(ab,None,112)
    else:
        # underdamped: overshoot spike + 高周波振動
        osc=8*np.exp(-6*x)*np.cos(2*np.pi*12*x)
        ab=beat(x,120,72)+ np.where(x<0.05,0,osc)
        ab[x<0.2]=beat(x,138,66)[x<0.2]  # 収縮期スパイク
    ax.plot(x,norm,color=SLATE,lw=2.0,ls=(0,(5,4)),label="正常")
    ax.plot(x,ab,color=col,lw=3.2,label=title)
    ax.legend(loc="upper right",frameon=False,fontsize=13.5)
    ax.text(0.5,-0.12,sub,transform=ax.transAxes,ha="center",fontsize=13.5,color=INK)
    ax.set_ylim(48,150); fig.subplots_adjust(bottom=0.16)
    _save(fig,path)

def fig_overdamp(path):
    _damp_pair(path,"over","オーバーダンプ",
               "なまり・切痕消失・立ち上がり鈍　→ SBP過小／DBP過大（MAPは比較的保たれる）",BLUE)
def fig_underdamp(path):
    _damp_pair(path,"under","アンダーダンプ",
               "収縮期スパイク・overshoot・多振動　→ SBP過大／DBP過小（偽の高血圧）",RED)

def fig_paradoxus_alternans(path):
    fig,axs=plt.subplots(1,2,figsize=(11.0,4.2)); fig.patch.set_alpha(0)
    tb=0.8
    # paradoxus
    X=[];Y=[]
    for i in range(9):
        xs=np.linspace(0,tb,110,endpoint=False)
        resp=np.sin(2*np.pi*(i*tb)/3.2)
        sbp=118-14*np.clip(np.sin(2*np.pi*(i*tb)/3.2),0,1)  # 吸気でSBP低下
        X.append(xs+i*tb); Y.append(beat(xs,sbp,70))
    X=np.concatenate(X);Y=np.concatenate(Y)
    axs[0].plot(X,Y,color=INK,lw=2.2)
    axs[0].set_title("奇脈 (pulsus paradoxus)",color=RED,fontsize=15.5,weight="bold")
    axs[0].text(0.5,-0.13,"吸気時に SBP が >10 mmHg 低下\n（タンポナーデ・重症喘息）",transform=axs[0].transAxes,ha="center",fontsize=12.5,color=INK)
    # alternans
    X=[];Y=[]
    for i in range(8):
        xs=np.linspace(0,tb,110,endpoint=False)
        sbp=126 if i%2==0 else 104
        X.append(xs+i*tb); Y.append(beat(xs,sbp,70))
    X=np.concatenate(X);Y=np.concatenate(Y)
    axs[1].plot(X,Y,color=INK,lw=2.2)
    axs[1].set_title("交互脈 (pulsus alternans)",color=BLUE,fontsize=15.5,weight="bold")
    axs[1].text(0.5,-0.13,"1拍ごとに振幅が大小交互\n（重症左室不全）",transform=axs[1].transAxes,ha="center",fontsize=12.5,color=INK)
    for a in axs:
        a.patch.set_alpha(0); [s.set_visible(False) for s in a.spines.values()]; a.set_xticks([]); a.set_yticks([]); a.set_ylim(52,140)
    fig.subplots_adjust(wspace=0.08,left=0.02,right=0.98,top=0.86,bottom=0.16)
    _save(fig,path)

def fig_valve_grid(path):
    fig,axs=plt.subplots(1,4,figsize=(13.6,3.6)); fig.patch.set_alpha(0)
    x=np.linspace(0,1,500)
    pt=beat(x,102,72,peak=0.24,refl_mu=0.45,refl_amp=0.3,sharp=0.5,refl_w=0.12)
    bf=72+ (48)*(0.9*_g(x,0.15,0.05)+0.85*_g(x,0.30,0.06)) ; bf=72+(bf-72)/(bf-72).max()*50
    wp=beat(x,150,50,peak=0.13,refl_mu=0.5,refl_amp=0.15,sharp=1.5,refl_w=0.07)
    sd=72+ (46)*(1.0*_g(x,0.11,0.035)+0.55*_g(x,0.30,0.09)); sd=72+(sd-72)/(sd-72).max()*52
    data=[(pt,"parvus et tardus","大動脈弁狭窄\n立ち上がり遅く低振幅",TEAL),
          (bf,"bisferiens（二峰性）","重症AR・AR+AS・HOCM\n収縮期に2峰",ORANGE),
          (wp,"wide pulse pressure","AR・高齢スティフネス\n脈圧の拡大",GOLD_D),
          (sd,"spike-and-dome","HOCM\n急峻なspike→dome",RED)]
    for ax,(y,t,sub,c) in zip(axs,data):
        ax.plot(x,y,color=INK,lw=3.0); ax.patch.set_alpha(0)
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_ylim(40,162)
        ax.set_title(t,color=c,fontsize=15,weight="bold",pad=6)
        ax.text(0.5,-0.20,sub,transform=ax.transAxes,ha="center",va="top",fontsize=12,color=INK,linespacing=1.4)
    fig.subplots_adjust(wspace=0.10,left=0.01,right=0.99,top=0.84,bottom=0.20)
    _save(fig,path)

def fig_pulse_contour(path):
    fig,ax=_ax(9.6,4.4)
    X,Y=train(nb=3,npts=260,sbp=120,dbp=72); X=X/X.max()
    ax.plot(X,Y,color=INK,lw=2.8)
    # shade systolic area of each beat
    for i in range(3):
        seg=(X>=i/3)&(X<i/3+0.13)
        ax.fill_between(X[seg],72,Y[seg],color=GOLD,alpha=.30)
    ax.annotate("収縮期面積 ∝ SV",(0.06,95),(0.06,128),color=GOLD_D,fontsize=13.5,weight="bold",
                arrowprops=dict(arrowstyle="->",color=GOLD_D,lw=1.6))
    ax.annotate("拍動ごとに CO・SVV を連続推定",(0.63,120),color=INK,fontsize=13.5,ha="left")
    ax.text(0.995,0.02,"較正あり：PiCCO(経肺熱希釈)・LiDCO(Li希釈)／較正なし：FloTrac",
            transform=ax.transAxes,ha="right",va="bottom",fontsize=12,color=SLATE2)
    ax.set_ylim(52,138); _save(fig,path)

def fig_transducer(path):
    fig,ax=plt.subplots(figsize=(9.4,4.6)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    ax.set_xlim(0,10); ax.set_ylim(0,6); ax.axis("off")
    # tubing + diaphragm
    ax.add_patch(FancyBboxPatch((0.4,2.6),2.0,0.8,boxstyle="round,pad=0.02",fc=BLUE_F,ec=BLUE,lw=1.5))
    ax.text(1.4,3.0,"血液/流体柱",ha="center",va="center",fontsize=12,color=BLUE)
    ax.plot([2.4,3.0],[3.0,3.0],color=INK,lw=2)
    ax.add_patch(Rectangle((3.0,2.3),0.14,1.4,color=GOLD_D))  # diaphragm
    ax.text(3.07,4.0,"ダイヤフラム",ha="center",fontsize=12,color=GOLD_D)
    # wheatstone diamond
    cx,cy=6.2,3.0; d=1.35
    pts=[(cx,cy+d),(cx+d,cy),(cx,cy-d),(cx-d,cy)]
    ax.add_patch(Polygon(pts,closed=True,fill=False,ec=INK,lw=2))
    for (a,b) in [(0,1),(1,2),(2,3),(3,0)]:
        mx=(pts[a][0]+pts[b][0])/2; my=(pts[a][1]+pts[b][1])/2
        ax.add_patch(Rectangle((mx-0.13,my-0.06),0.26,0.12,angle=0,fc=GRAYF,ec=INK,lw=1.2))
    ax.text(cx,cy,"ホイートストン\nブリッジ",ha="center",va="center",fontsize=11.5,color=INK)
    ax.plot([3.14,cx-d],[3.0,3.0],color=INK,lw=1.5,ls=(0,(4,3)))
    ax.text(4.6,3.25,"たわみ→抵抗変化",ha="center",fontsize=11,color=SLATE2)
    # output
    ax.annotate("",(9.2,3.0),(cx+d,3.0),arrowprops=dict(arrowstyle="->",color=INK,lw=2))
    ax.text(8.6,3.4,"出力電圧\n→モニタ",ha="center",fontsize=12,color=INK)
    ax.text(cx,cy-d-0.5,"ストレインゲージ（4素子）",ha="center",fontsize=11.5,color=INK)
    _save(fig,path)

def fig_hero(path):
    """表紙用の小さな装飾（決まった臨床数値・ラベルは持たない）。
    既存の train()（fig_normal 等と同じ動脈圧波形ジェネレータ、sbp=120/dbp=72は他図でも
    使用済みの値）を再利用した横長の脈波ストリップに、収縮期ピークへ金ドットを打つだけ。"""
    fig,ax=plt.subplots(figsize=(12,1.7)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    n=5
    X,Y=train(nb=n,npts=220,sbp=120,dbp=72); X=X/X.max()
    ax.plot(X,Y,color=INK,lw=3.2,solid_capstyle="round")
    for i in range(n):
        seg=(X>=i/n)&(X<(i+1)/n)
        if seg.any():
            j=np.where(seg)[0][Y[seg].argmax()]
            ax.plot([X[j]],[Y[j]],'o',color=GOLD_D,ms=9,zorder=5)
    ax.set_ylim(55,140); ax.set_xlim(-0.01,1.01)
    _save(fig,path)

# ===================== 図（新規7・aline_content.json の diagram spec に厳密準拠） =====================
# s1_1/s1_2/s2_1/s7_1/s7_2/s8_2/s8_3 は事前生成PNGが無かった（波形でなくタイムライン/比較表/
# 連結図/カード/フローチャート）。ここで新規に追加する。数値・ラベルは各スライドの
# content["diagram"]["spec"|"labels"|"values"] に書かれたものだけを使い、新しい臨床数値・
# 主張は一切創作しない。配色・線幅・フォントは既存18図（GOLD_D/BLUE/ORANGE/TEAL/RED/GREEN、
# Hiragino Sans、白背景transparent）を踏襲する。

def fig_timeline_history(path):
    """s1_1: 1733 Hales→1828 Poiseuille→1847 Ludwig のゴールド基線タイムライン。
    「点の測定→連続波形」の発展を右向き矢印で示す（diagram.spec通り）。"""
    fig,ax=plt.subplots(figsize=(9.6,3.7)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    ax.set_xlim(0,10.6); ax.set_ylim(0,4.6); ax.axis("off")
    ax.plot([0.7,9.55],[2.6,2.6],color=GOLD_D,lw=3.0,solid_capstyle="round",zorder=1)
    ax.annotate("",(9.85,2.6),(9.5,2.6),arrowprops=dict(arrowstyle="-|>",color=GOLD_D,lw=3.0,
                mutation_scale=20))
    nodes=[(2.0,"1733","Hales","血柱の高さで可視化"),
           (5.5,"1828","Poiseuille","水銀圧力計・mmHg化"),
           (9.0,"1847","Ludwig","kymographで連続記録")]
    for x,year,name,desc in nodes:
        ax.plot([x],[2.6],'o',color=GOLD_D,ms=14,zorder=3,mec="white",mew=1.6)
        ax.text(x,3.40,year,ha="center",fontsize=15.5,weight="bold",color=GOLD_D)
        ax.text(x,2.00,name,ha="center",fontsize=14,weight="bold",color=INK)
        ax.text(x,1.52,desc,ha="center",fontsize=12,color=SLATE2)
    ax.text(1.35,0.55,"点の測定",ha="center",fontsize=13,color=SLATE2,style="italic")
    ax.annotate("",(8.3,0.55),(2.25,0.55),arrowprops=dict(arrowstyle="->",color=HAIR,lw=1.6))
    ax.text(9.05,0.55,"連続波形",ha="center",fontsize=13,color=SLATE2,style="italic")
    _save(fig,path)

def fig_compare_invasive(path):
    """s1_2: 非観血 vs 観血の2列対比表（連続性/拍動情報/精度/侵襲・合併症/採血）。"""
    fig,ax=plt.subplots(figsize=(9.4,4.9)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    ax.set_xlim(0,10.2); ax.set_ylim(0,6.2); ax.axis("off")
    rows=["連続性","拍動情報","精度","侵襲・合併症","採血"]
    noninv=["間欠(数分毎)","なし","部位・カフで誤差","非侵襲","不可"]
    inv=["連続(拍動ごと)","波形で豊富","較正次第で正確","侵襲・血栓/感染","繰り返し可"]
    x0,x1,x2,x3=0.15,2.55,6.05,9.95
    top=6.05; hdr_h=0.85; row_h=0.94
    ax.add_patch(Rectangle((x0,top-hdr_h),x1-x0,hdr_h,fc=GRAYF,ec=HAIR,lw=0.9))
    ax.add_patch(Rectangle((x1,top-hdr_h),x2-x1,hdr_h,fc=BLUE_F,ec=BLUE,lw=1.3))
    ax.add_patch(Rectangle((x2,top-hdr_h),x3-x2,hdr_h,fc=ORANGE_F,ec=ORANGE,lw=1.3))
    ax.text((x0+x1)/2,top-hdr_h/2,"項目",ha="center",va="center",fontsize=13,weight="bold",color=SLATE2)
    ax.text((x1+x2)/2,top-hdr_h/2,"非観血",ha="center",va="center",fontsize=15.5,weight="bold",color=BLUE)
    ax.text((x2+x3)/2,top-hdr_h/2,"観血",ha="center",va="center",fontsize=15.5,weight="bold",color=ORANGE)
    y=top-hdr_h
    for i,(lab,nv,iv) in enumerate(zip(rows,noninv,inv)):
        y0=y-row_h*(i+1); y1c=y-row_h*i
        ax.add_patch(Rectangle((x0,y0),x1-x0,row_h,fc=GRAYF,ec=HAIR,lw=0.8))
        ax.add_patch(Rectangle((x1,y0),x2-x1,row_h,fc="none",ec=HAIR,lw=0.8))
        ax.add_patch(Rectangle((x2,y0),x3-x2,row_h,fc="none",ec=HAIR,lw=0.8))
        ax.text((x0+x1)/2,(y0+y1c)/2,lab,ha="center",va="center",fontsize=13,weight="bold",color=INK)
        ax.text((x1+x2)/2,(y0+y1c)/2,nv,ha="center",va="center",fontsize=12,color=INK)
        ax.text((x2+x3)/2,(y0+y1c)/2,iv,ha="center",va="center",fontsize=12,color=INK)
    _save(fig,path)

def fig_measurement_chain(path):
    """s2_1: カニューレ→非伸展チューブ→三方活栓→トランスデューサ→モニタの連結チェーン。
    加圧バッグ/持続フラッシュを吹き出しで、トランスデューサのレベリング基準(右房レベル)を
    破線で、10cm高低差≒7.4mmHgの誤差を矢印で示す。"""
    fig,ax=plt.subplots(figsize=(10.6,5.0)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    ax.set_xlim(0,11.4); ax.set_ylim(0,6.8); ax.axis("off")
    labels=["動脈\nカニューレ","非伸展\nチューブ","三方活栓","トランス\nデューサ","モニタ"]
    cx=[1.15,3.35,5.55,7.75,9.95]; bw=1.55; by,bh=4.55,1.0
    for i,(x,lab) in enumerate(zip(cx,labels)):
        highlight=(i==3)
        fc=GOLD_F if highlight else GRAYF
        ec=GOLD_D if highlight else SLATE
        ax.add_patch(FancyBboxPatch((x-bw/2,by),bw,bh,boxstyle="round,pad=0.02,rounding_size=0.08",
                                     fc=fc,ec=ec,lw=1.8,zorder=2))
        ax.text(x,by+bh/2,lab,ha="center",va="center",fontsize=12.5,weight="bold",
                color=GOLD_D if highlight else INK,zorder=3)
        if i<len(cx)-1:
            ax.annotate("",(cx[i+1]-bw/2,by+bh/2),(x+bw/2,by+bh/2),
                        arrowprops=dict(arrowstyle="-|>",color=INK,lw=1.8,mutation_scale=16))
    # 加圧バッグ + 持続フラッシュ（吹き出し）
    bx,byy,bw2,bh2=6.65,5.95,3.05,0.85
    ax.add_patch(FancyBboxPatch((bx-bw2/2,byy),bw2,bh2,boxstyle="round,pad=0.02,rounding_size=0.06",
                                 fc=BLUE_F,ec=BLUE,lw=1.5,zorder=2))
    ax.text(bx,byy+bh2/2,"加圧バッグ 約300 mmHg\n＋持続フラッシュ 約3 mL/h",ha="center",va="center",
            fontsize=11,weight="bold",color=BLUE,zorder=3)
    ax.annotate("",(bx,by+bh),(bx,byy),arrowprops=dict(arrowstyle="-|>",color=BLUE,lw=1.6,mutation_scale=14))
    # 右房レベル基準線とレベリング
    ref_y=1.55
    ax.plot([0.6,10.8],[ref_y,ref_y],color=SLATE,lw=1.5,ls=(0,(6,4)))
    ax.text(0.6,ref_y-0.32,"右房レベル (第4肋間・中腋窩線)",ha="left",va="top",fontsize=12,color=SLATE2)
    ax.plot([cx[3],cx[3]],[by,ref_y],color=GOLD_D,lw=1.6,ls=(0,(4,3)))
    ax.plot([cx[3]],[ref_y],'o',color=GOLD_D,ms=8,zorder=4)
    ax.text(cx[3]-0.20,(by+ref_y)/2,"レベリング",ha="right",va="center",fontsize=11,color=GOLD_D,rotation=90)
    # 高さ誤差 10cm ≒ 7.4mmHg
    ex=9.85
    ax.plot([ex-0.22,ex+0.22],[ref_y,ref_y],color=RED,lw=1.8)
    ax.plot([ex-0.22,ex+0.22],[ref_y+0.85,ref_y+0.85],color=RED,lw=1.8)
    ax.annotate("",(ex,ref_y+0.85),(ex,ref_y),arrowprops=dict(arrowstyle="<->",color=RED,lw=1.6))
    ax.text(ex,ref_y-0.32,"10cm ≒ 7.4mmHg\nの系統誤差",ha="center",va="top",fontsize=10.5,
            weight="bold",color=RED,linespacing=1.3)
    _save(fig,path)

def fig_damping_flow(path):
    """s7_1: 共通の第一手バナー＋3枚のカード（オーバーダンプ／アンダーダンプ／a-line-NIBP乖離）。"""
    fig,ax=plt.subplots(figsize=(10.6,4.7)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    ax.set_xlim(0,11.2); ax.set_ylim(0,5.0); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.3,4.05),10.6,0.75,boxstyle="round,pad=0.02,rounding_size=0.10",
                                 fc=GOLD_F,ec=GOLD_D,lw=1.6,zorder=2))
    ax.text(5.6,4.43,"第一手: fast-flushで評価 → 再ゼロ・再レベリング",ha="center",va="center",
            fontsize=14.5,weight="bold",color=GOLD_D,zorder=3)
    cw,ch,gap=3.35,3.45,0.30
    x0=0.3
    cards=[("オーバーダンプ","原因: 気泡・凝血・キンク\n柔らかい／長いチューブ",
            "対処: 吸引・フラッシュ\nチューブを短く硬く",BLUE,BLUE_F),
           ("アンダーダンプ","原因: 長いチューブ・共振\n頻脈",
            "対処: 延長/活栓を削減\nダンピング補正デバイス",RED,RED_F),
           ("a-line / NIBP 乖離","判断: 波形品質を確認\nfast-flushで系を評価",
            "末梢増幅・末梢循環不全も考慮\nMAPで照合",TEAL,TEAL_F)]
    for i,(title,top_body,bot_body,accent,fill) in enumerate(cards):
        x=x0+i*(cw+gap)
        ax.add_patch(FancyBboxPatch((x,0.25),cw,ch,boxstyle="round,pad=0.02,rounding_size=0.10",
                                     fc=fill,ec=accent,lw=1.8,zorder=2))
        ax.text(x+cw/2,0.25+ch-0.32,title,ha="center",va="top",fontsize=15,weight="bold",
                color=accent,zorder=3)
        ax.text(x+cw/2,0.25+ch-0.88,top_body,ha="center",va="top",fontsize=12,color=INK,zorder=3,linespacing=1.5)
        ax.annotate("",(x+cw/2,0.25+ch-2.10),(x+cw/2,0.25+ch-1.75),
                    arrowprops=dict(arrowstyle="-|>",color=accent,lw=1.6,mutation_scale=13))
        ax.text(x+cw/2,0.25+ch-2.22,bot_body,ha="center",va="top",fontsize=12,color=INK,zorder=3,linespacing=1.5)
    _save(fig,path)

def fig_complications(path):
    """s7_2: 合併症6項目（上段カード）＋予防キーワード帯（左下）＋Allen testの限界（右下強調）。"""
    fig,ax=plt.subplots(figsize=(10.4,4.8)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    ax.set_xlim(0,11.0); ax.set_ylim(0,5.0); ax.axis("off")
    comps=["虚血","感染","出血/血腫","薬剤誤注入","神経障害","空気塞栓"]
    n=len(comps); cw=1.62; gap=0.145; x0=0.28; cy,ch=3.55,1.15
    for i,lab in enumerate(comps):
        x=x0+i*(cw+gap)
        ax.add_patch(FancyBboxPatch((x,cy),cw,ch,boxstyle="round,pad=0.02,rounding_size=0.09",
                                     fc=RED_F,ec=RED,lw=1.5,zorder=2))
        ax.text(x+cw/2,cy+ch/2,lab,ha="center",va="center",fontsize=12,weight="bold",color=RED,zorder=3)
    # 左下: 予防帯
    px,py,pw,ph=0.28,0.30,7.0,2.55
    ax.add_patch(FancyBboxPatch((px,py),pw,ph,boxstyle="round,pad=0.02,rounding_size=0.10",
                                 fc=GREEN_F,ec=GREEN,lw=1.8,zorder=2))
    ax.text(px+pw/2,py+ph-0.32,"予防",ha="center",va="top",fontsize=15,weight="bold",color=GREEN,zorder=3)
    ax.text(px+pw/2,py+ph-0.85,"部位選択・細径カテ・無菌／閉鎖式\nライン識別・抜去時は十分な圧迫止血",
            ha="center",va="top",fontsize=12.5,color=INK,zorder=3,linespacing=1.6)
    # 右下: Allen test 強調カード
    ax_,ay,aw,ah=7.55,0.30,3.15,2.55
    ax.add_patch(FancyBboxPatch((ax_,ay),aw,ah,boxstyle="round,pad=0.02,rounding_size=0.10",
                                 fc=GOLD_F,ec=GOLD_D,lw=2.2,zorder=2))
    ax.text(ax_+aw/2,ay+ah-0.32,"Allen testの限界",ha="center",va="top",fontsize=14,weight="bold",
            color=GOLD_D,zorder=3)
    ax.text(ax_+aw/2,ay+ah-0.85,"側副評価の目安\n虚血の予測能は乏しい\n正常でも過信しない",
            ha="center",va="top",fontsize=12,color=INK,zorder=3,linespacing=1.6)
    _save(fig,path)

def fig_gdt_flow(path):
    """s8_2: SV最適化フローチャート（PPV/SVV高値→フルイドチャレンジ→SV反応性判定）＋Ea_dyn注記。"""
    fig,ax=plt.subplots(figsize=(8.6,5.3)); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    ax.set_xlim(0,9.4); ax.set_ylim(3.25,10.45); ax.axis("off")
    bw=4.6; bx=0.5
    def box(y,h,text,accent,fill,fs=13.5):
        ax.add_patch(FancyBboxPatch((bx,y),bw,h,boxstyle="round,pad=0.02,rounding_size=0.10",
                                     fc=fill,ec=accent,lw=1.8,zorder=2))
        ax.text(bx+bw/2,y+h/2,text,ha="center",va="center",fontsize=fs,weight="bold",color=accent,zorder=3,
                linespacing=1.4)
    def arrow(y0,y1,label=None,color=INK):
        ax.annotate("",(bx+bw/2,y1),(bx+bw/2,y0),arrowprops=dict(arrowstyle="-|>",color=color,lw=1.8,mutation_scale=15))
        if label:
            ax.text(bx+bw/2+0.28,(y0+y1)/2,label,ha="left",va="center",fontsize=11.5,weight="bold",color=color)
    box(9.15,0.95,"動的指標 (PPV/SVV) 高値?",GOLD_D,GOLD_F,fs=13.5)
    arrow(9.15,8.35,"Yes",GREEN)
    box(7.55,0.95,"フルイドチャレンジ\n(例 250〜500 mL)",BLUE,BLUE_F)
    arrow(7.55,6.75)
    box(5.95,0.95,"SV ↑ ≧ 10〜15% ?",GOLD_D,GOLD_F,fs=13.5)
    arrow(5.95,4.55,"Yes：反応性",GREEN)
    box(3.65,0.95,"反応性 → 再評価ループへ",GREEN,GREEN_F,fs=12.5)
    # ループバック（反応性→再評価=動的指標の評価へ戻る）
    ax.annotate("",(bx-0.35,9.15+0.475),(bx-0.35,3.65+0.475),
                arrowprops=dict(arrowstyle="-|>",color=GREEN,lw=1.6,
                                connectionstyle="arc3,rad=0.35",mutation_scale=13))
    # No分岐（非反応）
    nx,ny,nw,nh=6.15,3.65,2.75,1.75
    ax.annotate("",(nx,5.95+0.475),(bx+bw,5.95+0.475),arrowprops=dict(arrowstyle="-|>",color=RED,lw=1.8,mutation_scale=15))
    ax.text((bx+bw+nx)/2,5.95+0.475+0.28,"No：非反応",ha="center",va="bottom",fontsize=11.5,weight="bold",color=RED)
    ax.add_patch(FancyBboxPatch((nx,ny),nw,nh,boxstyle="round,pad=0.02,rounding_size=0.10",
                                 fc=RED_F,ec=RED,lw=1.8,zorder=2))
    ax.text(nx+nw/2,ny+nh/2,"非反応\n輸液中止\n昇圧/強心を検討",ha="center",va="center",fontsize=12,
            weight="bold",color=RED,zorder=3,linespacing=1.5)
    # Ea_dyn 参考ボックス（右上）
    ex,ey,ew,eh=6.05,8.25,3.0,1.85
    ax.add_patch(FancyBboxPatch((ex,ey),ew,eh,boxstyle="round,pad=0.02,rounding_size=0.10",
                                 fc=TEAL_F,ec=TEAL,lw=1.8,zorder=2))
    ax.text(ex+ew/2,ey+eh-0.30,"Ea_dyn = PPV/SVV",ha="center",va="top",fontsize=13,weight="bold",
            color=TEAL,zorder=3)
    ax.text(ex+ew/2,ey+eh-0.78,"圧反応性の予測\n(昇圧薬か輸液かの\n判断補助)",ha="center",va="top",
            fontsize=11,color=INK,zorder=3,linespacing=1.5)
    ax.plot([bx+bw,ex],[9.15+0.475,ey+eh/2],color=TEAL,lw=1.2,ls=(0,(4,3)),zorder=1)
    _save(fig,path)

def fig_special_situations(path):
    """s8_3: 4枚のカード（CPB後乖離／厳密血圧管理／頻回採血／小児・特殊集団）— fig_valve_grid と
    同じ1行4カードの構成。"""
    fig,axs=plt.subplots(1,4,figsize=(13.4,3.6)); fig.patch.set_alpha(0)
    data=[("CPB後の橈骨-大腿乖離","一過性に橈骨<中枢(大腿)\n→大腿/上腕測定を考慮",TEAL),
          ("厳密血圧管理","脳動脈瘤・CEA・大血管手術\n拍動ごとの制御",GOLD_D),
          ("頻回採血","ABG・電解質・乳酸の\n連続モニタリングに有用",BLUE),
          ("小児・特殊集団","細径カテ・部位選択\n合併症配慮",GREEN)]
    for ax,(t,sub,c) in zip(axs,data):
        ax.patch.set_alpha(0)
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_xlim(0,1); ax.set_ylim(0,1)
        ax.add_patch(FancyBboxPatch((0.06,0.08),0.88,0.84,boxstyle="round,pad=0.02,rounding_size=0.06",
                                     fc="white",ec=c,lw=2.0,zorder=2,transform=ax.transAxes))
        ax.set_title(t,color=c,fontsize=14.5,weight="bold",pad=8)
        ax.text(0.5,0.42,sub,transform=ax.transAxes,ha="center",va="center",fontsize=12.5,color=INK,linespacing=1.5)
    fig.subplots_adjust(wspace=0.12,left=0.01,right=0.99,top=0.84,bottom=0.10)
    _save(fig,path)

ALL={
 "s2_2_transducer":fig_transducer,"s2_3_fnzeta":fig_fnzeta,"s2_4_flush":fig_flush,
 "s3_1_anatomy":fig_anatomy,"s3_2_decomp":fig_decomp,"s3_3_cenper":fig_central_peripheral,"s3_4_indices":fig_indices,
 "s4_1_normal":fig_normal,"s4_2_optflush":fig_optflush,
 "s5_1_events":fig_events,"s5_2_ppv":fig_ppv,"s5_3_spv":fig_spv,"s5_4_svr":fig_svr,
 "s6_1_overdamp":fig_overdamp,"s6_2_underdamp":fig_underdamp,"s6_3_paradoxus":fig_paradoxus_alternans,"s6_4_valve":fig_valve_grid,
 "s8_1_pulsecontour":fig_pulse_contour,
 "s1_1_timeline":fig_timeline_history,"s1_2_compare":fig_compare_invasive,"s2_1_chain":fig_measurement_chain,
 "s7_1_flow":fig_damping_flow,"s7_2_complications":fig_complications,
 "s8_2_gdt":fig_gdt_flow,"s8_3_special":fig_special_situations,
}
if __name__=="__main__":
    import os
    out="figs"; os.makedirs(out,exist_ok=True)
    for name,fn in ALL.items():
        fn(f"{out}/{name}.png"); print("ok",name)
    fig_hero(f"{out}/hero.png"); print("ok hero (decorative, cover only)")
    print("DONE",len(ALL)+1)
