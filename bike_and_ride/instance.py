"""Problem data.

`small_instance()` returns the 9-node synthetic network used in the course project.
It is a hand-made test case, not the Isfahan data from the paper.
"""
from dataclasses import dataclass, field


def _symmetric(one_way):
    """Copy every (a, ..., b) entry to its reverse (b, ..., a)."""
    out = {}
    for key, value in one_way.items():
        out[key] = value
        out[tuple(reversed(key))] = value
    return out


@dataclass
class Instance:
    H1: list            # level-I hub candidates (transit stations)
    H2: list            # level-II hub candidates (BSS stations outside the transit catchment)
    R_k: dict           # level-II hubs within cycling range of each level-I hub
    transit: dict       # transit links between level-I hubs (adjacency lists)
    lane_pair: dict     # bicycle lane id -> (level-II hub i, level-I hub k) it serves
    lane_km: dict       # bicycle lane id -> length (km)
    w: dict             # private-car demand w_ij (trips)
    delta: dict         # Delta_ikmj = 1 if B&R via k, m is cheaper than the car
    lam: float          # site preparation cost per BSS station ($)
    dlt: float          # capacity cost per unit of demand passing through a hub ($)
    gamma: float        # bicycle lane construction cost ($/km)
    budget: float       # default budget ($)
    xy: dict = field(default_factory=dict)  # node coordinates, for plotting only

    @property
    def hubs(self):
        return self.H1 + self.H2

    @property
    def pairs(self):
        """Corresponding hub pairs (i, k): i in H2 within cycling range of k in H1."""
        return [(i, k) for k in self.H1 for i in self.R_k[k]]

    def partners(self, h):
        """Pairs that involve hub h."""
        return [p for p in self.pairs if h in p]

    def paths(self):
        """All B&R paths (i, k, m, j): cycle i->k, transit k->m, cycle m->j."""
        return [(i, k, m, j)
                for k in self.H1 for i in self.R_k[k]
                for m in self.transit[k] for j in self.R_k[m]
                if i != j]


def small_instance():
    """9-node test network (values from the course project, version 4.2.0)."""
    return Instance(
        H1=[3, 4, 5, 6],
        H2=[1, 2, 7, 8, 9],
        R_k={3: [1], 4: [1, 2], 5: [7, 8], 6: [9]},
        transit={3: [5], 4: [5, 6], 5: [3, 4], 6: [4]},
        lane_pair={1: (1, 3), 2: (1, 4), 3: (2, 4), 7: (7, 5), 8: (8, 5), 9: (9, 6)},
        lane_km={1: 0.6, 2: 1.4, 3: 0.8, 7: 0.6, 8: 0.5, 9: 0.8},
        w=_symmetric({(1, 7): 100, (1, 8): 150, (1, 9): 800,
                      (2, 7): 950, (2, 8): 350, (2, 9): 400}),
        delta=_symmetric({(1, 3, 5, 7): 1, (1, 3, 5, 8): 0, (1, 4, 6, 9): 1,
                          (1, 4, 5, 7): 1, (1, 4, 5, 8): 0, (2, 4, 6, 9): 1,
                          (2, 4, 5, 7): 1, (2, 4, 5, 8): 0}),
        lam=20_000,
        dlt=40,
        gamma=80_000,
        budget=5_000_000,
        xy={1: (1.6, 5.2), 2: (1.6, 2.8), 3: (5.2, 4.3), 4: (4.8, 2.0),
            5: (9.7, 4.6), 6: (9.9, 2.0), 7: (12.6, 5.7), 8: (12.7, 3.8), 9: (12.6, 0.8)},
    )
