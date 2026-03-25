"""
MoEFCC Themes Over Years — Charts with Historical Event Annotations
====================================================================
Run after: python moefcc_nlp_pipeline.py --step dataset

Usage:
    python themes_over_years.py --mode all
    python themes_over_years.py --mode line
    python themes_over_years.py --mode stacked
    python themes_over_years.py --mode pct
    python themes_over_years.py --mode events
    python themes_over_years.py --mode dashboard
"""

import argparse, pathlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec

THEME_COLORS = {
    "water_conservation":     "#185FA5",
    "biodiversity":           "#0F6E56",
    "soil_health":            "#BA7517",
    "climate_adaptation":     "#534AB7",
    "eco_friendly_practices": "#C0392B",
}
THEME_LABELS = {
    "water_conservation":     "Water conservation",
    "biodiversity":           "Biodiversity",
    "soil_health":            "Soil health",
    "climate_adaptation":     "Climate adaptation",
    "eco_friendly_practices": "Eco-friendly practices",
}
THEMES = list(THEME_COLORS.keys())

# Historical events with the theme they most impacted
EVENTS = {
    2009: ("Copenhagen\nSummit",       "climate_adaptation"),
    2012: ("Rio+20\nEarth Summit",     "eco_friendly_practices"),
    2015: ("Paris\nAgreement",         "climate_adaptation"),
    2019: ("Jal Jeevan\nMission",      "water_conservation"),
    2020: ("COVID-19\nPandemic",        None),
    2021: ("COP26\nGlasgow",           "climate_adaptation"),
    2022: ("LiFE\nMission",            "eco_friendly_practices"),
    2023: ("India G20\nPresidency",    "eco_friendly_practices"),
}

EVENT_DESC = {
    2009: "Copenhagen Climate Summit — India commits to 20-25% emission reduction by 2020",
    2012: "Rio+20 Earth Summit — Green Economy & Sustainable Development Goals framework",
    2015: "Paris Agreement — India pledges 33% emission intensity cut; 175 GW renewables",
    2019: "Jal Jeevan Mission — Rs 3.6 lakh crore to provide tap water to every rural home",
    2020: "COVID-19 Pandemic — Industrial slowdown; cleaner rivers/air; wildlife recovery",
    2021: "COP26 Glasgow — India: Net Zero 2070; 500 GW renewables by 2030 (Panchamrit)",
    2022: "LiFE Mission launched — Lifestyle for Environment; circular economy push at COP27",
    2023: "India G20 Presidency — Green Development Pact; Global Biofuel Alliance formed",
}


def load_pivot(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["year"] = df["report_year"].astype(str).str.extract(r"(\d{4})")[0].astype(int)
    pivot = df.groupby(["year","theme"]).size().unstack(fill_value=0)
    for t in THEMES:
        if t not in pivot.columns: pivot[t] = 0
    pivot = pivot[THEMES].sort_index()
    # Fill every year with interpolation (no gaps in charts)
    full = pd.RangeIndex(pivot.index.min(), pivot.index.max()+1)
    pivot = pivot.reindex(full)
    real = int(pivot[THEMES[0]].notna().sum())
    pivot[THEMES] = pivot[THEMES].interpolate(method="linear").clip(lower=0).round(0).astype(int)
    print(f"  Years with real data: {real} | Interpolated: {len(pivot)-real} | Total range: {len(pivot)}")
    return pivot


def _style(ax, title="", xlabel="Year", ylabel="Sentences"):
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8, loc="left")
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # ✅ FIX: remove .5 values on x-axis
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", alpha=0.2, linewidth=1)


def plot_line(pivot, ax=None, save=None):
    solo = ax is None
    if solo: fig, ax = plt.subplots(figsize=(13,6))
    for t in THEMES:
        ax.plot(pivot.index, pivot[t], label=THEME_LABELS[t],
                color=THEME_COLORS[t], linewidth=2.2, marker="o", markersize=3)
    _style(ax, "Sustainability theme sentences over time", ylabel="Sentences per report")
    ax.legend(fontsize=8, framealpha=0.3, loc="upper left")
    if solo:
        plt.tight_layout()
        if save: plt.savefig(save, dpi=150, bbox_inches="tight"); print(f"  Saved: {save}")
        plt.show(); plt.close()


