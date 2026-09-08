"""Monotone interval bounds for a declared, pre-funded fixed-horizon service model."""
def ceil_div(a,b): return -(-a//b)
def scaled(v,f,upper=False): return ceil_div(v*f,10000) if upper else v*f//10000

def stress(e,resources,scenario,route_cost):
    p0,p1=e['unit_price_cents']; c0,c1=e['unit_cost_cents']; a0,a1=e['acquisition_cents']; q0,q1=e['demand_units']
    price=[scaled(p0,scenario['price_bps']),scaled(p1,scenario['price_bps'],True)]
    cost=[scaled(c0+a0,scenario['cost_bps'])+route_cost,scaled(c1+a1,scenario['cost_bps'],True)+route_cost]
    demand=[scaled(q0,scenario['demand_bps']),scaled(q1,scenario['demand_bps'],True)]
    capacity=max(0,resources['available_minutes']-e['setup_minutes'])//e['delivery_minutes_per_unit']
    units=[min(demand[0],capacity),min(demand[1],capacity)]
    margin=[price[0]-cost[1],price[1]-cost[0]]
    overhead=e['upfront_cents']+e['fixed_period_cents']
    net=[min(units[0]*margin[0],units[1]*margin[0])-overhead,
         max(units[0]*margin[1],units[1]*margin[1])-overhead]
    goal=resources['target_surplus_cents']
    breakeven=ceil_div(overhead+goal,margin[0]) if margin[0]>0 else None
    return {'scenario_id':scenario['id'],'unit_price_cents':price,'unit_cash_cost_cents':cost,
            'deliverable_units':units,'capacity_units':capacity,'margin_cents':margin,'net_cash_cents':net,
            'prefund_cents':overhead+units[1]*cost[1],
            'minutes_at_upper_units':e['setup_minutes']+units[1]*e['delivery_minutes_per_unit'],
            'goal_units_at_lower_margin':breakeven,
            'cash_goal_met_at_lower_bound':net[0]>=goal,
            'loss_ceiling_met':net[0]>=-resources['max_loss_cents']}
