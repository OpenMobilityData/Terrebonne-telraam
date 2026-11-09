#!/usr/bin/env python3
"""Mode shares and daily counts by mode, winter and non-winter, for every counter on rue de Terrebonne.

Counters: the two Telraam S2 sensors (King Edward = the western portion, one-way westbound; Draper = the eastern
portion, one-way eastbound), four daylight classes (pedestrian, bike, car, heavy); and, for comparison on its own
panel, the borough's Eco-Counter loop at Kensington (bicycles and motor vehicles, 24 h, from the public
Terrebonne-access-requests repository). Telraam levels and loop levels are never drawn on one axis: the Telraam
sensors count in daylight only (night traffic is an undifferentiated "Night" class and is left out of every share).

Winter definition (--winter): nov16 = November 16 to March 31 (the City's official winter period for bike lanes,
default); dec1 = December 1 to March 31 (the window the borough proposes for the conversion). The rest of the
year, April 1 to the day before winter starts, is the non-winter period.

Valid day: at least MIN_HOURS reported hours and MIN_UPTIME hours of summed uptime (Telraam); a non-zero day
(loop; June 7, 2026, a counter-fault value, is also left out). All shares and daily means are over valid days.

Output (per winter definition): derived/mode-shares/<def>/{monthly,weekly,periods}_<counter>.csv and
figures/mode-shares/<def>/: shares_<counter>_<period>.png|svg (share of each mode by month, with the period total),
counts_<counter>_<period>.png|svg (mean daily count per mode by month), overview_<counter>.png|svg (weekly
bicycles and cars per valid day over the whole record, winters shaded, coverage strip) and yoy_<counter>.png|svg (+ derived yoy_<counter>.csv:
same calendar month year over year on the dates valid in every year shown). Months with fewer than
THIN_DAYS valid days are marked † and drawn lighter.

Usage: python3 scripts/telraam_mode_shares.py [--winter=nov16|dec1|both]   (needs openpyxl, matplotlib)
"""
import csv, glob, os, re, sys, datetime as dt, collections, textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
# The Telraam exports are not in this repository (Telraam owns the counts; see the README, « Data and licence »):
# they are read from TELRAAM_RAW, else the owner's private copy, else data/raw/ beside this repository.
def _raw_dir(here):
    for d in (os.environ.get('TELRAAM_RAW', ''), os.path.expanduser('~/GitHub/Terrebonne-private/data/telraam/raw'), os.path.join(here, '..', 'data', 'raw')):
        if d and os.path.isdir(d): return d
    return os.path.join(here, '..', 'data', 'raw')
LOOP_CSV = os.environ.get('KENSINGTON_DAILY', os.path.expanduser('~/GitHub/Terrebonne-access-requests/2026-581/derived/kensington_daily_borough_release_2025-07_2026-08.csv'))
LOOP_EXCLUDE = {dt.date(2026, 6, 7): 'counter-fault value (3,035), see the 2026-581 README'}

MIN_HOURS, MIN_UPTIME, THIN_DAYS = 8, 6.0, 7
WINTERS = {'nov16': ((11, 16), 'November 16 to March 31'), 'dec1': ((12, 1), 'December 1 to March 31')}
INK, MUTED, GRID, AXIS = '#1f2428', '#5f6b74', '#e2e4e1', '#c9cdd2'
# categorical hues in fixed order, validated (dataviz skill): pedestrian blue, bike aqua, car orange, heavy violet
MODES = [('pedestrian', 'Pedestrians', '#2a78d6'), ('bike', 'Bicycles', '#1baf7a'), ('car', 'Cars', '#eb6834'), ('heavy', 'Heavy vehicles', '#6250d6')]
LOOP_MODES = [('bike', 'Bicycles', '#1baf7a'), ('motor', 'Motor vehicles', '#eb6834')]
COUNTERS = {  # slug: (title, Telraam segment or None, source line, modes)
    'west': ('King Edward (western portion, west of Cavendish)', 13374, None, MODES),
    'east': ('Draper (eastern portion, east of Cavendish)', 13690, None, MODES),
    'kensington': ('Kensington (borough loop counter, 24 h)', None, None, LOOP_MODES),
}