def plot_stacked(pivot, ax=None, save=None):
    solo = ax is None
    if solo: fig, ax = plt.subplots(figsize=(13,6))
    x = np.arange(len(pivot))
    bottom = np.zeros(len(pivot))
    for t in THEMES:
        ax.bar(x, pivot[t], 0.72, bottom=bottom, label=THEME_LABELS[t],
               color=THEME_COLORS[t], alpha=0.88)
        bottom += pivot[t].values
    ax.set_xticks(x); ax.set_xticklabels(pivot.index, rotation=45, ha="right", fontsize=7)
    _style(ax, "Total sentences per report (stacked)")
    ax.legend(fontsize=8, framealpha=0.3, loc="upper left")
    if solo:
        plt.tight_layout()
        if save: plt.savefig(save, dpi=150, bbox_inches="tight"); print(f"  Saved: {save}")
        plt.show(); plt.close()


def plot_pct(pivot, ax=None, save=None):
    solo = ax is None
    if solo: fig, ax = plt.subplots(figsize=(13,6))
    totals = pivot.sum(axis=1)
    pct = pivot.div(totals, axis=0)*100
    x = np.arange(len(pct))
    bottom = np.zeros(len(pct))
    for t in THEMES:
        ax.bar(x, pct[t], 0.72, bottom=bottom, label=THEME_LABELS[t],
               color=THEME_COLORS[t], alpha=0.88)
        for i,(v,b) in enumerate(zip(pct[t].values, bottom)):
            if v > 9:
                ax.text(x[i], b+v/2, f"{v:.0f}%", ha="center", va="center",
                        fontsize=6, color="white", fontweight="bold")
        bottom += pct[t].values
    ax.set_xticks(x); ax.set_xticklabels(pct.index, rotation=45, ha="right", fontsize=7)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter()); ax.set_ylim(0,100)
    _style(ax, "Theme share (%) per year", ylabel="Share (%)")
    ax.legend(fontsize=8, framealpha=0.3, loc="upper right")
    if solo:
        plt.tight_layout()
        if save: plt.savefig(save, dpi=150, bbox_inches="tight"); print(f"  Saved: {save}")
        plt.show(); plt.close()


def plot_events(pivot, ax=None, save=None):
    """Line chart annotated with key historical events."""
    solo = ax is None
    if solo: fig, ax = plt.subplots(figsize=(15,7))
    for t in THEMES:
        ax.plot(pivot.index, pivot[t], label=THEME_LABELS[t],
                color=THEME_COLORS[t], linewidth=2.2, marker="o", markersize=3, zorder=3)
    ymax = int(pivot.values.max())
    used_y: list = []
    for yr, (label, theme) in sorted(EVENTS.items()):
        if yr < pivot.index.min() or yr > pivot.index.max(): continue
        color = THEME_COLORS.get(theme, "#666666") if theme else "#666666"
        ax.axvline(x=yr, color=color, linestyle="--", linewidth=1.0, alpha=0.55, zorder=2)
        y_pos = ymax * 0.92
        for _ in range(10):
            if not any(abs(y_pos - y) < ymax*0.14 for y in used_y): break
            y_pos -= ymax * 0.13
        used_y.append(y_pos)
        ax.annotate(label, xy=(yr, 0), xytext=(yr+0.15, y_pos), fontsize=7,
                    color=color, fontweight="bold", zorder=4,
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                              edgecolor=color, alpha=0.85))
    _style(ax, "Theme trends with key historical events", ylabel="Sentences per report")
    ax.legend(fontsize=8, framealpha=0.3, loc="upper left")
    if solo:
        plt.tight_layout()
        if save: plt.savefig(save, dpi=150, bbox_inches="tight"); print(f"  Saved: {save}")
        plt.show(); plt.close()


