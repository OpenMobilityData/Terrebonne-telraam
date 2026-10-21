# Terrebonne-telraam: two citizen traffic sensors on rue de Terrebonne (NDG, Montréal)

Hourly counts from two Telraam S2 sensors installed by the author on rue de Terrebonne, exported from the Telraam dashboard, with the scripts and figures drawn from them. Companion to [Terrebonne-access-requests](https://github.com/OpenMobilityData/Terrebonne-access-requests) (the borough's own counter and documents) and [Terrebonne-open-sources](https://github.com/OpenMobilityData/Terrebonne-open-sources) (public records). Nothing here is an official count: the borough's loop counter at Kensington is the record; these sensors are the check and the history.

## The sensors

| Segment | Telraam segment / instance | Location | Data |
|---|---|---|---|
| West | 13374 / 9794 | rue de Terrebonne at King Edward (west of Cavendish; the street is one-way westbound there) | August 15, 2024 → May 4, 2026 (last export) |
| East | 13690 / 10045 | rue de Terrebonne at Draper (east of Cavendish; one-way eastbound) | September 24, 2024 → January 24, 2026 (sensor stopped) |

Both are Telraam S2 units (same hardware throughout). They count in **daylight only**: the "Bike Total" column is the daylight bicycle count, both directions; night-time traffic is reported as an undifferentiated "Night" class. Each hourly row carries an uptime value (the fraction of the hour with the sensor counting), stored by the dashboard as "Good uptime - 0.75" or "Poor uptime - 0.40". Levels are therefore not comparable with the borough's 24-hour loop counter.

## Layout

| Path | Content |
|---|---|
| `data/raw/raw-data-20YY{East,West}60.xlsx` | Hourly exports (60-minute resolution) by calendar year, as downloaded; never edited. 15-minute exports and older partial snapshots stay outside this repository |
| `scripts/telraam_period_violins.py` | Year-over-year violin plots of daily bicycle counts for equivalent periods (whole winter, whole year, each month), comparing years on the calendar dates valid in every year shown; a period is drawn only when two years share at least 20 valid dates |
| `figures/year-over-year/` | The figures (PNG and SVG), `telraam_{west,east}_{period}_en` |

**Valid day** (for the figures): at least 8 reported hours and at least 6 hours of summed uptime.

## Winter coverage (checked October 20, 2026)

| Segment | Winter 2024–25 valid days | Winter 2025–26 valid days | Calendar dates valid in both |
|---|---:|---:|---:|
| King Edward | 119 of 121 | 68 (gaps December 13–28 and January 29 – March 6) | 66 |
| Draper | 120 of 121 | 53 (December and January 1–24 only) | 53 |

There are only two winters, both after the protected lane was built (2024); no pre-lane winter exists in this record. Summer and February have one year of data only and are not drawn. Weather differs between the years compared; the 2025–26 winter had the second-lowest snow loading of eleven seasons.

## Licence and provenance

The exports are the author's own sensor data, downloaded from the Telraam dashboard (telraam.net) in 2025–2026. Telraam publishes sensor data as open data; the licence applying to these exports will be stated here once confirmed. Figures and scripts: CC BY 4.0.

## About the author

The requests were filed, and the derived documents written, by Rick Hoge, a resident of Côte-des-Neiges–Notre-Dame-de-Grâce who cycles on Terrebonne in every season. He works as a data scientist and is a professor in the Faculty of Medicine at McGill University, where his research is in neuroscience and biomedical engineering, including the effects of physical activity on brain health. The work in this repository is personal: it was done as a resident, on his own time, from public records, and represents no position of McGill University or of any other organization; the affiliation is given for identification only. Corrections are welcome through the repository's issue tracker.
