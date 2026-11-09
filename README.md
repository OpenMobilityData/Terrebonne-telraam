# Terrebonne-telraam: two citizen traffic sensors on rue de Terrebonne (NDG, Montréal)

Hourly counts from two Telraam S2 sensors installed by the author on rue de Terrebonne, exported from the Telraam dashboard, with the scripts and figures drawn from them (the exports themselves are not published here: see « Data and licence »). Companion to [Terrebonne-access-requests](https://github.com/OpenMobilityData/Terrebonne-access-requests) (the borough's own counter and documents) and [Terrebonne-open-sources](https://github.com/OpenMobilityData/Terrebonne-open-sources) (public records). Nothing here is an official count: the borough's loop counter at Kensington is the record; these sensors are the check and the history.

## The sensors

| Segment | Telraam segment / instance | Location | Data |
|---|---|---|---|
| West | 13374 / 9794 | rue de Terrebonne at King Edward (west of Cavendish; the street is one-way westbound there) | August 15, 2024 → May 4, 2026 (last export) |
| East | 13690 / 10045 | rue de Terrebonne at Draper (east of Cavendish; one-way eastbound) | September 24, 2024 → January 24, 2026 (sensor stopped) |

Both are Telraam S2 units (same hardware throughout). They count in **daylight only**: the "Bike Total" column is the daylight bicycle count, both directions; night-time traffic is reported as an undifferentiated "Night" class. Each hourly row carries an uptime value (the fraction of the hour with the sensor counting), stored by the dashboard as "Good uptime - 0.75" or "Poor uptime - 0.40". Levels are therefore not comparable with the borough's 24-hour loop counter.

## Getting the data: the API first, the exports as the fallback

The hourly data can be pulled at any time from the Telraam API with `scripts/fetch_telraam.py` (modelled on [BikeStat](https://github.com/OpenMobilityData/BikeStat)'s `refresh-telraam.sh`: `POST https://telraam-api.net/v1/reports/traffic`, level `segments`, format `per-hour`, in 90-day chunks). API segment ids: 9000007290 (King Edward, instance 9794), 9000007489 (Draper, instance 10045). The API token lives in `~/.terrebonne-telraam.conf` (chmod 600; never in this repository). Output: `data/api/<west|east>_<year>.csv`, one row per hour, local time; the figure script uses these when present. The dashboard exports in `data/raw/` are the same data as downloaded in 2025–2026 and remain as the fallback copy. The older working folder of MATLAB scripts that grew around these sensors is retired; the data, not those scripts, are what this repository keeps.

## Layout

| Path | Content |
|---|---|
| (not in this repository) | The Telraam dashboard exports (`raw-data-20YY{East,West}{15,60}.xlsx`, 2024–2026) are kept privately by the author since October 29, 2026; see « Data and licence ». The scripts read them from a local copy (`TELRAAM_RAW`) |
| `scripts/fetch_telraam.py` | Pull the hourly data from the Telraam API into `data/api/` (token in a config file outside git) |
| `scripts/telraam_period_violins.py` | Year-over-year violin plots of daily bicycle counts for equivalent periods (whole winter, whole year, each month), comparing years on the calendar dates valid in every year shown; a period is drawn only when two years share at least 20 valid dates |
| `figures/year-over-year/` | The figures (PNG and SVG), `telraam_{west,east}_{period}_en` |
| `scripts/telraam_mode_shares.py [--winter=nov16\|dec1\|both]` → `derived/mode-shares/<def>/`, `figures/mode-shares/<def>/` | Mode shares (pedestrians, bicycles, cars, heavy vehicles) and mean daily counts by mode, by month, by ISO week and by period (winter / non-winter), for each sensor and, on its own panel, the borough's loop counter at Kensington (bicycles and motor vehicles, 24 h, from Terrebonne-access-requests); figures per period (`shares_…`, `counts_…`) and one weekly overview per counter (`overview_…`, bicycles and cars per valid day, winters shaded, coverage strip). Two winter definitions: `nov16` = November 16 – March 31 (default), `dec1` = December 1 – March 31 |
| `scripts/build_mode_shares_deck.py [--winter=nov16\|dec1]` → [`docs/telraam_mode_shares_deck_en.pdf`](docs/telraam_mode_shares_deck_en.pdf) (34 slides; [`_dec1`](docs/telraam_mode_shares_deck_en_dec1.pdf) variant) | Slide deck (beamer 16:9) built from the mode-share figures and tables: the question, the answer, counters and method, King Edward, Draper and Kensington slides, the period tables under both winter definitions, cautions, appendix with every remaining figure |
| `scripts/telraam_summaries.py` → `derived/daily.csv`, `derived/speeds_by_season.csv` | Daily totals per sensor (hours, uptime, bikes, cars, valid flag) and V85 / share of cars over 30 and 40 km/h by season, for downstream builds (the poster in Terrebonne-open-sources reads these) |

**Valid day** (for the figures): at least 8 reported hours and at least 6 hours of summed uptime.

## Winter coverage (checked October 20, 2026)

| Segment | Winter 2024–25 valid days | Winter 2025–26 valid days | Calendar dates valid in both |
|---|---:|---:|---:|
| King Edward | 119 of 121 | 68 (gaps December 13–28 and January 29 – March 6) | 66 |
| Draper | 120 of 121 | 53 (December and January 1–24 only) | 53 |

There are only two winters, both after the protected lane was built (2024); no pre-lane winter exists in this record. Summer and February have one year of data only and are not drawn. Weather differs between the years compared; the 2025–26 winter had the second-lowest snow loading of eleven seasons.

## Mode shares, winter and non-winter (November 9, 2026)

`scripts/telraam_mode_shares.py` answers « who uses the street », by month and by period, from the daylight classes of each sensor. Shares are of everything the sensor classified in daylight over valid days (night traffic is an undifferentiated class and is left out), so they are **daylight shares**: cars also drive at night, bicycles much less, and a 24-hour share would give bicycles less. The loop counter at Kensington, drawn on its own panel, gives the 24-hour picture for bicycles against motor vehicles.

The figures are collected in a slide deck, [`docs/telraam_mode_shares_deck_en.pdf`](docs/telraam_mode_shares_deck_en.pdf) (`scripts/build_mode_shares_deck.py`). With winter = November 16 – March 31 (`figures/mode-shares/nov16/`, tables in `derived/mode-shares/nov16/`):

| Counter | Period | Valid days | Pedestrians | Bicycles | Cars | Heavy | Bicycles per 100 cars |
|---|---|---:|---:|---:|---:|---:|---:|
| King Edward (west) | Non-winter 2025 (Apr 1 – Nov 15) | 229 | 33 % | 33 % | 34 % | 1 % | 98 |
| King Edward (west) | Winter 2024–25 | 134 | 32 % | 11 % | 55 % | 2 % | 20 |
| King Edward (west) | Winter 2025–26 | 83 | 21 % | 11 % | 60 % | 8 % | 19 |
| Draper (east) | Non-winter 2025 (Apr 1 – Nov 15) | 229 | 25 % | 17 % | 56 % | 2 % | 29 |
| Draper (east) | Winter 2024–25 | 135 | 25 % | 5 % | 67 % | 4 % | 7 |
| Draper (east) | Winter 2025–26 (to Jan 24) | 68 | 20 % | 5 % | 71 % | 4 % | 7 |
| Kensington loop (24 h) | Non-winter 2025 (Jul 26 – Nov 15) | 113 | — | 30 % | 70 % (motor) | — | 44 |
| Kensington loop (24 h) | Winter 2025–26 | 136 | — | 4 % | 96 % (motor) | — | 4 |

At King Edward, in daylight, bicycles and cars run about level from May to September (bicycles per 100 cars by month, 2025: May 98, June 143, July 121, August 99, September 93; April 78, October 75, November 31); of 51 non-winter weeks with at least four valid days, 17 had more bicycles than cars and 24 were within 20 % either way. In winter the ratio falls to about 20 per 100 at King Edward and 7 per 100 at Draper. The western sensor's record ends May 4, 2026 (last export); extending it needs a Telraam API token (`fetch_telraam.py`) or a new dashboard export. Heavy vehicles at King Edward rose from about 10 a day to 35 a day in winter 2025–26 (44 a day in January 2026); the cause is not examined here.

## Data and licence

The counts belong to Telraam. Under Telraam's terms of use ([Conditions of Participation](https://telraam.net/en/terms-of-use), s. 2, as read on October 29, 2026), « all intellectual rights relating to the traffic counts collected and any database into which they are incorporated by Telraam shall be owned by Telraam », and a participant has « a limited, non-exclusive, non-transferable personal access right to the counting data produced by your Telraam device ». The terms grant no licence to republish the data. The ten dashboard exports this repository first held (`data/raw/`, 2024–2026) were therefore removed on October 29, 2026; the author keeps them privately, and the scripts read them from a local copy. The same counts can be viewed on [telraam.net](https://telraam.net) and queried through Telraam's API (segments 9000007290, King Edward, and 9000007489, Draper), under Telraam's own terms. This note will be updated if Telraam grants permission to republish the exports.

The tables in `derived/` and the figures are computed from Telraam's counts (source: Telraam). The author's own work, the README, the figures and the method, is published under CC BY 4.0 ([`LICENSE`](LICENSE)), and the scripts under the MIT licence ([`LICENSE-CODE`](LICENSE-CODE)); neither licence covers Telraam's counts.

## Use of AI

Much of the code and many of the drafts in this repository were produced with an AI assistant, Anthropic's Claude, in interactive sessions directed by the author. The author chose the questions, supplied the sources, reviewed every output, and checked every quotation, page reference and figure against the documents; the author alone is responsible for the content. Commits to which the assistant contributed name it as co-author, so the division of work is visible in the history, and errors found in its work are corrected in the open like any other. Nothing in `raw/` is edited by anyone, human or machine. The practice follows the principles of the European Commission's « Living guidelines on the responsible use of generative AI in research » (Directorate-General for Research and Innovation with the European Research Area Forum, first published March 20, 2024 and updated since; [document page](https://research-and-innovation.ec.europa.eu/document/2b6cf7e5-36ac-41cb-aab5-0d32050143dc_en)): the researcher remains responsible for the output, the use of the tool is disclosed, sources and facts are verified, privacy and third-party rights are respected, and the tool is never an author.

Everything is open to review: all source code, documents and data in this repository are publicly visible, as is the complete change log of every file. Anyone is welcome to read any of it and check it for errors and omissions. Anyone with a concern is welcome to open an issue on GitHub; every issue submitted is publicly visible, as is its answer.

## About the author

The requests were filed, and the derived documents written, by Rick Hoge, a resident of Côte-des-Neiges–Notre-Dame-de-Grâce who cycles on Terrebonne in every season. He works as a data scientist and is a professor in the Faculty of Medicine at McGill University, where his research is in neuroscience and biomedical engineering, including the effects of physical activity on brain health. The work in this repository is personal: it was done as a resident, on his own time, from public records, and represents no position of McGill University or of any other organization; the affiliation is given for identification only. Corrections are welcome through the repository's issue tracker.
