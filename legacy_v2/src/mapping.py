import folium
from folium.plugins import MarkerCluster,HeatMap

def build(snapshot,chargers,candidates):
    m=folium.Map(location=[22.8,79.0],zoom_start=5,tiles='CartoDB positron')
    gap=folium.FeatureGroup(name='District gap'); ch=folium.FeatureGroup(name='Chargers'); rec=folium.FeatureGroup(name='Recommended zones'); heat=folium.FeatureGroup(name='EV demand heatmap')
    colors={'Very Low':'green','Low':'blue','Moderate':'orange','High':'red','Critical':'darkred'}
    for r in snapshot.itertuples():
        folium.CircleMarker([r.latitude,r.longitude],radius=8,color=colors.get(str(r.gap_level),'gray'),fill=True,fill_opacity=.75,popup=f'<b>{r.district}, {r.state}</b><br>EVs: {r.ev_count:,.0f}<br>Chargers: {r.chargers:,.0f}<br>EV/charger: {r.ev_per_charger:.1f}<br>Gap score: {r.gap_score:.1f}<br>Gap: {r.charger_gap:,.0f}').add_to(gap)
    cluster=MarkerCluster()
    for r in chargers.itertuples(): folium.CircleMarker([r.latitude,r.longitude],radius=3,color='black',fill=True,fill_opacity=.55).add_to(cluster)
    cluster.add_to(ch)
    for r in candidates.head(10).itertuples(): folium.Marker([r.latitude,r.longitude],popup=f'<b>#{r.rank} {r.district}, {r.state}</b><br>Priority score: {r.site_score:.1f}<br>{r.why_here}').add_to(rec)
    HeatMap([[r.latitude,r.longitude,max(float(r.ev_count),1)] for r in snapshot.itertuples()],radius=22,blur=18).add_to(heat)
    for layer in [gap,ch,rec,heat]: layer.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m
