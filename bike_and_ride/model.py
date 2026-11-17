"""MILP for Bike-and-Ride hub network design, written with gurobipy.

Constraint numbers in comments follow Tavassoli and Tamannaei (2020).
"""
from dataclasses import dataclass

import gurobipy as gp
from gurobipy import GRB


def build_model(inst, budget=None, demand_scale=1.0, big_m=None):
    """Build the stage-1 model: maximize the number of trips shifted from car to B&R.

    budget        construction budget in $ (default: inst.budget)
    demand_scale  multiplies every w_ij (for sensitivity analysis)
    big_m         None uses the smallest valid value M_h = number of pairs of hub h;
                  a number (for example 1e25) reproduces the course version
    """
    B = inst.budget if budget is None else budget
    w = {od: v * demand_scale for od, v in inst.w.items()}
    P = inst.paths()

    m = gp.Model("bike_and_ride")
    m.Params.OutputFlag = 0

    z = m.addVars(inst.hubs, vtype=GRB.BINARY, name="z")            # hub h is opened
    y = m.addVars(inst.pairs, vtype=GRB.BINARY, name="y")           # pair (i, k) is linked
    eta = m.addVars(list(inst.lane_km), vtype=GRB.BINARY, name="eta")  # lane l is built
    x = m.addVars(P, vtype=GRB.BINARY, name="x")                    # trip i->j shifts via k, m
    kappa = m.addVars(inst.hubs, lb=0.0, name="kappa")              # installation cost of hub h

    def demand(p):
        return w.get((p[0], p[3]), 0.0)

    shift = gp.quicksum(demand(p) * x[p] for p in P)
    m.setObjective(shift, GRB.MAXIMIZE)                                      # (1)

    for p in P:
        i, k, mm, j = p
        m.addConstr(x[p] <= y[i, k], name=f"access{p}")                     # (2)
        m.addConstr(x[p] <= y[j, mm], name=f"egress{p}")                    # (3)
        m.addConstr(x[p] <= inst.delta[p], name=f"cheaper{p}")              # (4)

    # (5) at most one path per OD pair
    for i in inst.H2:
        for j in inst.H2:
            through = [p for p in P if p[0] == i and p[3] == j]
            if len(through) > 1:
                m.addConstr(gp.quicksum(x[p] for p in through) <= 1, name=f"one_path[{i},{j}]")

    # (6)-(7) fixed site cost + capacity cost for all demand that passes through hub h
    for h in inst.hubs:
        passing = [p for p in P if h in p]
        m.addConstr(kappa[h] == inst.lam * z[h]
                    + inst.dlt * gp.quicksum(demand(p) * x[p] for p in passing),
                    name=f"hub_cost[{h}]")

    # (8), (10), (11), (13): hub h is opened if and only if at least one of its pairs is linked.
    # (9) and (12) are always satisfied because y >= 0, so they are not added.
    for h in inst.hubs:
        pairs_h = inst.partners(h)
        M = len(pairs_h) if big_m is None else big_m
        linked = gp.quicksum(y[p] for p in pairs_h)
        m.addConstr(linked >= 1 - M * (1 - z[h]), name=f"open_if_linked[{h}]")
        m.addConstr(linked <= M * z[h], name=f"link_if_open[{h}]")

    # (14) a linked pair needs its lane; a lane is built only for a linked pair
    for l, pair in inst.lane_pair.items():
        m.addConstr(eta[l] >= y[pair], name=f"lane_needed[{l}]")
        m.addConstr(eta[l] <= y[pair], name=f"lane_used[{l}]")

    cost = kappa.sum() + inst.gamma * gp.quicksum(inst.lane_km[l] * eta[l] for l in inst.lane_km)
    m.addConstr(cost <= B, name="budget")                                    # (15)

    m._data = dict(z=z, y=y, eta=eta, x=x, kappa=kappa, shift=shift, cost=cost, paths=P, w=w)
    return m


@dataclass
class Solution:
    shift: float          # trips moved from car to B&R
    total_demand: float   # all car trips in the instance
    cost: float           # construction cost of the network ($)
    hubs: list            # opened hubs
    pairs: list           # linked (i, k) pairs
    lanes: list           # built lane ids
    lane_km: float        # total length of built lanes
    paths: list           # (i, k, m, j) paths used by shifted trips


def solve(inst, budget=None, demand_scale=1.0, big_m=None, min_cost=True):
    """Solve the model.

    Stage 1 maximizes the modal shift. If min_cost is True, stage 2 keeps that shift
    and finds the cheapest network that achieves it (lexicographic optimization).
    """
    m = build_model(inst, budget, demand_scale, big_m)
    d = m._data
    m.optimize()
    if m.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Gurobi status {m.Status}")
    best_shift = m.ObjVal

    if min_cost:
        m.addConstr(d["shift"] >= best_shift - 1e-6, name="keep_best_shift")
        m.setObjective(d["cost"], GRB.MINIMIZE)
        m.optimize()

    lanes = sorted(l for l, v in d["eta"].items() if v.X > 0.5)
    return Solution(
        shift=round(best_shift, 6),
        total_demand=sum(d["w"].values()),
        cost=round(d["cost"].getValue(), 2),
        hubs=sorted(h for h, v in d["z"].items() if v.X > 0.5),
        pairs=sorted(p for p, v in d["y"].items() if v.X > 0.5),
        lanes=lanes,
        lane_km=round(sum(inst.lane_km[l] for l in lanes), 2),
        paths=[p for p in d["paths"] if d["x"][p].X > 0.5],
    )
