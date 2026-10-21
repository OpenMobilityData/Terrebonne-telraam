#!/usr/bin/env python3
"""Fetch hourly counts for the two Terrebonne Telraam segments from the Telraam API and write them as CSV.

Modelled on BikeStat's scripts/refresh-telraam.sh (same endpoint, same request body). The API returns at most about
three months per request, so the range is fetched in 90-day chunks and merged. Output: data/api/<name>_<year>.csv,
one row per hour: date (local, America/Toronto), uptime, bike, bike_lft, bike_rgt, pedestrian, car, heavy, night, v85.
Rows are the API's "per-hour" report at level "segments"; "bike" is the daylight bicycle count (both directions).

Credentials: a config file outside git (default ~/.terrebonne-telraam.conf, chmod 600), one line per segment:
    # name   api_segment_id   api_token
    west     9000007290       <token>
    east     9000007489       <token>
Usage: python3 scripts/fetch_telraam.py --start=2024-08-15 [--end=today] [--config=path] [--names=west,east]
"""
import csv, json, os, sys, datetime as dt, urllib.request, urllib.error, collections
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data', 'api')
ENDPOINT = 'https://telraam-api.net/v1/reports/traffic'
TZ = ZoneInfo('America/Toronto')
FIELDS = ['date', 'uptime', 'bike', 'bike_lft', 'bike_rgt', 'pedestrian', 'car', 'heavy', 'night', 'v85']

def read_config(path):
    seg = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.split('#', 1)[0].split()
            if len(line) == 3: seg[line[0]] = (line[1], line[2])
    return seg

def fetch(seg_id, token, start, end):
    body = json.dumps({'level': 'segments', 'id': str(seg_id), 'format': 'per-hour',
                       'time_start': start.strftime('%Y-%m-%d %H:%M:%SZ'), 'time_end': end.strftime('%Y-%m-%d %H:%M:%SZ')}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={'X-Api-Key': token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def main(argv):
    opts = dict(a[2:].split('=', 1) for a in argv if a.startswith('--') and '=' in a)
    cfg = read_config(os.path.expanduser(opts.get('config', '~/.terrebonne-telraam.conf')))
    names = opts.get('names', ','.join(cfg)).split(',')
    start = dt.datetime.fromisoformat(opts['start']).replace(tzinfo=dt.timezone.utc)
    end = (dt.datetime.fromisoformat(opts['end']) if 'end' in opts else dt.datetime.utcnow()).replace(tzinfo=dt.timezone.utc, minute=0, second=0, microsecond=0)
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        seg_id, token = cfg[name]
        rows = {}
        t0 = start
        while t0 < end:
            t1 = min(t0 + dt.timedelta(days=90), end)
            try:
                rep = fetch(seg_id, token, t0, t1)
            except urllib.error.HTTPError as e:
                sys.exit(f'{name}: HTTP {e.code} for {t0:%Y-%m-%d}..{t1:%Y-%m-%d}: {e.read()[:200]!r}')
            if 'report' not in rep:
                sys.exit(f'{name}: unexpected response shape: {str(rep)[:200]}')
            for r in rep['report']:
                ts = dt.datetime.fromisoformat(r['date'].replace('Z', '+00:00')).astimezone(TZ)
                rows[ts] = {'date': ts.strftime('%Y-%m-%d %H:%M'), 'uptime': r.get('uptime'), 'bike': r.get('bike'), 'bike_lft': r.get('bike_lft'),
                            'bike_rgt': r.get('bike_rgt'), 'pedestrian': r.get('pedestrian'), 'car': r.get('car'), 'heavy': r.get('heavy'),
                            'night': r.get('night'), 'v85': r.get('v85')}
            print(f'{name}: {t0:%Y-%m-%d}..{t1:%Y-%m-%d}: {len(rep["report"])} rows')
            t0 = t1
        byyear = collections.defaultdict(list)
        for ts in sorted(rows): byyear[ts.year].append(rows[ts])
        for y, rs in byyear.items():
            p = os.path.join(OUT, f'{name}_{y}.csv')
            old = {}
            if os.path.exists(p):
                with open(p, encoding='utf-8') as f: old = {r['date']: r for r in csv.DictReader(f)}
            old.update({r['date']: r for r in rs})
            with open(p, 'w', encoding='utf-8', newline='') as f:
                w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
                for k in sorted(old): w.writerow(old[k])
            print(f'  wrote {p} ({len(old)} hours)')

if __name__ == '__main__':
    main(sys.argv[1:])
