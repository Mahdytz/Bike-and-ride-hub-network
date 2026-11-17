"""Draw every figure in figures/ (run after run_sensitivity.py)."""
import csv

from bike_and_ride import small_instance, solve
from bike_and_ride.plots import (budget_figure, budget_networks_figure, demand_figure,
                                 network_figure, trip_patterns_figure)

inst = small_instance()

trip_patterns_figure("figures/trip_patterns.png")
network_figure(inst, solve(inst), "figures/network.png")
budget_networks_figure(inst, [(b, solve(inst, budget=b)) for b in (500_000, 1_000_000, 5_000_000)],
                       "figures/budget_networks.png")

with open("results/budget_sweep.csv") as f:
    rows = [(float(r["budget"]), float(r["shift"]), float(r["cost"])) for r in csv.DictReader(f)]
budget_figure([r for r in rows if r[0] <= 1_300_000], "figures/budget_curve.png")

with open("results/demand_sweep.csv") as f:
    rows = [(float(r["demand_factor"]), float(r["shift"]), float(r["cost"])) for r in csv.DictReader(f)]
demand_figure(rows, "figures/demand_cost.png")
print("figures written to figures/")
