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
| `scripts/telraam_summaries.py` → `derived/daily.csv`, `derived/speeds_by_season.csv` | Daily totals per sensor (hours, uptime, bikes, cars, valid flag) and V85 / share of cars over 30 and 40 km/h by season, for downstream builds (the poster in Terrebonne-open-sources reads these) |

**Valid day** (for the figures): at least 8 reported hours and at least 6 hours of summed uptime.

## Winter coverage (checked October 20, 2026)

| Segment | Winter 2024–25 valid days | Winter 2025–26 valid days | Calendar dates valid in both |
|---|---:|---:|---:|
| King Edward | 119 of 121 | 68 (gaps December 13–28 and January 29 – March 6) | 66 |
| Draper | 120 of 121 | 53 (December and January 1–24 only) | 53 |

There are only two winters, both after the protected lane was built (2024); no pre-lane winter exists in this record. Summer and February have one year of data only and are not drawn. Weather differs between the years compared; the 2025–26 winter had the second-lowest snow loading of eleven seasons.

## Data and licence

The counts belong to Telraam. Under Telraam's terms of use ([Conditions of Participation](https://telraam.net/en/terms-of-use), s. 2, as read on October 29, 2026), « all intellectual rights relating to the traffic counts collected and any database into which they are incorporated by Telraam shall be owned by Telraam », and a participant has « a limited, non-exclusive, non-transferable personal access right to the counting data produced by your Telraam device ». The terms grant no licence to republish the data. The ten dashboard exports this repository first held (`data/raw/`, 2024–2026) were therefore removed on October 29, 2026; the author keeps them privately, and the scripts read them from a local copy. The same counts can be viewed on [telraam.net](https://telraam.net) and queried through Telraam's API (segments 9000007290, King Edward, and 9000007489, Draper), under Telraam's own terms. This note will be updated if Telraam grants permission to republish the exports.

The tables in `derived/` and the figures are computed from Telraam's counts (source: Telraam). The author's own work, the README, the figures and the method, is published under CC BY 4.0 ([`LICENSE`](LICENSE)), and the scripts under the MIT licence ([`LICENSE-CODE`](LICENSE-CODE)); neither licence covers Telraam's counts.

## Use of AI

Much of the code and many of the drafts in this repository were produced with an AI assistant, Anthropic's Claude, in interactive sessions directed by the author. The author chose the questions, supplied the sources, reviewed every output, and checked every quotation, page reference and figure against the documents; the author alone is responsible for the content. Commits to which the assistant contributed name it as co-author, so the division of work is visible in the history, and errors found in its work are corrected in the open like any other. Nothing in `raw/` is edited by anyone, human or machine. The practice follows the principles of the European Commission's « Living guidelines on the responsible use of generative AI in research » (Directorate-General for Research and Innovation with the European Research Area Forum, first published March 20, 2024 and updated since; [document page](https://research-and-innovation.ec.europa.eu/document/2b6cf7e5-36ac-41cb-aab5-0d32050143dc_en)): the researcher remains responsible for the output, the use of the tool is disclosed, sources and facts are verified, privacy and third-party rights are respected, and the tool is never an author.

Everything is open to review: all source code, documents and data in this repository are publicly visible, as is the complete change log of every file. Anyone is welcome to read any of it and check it for errors and omissions. Anyone with a concern is welcome to open an issue on GitHub; every issue submitted is publicly visible, as is its answer.

## About the author

The requests were filed, and the derived documents written, by Rick Hoge, a resident of Côte-des-Neiges–Notre-Dame-de-Grâce who cycles on Terrebonne in every season. He works as a data scientist and is a professor in the Faculty of Medicine at McGill University, where his research is in neuroscience and biomedical engineering, including the effects of physical activity on brain health. The work in this repository is personal: it was done as a resident, on his own time, from public records, and represents no position of McGill University or of any other organization; the affiliation is given for identification only. Corrections are welcome through the repository's issue tracker.
