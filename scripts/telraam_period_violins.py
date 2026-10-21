#!/usr/bin/env python3
"""Year-over-year violin plots of DAILY bicycle counts from the two Telraam S2 sensors on rue de Terrebonne
(King Edward, segment 13374; Draper, segment 13690), for equivalent periods, on the same calendar dates each year.

For each sensor and period, the years that have data are compared on the calendar dates that are VALID in every one
of them (valid day = at least MIN_HOURS reported hours and at least MIN_UPTIME hours of summed uptime). One violin per
year, every day a point, median bar, middle-half box. A period is skipped when fewer than two years share MIN_DAYS dates.
Telraam counts bicycles in daylight only; "Bike Total" is the sensor's daylight count, both directions.
Input: ../data/raw/raw-data-20YY{East,West}60.xlsx (hourly). Output: ../figures/year-over-year/*.png|svg.
Usage: python3 scripts/telraam_period_violins.py   (needs openpyxl, matplotlib)
"""
import openpyxl, glob, os, re, datetime as dt, collections, statistics as st, random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT = os.path.join(HERE, '..', 'data', 'raw'), os.path.join(HERE, '..', 'figures', 'year-over-year')
MIN_HOURS, MIN_UPTIME, MIN_DAYS = 8, 6.0, 20
SEG = {'West': ('King Edward', 13374), 'East': ('Draper', 13690)}
INK, MUTED = '#1f2428', '#5f6b74'
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
# periods: (slug, label, start (month, day), end (month, day)); a period that crosses New Year is named by the year it starts in
PERIODS = [('winter', 'Winter, December 1 to March 31', (12, 1), (3, 31)),
           ('summer', 'Summer, June 1 to August 31', (6, 1), (8, 31)),
           ('year', 'Whole year, September 1 to August 31', (9, 1), (8, 31)),
          ] + [(dt.date(2001, m, 1).strftime('%B').lower(), dt.date(2001, m, 1).strftime('%B'), (m, 1), (m, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])) for m in range(1, 13)]

def uptime(v):
    if v is None: return 0.0
    if isinstance(v, (int, float)): return float(v)
    m = re.search(r'([0-9]*\.?[0-9]+)\s*$', str(v)); return float(m.group(1)) if m else 0.0

def daily(seg):
    day = collections.defaultdict(lambda: [0, 0.0, 0])
    for f in sorted(glob.glob(os.path.join(RAW, f'raw-data-20*{seg}60.xlsx'))):
        ws = openpyxl.load_workbook(f, read_only=True, data_only=True).active
        it = ws.iter_rows(values_only=True); hdr = next(it); ix = {h: i for i, h in enumerate(hdr)}
        for r in it:
            t = r[ix['Date and Time (Local)']]
            if t is None: continue
            if isinstance(t, str): t = dt.datetime.fromisoformat(t)
            d = t.date(); day[d][0] += 1; day[d][1] += uptime(r[ix['Uptime']]); day[d][2] += (r[ix['Bike Total']] or 0)
    valid = {d: v[2] for d, v in day.items() if v[0] >= MIN_HOURS and v[1] >= MIN_UPTIME}
    return valid, min(day), max(day)

def period_dates(start_year, s, e):
    a = dt.date(start_year, *s); b = dt.date(start_year + (1 if (e < s) else 0), *e)
    return [a + dt.timedelta(i) for i in range((b - a).days + 1)]

def violin(ax, i, v, col, rng):
    parts = ax.violinplot([v], positions=[i], widths=0.8, showextrema=False, showmedians=False, points=300, bw_method=0.2)
    for body in parts['bodies']: body.set_facecolor(col); body.set_edgecolor(col); body.set_alpha(0.22)
    ax.scatter([i + rng.uniform(-0.16, 0.16) for _ in v], v, s=10, color=col, alpha=0.55, linewidths=0, zorder=3)
    if len(v) >= 4:
        q1, med, q3 = st.quantiles(v, n=4)
        ax.add_patch(plt.Rectangle((i - 0.045, q1), 0.09, q3 - q1, facecolor=col, edgecolor='none', alpha=0.9, zorder=4))
    med = st.median(v)
    ax.plot([i - 0.11, i + 0.11], [med, med], color='#fcfcfb', linewidth=2.6, zorder=5); ax.plot([i - 0.11, i + 0.11], [med, med], color=INK, linewidth=1.4, zorder=6)
    return med

