import json, urllib.request
from datetime import datetime, timezone

LAT=-37.8016
LON=174.8711
TZ="Pacific/Auckland"

marine_url=(
    "https://marine-api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}&timezone={urllib.parse.quote(TZ)}"
    "&forecast_days=2&hourly=wave_height,wave_period,sea_level_height_msl"
)
wind_url=(
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}&timezone={urllib.parse.quote(TZ)}"
    "&forecast_days=2&hourly=wind_speed_10m,wind_direction_10m"
)

def get(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)

import urllib.parse
m=get(marine_url)
w=get(wind_url)

times=m["hourly"]["time"]
now=datetime.now(timezone.utc)
start=0
for i,t in enumerate(times):
    dt=datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
    if dt>=now:
        start=i
        break

end=min(start+12,len(times))
tides=[v for v in m["hourly"]["sea_level_height_msl"][start:end] if v is not None]
tmin=min(tides) if tides else 0
tmax=max(tides) if tides else 1

def direction(deg):
    if deg is None: return "--"
    return ["N","NE","E","SE","S","SW","W","NW"][round(deg/45)%8]

def score(wave,period,wind):
    s=3 if wave>=1.2 else 2 if wave>=0.7 else 1
    s+=3 if period>=12 else 2 if period>=10 else 1 if period>=8 else 0
    s+=2 if wind<=12 else 1 if wind<=20 else -2
    return s

rows=[]
for i in range(start,end):
    wave=m["hourly"]["wave_height"][i]
    period=m["hourly"]["wave_period"][i]
    wind=w["hourly"]["wind_speed_10m"][i]
    wd=w["hourly"]["wind_direction_10m"][i]
    tide=m["hourly"]["sea_level_height_msl"][i]
    pct=50 if tide is None or tmax<=tmin else max(8,min(100,round((tide-tmin)/(tmax-tmin)*100)))
    rows.append({
        "time":times[i],
        "wave_ft":round(wave*3.28084+5) if wave is not None else None,
        "period":round(period) if period is not None else None,
        "wind_kmh":round(wind) if wind is not None else None,
        "wind_dir":direction(wd),
        "tide_pct":pct,
        "face":"😍" if score(wave or 0,period or 0,wind if wind is not None else 99)>=7 else "🙂" if score(wave or 0,period or 0,wind if wind is not None else 99)>=4 else "🤯"
    })

with open("forecast.json","w",encoding="utf-8") as f:
    json.dump({"updated_utc":datetime.now(timezone.utc).isoformat(),"rows":rows},f,ensure_ascii=False,indent=2)
