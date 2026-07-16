import random,statistics,math

def percentile(values,p):
    v=sorted(values);idx=(len(v)-1)*p;lo=math.floor(idx);hi=math.ceil(idx)
    return v[lo] if lo==hi else v[lo]*(hi-idx)+v[hi]*(idx-lo)
def simulate(volume:float,a):
    rng=random.Random(42);profits=[]
    for _ in range(a.iterations):
        demand=max(0,rng.gauss(volume*a.conversion_rate,max(volume*a.demand_uncertainty,1)))
        variable=max(0,rng.gauss(a.unit_variable_cost,max(a.unit_variable_cost*a.cost_uncertainty,1)))
        sellable=demand*(1-a.defect_rate)*(1-a.return_rate)
        revenue=sellable*a.unit_sale_price
        tax=revenue*a.tax_rate
        cost=demand*variable+a.fixed_cost+a.marketing_cost+tax
        profits.append(revenue-cost)
    unit_margin=a.unit_sale_price*(1-a.defect_rate)*(1-a.return_rate)*(1-a.tax_rate)-a.unit_variable_cost
    breakeven=(a.fixed_cost+a.marketing_cost)/unit_margin if unit_margin>0 else float("inf")
    base=statistics.mean(profits)
    sensitivity={}
    for name,factor in {"sale_price":.1,"variable_cost":.1,"conversion_rate":.1}.items():
        if name=="sale_price": delta=volume*a.conversion_rate*a.unit_sale_price*factor
        elif name=="variable_cost": delta=-volume*a.conversion_rate*a.unit_variable_cost*factor
        else: delta=volume*a.conversion_rate*factor*max(unit_margin,0)
        sensitivity[name]=round(delta,2)
    return {"probability_profit":round(sum(p>0 for p in profits)/len(profits),4),"expected_profit":round(base,2),"p10":round(percentile(profits,.1),2),"p50":round(percentile(profits,.5),2),"p90":round(percentile(profits,.9),2),"value_at_risk_90":round(max(0,-percentile(profits,.1)),2),"break_even_volume":round(breakeven,2) if math.isfinite(breakeven) else None,"sensitivity":sensitivity,"top_risk_drivers":[x[0] for x in sorted(sensitivity.items(),key=lambda x:abs(x[1]),reverse=True)]}
