"""Checks on the 9-node instance. Run with: python -m pytest"""
from bike_and_ride import small_instance, solve


def test_base_case():
    sol = solve(small_instance())
    assert sol.shift == 4500
    assert sol.cost == 1_148_000
    assert sol.hubs == [1, 2, 4, 5, 6, 7, 9]


def test_every_opened_hub_is_linked():
    inst = small_instance()
    for budget in [300_000, 500_000, 1_000_000, 5_000_000]:
        sol = solve(inst, budget=budget, min_cost=False)
        linked = {h for pair in sol.pairs for h in pair}
        assert set(sol.hubs) == linked


def test_budget_is_respected():
    inst = small_instance()
    for budget in range(0, 1_300_001, 50_000):
        assert solve(inst, budget=budget).cost <= budget + 1e-6