def uptime(v):
    if v is None: return 0.0
    if isinstance(v, (int, float)): return float(v)
    m = re.search(r'([0-9]*\.?[0-9]+)\s*$', str(v)); return float(m.group(1)) if m else 0.0

def telraam_daily(seg):
    """{date: {'hours', 'uptime', 'pedestrian', 'bike', 'car', 'heavy', 'night'}} from the API CSVs or the dashboard exports"""
    day = collections.defaultdict(lambda: collections.Counter())
    api = sorted(glob.glob(os.path.join(ROOT, 'data', 'api', f'{seg}_20*.csv')))
    if api:
        for f in api:
            with open(f, encoding='utf-8') as fh:
                for r in csv.DictReader(fh):
                    d = dt.datetime.fromisoformat(r['date']).date(); c = day[d]
                    c['hours'] += 1; c['uptime'] += uptime(r['uptime'])
                    for k in ('pedestrian', 'bike', 'car', 'heavy', 'night'): c[k] += int(float(r[k] or 0))
        return day
    import openpyxl
    cols = {'pedestrian': 'Pedestrian Total', 'bike': 'Bike Total', 'car': 'Car Total', 'heavy': 'Large vehicle Total', 'night': 'Night Total'}
    for f in sorted(glob.glob(os.path.join(_raw_dir(HERE), f'raw-data-20*{seg.capitalize()}60.xlsx'))):
        ws = openpyxl.load_workbook(f, read_only=True, data_only=True).active
        it = ws.iter_rows(values_only=True); hdr = next(it); ix = {h: i for i, h in enumerate(hdr)}
        for r in it:
            t = r[ix['Date and Time (Local)']]
            if t is None: continue
            if isinstance(t, str): t = dt.datetime.fromisoformat(t)
            c = day[t.date()]; c['hours'] += 1; c['uptime'] += uptime(r[ix['Uptime']])
            for k, h in cols.items(): c[k] += int(r[ix[h]] or 0)
    return day

