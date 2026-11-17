"""Figures for the README (matplotlib only)."""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BLUE, GRAY, LIGHT, INK, MUTED = "#2a78d6", "#8a8984", "#d9d8d4", "#0b0b0b", "#52514e"
TRANSIT_STYLE = dict(color=GRAY, lw=2, ls=(0, (6, 3)))


def _legend(fig, show_built=True):
    handles = [
        Line2D([], [], marker="s", ls="", ms=10, mfc="white", mec=GRAY, label="Level-I hub candidate (transit station)"),
        Line2D([], [], marker="o", ls="", ms=10, mfc="white", mec=GRAY, label="Level-II hub candidate"),
        Line2D([], [], color=LIGHT, lw=1.5, label="Candidate bicycle lane"),
        Line2D([], [], label="Transit link", **TRANSIT_STYLE),
    ]
    if show_built:
        handles[2:2] = [Line2D([], [], marker="o", ls="", ms=10, mfc=BLUE, mec=BLUE, label="Opened hub"),
                        Line2D([], [], color=BLUE, lw=3, label="Built bicycle lane")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8.5, frameon=False)


def draw_network(ax, inst, sol=None, title="", lane_labels=True):
    """Draw the candidate network; if sol is given, highlight opened hubs and built lanes."""
    xy = inst.xy
    hubs = sol.hubs if sol else []
    lanes = sol.lanes if sol else []
    for k, ms in inst.transit.items():
        for m in ms:
            if k < m:
                ax.plot(*zip(xy[k], xy[m]), zorder=1, **TRANSIT_STYLE)
    for l, (i, k) in inst.lane_pair.items():
        built = l in lanes
        (x0, y0), (x1, y1) = xy[i], xy[k]
        ax.plot([x0, x1], [y0, y1], color=BLUE if built else (GRAY if sol is None else LIGHT),
                lw=3 if built else 1.5, zorder=2, solid_capstyle="round")
        if lane_labels:
            length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            nx, ny = -(y1 - y0) / length, (x1 - x0) / length
            if ny < 0:
                nx, ny = -nx, -ny
            ax.text((x0 + x1) / 2 + 0.55 * nx, (y0 + y1) / 2 + 0.35 * ny, f"{inst.lane_km[l]} km",
                    fontsize=8, color=MUTED, ha="center", va="center")
    for h in inst.hubs:
        opened = h in hubs
        ax.scatter(*xy[h], s=430, marker="s" if h in inst.H1 else "o",
                   facecolor=BLUE if opened else "white", edgecolor=BLUE if opened else GRAY,
                   lw=2, zorder=3)
        ax.text(*xy[h], str(h), ha="center", va="center", fontsize=10, fontweight="bold",
                color="white" if opened else INK, zorder=4)
    ax.set_title(title, fontsize=10.5, loc="left")
    ax.set_xlim(0.5, 13.8)
    ax.set_ylim(0, 6.6)
    ax.set_aspect("equal")
    ax.axis("off")


