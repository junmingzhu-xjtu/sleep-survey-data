#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《大学生睡眠时长现状及影响因素的横断面研究》候选插图

生成 3 张备选图(PNG 300dpi + PDF 矢量), 供选用:
  图1  睡眠时长分布(直方图 + 上课日/周末对比)      -> 可替代或补充 表2
  图2  多重线性回归森林图(B 值 + 95%CI)            -> 可替代 表6, 信息量最大
  图3  各维度相关性 + 不同特征睡眠不足检出率        -> 可替代 表5 / 表1

运行: python make_figures.py     输出目录: figures/
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(BASE, "figures")
os.makedirs(OUTDIR, exist_ok=True)

# ---------- 期刊风格 ----------
plt.rcParams.update({
    "font.family": "sans-serif",
    # 宋体须排在首位: matplotlib 在本机不做逐字回退, Times 在前会导致中文变成方框。
    # SimSun 自带西文字形(衬线), 与中文期刊插图惯例一致。
    "font.sans-serif": ["SimSun", "Times New Roman"],
    "axes.unicode_minus": False,
    "font.size": 9,
    "axes.labelsize": 9.5,
    "axes.titlesize": 10,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "axes.linewidth": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})

CM = 1 / 2.54
# 色盲友好配色(Okabe-Ito 衍生)
C_RISK = "#C1553B"   # 危险因素 砖红
C_PROT = "#2E7D8F"   # 保护因素 青蓝
C_NEUT = "#9AA0A6"   # 无统计学意义 灰
C_BAR = "#5B7DB1"    # 主色 蓝
C_ACC = "#D9A441"    # 强调 金

df = pd.read_csv(os.path.join(BASE, "..", "survey-data", "responses_github.csv"))
df = df[df["source"] == "demo"].copy()
N = len(df)

with open(os.path.join(BASE, "data", "analysis_results.json"), encoding="utf-8") as f:
    R = json.load(f)


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUTDIR, f"{name}.{ext}"))
    plt.close(fig)
    print("  已生成:", name + ".png / .pdf")


# ============================================================
# 图1  睡眠时长分布
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17.5 * CM, 7.2 * CM),
                               gridspec_kw={"width_ratios": [1.45, 1]})

y = df["Y"].values
bins = np.arange(4.75, 11.26, 0.5)
counts, edges = np.histogram(y, bins=bins)
centers = (edges[:-1] + edges[1:]) / 2
colors = [C_RISK if c < 7 else (C_ACC if c > 9 else C_PROT) for c in centers]
ax1.bar(centers, counts, width=0.46, color=colors, edgecolor="white", linewidth=0.6)

for v in (7, 9):
    ax1.axvline(v, color="0.25", ls="--", lw=0.9, zorder=0)
ax1.text(7, ax1.get_ylim()[1] * 0.97, " 7 h", ha="left", va="top", fontsize=8, color="0.25")
ax1.text(9, ax1.get_ylim()[1] * 0.97, " 9 h", ha="left", va="top", fontsize=8, color="0.25")

ax1.set_xlabel("加权日均睡眠时长 (h)")
ax1.set_ylabel("人数")
ax1.set_xlim(4.6, 11.4)
ax1.set_title("A  睡眠时长分布 (n=160)", loc="left", fontfamily="SimHei")

handles = [plt.Rectangle((0, 0), 1, 1, fc=c) for c in (C_RISK, C_PROT, C_ACC)]
labels = ["睡眠不足 <7 h (29.4%)", "睡眠充足 7~9 h (67.5%)", "睡眠过量 >9 h (3.1%)"]
ax1.legend(handles, labels, frameon=False, loc="upper left", handlelength=1.1,
           borderaxespad=0.3, labelspacing=0.35)

# --- B 上课日 vs 周末 vs 加权 ---
data = [df["I1"].values, df["I2"].values, df["Y"].values]
names = ["上课日", "周末", "加权日均"]
bp = ax2.boxplot(data, widths=0.55, patch_artist=True, showfliers=False,
                 medianprops=dict(color="black", lw=1.1),
                 whiskerprops=dict(lw=0.8), capprops=dict(lw=0.8),
                 boxprops=dict(lw=0.8))
