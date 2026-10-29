#!/usr/bin/env python3
"""Derived CSVs from the hourly Telraam data, for downstream builds (the poster, the figures):
  derived/daily.csv            one row per sensor and day: date, segment, hours, uptime_hours, bikes, cars, valid (>= 8 h, >= 6 h uptime)
  derived/speeds_by_season.csv one row per sensor and season: V85 median over daylight hours with >= 20 cars, middle half,
                               cars counted, share over 30 km/h, share over 40 km/h (winter = Dec–Mar, summer = Jun–Aug, shoulder = the rest)
Input: data/api/<west|east>_<year>.csv if present, else the dashboard exports raw-data-20YY{East,West}60.xlsx (private; see _raw_dir).
Usage: python3 scripts/telraam_summaries.py
"""
import csv, glob, os, re, datetime as dt, collections, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
# The Telraam exports are not in this repository (Telraam owns the counts; see the README, « Data and licence »):
# they are read from TELRAAM_RAW, else the owner's private copy, else data/raw/ beside this repository.
def _raw_dir(here):
    for d in (os.environ.get('TELRAAM_RAW', ''), os.path.expanduser('~/GitHub/Terrebonne-private/data/telraam/raw'), os.path.join(here, '..', 'data', 'raw')):
        if d and os.path.isdir(d): return d
    return os.path.join(here, '..', 'data', 'raw')
SEG = {'west': 'King Edward', 'east': 'Draper'}
BINS = ['Speed Car 0-10 km/h (%)', 'Speed Car 10-20 km/h (%)', 'Speed Car 20-30 km/h (%)', 'Speed Car 30-40 km/h (%)', 'Speed Car 40-50 km/h (%)', 'Speed Car 50-60 km/h (%)', 'Speed Car 60-70 km/h (%)', 'Speed Car 70+ km/h (%)']
def uptime(v):
    if v is None: return 0.0
    if isinstance(v, (int, float)): return float(v)
    m = re.search(r'([0-9]*\.?[0-9]+)\s*$', str(v)); return float(m.group(1)) if m else 0.0
def season(d): return 'winter' if d.month in (12, 1, 2, 3) else 'summer' if d.month in (6, 7, 8) else 'shoulder'
def hourly(seg):
    """yield (datetime, uptime, bikes, cars, v85, [pct bins] or None)"""
    api = sorted(glob.glob(os.path.join(ROOT, 'data', 'api', f'{seg}_20*.csv')))
    if api:
        for f in api:
            with open(f, encoding='utf-8') as fh:
                for r in csv.DictReader(fh):
                    yield dt.datetime.fromisoformat(r['date']), uptime(r['uptime']), int(float(r['bike'] or 0)), int(float(r['car'] or 0)), float(r['v85']) if r.get('v85') else None, None
        return
    import openpyxl
    for f in sorted(glob.glob(os.path.join(_raw_dir(HERE), f'raw-data-20*{seg.capitalize()}60.xlsx'))):
        ws = openpyxl.load_workbook(f, read_only=True, data_only=True).active
        it = ws.iter_rows(values_only=True); hdr = next(it); ix = {h: i for i, h in enumerate(hdr)}
        for r in it:
            t = r[ix['Date and Time (Local)']]
            if t is None: continue
            if isinstance(t, str): t = dt.datetime.fromisoformat(t)
            v = r[ix['Speed V85 km/h']]
            try: v = float(v) if v not in (None, '') else None
            except (TypeError, ValueError): v = None
            pct = [float(r[ix[b]] or 0) for b in BINS]
            yield t, uptime(r[ix['Uptime']]), int(r[ix['Bike Total']] or 0), int(r[ix['Car Total']] or 0), v, (pct if sum(pct) > 0 else None)
def main():
    daily_rows, speed_rows = [], []
    for seg, name in SEG.items():
        day = collections.defaultdict(lambda: [0, 0.0, 0, 0]); v85 = collections.defaultdict(list)
        cars = collections.Counter(); over30 = collections.Counter(); over40 = collections.Counter()
        for t, u, b, c, v, pct in hourly(seg):
            d = t.date(); day[d][0] += 1; day[d][1] += u; day[d][2] += b; day[d][3] += c
            if c >= 20 and v:
                s = season(d); v85[s].append(v)
                if pct: cars[s] += c; over30[s] += c * sum(pct[3:]) / 100; over40[s] += c * sum(pct[4:]) / 100
        for d in sorted(day):
            h, u, b, c = day[d]; daily_rows.append({'date': d.isoformat(), 'segment': seg, 'location': name, 'hours': h, 'uptime_hours': round(u, 2), 'bikes': b, 'cars': c, 'valid': int(h >= 8 and u >= 6)})
        for s in ('winter', 'summer', 'shoulder'):
            if v85[s]:
                q = st.quantiles(v85[s], n=4)
                speed_rows.append({'segment': seg, 'location': name, 'season': s, 'hours': len(v85[s]), 'v85_median': round(st.median(v85[s]), 1), 'v85_q1': round(q[0], 1), 'v85_q3': round(q[2], 1),
                                   'cars_counted': int(cars[s]), 'share_over_30': round(100 * over30[s] / cars[s], 1) if cars[s] else '', 'share_over_40': round(100 * over40[s] / cars[s], 1) if cars[s] else ''})
    os.makedirs(os.path.join(ROOT, 'derived'), exist_ok=True)
    for name, rows in (('daily.csv', daily_rows), ('speeds_by_season.csv', speed_rows)):
        with open(os.path.join(ROOT, 'derived', name), 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print('wrote derived/' + name, len(rows), 'rows')
if __name__ == '__main__':
    main()
