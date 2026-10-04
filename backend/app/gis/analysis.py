import numpy as np
import pandas as pd
from ..dsa.algorithms import haversine_km

def minmax(series):
    s=pd.Series(series,dtype=float)
    lo,hi=s.min(),s.max()
    if hi==lo:
        return pd.Series(50.0,index=s.index)
    return ((s-lo)/(hi-lo)*100).clip(0,100)

def gap_analysis(snapshot, target, chargers, weights):
    x=snapshot.copy()
    x["ev_per_charger"]=x.ev_count/x.chargers.clip(lower=1)
    x["required_chargers"]=np.ceil(x.ev_count/max(target,1)).astype(int)
    x["charger_gap"]=(x.required_chargers-x.chargers).clip(lower=0).astype(int)

    x["evn"]=minmax(x.ev_count)
    x["prn"]=minmax(x.ev_per_charger)
    x["popn"]=minmax(x.population)
    x["roadn"]=minmax(x.road_score)
    x["actn"]=minmax(x.activity_score)

    pts=chargers[["latitude","longitude"]].to_numpy(float) if len(chargers) else []
    near=[]
    for r in x.itertuples():
        near.append(min(
            [haversine_km(float(r.latitude),float(r.longitude),float(a),float(b)) for a,b in pts],
            default=np.nan
        ))
    x["nearest_charger_km"]=near
    fill=float(np.nanmedian(x.nearest_charger_km)) if x.nearest_charger_km.notna().any() else 0
    x["accessn"]=minmax(x.nearest_charger_km.fillna(fill))

    x["gap_score"]=(
        weights["ev_demand"]*x.evn+
        weights["ev_per_charger"]*x.prn+
        weights["population_demand"]*x.popn+
        weights["road_mobility"]*x.roadn+
        weights["activity"]*x.actn+
        weights["access_pressure"]*x.accessn
    ).round(2)

    x["gap_level"]=pd.cut(
        x.gap_score,[-.01,20,40,60,80,100.01],
        labels=["Very Low","Low","Moderate","High","Critical"]
    ).astype(str)
    return x

def candidate_recommendations(snapshot):
    x=snapshot.copy()
    x["site_score"]=(
        .30*minmax(x.ev_count)+
        .20*minmax(x.ev_per_charger)+
        .15*minmax(x.population)+
        .15*minmax(x.road_score)+
        .10*minmax(x.activity_score)+
        .10*minmax(x.charger_gap)
    ).round(2)

    qs={c:x[c].quantile(.75) for c in
        ["ev_count","ev_per_charger","charger_gap","road_score","activity_score"]}

    reasons=[]
    for r in x.itertuples():
        z=[]
        if r.ev_count>=qs["ev_count"]: z.append("high EV demand")
        if r.ev_per_charger>=qs["ev_per_charger"]: z.append("high EV-to-charger pressure")
        if r.charger_gap>=qs["charger_gap"]: z.append("large charger gap")
        if r.road_score>=qs["road_score"]: z.append("strong road access")
        if r.activity_score>=qs["activity_score"]: z.append("strong activity")
        reasons.append(z or ["balanced demand/infrastructure indicators"])
    x["why_here"]=reasons
    x=x.sort_values("site_score",ascending=False).reset_index(drop=True)
    x["rank"]=np.arange(1,len(x)+1)
    x["additional_chargers"]=x["charger_gap"]
    return x