for patch, c in zip(bp["boxes"], [C_BAR, C_ACC, C_PROT]):
    patch.set_facecolor(c)
    patch.set_alpha(0.55)

rng = np.random.default_rng(20260826)
for i, d in enumerate(data, start=1):
    ax2.scatter(rng.normal(i, 0.055, len(d)), d, s=3.5, color="0.30",
                alpha=0.30, linewidths=0, zorder=3)
for i, d in enumerate(data, start=1):
    ax2.scatter(i, d.mean(), marker="D", s=22, color="white",
                edgecolor="black", linewidth=0.9, zorder=5)
    ax2.text(i + 0.30, d.mean(), f"{d.mean():.2f}", va="center", fontsize=8)

ax2.axhline(7, color="0.25", ls="--", lw=0.9, zorder=0)
ax2.set_xticks([1, 2, 3])
ax2.set_xticklabels(names)
ax2.set_ylabel("睡眠时长 (h)")
ax2.set_title("B  上课日与周末比较", loc="left", fontfamily="SimHei")
ax2.set_ylim(4.4, 11.6)

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout(w_pad=2.0)
save(fig, "图1_睡眠时长分布")


# ============================================================
# 图2  多重线性回归森林图
# ============================================================
rows = [r for r in R["table6"]["rows"] if r["var"] != "常量"]
for r in rows:
    lo, hi = r["CI95"].strip("[]").split(",")
    r["lo"], r["hi"] = float(lo), float(hi)
    r["sig"] = r["P"] == "<0.001" or float(r["P"]) < 0.05
    r["label"] = r["var"].split(" ")[-1] if r["var"].startswith("X") else r["var"]

rows.sort(key=lambda r: r["beta"])          # 由负到正, 画出来保护因素在上
ypos = np.arange(len(rows))

fig, ax = plt.subplots(figsize=(16 * CM, 12 * CM))
ax.axvline(0, color="0.35", lw=1.0, zorder=1)

for i, r in enumerate(rows):
    if not r["sig"]:
        c = C_NEUT
    else:
        c = C_PROT if r["B"] > 0 else C_RISK
    ax.plot([r["lo"], r["hi"]], [i, i], color=c, lw=1.6, solid_capstyle="round", zorder=2)
    ax.scatter(r["B"], i, s=34, color=c, zorder=3, edgecolor="white", linewidth=0.7)

ax.set_yticks(ypos)
ax.set_yticklabels([r["label"] for r in rows])
ax.set_ylim(-0.8, len(rows) - 0.2)
ax.set_xlabel("偏回归系数 B 及其 95%CI (h)")
ax.set_title("大学生睡眠时长影响因素的多重线性回归 (Enter 法, n=160)",
             loc="left", fontfamily="SimHei", pad=10)

# 右侧数值列
xr = ax.get_xlim()[1]
span = ax.get_xlim()[1] - ax.get_xlim()[0]
ax.text(xr + span * 0.06, len(rows) - 0.2, "β′", ha="center", va="bottom",
        fontsize=8.5, fontfamily="SimHei")
ax.text(xr + span * 0.22, len(rows) - 0.2, "P 值", ha="center", va="bottom",
        fontsize=8.5, fontfamily="SimHei")
for i, r in enumerate(rows):
    w = "SimHei" if r["sig"] else "SimSun"
    ax.text(xr + span * 0.06, i, f"{r['beta']:.3f}", ha="center", va="center",
            fontsize=8, fontfamily=w)
    ax.text(xr + span * 0.22, i, r["P"], ha="center", va="center",
            fontsize=8, fontfamily=w)
ax.set_xlim(ax.get_xlim()[0], xr + span * 0.30)
ax.spines[["top", "right"]].set_visible(False)

handles = [plt.Line2D([], [], color=c, lw=1.6, marker="o", ms=5.5, mec="white")
           for c in (C_PROT, C_RISK, C_NEUT)]
ax.legend(handles, ["保护因素 (P<0.05)", "危险因素 (P<0.05)", "无统计学意义"],
          frameon=False, loc="lower right", handlelength=1.5, labelspacing=0.35)

