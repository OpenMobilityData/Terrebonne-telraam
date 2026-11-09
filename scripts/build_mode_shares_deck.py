#!/usr/bin/env python3
"""Slide deck (beamer 16:9, English) from the mode-share figures and tables of telraam_mode_shares.py.

Reads derived/mode-shares/<def>/periods_*.csv and monthly_west.csv for the numbers, figures/mode-shares/<def>/ for the
charts; the alternative winter definition's period table is shown on one slide for comparison. Writes
docs/telraam_mode_shares_deck_en.pdf (the .tex beside it). Run telraam_mode_shares.py --winter=both first.
Usage: python3 scripts/build_mode_shares_deck.py [--winter=nov16|dec1]   (needs pdflatex)
"""
import csv, os, sys, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
DOCS = os.path.join(ROOT, 'docs'); URL = 'https://github.com/OpenMobilityData/Terrebonne-telraam'
WINTERS = {'nov16': 'November 16 to March 31', 'dec1': 'December 1 to March 31'}
TITLES = {'west': 'King Edward (western portion)', 'east': 'Draper (eastern portion)', 'kensington': 'Kensington loop (24 h)'}
STAMP = datetime.datetime.now().strftime('%B %-d, %Y')

def rows(wdef, name): return list(csv.DictReader(open(os.path.join(ROOT, 'derived', 'mode-shares', wdef, name), encoding='utf-8')))
def esc(s): return s.replace('%', '\\%').replace('&', '\\&').replace('–', '--')
def pct(v): return f'{float(v):.0f}\\,\\%' if v not in ('', None) else '--'
def num(v): return f'{float(v):,.0f}' if v not in ('', None) else '--'
def fig(wdef, name, w=0.92): return f'\\includegraphics[width={w}\\textwidth]{{../figures/mode-shares/{wdef}/{name}.png}}'
def frame_fig(title, wdef, name, note='', w=0.92):
    return f'\\begin{{frame}}{{{esc(title)}}}\\centering{fig(wdef, name, w)}' + (f'\\\\{{\\scriptsize {note}}}' if note else '') + '\\end{frame}\n'

def period_table(wdef):
    out = ['\\resizebox{\\textwidth}{!}{\\begin{tabular}{llrrrrrr}\\toprule', 'Counter & Period & Valid days & Pedestrians & Bicycles & Cars & Heavy & Bicycles per 100 cars\\\\\\midrule']
    for c in ('west', 'east', 'kensington'):
        for r in rows(wdef, f'periods_{c}.csv'):
            if int(r['valid_days']) < 20: continue
            lab = r['label'].split(' (')[0]; span = f"{r['first_day'][5:]} to {r['last_day'][5:]}"
            if c == 'kensington':
                out.append(f"{TITLES[c]} & {lab} ({span}) & {r['valid_days']} & -- & {pct(r['bike_share_pct'])} & {pct(r['motor_share_pct'])}\\textsuperscript{{m}} & -- & {num(r['bikes_per_100_motor'])}\\\\")
            else:
                out.append(f"{TITLES[c]} & {lab} ({span}) & {r['valid_days']} & {pct(r['pedestrian_share_pct'])} & {pct(r['bike_share_pct'])} & {pct(r['car_share_pct'])} & {pct(r['heavy_share_pct'])} & {num(r['bikes_per_100_cars'])}\\\\")
        out.append('\\addlinespace')
    out.append('\\bottomrule\\end{tabular}}')
    return '\n'.join(out)

def monthly_ratio_line(wdef):
    m = {r['month']: r for r in rows(wdef, 'monthly_west.csv')}
    names = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']
    return ', '.join(f"{n} {float(m[f'2025-{i + 4:02d}']['bikes_per_100_cars']):.0f}" for i, n in enumerate(names) if f'2025-{i + 4:02d}' in m)

