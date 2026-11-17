"""Solve the base case (budget $5M) and print the network."""
from bike_and_ride import small_instance, solve

inst = small_instance()
sol = solve(inst)

print(f"Trips shifted from car to B&R: {sol.shift:,.0f} of {sol.total_demand:,.0f}")
print(f"Construction cost:             ${sol.cost:,.0f}")
print(f"Opened hubs:                   {sol.hubs}")
print(f"Linked pairs (i, k):           {sol.pairs}")
print(f"Bicycle lanes:                 {sol.lanes} ({sol.lane_km} km)")
print("Paths used (i, k, m, j):")
for p in sol.paths:
    print(f"  {p}  demand {inst.w[p[0], p[3]]}")
