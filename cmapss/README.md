# C-MAPSS for time-i-gram

Preprocessed from the NASA C-MAPSS Turbofan Engine Degradation Simulation data (in `../CMAPSS Jet Engine Simulated Data/`) by `prep_cmapss.py`:

```bash
python3 prep_cmapss.py "../CMAPSS Jet Engine Simulated Data" .
```

Source: A. Saxena, K. Goebel, D. Simon, and N. Eklund, "Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation", PHM08, Denver CO, 2008. NASA Prognostics Center of Excellence Data Repository.

## Synthetic clock

C-MAPSS counts operational cycles, not dates. Every engine gets `date = 2000-01-01 + (cycle − 1) days` (1 cycle = 1 day), so that `csv-time` can read it (`dateFields: ["date"]`). The dates have no meaning: show these files on a relative axis (`x.relative`, `unit: "day"`), where offsets read as cycles.

## Files

| File | Rows | One row per | Columns |
|---|---|---|---|
| `fd001_train.csv` | 20,631 | engine × cycle | `unit, cycle, date, life, rul, hi, hi_smooth`, 14 sensors |
| `fd001_train_sensors_long.csv` | 123,786 | engine × cycle × sensor | `unit, date, sensor, z` |
| `fd001_train_engines.csv` | 100 | engine | `unit, start_date, failure_date, life` |
| `fd001_test.csv` | 13,096 | engine × cycle | as train, plus `failure_date` |
| `fd001_test_engines.csv` | 100 | engine | `unit, start_date, last_date, failure_date, cycles_observed, rul_end` |
| `fd003_train.csv` | 24,720 | engine × cycle | as train, plus `fault_mode` |
| `fd002_train.csv` | 53,759 | engine × cycle | `unit, cycle, date, life, rul, condition, s11, s11_normalized, hi, hi_smooth` |

- `life`: the engine's total cycles; `rul`: remaining useful life (cycles to failure) at that row.
- `z`: the sensor's z-score against the engine's first 30 cycles, signed so that up = degradation. FD002 uses a per-condition baseline instead, pooled over the fleet.
- `hi`: health index, the mean `z` of the sensors that degrade in every engine; `hi_smooth`: trailing 10-cycle mean.
- Test files: the series stop before failure. `failure_date` = last observed cycle + true RUL (`RUL_FD001.txt`).
- `fault_mode` (FD003): not labeled in the source. It is inferred from whether φ (s12) falls (HPC, as in FD001) or rises (fan) near failure; 56 HPC, 44 fan.
- `condition` (FD002): altitude, Mach and throttle resolver angle, rounded to their 6 set points.
- Long-file sensors: T50 (LPT outlet temp.), Ps30 (HPC outlet static pressure), phi (fuel flow / Ps30), P30 (HPC outlet pressure), BPR (bypass ratio), W32 (LPT coolant bleed).