def main():
    os.makedirs(OUT, exist_ok=True); rng = random.Random(1)
    for seg, (name, segid) in SEG.items():
        valid, first, last = daily(seg)
        print(f'== {name} (segment {segid}): data {first} to {last}; valid days {len(valid)}')
        for slug, label, s, e in PERIODS:
            years = {}
            for y in range(first.year - 1, last.year + 1):
                ds = [d for d in period_dates(y, s, e) if d in valid]
                if ds: years[y] = {(d.month, d.day): valid[d] for d in ds}
            if len(years) < 2: print(f'   {slug}: only {len(years)} year(s) with data, skipped'); continue
            common = set.intersection(*(set(m.keys()) for m in years.values()))
            # drop years that would leave too few common dates: keep the largest set of years sharing >= MIN_DAYS dates
            if len(common) < MIN_DAYS:
                best = None
                ys = sorted(years)
                for i in range(len(ys)):
                    for j in range(i + 1, len(ys)):
                        c = set(years[ys[i]]) & set(years[ys[j]])
                        if len(c) >= MIN_DAYS and (best is None or len(c) > len(best[1])): best = ([ys[i], ys[j]], c)
                if best is None: print(f'   {slug}: fewer than {MIN_DAYS} common dates, skipped'); continue
                years = {y: years[y] for y in best[0]}; common = best[1]
            ys = sorted(years); series = {y: [years[y][k] for k in sorted(common)] for y in ys}
            ylabel = lambda y: (f'{y}' if s <= e else f'{y}–{str(y + 1)[2:]}')
            fig, ax = plt.subplots(figsize=(max(8.5, 4 + 2.2 * len(ys)), 6.6), dpi=150)
            top = max(max(v) for v in series.values()) * 1.12
            for i, y in enumerate(ys):
                med = violin(ax, i, series[y], PAL[i % len(PAL)], rng)
            ax.set_xticks(range(len(ys)))
            ax.set_xticklabels([f'{ylabel(y)}\n{len(series[y])} days\nmedian {st.median(series[y]):.0f} · mean {st.mean(series[y]):.0f}' for y in ys], fontsize=9.5, color=INK, linespacing=1.5)
            ax.set_xlim(-0.6, len(ys) - 0.4); ax.set_ylim(0, top); ax.set_ylabel('bicycles per day (daylight count)', fontsize=10, color=MUTED)
            for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
            ax.spines['left'].set_color('#c9cdd2'); ax.spines['bottom'].set_color('#c9cdd2')
            ax.yaxis.grid(True, color='#e2e4e1', linewidth=0.8, zorder=0); ax.set_axisbelow(True); ax.tick_params(colors=MUTED, length=0)
            months = sorted({k[0] for k in common}, key=lambda m: ((m - 9) % 12))
            cov = ', '.join(f'{dt.date(2001, m, 1):%b} {sum(1 for k in common if k[0] == m)}' for m in months)
            fig.suptitle(f'{label}\nDaily bicycle counts, rue de Terrebonne at {name} (Telraam sensor)', x=0.07, ha='left', fontsize=10.5, fontweight='bold', color=INK, y=0.99, linespacing=1.3)
            import textwrap
            covline = textwrap.fill(f'Dates valid in every year shown: {cov}.', 105)
            ax.set_title(f'Same {len(common)} calendar dates in each year; every day is a point; bar = median, box = middle half. Daylight counts, both directions.\n{covline}', loc='left', fontsize=8.0, color=MUTED, pad=10, linespacing=1.3)
            fig.text(0.07, 0.012, f'Source: Telraam S2 sensor (segment {segid}) operated by a resident, hourly data; data from {first:%B %-d, %Y} to {last:%B %-d, %Y}. Valid day = at least {MIN_HOURS} reported hours and {MIN_UPTIME:.0f} h of uptime. '
                     'The sensor counts bicycles in daylight only, so levels are not comparable with the borough\'s loop counter at Kensington. Weather differs between years.', fontsize=7.1, color=MUTED, wrap=True)
            fig.subplots_adjust(left=0.13, right=0.97, top=0.80, bottom=0.24)
            for ext in ('png', 'svg'):
                fig.savefig(os.path.join(OUT, f'telraam_{seg.lower()}_{slug}_en.{ext}'))
            plt.close(fig)
            print(f'   {slug}: years {[ylabel(y) for y in ys]}, {len(common)} common dates; medians ' + ', '.join(f'{ylabel(y)} {st.median(series[y]):.0f}' for y in ys))

if __name__ == '__main__':
    main()