def loop_daily():
    day = {}
    if not os.path.isfile(LOOP_CSV): print('loop counter file not found, skipped:', LOOP_CSV); return day
    with open(LOOP_CSV, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            d = dt.date.fromisoformat(r['date']); b, m = int(float(r['bike'])), int(float(r['motor']))
            day[d] = collections.Counter({'hours': 24, 'uptime': 24.0, 'bike': b, 'motor': m, 'excluded': int(d in LOOP_EXCLUDE or (b == 0 and m == 0) or b == 0)})
    return day

def valid(c, loop):
    if loop: return not c.get('excluded')
    return c['hours'] >= MIN_HOURS and c['uptime'] >= MIN_UPTIME

def period_of(d, start):
    """(slug, label, first day, last day) of the winter / non-winter period holding d"""
    m, dd = start
    if (d.month, d.day) >= (m, dd): y = d.year
    elif d <= dt.date(d.year, 3, 31): y = d.year - 1
    else:
        a, b = dt.date(d.year, 4, 1), dt.date(d.year, m, dd) - dt.timedelta(1)
        return f'non-winter-{d.year}', f'Non-winter {d.year} (April 1 to {b:%B %-d})', a, b
    a, b = dt.date(y, m, dd), dt.date(y + 1, 3, 31)
    return f'winter-{y}-{str(y + 1)[2:]}', f'Winter {y}–{str(y + 1)[2:]} ({a:%B %-d} to March 31)', a, b

def month_label(ym): return dt.date(ym[0], ym[1], 1).strftime('%b %Y')

def aggregate(daily, modes, keyf):
    """{key: Counter(valid_days, days_reported, hours, <mode> totals)} over valid days only"""
    out = collections.defaultdict(collections.Counter)
    for d, c in daily.items():
        k = keyf(d); out[k]['days_reported'] += 1
        if not c['_valid']: continue
        out[k]['valid_days'] += 1; out[k]['hours'] += c['hours']
        for m, _, _ in modes: out[k][m] += c[m]
    return out

def shares(c, modes):
    tot = sum(c[m] for m, _, _ in modes)
    return {m: (100.0 * c[m] / tot if tot else 0.0) for m, _, _ in modes}, tot

def write_csv(path, rows):
    if not rows: return
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def table_rows(agg, modes, labelf, extra):
    rows = []
    for k in sorted(agg):
        c = agg[k]; sh, tot = shares(c, modes); n = c['valid_days']
        r = collections.OrderedDict(); r.update(labelf(k)); r.update(extra(k))
        r['days_reported'] = c['days_reported']; r['valid_days'] = n; r['hours_counted'] = c['hours']
        for m, _, _ in modes: r[f'{m}_total'] = c[m]
        for m, _, _ in modes: r[f'{m}_per_day'] = round(c[m] / n, 1) if n else ''
        for m, _, _ in modes: r[f'{m}_share_pct'] = round(sh[m], 1) if n else ''
        mv = 'car' if any(m == 'car' for m, _, _ in modes) else 'motor'
        r[f'bikes_per_100_{mv}s' if mv == 'car' else 'bikes_per_100_motor'] = round(100.0 * c['bike'] / c[mv], 1) if c[mv] else ''
        rows.append(r)
    return rows

def chrome(ax):
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
    ax.spines['left'].set_color(AXIS); ax.spines['bottom'].set_color(AXIS); ax.tick_params(colors=MUTED, length=0)
    ax.set_axisbelow(True)

def footer(fig, counter, first, last, loop):
    if loop:
        txt = (f'Source: the borough\'s Eco-Counter loop at Terrebonne/Kensington, daily totals released under access request 2026-581 (bundle 01, pp. 74–81), '
               f'{first:%B %-d, %Y} to {last:%B %-d, %Y}; 24-hour counts, both directions. Zero days (outage, May 29–31, 2026) and the June 7, 2026 counter-fault value are left out; '
               'the westbound bicycle channel is degraded from about March 1, 2026, so bicycle figures from then on are lower bounds. Not comparable in level with the Telraam sensors.')
    else:
        seg = COUNTERS[counter][1]
        txt = (f'Source: Telraam S2 sensor (segment {seg}) operated by a resident, hourly data from {first:%B %-d, %Y} to {last:%B %-d, %Y}. '
               f'Valid day = at least {MIN_HOURS} reported hours and {MIN_UPTIME:.0f} h of uptime; shares and means are over valid days only. '
               'The sensor classifies in daylight only (night traffic is an undifferentiated class, left out here), so these are daylight shares and daylight counts, both directions; '
               'levels are not comparable with the borough\'s 24-hour loop counter. Counts: Telraam.')
    fig.text(0.06, 0.012, txt, fontsize=7.0, color=MUTED, wrap=True)

def fig_shares(counter, title, modes, months, agg, period_label, period_total, out, first, last, loop, wdef):
    """100 % stacked horizontal bars, one row per month, plus the period total row"""
    rows = [(month_label(k), agg[k]) for k in months] + [('Whole period', period_total)]
    n = len(rows); h = 1.5 + 0.42 * n + 1.9
    fig, ax = plt.subplots(figsize=(10, h), dpi=150)
    ys = list(range(n))[::-1]
    for y, (lab, c) in zip(ys, rows):
        sh, tot = shares(c, modes); thin = c['valid_days'] < THIN_DAYS; left = 0.0
        alpha = 0.45 if thin else 1.0
        for m, name, col in modes:
            w = sh[m]
            if w <= 0: continue
            ax.barh(y, w, left=left, height=0.62 if lab != 'Whole period' else 0.78, color=col, alpha=alpha, edgecolor='#fcfcfb', linewidth=1.5)
            big = lab == 'Whole period'
            if w >= 3.5: ax.text(left + w / 2, y, f'{w:.0f}%', ha='center', va='center', fontsize=(8.2 if w >= 7 else 7.2) if not big else 9, color='white', fontweight='bold' if big else 'normal')
            elif m == 'bike':   # the subject of the chart is always labelled: above the segment when it is too narrow
                ax.text(left + w / 2, y + (0.42 if big else 0.34), f'{w:.1f}%', ha='center', va='bottom', fontsize=7.2, color=col, fontweight='bold' if big else 'normal')
            left += w
        ax.text(101, y, f'{c["valid_days"]} d{"†" if thin else ""}', va='center', fontsize=8, color=MUTED)
    ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], fontsize=9.5, color=INK)
    ax.get_yticklabels()[-1].set_fontweight('bold')
    ax.set_xlim(0, 108); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(['0', '25', '50', '75', '100 %'], fontsize=8.5)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8); chrome(ax); ax.spines['left'].set_visible(False)
    ax.axhline(0.5, color=AXIS, linewidth=0.8)
    ax.legend(handles=[Patch(color=col, label=name) for _, name, col in modes], loc='lower left', bbox_to_anchor=(0, 1.01), ncol=len(modes), frameon=False, fontsize=8.5, handlelength=1.2, borderaxespad=0)
    basis = 'Share of all vehicles counted, 24 h' if loop else 'Share of everything the sensor classified in daylight'
    fig.suptitle(f'{period_label}: {"what the loop counted" if loop else "who used the street"}\nrue de Terrebonne at {title}', x=0.06, ha='left', fontsize=10.5, fontweight='bold', color=INK, y=0.995, linespacing=1.3)
    ax.set_title(textwrap.fill(f'{basis}, by month and for the whole period (right: valid days; † fewer than {THIN_DAYS}, drawn lighter). Winter = {WINTERS[wdef][1]}; a month cut by the winter boundary is shown whole, in the period holding most of it; the period row is over the period\'s exact days.', 125), loc='left', fontsize=8, color=MUTED, pad=24, linespacing=1.3)
    footer(fig, counter, first, last, loop)
    fig.subplots_adjust(left=0.17, right=0.95, top=1 - 1.25 / h, bottom=1.2 / h)
    for ext in ('png', 'svg'): fig.savefig(f'{out}.{ext}')
    plt.close(fig)

