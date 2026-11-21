# Pass predictor

Predicts when the satellite will pass over the ground station.

It downloads satellite orbit data from [CelesTrak](https://celestrak.org/) and uses it to compute passes with [Skyfield](https://rhodesmill.org/skyfield/).

```
CelesTrak -> orbit_elements (orbit_source.py) -> predicted passes (orbit.py) -> sessions -> MCC, state manager
```

## Files

| File | Purpose |
|---|---|
| `orbit.py` | Predicts passes based orbit data, station, and time window. |
| `orbit_source.py` | Downloads orbit data from CelesTrak, validates it, and stores it in orbit_elements. Also stores orbit data entered by hand. |
| `__main__.py` | CLI. |
| `../config/env_settings/pass_prediction_config.py` | Config, read from `PASS_PREDICTION_*` env variables. |

## Running

```sh
cd backend
uv run python -m app.pass_prediction fetch  # download orbit data if a refresh is possible
uv run python -m app.pass_prediction add-omm path/to.json  # store manual orbit data
```

## Settings

| Variable | Default | Notes |
|---|---|---|
| `PASS_PREDICTION_NORAD_CAT_ID` | `25544` | Satellite to track (the ISS, for development) |
| `PASS_PREDICTION_STATION_LATITUDE_DEG` | `43.4730` | Defaults to E7 |
| `PASS_PREDICTION_STATION_LONGITUDE_DEG` | `-80.5395` | |
| `PASS_PREDICTION_STATION_ALTITUDE_M` | `372.0` | |
| `PASS_PREDICTION_MIN_ELEVATION_DEG` | `15.0` | Elevation above the horizon where a pass starts and ends |
| `PASS_PREDICTION_PRE_PADDING_S` | `60` | Session time before the pass starts, for station setup |
| `PASS_PREDICTION_POST_PADDING_S` | `60` | Session time after the pass ends |
| `PASS_PREDICTION_WINDOW_DAYS` | `7` | How far ahead to predict |
| `PASS_PREDICTION_FREEZE_HOURS` | `12.0` | How long before a session its times stop changing |
| `PASS_PREDICTION_REFRESH_HOURS` | `6.0` | Minimum time between downloads, can't be below 2 |
| `PASS_PREDICTION_CELESTRAK_URL` | CelesTrak's GP API | |
| `PASS_PREDICTION_REQUEST_TIMEOUT_S` | `30.0` | |

## Orbit data

The orbit data format is an OMM record (Orbit Mean-Elements Message), which is a JSON object with fields like `EPOCH`, `MEAN_MOTION`, and `INCLINATION`. It describes the orbit at the epoch. It must be refreshed regularly as it loses accuracy the further you predict from it.

The `orbit_elements` table stores OMM records. The record itself is in the `omm` column. `norad_cat_id` and `epoch` are copies of the OMM fields used for lookups and uniqueness. We always use the latest epoch when predicting passes.

The `orbit_fetch_attempts` table stores download attempts, whether or not they were successful. It tells us if downloads have been failing and lets the predictor know when we last attempted to download.