def main(argv):
    opts = dict(a[2:].split('=', 1) for a in argv if a.startswith('--') and '=' in a)
    wdef = opts.get('winter', 'nov16'); alt = 'dec1' if wdef == 'nov16' else 'nov16'
    os.makedirs(DOCS, exist_ok=True)
    pw = {r['period']: r for r in rows(wdef, 'periods_west.csv')}; pe = {r['period']: r for r in rows(wdef, 'periods_east.csv')}; pk = {r['period']: r for r in rows(wdef, 'periods_kensington.csv')}
    nw25, w2425, w2526 = pw['non-winter-2025'], pw['winter-2024-25'], pw['winter-2025-26']
    weekly = [r for r in rows(wdef, 'weekly_west.csv') if r['valid_days'] and int(r['valid_days']) >= 4 and r['period'].startswith('non')]
    n_more = sum(1 for r in weekly if float(r['bike_total']) > float(r['car_total'])); n_close = sum(1 for r in weekly if 0.8 <= float(r['bike_total']) / float(r['car_total']) <= 1.25)
    west_first, west_last = rows(wdef, 'periods_west.csv')[0]['first_day'], max(r['last_day'] for r in rows(wdef, 'periods_west.csv'))
    tex = r'''\documentclass[aspectratio=169,10pt]{beamer}\usetheme{default}\usecolortheme{seahorse}\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}[frame number]
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{helvet}\usepackage{booktabs}
\title{Who uses rue de Terrebonne, by season}\subtitle{Pedestrians, bicycles, cars and heavy vehicles on the two Telraam sensors and the borough\textquoteright{}s loop counter, winter and non-winter}\author{Terrebonne-telraam (a resident of Côte-des-Neiges--Notre-Dame-de-Grâce)}\date{''' + STAMP + r'''}
\begin{document}
\begin{frame}\titlepage\end{frame}
\begin{frame}{The question}\begin{itemize}
\item A reader of the Telraam dashboard for the western portion asked whether there is « almost always more bike traffic than car traffic until the winter months », and for the shares of pedestrians, bicycles, cars and heavy vehicles by week or month over the year. The dashboard shows two weeks at a time, with gaps.
\item This deck answers from the full hourly record of both sensors (King Edward, west of Cavendish, ''' + esc(datetime.date.fromisoformat(west_first).strftime('%B %-d, %Y')) + ' to ' + esc(datetime.date.fromisoformat(west_last).strftime('%B %-d, %Y')) + r'''; Draper, east of Cavendish, September 24, 2024 to January 24, 2026) and, on its own panel, from the borough\textquoteright{}s 24-hour loop counter at Kensington (July 26, 2025 to August 31, 2026, released under access request 2026-581).
\item Winter here is ''' + WINTERS[wdef] + r''' (the City\textquoteright{}s winter period for bike lanes); the alternative, ''' + WINTERS[alt] + r''' (the borough\textquoteright{}s proposed conversion window), is tabled at the end. Non-winter is the rest of the year, from April 1.
\end{itemize}\end{frame}
\begin{frame}{The answer in one slide}\begin{itemize}
\item At King Edward, in daylight, bicycles and cars run about level from May to September, and bicycles are ahead in June and July. Bicycles per 100 cars by month, 2025: ''' + monthly_ratio_line(wdef) + r'''. In winter the ratio falls to about ''' + f"{float(w2425['bikes_per_100_cars']):.0f}" + r''' per 100.
\item Of ''' + str(len(weekly)) + r''' non-winter weeks with at least four valid days, ''' + str(n_more) + r''' had more bicycles than cars and ''' + str(n_close) + r''' were within 20\,\% either way. « Almost always more bikes than cars » overstates it; « about as many bikes as cars in daylight from May to September » is what the sensor shows.
\item Shares, April 1 to November 15, 2025, King Edward: pedestrians ''' + pct(nw25['pedestrian_share_pct']) + r''', bicycles ''' + pct(nw25['bike_share_pct']) + r''', cars ''' + pct(nw25['car_share_pct']) + r''', heavy ''' + pct(nw25['heavy_share_pct']) + r'''. Winter 2024--25: ''' + pct(w2425['pedestrian_share_pct']) + ' / ' + pct(w2425['bike_share_pct']) + ' / ' + pct(w2425['car_share_pct']) + ' / ' + pct(w2425['heavy_share_pct']) + r'''. Winter 2025--26: ''' + pct(w2526['pedestrian_share_pct']) + ' / ' + pct(w2526['bike_share_pct']) + ' / ' + pct(w2526['car_share_pct']) + ' / ' + pct(w2526['heavy_share_pct']) + r'''.
\item The eastern portion is a different street: at Draper, ''' + f"{float(pe['non-winter-2025']['bikes_per_100_cars']):.0f}" + r''' bicycles per 100 cars outside winter and ''' + f"{float(pe['winter-2024-25']['bikes_per_100_cars']):.0f}" + r''' in winter, with car volumes about four times King Edward\textquoteright{}s.
\item These are daylight shares. Over 24 hours the loop at Kensington counted ''' + f"{float(pk['non-winter-2025']['bikes_per_100_motor']):.0f}" + r''' bicycles per 100 motor vehicles outside winter and ''' + f"{float(pk['winter-2025-26']['bikes_per_100_motor']):.0f}" + r''' in winter.
\end{itemize}\end{frame}
\begin{frame}{Counters and method}\begin{itemize}
\item \textbf{Telraam S2} sensors (King Edward, segment 13374; Draper, segment 13690), hourly counts in four daylight classes: pedestrian, bike, car, large vehicle (« heavy »). Night traffic is one undifferentiated class and is left out of every share, so the shares are daylight shares: cars also drive at night, bicycles much less, and a 24-hour share would give bicycles less.
\item \textbf{Valid day} = at least 8 reported hours and 6 hours of summed uptime. King Edward: 572 of 575 days; Draper: 484 of 488. The gaps are whole outages (King Edward: December 13--28, 2025 and January 29 -- March 6, 2026), not bad days mixed in.
\item \textbf{Shares and means are over valid days only.} A month with fewer than 7 valid days is marked \dag{} and drawn lighter. A month cut by the winter boundary is shown whole in the period holding most of it; the period rows are over the period\textquoteright{}s exact days.
\item \textbf{Loop counter at Kensington} (Eco-Counter ZELT EVO, the borough\textquoteright{}s): bicycles and motor vehicles, 24 h, daily totals as released (zero days of May 29--31, 2026 and the June 7, 2026 counter-fault value left out; the westbound bicycle channel is degraded from about March 1, 2026, so bicycle figures from then on are lower bounds). Never drawn on the same axis as a Telraam sensor.
\item Script: \texttt{scripts/telraam\_mode\_shares.py}; tables by month, ISO week and period in \texttt{derived/mode-shares/}; this deck: \texttt{scripts/build\_mode\_shares\_deck.py}.
\end{itemize}\end{frame}
\section{King Edward, the western portion}
''' + frame_fig('King Edward: bicycles and cars week by week', wdef, 'overview_west', 'Weekly mean per valid day, daylight. The two lines cross in late spring and part in October; the shaded winters show bicycles at a tenth or less of the summer level while cars fall by about a third.', 0.9) \
      + frame_fig('King Edward, non-winter 2025: who used the street', wdef, 'shares_west_non-winter-2025', 'Three roughly equal thirds from May to September; the car share rises in April, October and November.', 0.8) \
      + frame_fig('King Edward, non-winter 2025: daily counts by mode', wdef, 'counts_west_non-winter-2025', '', 0.86) \
      + frame_fig('King Edward, winter 2024--25: who used the street', wdef, 'shares_west_winter-2024-25', '', 0.8) \
      + frame_fig('King Edward, winter 2025--26: who used the street', wdef, 'shares_west_winter-2025-26', '83 valid days: December has 15 and February none (outages). Heavy vehicles rose from about 10 a day to 35 a day this winter (44 a day in January); the cause is not examined here.', 0.8) \
      + frame_fig('King Edward, winter 2025--26: daily counts by mode', wdef, 'counts_west_winter-2025-26', '', 0.86) \
      + frame_fig('Is cycling increasing at King Edward? Same months, year over year', wdef, 'yoy_west', 'Mean per day on the dates valid in both years. Late summer 2025 ran above 2024 (August, September); October, March and April are level year on year; November 2025 and January 2026 ran below. The record ends May 4, 2026: nothing after that date is in these figures.', 0.72) \
      + r'''\section{Draper, the eastern portion}
''' + frame_fig('Draper: bicycles and cars week by week', wdef, 'overview_east', 'Car volumes four times those at King Edward (the street is one-way eastbound here and carries through traffic to Girouard); bicycles at about three in ten cars in summer, one in fifteen in winter. The sensor stopped on January 24, 2026.', 0.9) \
      + frame_fig('Draper, non-winter 2025: who used the street', wdef, 'shares_east_non-winter-2025', '', 0.8) \
      + frame_fig('Draper, winter 2024--25: who used the street', wdef, 'shares_east_winter-2024-25', '', 0.8) \
      + r'''\section{Kensington, the borough\textquoteright{}s loop counter}
''' + frame_fig('Kensington loop: bicycles and motor vehicles week by week (24 h)', wdef, 'overview_kensington', 'The official record, 24 hours, both directions. Bicycle figures from March 2026 are lower bounds (westbound channel degraded).', 0.9) \
      + frame_fig('Kensington loop, non-winter 2025: what the loop counted', wdef, 'shares_kensington_non-winter-2025', 'Two modes only (the loop does not see pedestrians). Bicycles three in ten of all vehicles over 24 hours, July 26 to November 15, 2025.', 0.8) \
      + frame_fig('Kensington loop, winter 2025--26: what the loop counted', wdef, 'shares_kensington_winter-2025-26', '', 0.8) \
      + r'''\section{Summary tables}
\begin{frame}{Every counter and period, winter = ''' + WINTERS[wdef] + r'''}\centering{\scriptsize
''' + period_table(wdef) + r'''
\\[4pt] Shares of everything classified in daylight (Telraam) or of all vehicles counted over 24 h (loop; \textsuperscript{m} = motor vehicles). Periods with fewer than 20 valid days omitted. Non-winter periods are cut by the record\textquoteright{}s first and last days.}\end{frame}
\begin{frame}{The same with winter = ''' + WINTERS[alt] + r'''}\centering{\scriptsize
''' + period_table(alt) + r'''
\\[4pt] The borough\textquoteright{}s proposed conversion window. The shares move by a point or two: the second half of November is a transition fortnight, not a winter one, at either end of the street.}\end{frame}
\begin{frame}{Cautions}\begin{itemize}
\item \textbf{Daylight only.} The Telraam shares exclude night traffic, which is mostly motor traffic. The loop counter\textquoteright{}s 24-hour ratio (about 44 bicycles per 100 motor vehicles outside winter at Kensington) is the comparable official figure; the Telraam sensors are the check and the history, not the record.
\item \textbf{Two ends, two streets.} West of Cavendish the street is one-way westbound with about 350 cars a day in daylight; east of it, one-way eastbound with about 1,500. A statement about « the western portion » does not transfer to the whole street.
\item \textbf{Classification.} Telraam\textquoteright{}s classes are the sensor\textquoteright{}s; the winter rise in « heavy vehicles » at King Edward may be snow equipment, classification drift, or both. The snow-day divergence between Telraam and the loop (Terrebonne-open-sources, 2026-winter-counts-user-frequency) is unresolved.
\item \textbf{The record ends May 4, 2026} at King Edward. Extending it needs a Telraam API token or a new dashboard export; the dashboard\textquoteright{}s recent months, with their outages, are not in these figures.
\item Code, tables, figures: \url{''' + URL + r'''}. Counts: Telraam (its terms of use; the exports are not republished) and the borough\textquoteright{}s release under access request 2026-581.
\end{itemize}\end{frame}
\appendix
\section{Appendix: the remaining figures}
'''
    shown = {'overview_west', 'shares_west_non-winter-2025', 'counts_west_non-winter-2025', 'shares_west_winter-2024-25', 'shares_west_winter-2025-26', 'counts_west_winter-2025-26',
             'overview_east', 'shares_east_non-winter-2025', 'shares_east_winter-2024-25', 'overview_kensington', 'shares_kensington_non-winter-2025', 'shares_kensington_winter-2025-26', 'yoy_west'}
    figdir = os.path.join(ROOT, 'figures', 'mode-shares', wdef)
    for f in sorted(os.listdir(figdir)):
        if not f.endswith('.png'): continue
        name = f[:-4]
        if name in shown: continue
        parts = name.split('_', 2)
        if len(parts) == 2:
            kind, counter = parts; title = f"{TITLES[counter]}: same months, year over year"
        else:
            kind, counter, period = parts
            title = f"{TITLES[counter]}, {period.replace('non-winter-', 'non-winter ').replace('winter-', 'winter ').replace('-', '--')}: {'who used the street' if kind == 'shares' else 'daily counts by mode'}"
        tex += frame_fig(title, wdef, name, '', 0.8 if kind == 'shares' else 0.86)
    tex += '\\end{document}\n'
    name = 'telraam_mode_shares_deck_en' + ('' if wdef == 'nov16' else f'_{wdef}')
    open(os.path.join(DOCS, name + '.tex'), 'w', encoding='utf-8').write(tex)
    for _ in range(3): subprocess.run(['pdflatex', '-interaction=batchmode', name + '.tex'], cwd=DOCS, capture_output=True, text=True)
    log = open(os.path.join(DOCS, name + '.log'), encoding='latin-1').read(); errs = [l for l in log.splitlines() if l.startswith('!')]
    for e in ('.aux', '.log', '.nav', '.out', '.snm', '.toc'):
        try: os.remove(os.path.join(DOCS, name + e))
        except OSError: pass
    pi = subprocess.run(['pdfinfo', os.path.join(DOCS, name + '.pdf')], capture_output=True, text=True).stdout
    print(name, (pi.split('Pages:')[1].split()[0] if 'Pages:' in pi else '?'), 'pages', ('ERRORS: ' + '; '.join(errs[:5])) if errs else 'ok')

if __name__ == '__main__':
    main(sys.argv[1:])