def fig_counts(counter, title, modes, months, agg, period_label, period_total, out, first, last, loop, wdef):
    """grouped bars: mean count per valid day, by mode and month, with the period mean as the last group"""
    keys = months + ['Whole period']; n = len(keys); k = len(modes); bw = 0.8 / k
    fig, ax = plt.subplots(figsize=(max(8.5, 1.6 + 0.9 * n), 5.6), dpi=150)
    top = 0
    for j, (m, name, col) in enumerate(modes):
        xs, vals, alphas = [], [], []
        for i, key in enumerate(keys):
            c = period_total if key == 'Whole period' else agg[key]; nd = c['valid_days']
            v = c[m] / nd if nd else 0; vals.append(v); xs.append(i - 0.4 + bw * (j + 0.5)); alphas.append(0.45 if nd < THIN_DAYS else 1.0)
            top = max(top, v)
        for x, v, a in zip(xs, vals, alphas): ax.bar(x, v, width=bw * 0.92, color=col, alpha=a, zorder=3)
    labs = []
    for i, key in enumerate(keys):
        c = period_total if key == 'Whole period' else agg[key]; nd = c['valid_days']
        labs.append((month_label(key) if key != 'Whole period' else 'Whole period') + f'\n{nd} d{"†" if nd < THIN_DAYS else ""}')
        if key == 'Whole period': ax.axvspan(i - 0.5, i + 0.5, color='#f1f2ef', zorder=0)
    ax.set_xticks(range(n)); ax.set_xticklabels(labs, fontsize=8.5, color=INK, linespacing=1.4)
    ax.set_xlim(-0.6, n - 0.4); ax.set_ylim(0, top * 1.15)
    ax.set_ylabel('mean count per valid day' + ('' if loop else ' (daylight)'), fontsize=9.5, color=MUTED)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0); chrome(ax)
    ax.legend(handles=[Patch(color=col, label=name) for _, name, col in modes], loc='lower left', bbox_to_anchor=(0, 1.01), ncol=k, frameon=False, fontsize=8.5, handlelength=1.2, borderaxespad=0)
    fig.suptitle(f'{period_label}: daily counts by mode\nrue de Terrebonne at {title}', x=0.06, ha='left', fontsize=10.5, fontweight='bold', color=INK, y=0.995, linespacing=1.3)
    ax.set_title(textwrap.fill(f'Mean per valid day, by month and for the whole period (under each month: valid days; † fewer than {THIN_DAYS}, drawn lighter). Winter = {WINTERS[wdef][1]}; a month cut by the winter boundary is shown whole, in the period holding most of it; the period group is over the period\'s exact days.', 125), loc='left', fontsize=8, color=MUTED, pad=24, linespacing=1.3)
    footer(fig, counter, first, last, loop)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.78, bottom=0.25)
    for ext in ('png', 'svg'): fig.savefig(f'{out}.{ext}')
    plt.close(fig)

