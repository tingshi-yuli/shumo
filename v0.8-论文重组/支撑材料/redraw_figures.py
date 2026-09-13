"""Redraw the paper's 13 figures from the continuation workspace, without solving.

From A题work:
    python v0.6-论文修订/redraw_figures.py
Optional relocated input tree:
    python v0.6-论文修订/redraw_figures.py --source-dir PATH/改进模型

Read-only dependencies beneath --source-dir:
  make_figures.py, p2_report.py, model.py;
  runs/{q1_final,q2_full,q4_final}.json.gz;
  p2/runs/q{3,4}_h*_hm*.json (the 18 scan cases in p2_report.EXPECTED).
The sibling 附件 directory must contain 附件1.xlsx and 附件2.xlsx.
Python dependencies: numpy, scipy, openpyxl, matplotlib; installed Chinese font.
Skill helpers in 绘图工具 are unmodified copies of math-modeling/tools/figure/scripts.

Each existing stem receives PDF, editable-text SVG and 600-DPI PNG at 15 cm width.
The frozen solver, inputs and numeric outputs are never written or recomputed.
No p2_report.main(), Solver.run(), workbook generation, or original figure save
routine is called. Q3 uses the q2_full cache, exactly as make_figures.py does.

Figure contracts: raw figures describe observed environmental/radius inputs;
process figures describe the frozen time histories; result figures use the same
sample() interpolation and physical-distance grid as make_figures.py. Q4's
out-of-domain samples remain missing. The heatmap uses actual final times and
status fields, one common color scale, and explicit right-censoring if present.
"""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import json
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle
from matplotlib.ticker import LogFormatterMathtext, LogLocator, NullFormatter

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT.parent / "数模项目_续接" / "工作区" / "改进模型"
PALETTE = ("#5B758C", "#B18B72", "#82988A", "#555D66")
BLUE, ORANGE, GREEN, CHARCOAL = PALETTE
WIDTH = 15.0 / 2.54
STEMS = (
    "raw_q1_environment", "raw_q2_environment_relation", "raw_q3_radius",
    "raw_q4_shrinkage", "process_q1_temperature", "process_q2_moisture",
    "process_q3_wet_fraction", "process_q4_shrinkage_moisture",
    "result_q1_profile", "result_q2_profile", "result_q3_endpoint",
    "result_q4_endpoint", "p2_boundary_sensitivity",
)


def configure_style():
    sys.path.insert(0, str(ROOT / "绘图工具"))
    from setup_style import setup_style
    from export_figure import export_figure

    info = setup_style(journal="general", lang="zh", use_sciplots=False)
    available = {font.name for font in font_manager.fontManager.ttflist}
    chinese_font = next((name for name in ("Microsoft YaHei", "SimSun")
                         if name in available), info["cjk_font"])
    plt.rcParams.update({
        "font.family": "sans-serif",
        # Normal text must select a CJK font directly; family-list glyph fallback
        # is not available in every Matplotlib exporter. Math stays independent.
        "font.sans-serif": [chinese_font],
        "mathtext.fontset": "dejavusans",
        "axes.unicode_minus": False,
        "text.usetex": False,
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "axes.titlepad": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "legend.frameon": False,
        "axes.labelcolor": CHARCOAL,
        "axes.edgecolor": CHARCOAL,
        "text.color": CHARCOAL,
        "xtick.color": CHARCOAL,
        "ytick.color": CHARCOAL,
        "axes.linewidth": 0.65,
        "lines.linewidth": 1.5,
        "lines.markersize": 3.5,
        "axes.prop_cycle": cycler(color=PALETTE) + cycler(linestyle=("-", "--", "-.", ":")),
        "grid.color": CHARCOAL,
        "grid.alpha": 0.12,
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    return export_figure


def canvas(panels=1, height_cm=8.4, sharex=False):
    fig, axes = plt.subplots(1, panels, figsize=(WIDTH, height_cm / 2.54),
                             sharex=sharex, layout="constrained", squeeze=False)
    for ax in axes.flat:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y")
        ax.margins(x=0.02)
    return fig, axes[0]


def line(ax, x, y, label, color=BLUE, linestyle="-", marker=None):
    return ax.plot(x, y, label=label, color=color, linestyle=linestyle,
                   marker=marker, markevery=max(1, len(x) // 12),
                   markerfacecolor="white", markeredgewidth=0.8)[0]


def log_moisture_axis(ax):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10))
    # Explicit math font ensures 10^{-1}, etc. retain their minus signs.
    ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=(2, 5)))
    ax.yaxis.set_minor_formatter(NullFormatter())


