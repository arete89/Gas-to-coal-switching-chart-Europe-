from datetime import date

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

import config
from switching import coal_efficiency_levels

SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
RED = "#e34948"
BLUE = "#2a78d6"
BLUE_LIGHT = "#9ec5f4"
BLUE_DARK = "#104281"


def blue_ramp(n):
    """n colors from light->dark blue — one step per coal efficiency level
    (lightest = least efficient/easiest for gas to beat, darkest = most
    efficient/hardest to beat)."""
    lo = mcolors.to_rgb(BLUE_LIGHT)
    hi = mcolors.to_rgb(BLUE_DARK)
    if n == 1:
        return [BLUE_DARK]
    return [mcolors.to_hex([lo[c] + (hi[c] - lo[c]) * i / (n - 1) for c in range(3)]) for i in range(n)]


def plot_switching_chart(df: pd.DataFrame, out_path: str):
    fig, ax = plt.subplots(figsize=(11, 6), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    # One threshold line per coal efficiency (ascending efficiency -> strictly
    # descending threshold, since more efficient coal is harder for gas to
    # beat). Shade the strip between each adjacent pair so the chart reads as
    # discrete regimes: below the lowest line, gas beats every coal plant in
    # the set; above the highest line, it beats none; each shaded strip in
    # between is "beats everything less efficient than this line, not this
    # line or above."
    levels = coal_efficiency_levels()
    thresholds = [df[f"coal_eff_{level:.3f}"] for level in levels]
    colors = blue_ramp(len(levels))
    n = len(levels)

    for i in range(n - 1):
        ax.fill_between(df.index, thresholds[i], thresholds[i + 1], color=colors[i], alpha=0.14, linewidth=0)

    last_x = df.index[-1]
    for level, t, color in zip(levels, thresholds, colors):
        ax.plot(df.index, t, color=color, linewidth=1.4, linestyle="--")
        ax.annotate(
            f"{level:.0%} coal", xy=(last_x, t.iloc[-1]), xytext=(8, 0),
            textcoords="offset points", va="center", ha="left",
            color=color, fontsize=9, fontweight="bold", clip_on=False,
        )

    ax.plot(df.index, df["gas"], color=RED, linewidth=2, label="TTF gas price")
    ax.annotate(
        "TTF gas", xy=(last_x, df["gas"].iloc[-1]), xytext=(8, 0),
        textcoords="offset points", va="center", ha="left",
        color=RED, fontsize=9, fontweight="bold", clip_on=False,
    )

    ax.set_ylabel("EUR / MWh", color=INK_SECONDARY, fontsize=10)

    fig.text(
        0.06, 0.97,
        f"European gas price vs. gas-to-coal switching range — as of {date.today():%Y-%m-%d}",
        color=INK_PRIMARY, fontsize=14, fontweight="bold", ha="left", va="top",
    )
    if config.DATA_SOURCE == "refinitiv":
        carbon_note = "carbon: live EUA front-month (LSEG Workspace)"
    else:
        carbon_note = (f"carbon flat at €{config.CARBON_PRICE_EUR_PER_T:.0f}/t "
                        f"({config.CARBON_PRICE_AS_OF}) — free-source proxy, see README")
    fig.text(
        0.06, 0.925,
        f"Gas at {config.GAS_EFF:.1%} efficiency (EU market benchmark) vs coal at "
        f"each labeled efficiency; {carbon_note}",
        color=INK_MUTED, fontsize=9, ha="left", va="top",
    )

    ax.grid(True, color=GRIDLINE, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(BASELINE)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    fig.tight_layout(rect=[0, 0, 0.9, 0.88])
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)