def fig_overview(counter, title, modes, daily, start, out, first, last, loop, wdef):
    """weekly bicycles and cars (or motor vehicles) per valid day over the whole record; winters shaded; coverage strip"""
    mv = 'motor' if loop else 'car'
    weeks = aggregate(daily, modes, lambda d: d - dt.timedelta(d.weekday()))
    ks = sorted(weeks); xs = [k + dt.timedelta(3) for k in ks]
    bike = [weeks[k]['bike'] / weeks[k]['valid_days'] if weeks[k]['valid_days'] else float('nan') for k in ks]
    cars = [weeks[k][mv] / weeks[k]['valid_days'] if weeks[k]['valid_days'] else float('nan') for k in ks]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 6.4), dpi=150, sharex=True, gridspec_kw={'height_ratios': [5, 1], 'hspace': 0.08})
    # winters shaded
    for y in range(first.year - 1, last.year + 1):
        a, b = dt.date(y, *start), dt.date(y + 1, 3, 31)
        if b < first or a > last: continue
        for a_ in (ax, ax2): a_.axvspan(max(a, first - dt.timedelta(3)), min(b, last + dt.timedelta(3)), color='#eef0f4', zorder=0)
        ax.text(max(a, first) + (min(b, last) - max(a, first)) / 2, 0.97, f'winter {y}–{str(y + 1)[2:]}', transform=ax.get_xaxis_transform(), ha='center', va='top', fontsize=8, color=MUTED)
    cb, cc = dict((m, col) for m, _, col in modes)['bike'], dict((m, col) for m, _, col in modes)[mv]
    ax.plot(xs, cars, color=cc, linewidth=2, marker='o', markersize=3.2, label='Cars' if not loop else 'Motor vehicles', zorder=3)
    ax.plot(xs, bike, color=cb, linewidth=2, marker='o', markersize=3.2, label='Bicycles', zorder=4)
    ax.set_ylim(0, None); ax.set_ylabel('per valid day, weekly mean' + ('' if loop else ' (daylight)'), fontsize=9.5, color=MUTED)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0); chrome(ax); ax.spines['bottom'].set_visible(False)
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.01), ncol=2, frameon=False, fontsize=8.5, handlelength=1.6, borderaxespad=0)
    ax2.bar(xs, [weeks[k]['valid_days'] for k in ks], width=6, color='#9aa3ab', zorder=3)
    ax2.set_ylim(0, 7.6); ax2.set_yticks([0, 7]); ax2.set_ylabel('valid\ndays', fontsize=8, color=MUTED, rotation=0, ha='right', va='center')
    chrome(ax2); ax2.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax2.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=[1, 4, 7, 10])); ax2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b\n%Y'))
    ax2.xaxis.set_minor_locator(matplotlib.dates.MonthLocator()); ax2.tick_params(axis='x', labelsize=8.5)
    fig.suptitle(f'Bicycles and {"motor vehicles" if loop else "cars"} week by week\nrue de Terrebonne at {title}', x=0.06, ha='left', fontsize=10.5, fontweight='bold', color=INK, y=0.995, linespacing=1.3)
    ax.set_title(f'Weekly mean per valid day (weeks with no valid day leave a gap); shaded = winter, {WINTERS[wdef][1]}; bottom strip = valid days in the week (coverage).', loc='left', fontsize=8, color=MUTED, pad=26)
    footer(fig, counter, first, last, loop)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.84, bottom=0.2)
    for ext in ('png', 'svg'): fig.savefig(f'{out}.{ext}')
    plt.close(fig)
    return weeks

