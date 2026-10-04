from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("/app/data")
if not DATA_DIR.exists():
    DATA_DIR = Path(__file__).resolve().parents[2] / "data"

REG_COLS = [
    "state","district","year","ev_count","population",
    "road_score","activity_score","latitude","longitude"
]
CHG_COLS = ["charger_id","state","district","latitude","longitude"]

STATES = {
    "Delhi": ["New Delhi","North Delhi","South Delhi"],
    "Uttar Pradesh": ["Lucknow","Noida","Varanasi","Ghazipur","Gorakhpur"],
    "Maharashtra": ["Mumbai","Pune","Nagpur","Nashik"],
    "Karnataka": ["Bengaluru Urban","Mysuru","Mangaluru"],
    "Tamil Nadu": ["Chennai","Coimbatore","Madurai","Salem"],
    "Telangana": ["Hyderabad","Warangal","Karimnagar"],
    "Gujarat": ["Ahmedabad","Surat","Vadodara","Rajkot"],
    "Rajasthan": ["Jaipur","Jodhpur","Udaipur","Kota"],
    "West Bengal": ["Kolkata","Howrah","Siliguri"],
    "Kerala": ["Thiruvananthapuram","Kochi","Kozhikode"],
}

CENTERS = {
    "Delhi": (28.61,77.21), "Uttar Pradesh": (26.85,80.95),
    "Maharashtra": (19.08,72.88), "Karnataka": (12.97,77.59),
    "Tamil Nadu": (13.08,80.27), "Telangana": (17.39,78.49),
    "Gujarat": (23.02,72.57), "Rajasthan": (26.91,75.79),
    "West Bengal": (22.57,88.36), "Kerala": (8.52,76.94)
}

def demo_reg(seed=42):
    rng=np.random.default_rng(seed)
    rows=[]
    factors={
        "Delhi":1.9,"Uttar Pradesh":1.0,"Maharashtra":1.7,"Karnataka":1.8,
        "Tamil Nadu":1.45,"Telangana":1.35,"Gujarat":1.3,"Rajasthan":.9,
        "West Bengal":1.0,"Kerala":1.2
    }
    for state,districts in STATES.items():
        lat0,lon0=CENTERS[state]
        for district in districts:
            pop0=int(rng.integers(7,40)*100000)
            ev0=max(500,int(pop0*.0025*factors[state]*rng.uniform(.75,1.35)))
            road=float(rng.uniform(35,95))
            act=float(rng.uniform(30,98))
            lat=lat0+rng.normal(0,.22); lon=lon0+rng.normal(0,.28)
            for year in range(2021,2027):
                ev=ev0*((1.12+.025*rng.random())**(year-2021))*rng.uniform(.95,1.06)
                pop=pop0*(1.012**(year-2021))*rng.uniform(.99,1.01)
                rows.append([
                    state,district,year,int(ev),int(pop),round(road,2),
                    round(act,2),round(lat,5),round(lon,5),"DEMO/SYNTHETIC"
                ])
    return pd.DataFrame(rows,columns=REG_COLS+["source"])

def demo_chargers(reg_df,seed=42):
    rng=np.random.default_rng(seed)
    latest=reg_df[reg_df.year==reg_df.year.max()]
    rows=[]; i=1
    for r in latest.itertuples():
        n=max(1,int(r.ev_count/rng.uniform(115,205)+r.activity_score/28))
        for _ in range(n):
            rows.append([
                f"DEMO-{i:05d}",r.state,r.district,
                float(r.latitude+rng.normal(0,.025)),
                float(r.longitude+rng.normal(0,.03)),
                "DEMO/SYNTHETIC"
            ])
            i+=1
    return pd.DataFrame(rows,columns=CHG_COLS+["source"])

def validate_reg(df):
    missing=[c for c in REG_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"vehicle_registrations.csv missing columns: {missing}")
    x=df.copy()
    for c in ["year","ev_count","population","road_score","activity_score","latitude","longitude"]:
        x[c]=pd.to_numeric(x[c],errors="coerce")
    x=x.dropna(subset=REG_COLS)
    x["ev_count"]=x.ev_count.clip(lower=0)
    x["population"]=x.population.clip(lower=1)
    x["road_score"]=x.road_score.clip(0,100)
    x["activity_score"]=x.activity_score.clip(0,100)
    return x

def validate_chg(df):
    missing=[c for c in CHG_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"chargers.csv missing columns: {missing}")
    x=df.copy()
    for c in ["latitude","longitude"]:
        x[c]=pd.to_numeric(x[c],errors="coerce")
    x=x.dropna(subset=CHG_COLS)
    return x[x.latitude.between(-90,90)&x.longitude.between(-180,180)]

def load_data():
    reg_path=DATA_DIR/"vehicle_registrations.csv"
    chg_path=DATA_DIR/"chargers.csv"
    if reg_path.exists():
        reg=validate_reg(pd.read_csv(reg_path)); reg_mode="REAL IMPORTED DATA"
    else:
        reg=demo_reg(); reg_mode="DEMO/SYNTHETIC"
    if chg_path.exists():
        chg=validate_chg(pd.read_csv(chg_path)); chg_mode="REAL IMPORTED DATA"
    else:
        chg=demo_chargers(reg); chg_mode="DEMO/SYNTHETIC"
    return reg,chg,reg_mode,chg_mode

def latest_snapshot(reg,chg):
    year=int(reg.year.max())
    s=reg[reg.year==year].copy()
    counts=chg.groupby(["state","district"]).size().reset_index(name="chargers")
    s=s.merge(counts,on=["state","district"],how="left")
    s["chargers"]=s["chargers"].fillna(0).astype(int)
    return s,year

def data_quality(reg,chg):
    return {
        "registration_rows": int(len(reg)),
        "charger_points": int(len(chg)),
        "states": int(reg.state.nunique()),
        "districts": int(reg.district.nunique()),
        "years": int(reg.year.nunique()),
        "start_year": int(reg.year.min()),
        "end_year": int(reg.year.max()),
        "registration_source": str(reg.source.iloc[0]) if "source" in reg else "UNKNOWN",
        "charger_source": str(chg.source.iloc[0]) if "source" in chg else "UNKNOWN",
    }
