import math
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .config import GAP_WEIGHTS

def mm(s):
    s=pd.Series(s).astype(float); lo,hi=s.min(),s.max()
    if hi==lo:return pd.Series(50.0,index=s.index)
    return ((s-lo)/(hi-lo)*100).clip(0,100)

def hav(a,b,c,d):
    R=6371.; p1,p2=math.radians(a),math.radians(c); dp=math.radians(c-a); dl=math.radians(d-b); z=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(z))

def gap(snapshot, target, chargers):
    x=snapshot.copy(); x['ev_per_charger']=x.ev_count/x.chargers.clip(lower=1); x['required_chargers']=np.ceil(x.ev_count/max(target,1)).astype(int); x['charger_gap']=(x.required_chargers-x.chargers).clip(lower=0)
    x['evn']=mm(x.ev_count); x['prn']=mm(x.ev_per_charger); x['popn']=mm(x.population); x['roadn']=mm(x.road_score); x['actn']=mm(x.activity_score)
    pts=chargers[['latitude','longitude']].to_numpy(float) if len(chargers) else []
    near=[]
    for r in x.itertuples():
        near.append(min([hav(float(r.latitude),float(r.longitude),float(a),float(b)) for a,b in pts],default=np.nan))
    x['nearest_charger_km']=near; x['accessn']=mm(x.nearest_charger_km.fillna(x.nearest_charger_km.median() if x.nearest_charger_km.notna().any() else 0))
    x['gap_score']=(GAP_WEIGHTS['ev_demand']*x.evn+GAP_WEIGHTS['ev_per_charger']*x.prn+GAP_WEIGHTS['population_demand']*x.popn+GAP_WEIGHTS['road_mobility']*x.roadn+GAP_WEIGHTS['activity']*x.actn+GAP_WEIGHTS['access_pressure']*x.accessn).round(2)
    x['gap_level']=pd.cut(x.gap_score,[-.01,20,40,60,80,100.01],labels=['Very Low','Low','Moderate','High','Critical'])
    return x

def train_frame(df):
    x=df.sort_values(['state','district','year']).copy(); g=x.groupby(['state','district'],group_keys=False); x['lag1']=g.ev_count.shift(1); x['lag2']=g.ev_count.shift(2); x['growth']=g.ev_count.pct_change().replace([np.inf,-np.inf],np.nan).clip(-.5,2); return x.dropna(subset=['lag1','lag2','growth'])

def forecast(df,horizon=5):
    x=train_frame(df); f=['year','population','road_score','activity_score','chargers','lag1','lag2','growth']
    if len(x)<12: raise ValueError('Not enough historical rows for forecasting.')
    hold=int(x.year.max()); tr=x[x.year<hold]; te=x[x.year==hold]
    if len(tr)<8 or len(te)<2: hold-=1; tr=x[x.year<hold]; te=x[x.year==hold]
    model=RandomForestRegressor(n_estimators=400,max_depth=10,min_samples_leaf=2,random_state=42,n_jobs=-1); model.fit(tr[f],tr.ev_count); pred=model.predict(te[f])
    metrics={'MAE':float(mean_absolute_error(te.ev_count,pred)),'RMSE':float(np.sqrt(mean_squared_error(te.ev_count,pred))),'R2':float(r2_score(te.ev_count,pred)),'holdout_year':hold}
    model.fit(x[f],x.ev_count); latest=df.sort_values('year').groupby(['state','district']).tail(1); hist={(r.state,r.district):df[(df.state==r.state)&(df.district==r.district)].sort_values('year').ev_count.tolist() for r in latest.itertuples()}; out=[]; last=int(df.year.max())
    for step in range(1,horizon+1):
        fy=last+step
        for r in latest.itertuples():
            key=(r.state,r.district); vals=hist[key]; lag1=vals[-1]; lag2=vals[-2] if len(vals)>1 else vals[-1]; growth=(lag1/lag2-1) if lag2 else 0
            row={'year':fy,'population':r.population*(1.012**step),'road_score':r.road_score,'activity_score':r.activity_score,'chargers':r.chargers,'lag1':lag1,'lag2':lag2,'growth':float(np.clip(growth,-.5,2))}
            ev=max(0,int(round(model.predict(pd.DataFrame([row])[f])[0]))); hist[key]=vals+[ev]; out.append({'state':r.state,'district':r.district,'year':fy,'predicted_ev':ev,'chargers':r.chargers,'latitude':r.latitude,'longitude':r.longitude})
    return pd.DataFrame(out),metrics

def recommend(s):
    x=s.copy(); x['site_score']=(.30*mm(x.ev_count)+.20*mm(x.ev_per_charger)+.15*mm(x.population)+.15*mm(x.road_score)+.10*mm(x.activity_score)+.10*mm(x.charger_gap)).round(2)
    qs={c:x[c].quantile(.75) for c in ['ev_count','ev_per_charger','charger_gap','road_score','activity_score']}
    def why(r):
        z=[]
        if r.ev_count>=qs['ev_count']:z.append('high EV demand')
        if r.ev_per_charger>=qs['ev_per_charger']:z.append('high EV-to-charger pressure')
        if r.charger_gap>=qs['charger_gap']:z.append('large charger gap')
        if r.road_score>=qs['road_score']:z.append('strong road access')
        if r.activity_score>=qs['activity_score']:z.append('strong activity')
        return '; '.join(z) if z else 'balanced demand/infrastructure indicators'
    x['why_here']=x.apply(why,axis=1); x=x.sort_values('site_score',ascending=False).reset_index(drop=True); x['rank']=np.arange(1,len(x)+1); return x
