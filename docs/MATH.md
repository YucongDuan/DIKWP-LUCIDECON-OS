# Arithmetic contract

For each route and scenario, round price bounds outward and cost/demand bounds outward in integer cents/units. Capacity is max(0, available_minutes - setup_minutes) // delivery_minutes_per_unit. Units are demand clipped to capacity. Per-unit route money is included once in unit cost; transport/travel/maintenance must be declared in the input costs when relevant.

m_low = price_low - cost_high - acquisition_high - route_cost
m_high = price_high - cost_low - acquisition_low - route_cost
net_low = min(q_low*m_low, q_high*m_low) - fixed - upfront
net_high = max(q_low*m_high, q_high*m_high) - fixed - upfront
prefund = fixed + upfront + q_high*(cost_high + acquisition_high + route_cost)

The min/max expressions remain correct when margins are negative. Scenario factors operate on interval endpoints. These bounds are deterministic under the declared rectangular assumptions, not statistical confidence intervals. Negative dependence/correlation, demand-price elasticity and endogenous competitor response are not inferred. Received payments do not finance later units in this deliberately conservative pre-funding model.

Routes first pass declared access/quality/data/time/per-unit budget gates. All such routes receive economic stress checks. Affordable all-scenario target-meeting routes have priority, otherwise affordable candidate pilots, otherwise diagnostic-only routes. Within that class and a comparable energy boundary, select the lowest upper Joule bound; this is not a global physical optimum. Unknown energy is excluded from energy ranking. If no comparable energy exists and no hard energy budget is present, disclose a cost fallback.

Settlement conserves gross exactly: repair + commons + newcomer + planned payouts + holds = gross. Rates apply after repair, their sum cannot exceed 10000 basis points, and largest-remainder apportionment uses deterministic ID tie-breaking. Unverified/disputed weights remain in the denominator and their apportioned amounts remain held. All-zero weights hold the entire distributable remainder. Claims larger than gross record a repair shortfall rather than create funds.

The market experiment is a fixed pool with a declared reinforcement exponent. Changing the exponent changes whether initial exposure persists. A newcomer floor and individual cap can be infeasible; this is rejected. A policy can also increase HHI; a counterexample is bundled. Neither redistributing a pool nor lowering concentration proves new demand, income or welfare.