YOY_MIN_DATES = 15
YEAR_SHADES = {2024: '#86b6ef', 2025: '#2a78d6', 2026: '#104281'}   # one hue, ordinal (dataviz sequential blue 250 / 450 / 650)

def fig_yoy(counter, title, modes, daily, out, csv_path, first, last, loop):
    """same calendar month, year over year, on the dates valid in every year shown (>= YOY_MIN_DATES common dates): mean bicycles and cars per day"""
    mv = 'motor' if loop else 'car'
    bym = collections.defaultdict(lambda: collections.defaultdict(dict))   # month -> year -> day -> counter
    for d, c in daily.items():
        if c['_valid']: bym[d.month][d.year][d.day] = c
    panels = []; rows = []
    for m in sorted(bym):
        years = sorted(y for y in bym[m] if len(bym[m][y]) >= YOY_MIN_DATES)
        if len(years) < 2: continue
        common = set.intersection(*(set(bym[m][y]) for y in years))
        if len(common) < YOY_MIN_DATES: continue
        vals = {y: (sum(bym[m][y][d]['bike'] for d in common) / len(common), sum(bym[m][y][d][mv] for d in common) / len(common)) for y in years}
        panels.append((m, years, len(common), vals))
        for y in years: rows.append({'month': dt.date(2001, m, 1).strftime('%B'), 'year': y, 'common_dates': len(common), 'bikes_per_day': round(vals[y][0], 1), f'{mv}s_per_day' if mv == 'car' else 'motor_per_day': round(vals[y][1], 1)})
    if not panels: return
    allyears = sorted({y for _, ys, _, _ in panels for y in ys}); k = len(allyears); bw = 0.8 / k
    # totals over the same dates in every year of the set: the most recent two years over every month they share, and all years over the months they all share
    totals = []; seen = set()
    for kk in sorted({len(ys) for _, ys, _, _ in panels} | {2}, reverse=True):
        yrs = allyears[-kk:]; ms = [(m, ys, n, vals) for m, ys, n, vals in panels if set(yrs) <= set(ys)]
        if len(ms) < 2 or tuple(m for m, *_ in ms) in seen: continue
        seen.add(tuple(m for m, *_ in ms))
        pooled = {y: (0.0, 0.0) for y in yrs}; ndates = 0
        for m, ys, n, vals in ms:
            ndates += n
            for y in yrs: pooled[y] = (pooled[y][0] + vals[y][0] * n, pooled[y][1] + vals[y][1] * n)
        pooled = {y: (pooled[y][0] / ndates, pooled[y][1] / ndates) for y in yrs}
        label = (f'{dt.date(2001, ms[0][0], 1):%b}–{dt.date(2001, ms[-1][0], 1):%b}' if len(ms) == ms[-1][0] - ms[0][0] + 1 else f'{len(ms)} shared months') + f'\n{yrs[0]}–{str(yrs[-1])[2:]}'
        totals.append((label, yrs, ndates, pooled))
        for y in yrs: rows.append({'month': 'TOTAL ' + label.replace('\n', ', '), 'year': y, 'common_dates': ndates, 'bikes_per_day': round(pooled[y][0], 1), f'{mv}s_per_day' if mv == 'car' else 'motor_per_day': round(pooled[y][1], 1)})
    write_csv(csv_path, rows)
    groups = panels + totals; gap = 0.6
    xpos = [i for i in range(len(panels))] + [len(panels) + gap + 1.5 * j for j in range(len(totals))]
    fig, axes = plt.subplots(2, 1, figsize=(max(7.5, 1.5 + 1.25 * len(groups) + 0.5 * len(totals)), 7.4), dpi=150, sharex=True, gridspec_kw={'hspace': 0.3})
    for ax, idx, lab in ((axes[0], 0, 'bicycles per valid day' + ('' if loop else ' (daylight)')), (axes[1], 1, ('motor vehicles' if loop else 'cars') + ' per valid day' + ('' if loop else ' (daylight)'))):
        top = 0
        if totals: ax.axvspan(len(panels) + gap - 0.55, xpos[-1] + 0.55, color='#f1f2ef', zorder=0)
        for g, (_, ys, n, vals) in zip(xpos, groups):
            for y in ys:
                j = allyears.index(y); x = g - 0.4 + bw * (j + 0.5); v = vals[y][idx]; top = max(top, v)
                ax.bar(x, v, width=bw * 0.9, color=YEAR_SHADES.get(y, '#2a78d6'), zorder=3)
                ax.text(x, v, f'{v:.0f}', ha='center', va='bottom', fontsize=7, color=INK)
        ax.set_ylim(0, top * 1.18); ax.set_ylabel(lab, fontsize=9, color=MUTED); ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0); chrome(ax)
    axes[1].set_xticks(xpos); axes[1].set_xticklabels([f'{dt.date(2001, m, 1):%B}\n{n} dates' for m, _, n, _ in panels] + [f'Total\n{lab}\n{n} dates a year' for lab, _, n, _ in totals], fontsize=8.5, color=INK, linespacing=1.4)
    for t in axes[1].get_xticklabels()[len(panels):]: t.set_fontweight('bold')
    axes[1].set_xlim(-0.6, xpos[-1] + 0.65)
    axes[0].legend(handles=[Patch(color=YEAR_SHADES.get(y, '#2a78d6'), label=str(y)) for y in allyears], loc='lower left', bbox_to_anchor=(0, 1.01), ncol=k, frameon=False, fontsize=8.5, handlelength=1.2, borderaxespad=0)
    fig.suptitle(f'Same month, year over year: bicycles and {"motor vehicles" if loop else "cars"}\nrue de Terrebonne at {title}', x=0.06, ha='left', fontsize=10.5, fontweight='bold', color=INK, y=0.995, linespacing=1.3)
    axes[0].set_title(textwrap.fill(f'Mean per day on the calendar dates valid in every year shown (at least {YOY_MIN_DATES} common dates; the number under each month). Totals at the right pool those same dates over the months the years share. Weather and the sensor\'s uptime differ between years.', 150), loc='left', fontsize=8, color=MUTED, pad=22, linespacing=1.3)
    footer(fig, counter, first, last, loop)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.2)
    for ext in ('png', 'svg'): fig.savefig(f'{out}.{ext}')
    plt.close(fig)
    print('   year over year: ' + '; '.join(f'{dt.date(2001, m, 1):%b} ' + ' / '.join(f'{y} {vals[y][0]:.0f}' for y in ys) for m, ys, n, vals in panels) + ' | totals: ' + '; '.join(f'{lab.replace(chr(10), " ")} ({n} d) ' + ' / '.join(f'{y} {vals[y][0]:.0f} bikes, {vals[y][1]:.0f} ' + mv for y in ys) for lab, ys, n, vals in totals))

