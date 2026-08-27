#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《大学生睡眠时长现状及影响因素的横断面研究》统计分析脚本
数据: survey-server/survey-data/responses_github.csv 中 source=demo 的 160 条
输出: data/analysis_results.json(全部统计量) + 控制台三线表(中华流行病学杂志格式)

方法: 描述性统计、χ²检验、t检验(Levene方差齐性判断)/单因素方差分析、
      Pearson相关、多重线性回归(Enter,含哑变量、95%CI、VIF)、Cronbach's α
"""
import json
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "..", "survey-data", "responses_github.csv")
OUT = os.path.join(BASE, "data", "analysis_results.json")

df = pd.read_csv(SRC)
df = df[df["source"] == "demo"].copy()
N = len(df)
df["short"] = (df["Y"] < 7).astype(int)

# ---------- 反向题转换(信度分析用原始题) ----------
REV_ITEMS = {"D": ["D4", "D5"], "E": ["E4"], "G": ["G3", "G5"], "H": ["H5"]}
for it in [i for v in REV_ITEMS.values() for i in v]:
    df[it + "r"] = 6 - df[it]
DIM_ITEMS = {
    "学业负担": ["B1", "B2", "B3", "B4", "B5"],
    "睡前电子屏幕使用": ["C1", "C2", "C3", "C4", "C5"],
    "运动锻炼": ["D1", "D2", "D3", "D4r", "D5r"],
    "心理压力": ["E1", "E2", "E3", "E4r", "E5"],
    "咖啡因摄入": ["F1", "F2", "F3", "F4", "F5"],
    "作息规律性": ["G1", "G2", "G3r", "G4", "G5r"],
    "睡眠环境": ["H1", "H2", "H3", "H4", "H5r"],
}
DIM_X = {"学业负担": "X1", "睡前电子屏幕使用": "X2", "运动锻炼": "X3",
         "心理压力": "X4", "咖啡因摄入": "X5", "作息规律性": "X6", "睡眠环境": "X7"}

R = {"n": N}


def msd(s):
    return "%.2f±%.2f" % (s.mean(), s.std(ddof=1))


def chisq(col):
    """按卫生统计学惯例选择检验方法。

    2×2 表: n≥40 且所有理论频数 T≥5 -> 非校正 Pearson χ²
            n≥40 且有 1≤T<5        -> Fisher 确切概率法
            n<40 或 T<1            -> Fisher 确切概率法
    R×C 表: T<5 的格子占比<20% 且所有 T≥1 -> Pearson χ²
    返回 (统计量或None, P, 方法名, 最小理论频数, Yates校正值备查)
    """
    tab = pd.crosstab(df[col], df["short"])
    chi2, p, dof, exp = stats.chi2_contingency(tab, correction=False)
    tmin = exp.min()
    n = int(tab.values.sum())
    if tab.shape == (2, 2):
        chi2_y, p_y, _, _ = stats.chi2_contingency(tab, correction=True)
        yates = {"chi2": round(chi2_y, 3), "P": fmt_p(p_y)}
        if n >= 40 and tmin >= 5:
            return chi2, p, "χ²", tmin, yates
        _, p_f = stats.fisher_exact(tab)
        return None, p_f, "Fisher", tmin, yates
    small = (exp < 5).sum() / exp.size
    method = "χ²" if (small < 0.2 and tmin >= 1) else "χ²(需注意小理论频数)"
    return chi2, p, method, tmin, None


def fmt_p(p):
    return "<0.001" if p < 0.001 else "%.3f" % p


# ================= 表1 一般资料与睡眠不足检出率 =================
t1 = []
for col, label in [("A1", "性别"), ("A2", "年级"), ("A3", "专业类别"), ("A4", "住宿情况")]:
    rows = []
    for g, sub in df.groupby(col, sort=False):
        rows.append({"group": g, "n": len(sub), "pct": len(sub) / N * 100,
                     "short_n": int(sub["short"].sum()),
                     "short_pct": sub["short"].mean() * 100})
    chi2, p, method, tmin, yates = chisq(col)
    t1.append({"var": label, "rows": rows,
               "chi2": None if chi2 is None else round(chi2, 3),
               "P": fmt_p(p), "method": method,
               "T_min": round(tmin, 2), "yates_ref": yates})
R["table1"] = t1

# ================= 表2 睡眠时长分布 =================
t2 = {}
t2["I1"] = msd(df["I1"]); t2["I2"] = msd(df["I2"]); t2["Y"] = msd(df["Y"])
t2["Y_short"] = [int((df["Y"] < 7).sum()), (df["Y"] < 7).mean() * 100]
t2["Y_ok"] = [int(((df["Y"] >= 7) & (df["Y"] <= 9)).sum()), ((df["Y"] >= 7) & (df["Y"] <= 9)).mean() * 100]
t2["Y_long"] = [int((df["Y"] > 9).sum()), (df["Y"] > 9).mean() * 100]
t2["by_group"] = []
for col in ["A1", "A2", "A3", "A4"]:
    for g, sub in df.groupby(col, sort=False):
        t2["by_group"].append({
            "var": col, "group": g, "n": len(sub), "Y": msd(sub["Y"]),
            "short": [int((sub["Y"] < 7).sum()), (sub["Y"] < 7).mean() * 100],
            "ok": [int(((sub["Y"] >= 7) & (sub["Y"] <= 9)).sum()), ((sub["Y"] >= 7) & (sub["Y"] <= 9)).mean() * 100],
            "long": [int((sub["Y"] > 9).sum()), (sub["Y"] > 9).mean() * 100]})
R["table2"] = t2

# ================= 表3 信度与维度得分 =================
t3 = []
for dim, items in DIM_ITEMS.items():
    a = (len(items) / (len(items) - 1)) * (1 - df[items].var(ddof=1).sum() / df[items].sum(axis=1).var(ddof=1))
    xk = DIM_X[dim]
    t3.append({"dim": dim, "xk": xk, "k": len(items),
               "alpha": round(a, 3), "score": msd(df[xk])})
R["table3"] = t3

# ================= 表4 协变量与睡眠时长的比较 =================
t4 = []
for col, label in [("A1", "性别"), ("A3", "专业类别"), ("A4", "住宿情况")]:
    g1, g2 = df[df[col] == df[col].unique()[0]]["Y"], df[df[col] == df[col].unique()[1]]["Y"]
    lev = stats.levene(g1, g2).pvalue
    t = stats.ttest_ind(g1, g2, equal_var=(lev >= 0.05))
    t4.append({"var": label, "groups": [df[col].unique()[0], df[col].unique()[1]],
               "n": [len(g1), len(g2)], "Y": [msd(g1), msd(g2)],
               "stat": round(t.statistic, 3), "P": fmt_p(t.pvalue)})
g = [df[df["A2"] == gr]["Y"] for gr in ["大一", "大二", "大三", "大四", "大五"]]
f = stats.f_oneway(*g)
t4.append({"var": "年级", "groups": ["大一", "大二", "大三", "大四", "大五"],
           "n": [len(x) for x in g], "Y": [msd(x) for x in g],
           "stat": round(f.statistic, 3), "P": fmt_p(f.pvalue)})
R["table4"] = t4

# ================= 表5 相关分析 =================
t5 = []
for dim, xk in DIM_X.items():
    r_, p_ = stats.pearsonr(df[xk], df["Y"])
    t5.append({"dim": dim, "xk": xk, "r": round(r_, 3), "P": fmt_p(p_)})
R["table5"] = t5

# ================= 表6 多重线性回归 =================
Xcols, names = [], []
Xcols.append(np.ones(N)); names.append("常量")
Xcols.append((df["A1"] == "女").astype(float).values); names.append("性别(女)")
for gr in ["大二", "大三", "大四", "大五"]:
    Xcols.append((df["A2"] == gr).astype(float).values); names.append("年级(" + gr + ")")
Xcols.append((df["A3"] == "医学类").astype(float).values); names.append("专业类别(医学类)")
Xcols.append((df["A4"] == "住校").astype(float).values); names.append("住宿情况(住校)")
for dim, xk in DIM_X.items():
    Xcols.append(df[xk].values); names.append(xk + " " + dim)
X = np.column_stack(Xcols)
y = df["Y"].values
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
resid = y - X @ beta
dof = N - X.shape[1]
mse = resid @ resid / dof
cov = mse * np.linalg.inv(X.T @ X)
se = np.sqrt(np.diag(cov))
tvals = beta / se
pvals = [2 * stats.t.sf(abs(t), dof) for t in tvals]  # t 分布(df=N-k-1),与 SPSS 一致
tcrit = stats.t.ppf(0.975, dof)
ci = np.column_stack([beta - tcrit * se, beta + tcrit * se])
# 标准化 β 与 VIF
sd_y = y.std(ddof=1)
beta_std = beta * X.std(axis=0, ddof=1) / sd_y
vifs = []
for i in range(1, X.shape[1]):
    xi = X[:, i]
    oth = np.column_stack([X[:, j] for j in range(X.shape[1]) if j != i])
    b_, *_ = np.linalg.lstsq(oth, xi, rcond=None)
    r2i = 1 - ((xi - oth @ b_) ** 2).sum() / ((xi - xi.mean()) ** 2).sum()
    vifs.append(1 / (1 - r2i))
ss_res = resid @ resid
ss_tot = ((y - y.mean()) ** 2).sum()
r2 = 1 - ss_res / ss_tot
adj_r2 = 1 - (1 - r2) * (N - 1) / dof
f_stat = (ss_tot - ss_res) / (X.shape[1] - 1) / (ss_res / dof)
f_p = 1 - stats.f.cdf(f_stat, X.shape[1] - 1, dof)
t6 = []
for i, nm in enumerate(names):
    t6.append({"var": nm,
               "B": round(beta[i], 3), "SE": round(se[i], 3),
               "beta": round(beta_std[i], 3), "t": round(tvals[i], 3),
               "P": fmt_p(pvals[i]),
               "CI95": "[%.3f, %.3f]" % (ci[i, 0], ci[i, 1]),
               "VIF": None if i == 0 else round(vifs[i - 1], 3)})
R["table6"] = {"rows": t6, "F": round(f_stat, 3), "F_P": fmt_p(f_p),
               "R2": round(r2, 3), "adjR2": round(adj_r2, 3), "n": N, "k": X.shape[1] - 1}

os.makedirs(os.path.join(BASE, "data"), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=2)
print("分析完成,结果已保存:", OUT)
print("样本量 n =", N)

def print_table(title, header, rows):
    print("\n" + title)
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")

# ---- 打印各表 ----
for tb in t1:
    rows = [[g["group"], "%d(%.1f)" % (g["n"], g["pct"]), "%d(%.1f)" % (g["short_n"], g["short_pct"])] for g in tb["rows"]]
    stat_txt = "Fisher确切概率法" if tb["chi2"] is None else "χ²=%.3f" % tb["chi2"]
    print_table("表1 %s 与睡眠不足检出率 (%s, P=%s, T_min=%.2f)"
                % (tb["var"], stat_txt, tb["P"], tb["T_min"]),
                ["分组", "例数(%)", "睡眠不足例数(%)"], rows)

print_table("表2 睡眠时长分布 (Y=%.3f, 不足率=%.1f%%)" % (df["Y"].mean(), df["short"].mean() * 100),
            ["指标", "x̄±s 或 n(%)"],
            [["上课日", t2["I1"]], ["周末", t2["I2"]], ["加权日均", t2["Y"]],
             ["睡眠不足<7h", "%d(%.1f%%)" % tuple(t2["Y_short"])],
             ["睡眠充足7-9h", "%d(%.1f%%)" % tuple(t2["Y_ok"])],
             ["睡眠过量>9h", "%d(%.1f%%)" % tuple(t2["Y_long"])]])

print_table("表3 信度与得分", ["维度", "条目数", "Cronbach's α", "得分(x̄±s)"],
            [[t["dim"], t["k"], t["alpha"], t["score"]] for t in t3])

print_table("表4 协变量比较", ["变量", "分组", "n", "Y(x̄±s)", "t/F", "P"],
            [[tb["var"], "%s/%s" % (tb["groups"][0], tb["groups"][1]) if len(tb["groups"]) == 2 else "/".join(tb["groups"]),
              "%d/%d" % (tb["n"][0], tb["n"][1]) if len(tb["n"]) == 2 else "+".join(map(str, tb["n"])),
              "%s/%s" % (tb["Y"][0], tb["Y"][1]) if len(tb["Y"]) == 2 else "/".join(tb["Y"]),
              tb["stat"], tb["P"]] for tb in t4])

print_table("表5 相关分析", ["维度", "r", "P"], [[t["dim"], t["r"], t["P"]] for t in t5])

print_table("表6 多重线性回归 (F=%.3f, P=%s, 调整R²=%.3f)" % (t6[0]["B"] and R["table6"]["F"], R["table6"]["F_P"], R["table6"]["adjR2"]),
            ["变量", "B", "SE", "β", "t", "P", "95%CI", "VIF"],
            [[t["var"], t["B"], t["SE"], t["beta"], t["t"], t["P"], t["CI95"], t["VIF"]] for t in t6])