def load_scan(source, expected):
    """Use p2_report's case contract, never its hard-coded BASE endpoint values."""
    scans = {3: {}, 4: {}}
    for name in expected:
        if "_hm" not in name:
            continue
        path = source / "p2" / "runs" / f"{name}.json"
        run = json.loads(path.read_text(encoding="utf-8"))
        question = int(name[1])
        signature = run["signature"]
        factors = (float(signature["h_factor"]), float(signature["hm_factor"]))
        if run["status"] not in ("endpoint_reached", "right_censored"):
            raise ValueError(f"No usable endpoint evidence: {path}")
        scans[question][factors] = (float(run["final"]["t"]) / 3600, run["status"])
    return scans


def draw_inputs(inputs, save):
    air, radii = inputs.air, inputs.radii
    times = air[:, 0] / 3600
    fig, axes = canvas(2, height_cm=8.0, sharex=True)
    line(axes[0], times, air[:, 1], "温度观测", BLUE)
    line(axes[1], times, air[:, 2], "浓度观测", GREEN, "-.")
    axes[0].set(xlabel="时间 / h", ylabel="烘房温度 / °C", title="(a) 环境温度")
    axes[1].set(xlabel="时间 / h", ylabel="有效水分浓度 / (kg/kg)", title="(b) 环境水分")
    for ax in axes:
        ax.legend(loc="best")
    save(fig, "raw_q1_environment")

    fig, (ax,) = canvas()
    ax.plot(air[:, 1], air[:, 2], color=BLUE, linewidth=0.9,
            label="时间顺序连线", zorder=1)
    ax.scatter(air[:, 1], air[:, 2], s=10, color=ORANGE,
               linewidths=0, label="附件1观测", zorder=2)
    ax.set(xlabel="烘房温度 / °C", ylabel="有效水分浓度 / (kg/kg)", title="环境状态关系")
    ax.legend(loc="best")
    save(fig, "raw_q2_environment_relation")

    times = radii[:, 0] / 3600
    fig, (ax,) = canvas()
    line(ax, times, radii[:, 1], "分段线性插值", BLUE, "--")
    ax.scatter(times, radii[:, 1], s=18, color=ORANGE, marker="o",
               label="附件2观测", zorder=3)
    ax.set(xlabel="时间 / h", ylabel="半径 / cm", title="半径观测与插值")
    ax.legend(loc="best")
    save(fig, "raw_q3_radius")

    ratio = radii[:, 1] / radii[0, 1]
    fig, axes = canvas(2, height_cm=8.0, sharex=True)
    line(axes[0], times, ratio, "半径比", ORANGE, "--", "o")
    line(axes[1], times, ratio ** 2, "截面积比", GREEN, "-.", "s")
    axes[0].set(xlabel="时间 / h", ylabel=r"$R(t)/R(0)$（无量纲）", title="(a) 相对半径", ylim=(0, 1.05))
    axes[1].set(xlabel="时间 / h", ylabel=r"$[R(t)/R(0)]^2$（无量纲）", title="(b) 相对截面积", ylim=(0, 1.05))
    for ax in axes:
        ax.legend(loc="best")
    save(fig, "raw_q4_shrinkage")