def run(wdef):
    start, wlabel = WINTERS[wdef]
    dout, fout = os.path.join(ROOT, 'derived', 'mode-shares', wdef), os.path.join(ROOT, 'figures', 'mode-shares', wdef)
    os.makedirs(dout, exist_ok=True); os.makedirs(fout, exist_ok=True)
    print(f'== winter = {wlabel}')
    for counter, (title, seg, _, modes) in COUNTERS.items():
        loop = seg is None
        daily = loop_daily() if loop else telraam_daily(counter)
        if not daily: continue
        for d, c in daily.items(): c['_valid'] = int(valid(c, loop))
        first, last = min(daily), max(daily)
        months = aggregate(daily, modes, lambda d: (d.year, d.month))
        weeks = aggregate(daily, modes, lambda d: d - dt.timedelta(d.weekday()))
        periods = aggregate(daily, modes, lambda d: period_of(d, start))
        # month -> period of its 15th (a month split by Nov 16 is placed with the period holding most of it; both tables carry the day-level period too)
        mp = {k: period_of(dt.date(k[0], k[1], 15), start) for k in months}
        write_csv(os.path.join(dout, f'monthly_{counter}.csv'), table_rows(months, modes, lambda k: {'month': f'{k[0]}-{k[1]:02d}'}, lambda k: {'period': mp[k][0]}))
        write_csv(os.path.join(dout, f'weekly_{counter}.csv'), table_rows(weeks, modes, lambda k: {'week_monday': k.isoformat()}, lambda k: {'period': period_of(k + dt.timedelta(3), start)[0]}))
        prow = table_rows(periods, modes, lambda k: {'period': k[0], 'label': k[1], 'first_day': max(k[2], first).isoformat(), 'last_day': min(k[3], last).isoformat()}, lambda k: {'days_in_window': (min(k[3], last) - max(k[2], first)).days + 1})
        write_csv(os.path.join(dout, f'periods_{counter}.csv'), prow)
        print(f'-- {title}: {first} to {last}, {sum(c["_valid"] for c in daily.values())} valid days of {len(daily)}')
        for r in prow:
            sh = ' '.join(f'{m} {r[f"{m}_share_pct"]}%' for m, _, _ in modes)
            print(f'   {r["label"]}: {r["valid_days"]} valid days; per day ' + ', '.join(f'{m} {r[f"{m}_per_day"]}' for m, _, _ in modes) + f'; shares {sh}')
        for k in sorted(periods):
            if periods[k]['valid_days'] == 0: continue
            ms = [m for m in sorted(months) if mp[m] == k and months[m]['valid_days'] > 0]
            if not ms: continue
            # the period total is over the period's own days (day-level), not the months' rounding
            fig_shares(counter, title, modes, ms, months, k[1], periods[k], os.path.join(fout, f'shares_{counter}_{k[0]}'), first, last, loop, wdef)
            fig_counts(counter, title, modes, ms, months, k[1], periods[k], os.path.join(fout, f'counts_{counter}_{k[0]}'), first, last, loop, wdef)
        fig_overview(counter, title, modes, daily, start, os.path.join(fout, f'overview_{counter}'), first, last, loop, wdef)
        fig_yoy(counter, title, modes, daily, os.path.join(fout, f'yoy_{counter}'), os.path.join(dout, f'yoy_{counter}.csv'), first, last, loop)

def main(argv):
    opts = dict(a[2:].split('=', 1) for a in argv if a.startswith('--') and '=' in a)
    w = opts.get('winter', 'nov16')
    for wdef in (list(WINTERS) if w == 'both' else [w]): run(wdef)

if __name__ == '__main__':
    main(sys.argv[1:])