note = f"模型 F=18.896, P<0.001, 调整 R²={R['table6']['adjR2']:.3f}; 各变量 VIF<2"
fig.text(0.01, -0.005, "注：" + note, fontsize=8, color="0.3")
fig.tight_layout()
save(fig, "图2_回归森林图")


# ============================================================
# 图3  相关性 + 检出率
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17.5 * CM, 7.6 * CM),
                               gridspec_kw={"width_ratios": [1.15, 1]})

t5 = sorted(R["table5"], key=lambda d: d["r"])
labs = [f"{d['dim']}" for d in t5]
rv = [d["r"] for d in t5]
cols = [C_PROT if v > 0 else C_RISK for v in rv]
ax1.barh(np.arange(len(rv)), rv, color=cols, height=0.62,
         edgecolor="white", linewidth=0.6)
ax1.axvline(0, color="0.35", lw=1.0)
ax1.set_yticks(np.arange(len(rv)))
ax1.set_yticklabels(labs)
ax1.set_xlabel("Pearson 相关系数 r")
ax1.set_xlim(-0.52, 0.52)
ax1.set_title("A  各维度得分与睡眠时长的相关性", loc="left", fontfamily="SimHei")
for i, v in enumerate(rv):
    off = 0.02 if v > 0 else -0.02
    ax1.text(v + off, i, f"{v:.3f}", va="center",
             ha="left" if v > 0 else "right", fontsize=8)

# --- B 检出率 ---
groups, rates, sig_marks = [], [], []
order = {"性别": ["男", "女"], "年级": ["大一", "大二", "大三", "大四", "大五"],
         "专业类别": ["医学类", "非医学类"], "住宿情况": ["住校", "走读"]}
pmap = {t["var"]: t["P"] for t in R["table1"]}
seps, xt, blockc = [], 0, []
for var in ["性别", "年级", "专业类别", "住宿情况"]:
    tb = next(t for t in R["table1"] if t["var"] == var)
    lookup = {r["group"]: r for r in tb["rows"]}
    start = xt
    for g in order[var]:
        groups.append(g)
        rates.append(lookup[g]["short_pct"])
        xt += 1
    blockc.append((start + xt - 1) / 2)
    seps.append(xt - 0.5)
    p = pmap[var]
    sig_marks.append("*" if (p != "<0.001" and float(p) < 0.05) else ("ns" if p != "<0.001" else "*"))

bars = ax2.bar(np.arange(len(rates)), rates, color=C_BAR, width=0.68,
               edgecolor="white", linewidth=0.6)
for b, v in zip(bars, rates):
    ax2.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f}",
             ha="center", fontsize=7.5)
ax2.axhline(29.4, color=C_ACC, ls="--", lw=1.0, zorder=0)
ax2.text(len(rates) - 0.4, 30.6, "总体 29.4%", ha="right", fontsize=7.5, color="#9C7526")

for s in seps[:-1]:
    ax2.axvline(s, color="0.85", lw=0.8, zorder=0)
ax2.set_xticks(np.arange(len(groups)))
ax2.set_xticklabels(groups, fontsize=7.8)
ax2.set_ylabel("睡眠不足检出率 (%)")
ax2.set_ylim(0, 56)
ax2.set_title("B  不同特征学生睡眠不足检出率", loc="left", fontfamily="SimHei")

for c, var, m in zip(blockc, ["性别", "年级", "专业类别", "住宿情况"], sig_marks):
    ax2.text(c, 51.5, f"{var} {m}", ha="center", fontsize=7.8,
             fontfamily="SimHei" if m == "*" else "SimSun",
             color="black" if m == "*" else "0.45")

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)
fig.text(0.01, -0.02, "注：* P<0.05；ns 差异无统计学意义。专业类别 χ²=4.334, P=0.037；"
                      "住宿情况 Fisher 确切概率法 P=0.024", fontsize=7.6, color="0.3")
fig.tight_layout(w_pad=2.0)
save(fig, "图3_相关性与检出率")

print("\n全部完成, 输出目录:", OUTDIR)
