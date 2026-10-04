import heapq
import math
from collections import defaultdict
import numpy as np

def haversine_km(lat1, lon1, lat2, lon2):
    R=6371.0
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1)
    dl=math.radians(lon2-lon1)
    z=math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(z))

def dijkstra(graph, start, goal):
    q=[(0,start)]
    dist={start:0}
    prev={}
    while q:
        d,u=heapq.heappop(q)
        if u==goal: break
        if d!=dist.get(u): continue
        for v,w in graph.get(u,[]):
            nd=d+w
            if nd<dist.get(v,float("inf")):
                dist[v]=nd; prev[v]=u
                heapq.heappush(q,(nd,v))
    return _reconstruct(prev,start,goal,dist.get(goal,float("inf")))

def astar(graph, coords, start, goal):
    q=[(0,start)]
    g={start:0}; prev={}
    def h(a,b):
        la,loa=coords[a]; lb,lob=coords[b]
        return haversine_km(la,loa,lb,lob)
    while q:
        _,u=heapq.heappop(q)
        if u==goal: break
        for v,w in graph.get(u,[]):
            ng=g[u]+w
            if ng<g.get(v,float("inf")):
                g[v]=ng; prev[v]=u
                heapq.heappush(q,(ng+h(v,goal),v))
    return _reconstruct(prev,start,goal,g.get(goal,float("inf")))

def _reconstruct(prev,start,goal,cost):
    if goal!=start and goal not in prev:
        return {"reachable":False,"cost":None,"path":[]}
    path=[goal]
    while path[-1]!=start:
        path.append(prev[path[-1]])
    path.reverse()
    return {"reachable":True,"cost":cost,"path":path}

def priority_queue_rank(items, score_key="score"):
    heap=[(-float(x[score_key]),i,x) for i,x in enumerate(items)]
    heapq.heapify(heap)
    out=[]
    while heap:
        _,_,x=heapq.heappop(heap)
        out.append(x)
    return out

def kd_nearest(points, query, k=5):
    # SciPy KD-tree when available; brute-force fallback keeps the API portable.
    try:
        from scipy.spatial import cKDTree
        arr=np.asarray(points,float)
        tree=cKDTree(arr)
        _,idx=tree.query(np.asarray(query,float),k=min(k,len(arr)))
        return np.atleast_1d(idx).tolist()
    except Exception:
        q=np.asarray(query,float)
        d=[float(np.linalg.norm(np.asarray(p)-q)) for p in points]
        return list(np.argsort(d)[:k])

def greedy_site_selection(candidates, budget):
    selected=[]
    used=set()
    for c in sorted(candidates,key=lambda x: x.get("site_score",0),reverse=True):
        key=(c.get("state"),c.get("district"))
        if key in used: continue
        selected.append(c); used.add(key)
        if len(selected)>=budget: break
    return selected