def draw_processes(q1, q2, q4, save):
    history = q1["long"]
    times = np.asarray([s["t"] for s in history]) / 3600
    fig, (ax,) = canvas()
    line(ax, times, [s["T"][0] for s in history], "中心", BLUE, "-", "o")
    line(ax, times, [s["T"][-1] for s in history], "表面", ORANGE, "--", "s")
    ax.set(xlabel="时间 / h", ylabel="温度 / °C", title="预热温度响应")
    ax.legend(loc="best")
    save(fig, "process_q1_temperature")

    history = q2["long"]
    times = np.asarray([s["t"] for s in history]) / 3600
    fig, (ax,) = canvas()
    line(ax, times, [s["C"][0] for s in history], "中心", BLUE, "-", "o")
    line(ax, times, [s["C"][-1] for s in history], "表面", ORANGE, "--", "s")
    log_moisture_axis(ax)
    ax.set(xlabel="时间 / h", ylabel="干基含水率 / (kg/kg，对数轴)", title="固定半径失水过程")
    ax.legend(loc="best")
    save(fig, "process_q2_moisture")

    fig, (ax,) = canvas()
    line(ax, times, [100 * s["wet_fraction"] for s in history], "未达标截面积", GREEN, "-.")
    ax.set(xlabel="时间 / h", ylabel="未达标截面积比例 / %", title="未达标核心变化", ylim=(0, 103))
    ax.legend(loc="best")
    save(fig, "process_q3_wet_fraction")

    history = q4["long"]
    times = np.asarray([s["t"] for s in history]) / 3600
    fig, axes = canvas(2, height_cm=8.0, sharex=True)
    line(axes[0], times, [s["radius_cm"] for s in history], "收缩半径", ORANGE, "--")
    line(axes[1], times, [s["C"][0] for s in history], "中心含水率", BLUE, "-")
    axes[0].set(xlabel="时间 / h", ylabel="半径 / cm", title="(a) 收缩几何")
    axes[1].set(xlabel="时间 / h", ylabel="干基含水率 / (kg/kg)", title="(b) 中心失水")
    for ax in axes:
        ax.legend(loc="best")
    save(fig, "process_q4_shrinkage_moisture")


def draw_profiles(q1, q2, q4, sample, save):
    # Match the inherited physical sampling grid, including missing Q4 samples.
    distances = np.arange(0, 2.001, 0.1)
    cases = (
        ("result_q1_profile", q1["summaries"]["1800"], "T", "预热末端温度", "温度 / °C", BLUE, "1800 s", False),
        ("result_q2_profile", q2["summaries"]["10800"], "C", "3 h 含水率剖面", "干基含水率 / (kg/kg)", GREEN, "3 h", False),
        ("result_q3_endpoint", q2["final"], "C", "固定半径终点剖面", "干基含水率 / (kg/kg)", BLUE, "首次达标", True),
        ("result_q4_endpoint", q4["final"], "C", "收缩终点剖面", "干基含水率 / (kg/kg)", ORANGE, "有效域采样", True),
    )
    for stem, snapshot, field, title, ylabel, color, label, endpoint in cases:
        values = np.asarray(sample(snapshot, field, distances), dtype=float)
        fig, (ax,) = canvas()
        line(ax, distances, values, label, color, "-", "o")
        if endpoint:
            ax.axhline(0.15, color=CHARCOAL, linestyle="--", linewidth=1.0,
                       label="达标阈值 0.15 kg/kg")
        if stem == "result_q4_endpoint":
            radius = snapshot["radius_cm"]
            # Blank outer domain is not interpreted as zero moisture or extrapolated.
            ax.axvline(radius, color=GREEN, linestyle=":", linewidth=1.1,
                       label=f"当前表面 {radius:g} cm")
            ax.set_xlim(0, distances[-1])
            ax.text((radius + distances[-1]) / 2, 0.35, "材料域外\n不外推", ha="center",
                    va="center", transform=ax.get_xaxis_transform(), fontsize=8)
        ax.set(xlabel="到中心的物理距离 / cm", ylabel=ylabel, title=title)
        ax.legend(loc="best")
        save(fig, stem)


