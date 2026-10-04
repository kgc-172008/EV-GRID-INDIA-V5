import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURES=[
    "year","population","road_score","activity_score",
    "chargers","lag1","lag2","growth"
]

def train_frame(df):
    x=df.sort_values(["state","district","year"]).copy()
    g=x.groupby(["state","district"],group_keys=False)
    x["lag1"]=g.ev_count.shift(1)
    x["lag2"]=g.ev_count.shift(2)
    x["growth"]=g.ev_count.pct_change().replace([np.inf,-np.inf],np.nan).clip(-.5,2)
    return x.dropna(subset=["lag1","lag2","growth"])

def forecast(df,horizon=5):
    x=train_frame(df)
    if len(x)<12:
        raise ValueError("Not enough historical rows for forecasting.")
    hold=int(x.year.max())
    train=x[x.year<hold]
    test=x[x.year==hold]
    if len(train)<8 or len(test)<2:
        hold-=1; train=x[x.year<hold]; test=x[x.year==hold]
    model=RandomForestRegressor(
        n_estimators=400,max_depth=10,min_samples_leaf=2,
        random_state=42,n_jobs=-1
    )
    model.fit(train[FEATURES],train.ev_count)
    pred=model.predict(test[FEATURES])
    metrics={
        "MAE":float(mean_absolute_error(test.ev_count,pred)),
        "RMSE":float(np.sqrt(mean_squared_error(test.ev_count,pred))),
        "R2":float(r2_score(test.ev_count,pred)),
        "holdout_year":hold
    }
    model.fit(x[FEATURES],x.ev_count)
    latest=df.sort_values("year").groupby(["state","district"]).tail(1)
    histories={
        (r.state,r.district):
        df[(df.state==r.state)&(df.district==r.district)]
        .sort_values("year").ev_count.tolist()
        for r in latest.itertuples()
    }
    out=[]; last=int(df.year.max())
    for step in range(1,horizon+1):
        fy=last+step
        for r in latest.itertuples():
            vals=histories[(r.state,r.district)]
            lag1=vals[-1]
            lag2=vals[-2] if len(vals)>1 else vals[-1]
            growth=(lag1/lag2-1) if lag2 else 0
            row={
                "year":fy,
                "population":r.population*(1.012**step),
                "road_score":r.road_score,
                "activity_score":r.activity_score,
                "chargers":r.chargers,
                "lag1":lag1,
                "lag2":lag2,
                "growth":float(np.clip(growth,-.5,2))
            }
            ev=max(0,int(round(model.predict(pd.DataFrame([row])[FEATURES])[0])))
            histories[(r.state,r.district)]=vals+[ev]
            out.append({
                "state":r.state,"district":r.district,"year":fy,
                "predicted_ev":ev,"chargers":int(r.chargers),
                "latitude":float(r.latitude),"longitude":float(r.longitude)
            })
    return pd.DataFrame(out),metrics

def cluster_demand(snapshot,n_clusters=4):
    x=snapshot.copy()
    cols=["ev_count","ev_per_charger","population","charger_gap","road_score","activity_score"]
    for c in cols:
        if c not in x: x[c]=0
    z=x[cols].replace([np.inf,-np.inf],np.nan).fillna(0)
    n=max(1,min(n_clusters,len(x)))
    model=KMeans(n_clusters=n,random_state=42,n_init=10)
    x["cluster"]=model.fit_predict(z)
    return x

def predict_station_load(features):
    # Interface intentionally requires historical session data for real training.
    # V4 returns a transparent heuristic fallback when that dataset is absent.
    traffic=float(features.get("traffic_index",50))
    occupancy=float(features.get("current_occupancy",50))
    arrivals=float(features.get("arrivals_index",50))
    predicted=min(100,max(0,0.45*occupancy+0.30*traffic+0.25*arrivals))
    return {
        "predicted_peak_occupancy":round(predicted,1),
        "data_status":"HEURISTIC — provide historical station-session data for trained prediction",
    }
