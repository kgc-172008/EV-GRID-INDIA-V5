import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium
from src.data import load_reg,load_chg,latest_snapshot,quality
from src.analytics import gap,forecast,recommend
from src.mapping import build
from src.config import TARGET_EV_PER_CHARGER,GAP_WEIGHTS

st.set_page_config(page_title='EV-GRID INDIA',page_icon='⚡',layout='wide')
st.title('⚡ EV-GRID INDIA')
st.caption('From EV registrations to the next charging station — explainable planning intelligence.')
reg,reg_mode=load_reg(); chg,chg_mode=load_chg(reg); snap,year=latest_snapshot(reg,chg)
with st.sidebar:
    st.header('Planning Controls'); target=st.slider('Target EVs per charger',50,500,TARGET_EV_PER_CHARGER,10)
    states=['All India']+sorted(snap.state.unique()); state=st.selectbox('State',states)
view=snap if state=='All India' else snap[snap.state==state].copy(); view=gap(view,target,chg)
if 'DEMO' in reg_mode or 'DEMO' in chg_mode: st.warning('DEMO MODE: bundled numbers are synthetic. Replace data/vehicle_registrations.csv and data/chargers.csv with documented real/open data.')
else: st.success('REAL/IMPORTED DATA MODE')
cols=st.columns(5); cols[0].metric('EV registrations',f'{view.ev_count.sum():,.0f}'); cols[1].metric('Chargers',f'{view.chargers.sum():,.0f}'); cols[2].metric('EV / charger',f'{view.ev_count.sum()/max(view.chargers.sum(),1):,.1f}'); cols[3].metric('High/Critical zones',str(int(view.gap_level.isin(['High','Critical']).sum()))); cols[4].metric('Estimated extra chargers',f'{view.charger_gap.sum():,.0f}')
t1,t2,t3,t4,t5,t6,t7=st.tabs(['National Map','Gap Intelligence','Forecast','AI Recommendations','Scenario','Data Quality','Methodology'])
with t1:
    rec=recommend(view); st_folium(build(view,chg,rec),use_container_width=True,height=650)
with t2:
    tab=view[['state','district','ev_count','chargers','ev_per_charger','required_chargers','charger_gap','nearest_charger_km','gap_score','gap_level']].sort_values('gap_score',ascending=False)
    st.dataframe(tab,use_container_width=True,hide_index=True); st.download_button('Download district intelligence',tab.to_csv(index=False).encode(),'district_intelligence.csv','text/csv')
    st.plotly_chart(px.bar(tab.head(15).sort_values('gap_score'),x='gap_score',y='district',color='gap_level',orientation='h',title='Top underserved zones'),use_container_width=True)
with t3:
    try:
        h=st.slider('Forecast horizon',1,7,5); fut,met=forecast(reg,h)
        a,b,c=st.columns(3); a.metric(f"MAE — holdout {met['holdout_year']}",f"{met['MAE']:,.0f}"); b.metric('RMSE',f"{met['RMSE']:,.0f}"); c.metric('R²',f"{met['R2']:.3f}")
        fv=fut if state=='All India' else fut[fut.state==state]; agg=fv.groupby('year',as_index=False).predicted_ev.sum(); st.plotly_chart(px.line(agg,x='year',y='predicted_ev',markers=True,title=f'EV forecast — {state}'),use_container_width=True)
        last=fv[fv.year==fv.year.max()].copy(); last['required_chargers']=np.ceil(last.predicted_ev/target).astype(int); last['additional_chargers']=(last.required_chargers-last.chargers).clip(lower=0); st.dataframe(last[['state','district','year','predicted_ev','chargers','required_chargers','additional_chargers']].sort_values('additional_chargers',ascending=False),use_container_width=True,hide_index=True)
    except Exception as e: st.error(str(e))
with t4:
    rec=recommend(view); 
    for _,r in rec.head(10).iterrows():
        with st.container(border=True):
            l,m,rcol=st.columns([1,4,2]); l.metric('Rank',int(r['rank'])); m.markdown(f"### {r['district']}, {r['state']}"); m.write(f"**Why here:** {r['why_here']}"); rcol.metric('Priority score',f"{r['site_score']:.1f}")
    st.download_button('Download ranked recommendations',rec.to_csv(index=False).encode(),'ranked_recommendations.csv','text/csv')
with t5:
    st.subheader('What happens under different growth assumptions?'); yrs=st.slider('Years ahead',1,10,5); low=st.slider('Low growth %',0.,30.,8.,.5); base=st.slider('Base growth %',0.,30.,15.,.5); high=st.slider('High growth %',0.,40.,22.,.5)
    current=float(view.ev_count.sum()); chargers=int(view.chargers.sum()); rows=[]
    for name,g in [('Low',low),('Base',base),('High',high)]:
        pev=current*((1+g/100)**yrs); req=int(np.ceil(pev/target)); rows.append([name,g,pev,req,max(0,req-chargers)])
    s=pd.DataFrame(rows,columns=['Scenario','Growth %','Projected EVs','Required Chargers','Additional Chargers']); st.dataframe(s,use_container_width=True,hide_index=True); st.plotly_chart(px.bar(s,x='Scenario',y='Additional Chargers',text_auto=True,title=f'Additional chargers in +{yrs} years'),use_container_width=True)
with t6:
    q=quality(reg,chg); a,b,c,d=st.columns(4); a.metric('Registration rows',f"{q['reg_rows']:,}"); b.metric('Charger points',f"{q['charger_points']:,}"); c.metric('Districts',str(q['districts'])); d.metric('Years',str(q['years'])); st.write({'vehicle_registrations':reg_mode,'chargers':chg_mode,'registration_range':f"{q['start']}–{q['end']}"}); st.markdown('**Readiness rule:** every real dataset should carry source/provenance and retrieval date; synthetic data must stay labeled.')
with t7:
    st.markdown('### Transparent model'); st.write('Gap Score = 35% EV demand + 20% EV/chg pressure + 15% population + 15% road/mobility + 10% activity + 5% access pressure. These are prototype weights, not official government weights.')
    st.write('Forecasting uses a Random Forest baseline with chronological holdout validation. Charger requirement = ceil(predicted EVs / configurable target EVs per charger).')
    st.write('District-zone ranking is a planning recommendation. Final deployment still requires land, grid capacity, traffic access, safety, permissions and cost checks.')
    st.markdown('### Official/open-data starting points'); st.markdown('- VAHAN Public Dashboard: https://www.analytics.parivahan.gov.in/analytics/publicdashboard/vahan\n- Open Charge Map API: https://openchargemap.org/develop\n- Census Population Finder: https://censusindia.gov.in/census.website/en/data/population-finder')
st.caption(f'EV-GRID INDIA v2 | Latest registration year: {year}')