def network_figure(inst, sol, path):
    """Test network (left) and the optimal network for the base case (right)."""
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 3.9))
    draw_network(axes[0], inst, None, "Test network: candidate hubs and lanes")
    draw_network(axes[1], inst, sol,
                 f"Optimal network, budget \\$5M: {sol.shift:,.0f} trips shifted, cost \\${sol.cost / 1e6:.3f}M")
    _legend(fig)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def budget_networks_figure(inst, sols, path):
    """sols: list of (budget, Solution). One small map per budget."""
    fig, axes = plt.subplots(1, len(sols), figsize=(5.2 * len(sols), 3.5))
    for ax, (b, sol) in zip(axes, sols):
        draw_network(ax, inst, sol, f"Budget ${b / 1e6:g}M: {sol.shift:,.0f} trips shifted",
                     lane_labels=False)
    _legend(fig)
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def budget_figure(rows, path):
    """rows: list of (budget, shift, cost) from the budget sweep."""
    b = [r[0] / 1000 for r in rows]
    s = [r[1] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.step(b, s, where="post", color=BLUE, lw=2)
    full = next(r for r in rows if r[1] >= max(s))
    ax.scatter([full[0] / 1000], [full[1]], s=60, color=BLUE, zorder=3)
    ax.annotate(f"All eligible trips shifted\nfrom ${full[2] / 1e6:.3f}M",
                (full[0] / 1000, full[1]), xytext=(-150, -45), textcoords="offset points",
                fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=GRAY, lw=1))
    ax.set_xlabel("Budget (thousand $)")
    ax.set_ylabel("Trips shifted from car to B&R")
    ax.set_ylim(0, max(s) * 1.1)
    ax.set_xlim(0, max(b))
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#ecebe8", lw=0.8)
    ax.set_title("Modal shift against budget (cheapest network at each budget)", fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def demand_figure(rows, path):
    """rows: list of (demand_factor, shift, cost) from the demand sweep."""
    labels = [f"{f:g} W" for f, _, _ in rows]
    costs = [c / 1e6 for _, _, c in rows]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    bars = ax.bar(labels, costs, width=0.55, color=BLUE)
    for bar, (_, shift, _) in zip(bars, rows):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.04,
                f"{shift:,.0f} trips", ha="center", fontsize=9, color=MUTED)
    ax.set_xlabel("Car demand (multiple of the base demand W)")
    ax.set_ylabel("Network cost (million $)")
    ax.set_ylim(0, max(costs) * 1.18)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#ecebe8", lw=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Network cost against demand (budget $5M, same 7 hubs in every case)", fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def trip_patterns_figure(path):
    """Schematic of the three B&R trip patterns defined in the paper (redrawn, simplified)."""
    walk = dict(color=GRAY, lw=1.6, ls=(0, (1.5, 2.5)))
    cycle = dict(color=BLUE, lw=3)
    transit = dict(color=INK, lw=2, ls=(0, (6, 3)))
    x = [0, 2, 4.5, 8.5, 11, 13]
    rows = [
        ("(1)", [("Origin", "dot"), ("i", "circle"), ("k", "square"), ("m", "square"), ("j", "circle"), ("Destination", "dot")],
         [walk, cycle, transit, cycle, walk]),
        ("(2)", [("Origin", "dot"), ("i", "circle"), ("k", "square"), ("m = j", "square"), ("Destination", "dot")],
         [walk, cycle, transit, walk]),
        ("(3)", [("Origin", "dot"), ("k = i", "square"), ("m", "square"), ("j", "circle"), ("Destination", "dot")],
         [walk, transit, cycle, walk]),
    ]
    xs = [x, [0, 2, 4.5, 8.5, 11], [2, 4.5, 8.5, 11, 13]]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for r, ((label, nodes, legs), xx) in enumerate(zip(rows, xs)):
        yv = 2 - r
        ax.text(-2.4, yv, f"Pattern {label}", va="center", fontsize=10, color=INK)
        for a in range(len(legs)):
            ax.plot([xx[a], xx[a + 1]], [yv, yv], zorder=1, **legs[a])
        for (name, kind), xv in zip(nodes, xx):
            if kind == "dot":
                ax.scatter(xv, yv, s=40, color=GRAY, zorder=2)
            else:
                ax.scatter(xv, yv, s=170, marker="s" if kind == "square" else "o",
                           facecolor="white", edgecolor=BLUE if kind == "circle" else INK, lw=2, zorder=2)
            ax.text(xv, yv - 0.3, name, ha="center", va="top", fontsize=9.5,
                    style="normal" if kind == "dot" else "italic", color=INK)
    handles = [Line2D([], [], label="Walk", **walk), Line2D([], [], label="Cycle (bike-sharing)", **cycle),
               Line2D([], [], label="Transit", **transit),
               Line2D([], [], marker="o", ls="", ms=9, mfc="white", mec=BLUE, label="Level-II hub"),
               Line2D([], [], marker="s", ls="", ms=9, mfc="white", mec=INK, label="Level-I hub (transit station)")]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=5, fontsize=8.5, frameon=False)
    ax.set_xlim(-2.6, 13.8)
    ax.set_ylim(-0.75, 2.4)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