def draw_sensitivity(scans, save):
    # Shared normalization makes equal color mean equal drying time in both panels.
    completed = [value for scan in scans.values() for value, status in scan.values()
                 if status == "endpoint_reached"]
    if not completed:
        raise ValueError("No completed P2 scan endpoints are available for a time heatmap")
    norm = Normalize(vmin=min(completed), vmax=max(completed))
    cmap = LinearSegmentedColormap.from_list("paper_blue", ["#F5F6F7", BLUE])
    fig, axes = canvas(2, height_cm=8.6)
    any_censored = False
    for ax, question in zip(axes, (3, 4)):
        scan = scans[question]
        heat_factors = sorted({h for h, _ in scan})
        mass_factors = sorted({m for _, m in scan})
        values = np.asarray([[scan[h, m][0] for m in mass_factors] for h in heat_factors])
        censored = np.asarray([[scan[h, m][1] == "right_censored" for m in mass_factors]
                               for h in heat_factors])
        any_censored |= bool(censored.any())
        # pcolormesh stays vector-based in SVG/PDF, unlike imshow.
        mesh = ax.pcolormesh(np.ma.masked_where(censored, values), cmap=cmap, norm=norm,
                             edgecolors="white", linewidth=1.2, shading="flat", rasterized=False)
        ax.set(xticks=np.arange(len(mass_factors)) + 0.5,
               xticklabels=[f"{v:g}" for v in mass_factors],
               yticks=np.arange(len(heat_factors)) + 0.5,
               yticklabels=[f"{v:g}" for v in heat_factors],
               xlabel=r"$h_m/h_{m0}$（无量纲）", ylabel=r"$h/h_0$（无量纲）",
               title=f"({'a' if question == 3 else 'b'}) 问题{question}")
        ax.invert_yaxis()
        ax.set_aspect("equal")
        ax.grid(False)
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for i in range(len(heat_factors)):
            for j in range(len(mass_factors)):
                value = values[i, j]
                if censored[i, j]:
                    ax.add_patch(Rectangle((j, i), 1, 1, facecolor="#F5F6F7",
                                           edgecolor=CHARCOAL, hatch="///", linewidth=0.5))
                text = (">" if censored[i, j] else "") + f"{value:.3f}"
                color = "white" if not censored[i, j] and norm(value) > 0.65 else CHARCOAL
                ax.text(j + 0.5, i + 0.5, text, ha="center", va="center", fontsize=8, color=color)
    colorbar = fig.colorbar(mesh, ax=list(axes), orientation="horizontal", fraction=0.085, pad=0.08, shrink=0.8)
    colorbar.set_label("首次全域达标时间 / h" if not any_censored else "首次全域达标时间 / h（斜线及 > 表示右删失下界）")
    save(fig, "p2_boundary_sensitivity")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    output = ROOT / "论文" / "figs"
    # Imports must not create __pycache__ files in the read-only continuation tree.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    original = importlib.import_module("make_figures")
    report = importlib.import_module("p2_report")
    model = importlib.import_module("model")
    export = configure_style()
    scans = load_scan(source, report.EXPECTED)
    inputs = model.Inputs()
    runs = []
    for name in ("q1_final", "q2_full", "q4_final"):
        cached = original.load(name)
        # The potentially huge per-second short output is not used for drawing.
        runs.append({key: cached[key] for key in ("long", "summaries", "final")})
        del cached
    written = []

    def save(fig, stem):
        if stem not in STEMS:
            raise ValueError(f"Unknown paper figure stem: {stem}")
        export(fig, basename=str(output / stem), formats=("pdf", "svg", "png"),
               size_inches=tuple(fig.get_size_inches()), dpi=600,
               tight=False, grayscale_preview=False)
        plt.close(fig)
        written.append(stem)

    draw_inputs(inputs, save)
    draw_processes(*runs, save)
    draw_profiles(*runs, model.sample, save)
    draw_sensitivity(scans, save)
    print(f"Source: {source}")
    print(f"Output: {output}")
    print(f"Exported {len(written)} figure stems in PDF/SVG/600-DPI PNG; width = 15 cm.")


if __name__ == "__main__":
    main()
