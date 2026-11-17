"""Budget and demand sensitivity analysis.

Writes results/budget_sweep.csv and results/demand_sweep.csv.
"""
import csv

from bike_and_ride import small_instance, solve

inst = small_instance()
FIELDS = ["shift", "share_of_car_trips", "cost", "hubs", "lanes", "lane_km"]


def row(value, sol):
    share = sol.shift / sol.total_demand if sol.total_demand else 0.0
    return [value, sol.shift, round(share, 3), sol.cost,
            " ".join(map(str, sol.hubs)), " ".join(map(str, sol.lanes)), sol.lane_km]


# budget: $0 to $1.3M in $10,000 steps, plus the values used in the course project
budgets = sorted(set(range(0, 1_300_001, 10_000)) | {2_500_000, 5_000_000, 10_000_000, 100_000_000})
with open("results/budget_sweep.csv", "w", newline="") as f:
    out = csv.writer(f)
    out.writerow(["budget"] + FIELDS)
    for b in budgets:
        sol = solve(inst, budget=b)
        out.writerow(row(b, sol))

# demand: every w_ij multiplied by a factor, budget fixed at $5M
with open("results/demand_sweep.csv", "w", newline="") as f:
    out = csv.writer(f)
    out.writerow(["demand_factor"] + FIELDS)
    for factor in [0.25, 0.5, 1.0, 2.0]:
        sol = solve(inst, demand_scale=factor)
        out.writerow(row(factor, sol))
        print(f"demand x{factor}: shift {sol.shift:,.0f}, cost ${sol.cost:,.0f}, hubs {sol.hubs}")

for b in [500_000, 1_000_000, 2_500_000, 5_000_000]:
    sol = solve(inst, budget=b)
    print(f"budget ${b:,}: shift {sol.shift:,.0f}, cost ${sol.cost:,.0f}, hubs {sol.hubs}, {sol.lane_km} km")