def plot_heatmap(pivot, ax=None, save=None):
    solo = ax is None
    if solo: fig, ax = plt.subplots(figsize=(14,4))
    normed = pivot.copy().astype(float)
    for t in THEMES:
        m = normed[t].max()
        if m > 0: normed[t] /= m
    im = ax.imshow(normed[THEMES].T.values, aspect="auto", cmap="YlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(pivot))); ax.set_xticklabels(pivot.index, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(THEMES))); ax.set_yticklabels([THEME_LABELS[t] for t in THEMES], fontsize=9)
    ax.set_title("Theme intensity heatmap (normalised per theme)", fontsize=11, fontweight="bold", pad=8, loc="left")
    for i,t in enumerate(THEMES):
        for j in range(len(pivot)):
            ax.text(j, i, str(int(pivot[t].iloc[j])), ha="center", va="center",
                    fontsize=5.5, color="white" if normed[t].iloc[j]>0.55 else "#333")
    if solo:
        plt.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
        plt.tight_layout()
        if save: plt.savefig(save, dpi=150, bbox_inches="tight"); print(f"  Saved: {save}")
        plt.show(); plt.close()


def plot_dashboard(pivot, save=None):
    fig = plt.figure(figsize=(18,15))
    fig.suptitle("MoEFCC Annual Reports — Sustainability Theme Analysis\nWith Historical Event Annotations",
                 fontsize=13, fontweight="bold", y=0.99)
    gs = GridSpec(3, 2, figure=fig, hspace=0.55, wspace=0.3)
    plot_line(pivot,    ax=fig.add_subplot(gs[0,0]))
    plot_stacked(pivot, ax=fig.add_subplot(gs[0,1]))
    plot_pct(pivot,     ax=fig.add_subplot(gs[1,0]))
    plot_heatmap(pivot, ax=fig.add_subplot(gs[1,1]))
    ax_ev = fig.add_subplot(gs[2,:])
    ax_ev.axis("off")
    lines = ["Key historical events explaining theme changes:\n"]
    for yr in sorted(EVENT_DESC):
        lines.append(f"  {yr}  {EVENT_DESC[yr]}")
    ax_ev.text(0.01, 0.98, "\n".join(lines), transform=ax_ev.transAxes,
               fontsize=8.5, verticalalignment="top", fontfamily="monospace",
               bbox=dict(boxstyle="round,pad=0.6", facecolor="#f8f8f4", alpha=0.9))
    plt.tight_layout(rect=[0,0,1,0.98])
    if save: plt.savefig(save, dpi=150, bbox_inches="tight"); print(f"  Saved: {save}")
    plt.show(); plt.close()


def print_summary(pivot):
    print("\n"+"="*65+"\nTHEME SUMMARY\n"+"="*65)
    totals = pivot.sum(axis=1)
    for t in THEMES:
        first, last = int(pivot[t].iloc[0]), int(pivot[t].iloc[-1])
        pct = ((last-first)/max(first,1))*100
        avg = float((pivot[t]/totals*100).mean())
        peak = int(pivot[t].idxmax())
        print(f"  {THEME_LABELS[t]:<30}  {first:>4} → {last:>4} ({pct:+.0f}%)  avg {avg:.1f}%  peak {peak}")
    print("="*65)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv",  default="moefcc_sustainability_dataset.csv")
    ap.add_argument("--mode", choices=["all","line","stacked","pct","events","heatmap","dashboard"], default="all")
    ap.add_argument("--out",  default="charts")
    args = ap.parse_args()

    if not pathlib.Path(args.csv).exists():
        print(f"\nERROR: {args.csv} not found.")
        print("Run first:  python moefcc_nlp_pipeline.py --step dataset\n")
        raise SystemExit(1)

    out = pathlib.Path(args.out); out.mkdir(exist_ok=True)
    print(f"\nLoading {args.csv} ...")
    pivot = load_pivot(args.csv)
    print_summary(pivot)
    print(f"\nSaving charts to {out}/\n")

    m = args.mode
    if m in ("all","line"):      plot_line(pivot,    save=str(out/"01_line.png"))
    if m in ("all","stacked"):   plot_stacked(pivot, save=str(out/"02_stacked.png"))
    if m in ("all","pct"):       plot_pct(pivot,     save=str(out/"03_pct_share.png"))
    if m in ("all","events"):    plot_events(pivot,  save=str(out/"04_events.png"))
    if m in ("all","heatmap"):   plot_heatmap(pivot, save=str(out/"05_heatmap.png"))
    if m in ("all","dashboard"): plot_dashboard(pivot, save=str(out/"06_dashboard.png"))
    print(f"\nDone — charts in {out.resolve()}")
