"""Preprocess NASA C-MAPSS (Saxena et al., PHM08) into CSV files for time-i-gram examples.

Usage: python3 prep_cmapss.py <dir with train_FD00x.txt ...> <output dir>

Time: C-MAPSS counts operational cycles, not dates. Every engine gets a synthetic clock,
`date` = 2000-01-01 + (cycle - 1) days (1 cycle = 1 day), so that `csv-time` can read it. Absolute
dates carry no meaning: use the relative time coordinate system (`x.relative`, unit "day") in specs.

Health index (`hi`): each sensor is turned into a z-score against the engine's own healthy baseline
(its first BASELINE cycles; per operating condition in FD002/FD004), with its sign flipped so that
up = degradation, and the z-scores of the HI sensors are averaged. `hi_smooth` is a trailing mean over
SMOOTH cycles.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DATE = pd.Timestamp('2000-01-01')
BASELINE = 30  # healthy cycles at the start of each engine
SMOOTH = 10

COLS = ['unit', 'cycle', 'setting1', 'setting2', 'setting3'] + [f's{i}' for i in range(1, 22)]

# Saxena et al. 2008, Table 2. Sensors s1, s5, s6, s10, s16, s18, s19 are constant in FD001/FD003.
SENSORS = {
    's2': ('T24', 'LPC outlet temperature'),
    's3': ('T30', 'HPC outlet temperature'),
    's4': ('T50', 'LPT outlet temperature'),
    's7': ('P30', 'HPC outlet pressure'),
    's8': ('Nf', 'Physical fan speed'),
    's9': ('Nc', 'Physical core speed'),
    's11': ('Ps30', 'HPC outlet static pressure'),
    's12': ('phi', 'Fuel flow / Ps30'),
    's13': ('NRf', 'Corrected fan speed'),
    's14': ('NRc', 'Corrected core speed'),
    's15': ('BPR', 'Bypass ratio'),
    's17': ('htBleed', 'Bleed enthalpy'),
    's20': ('W31', 'HPT coolant bleed'),
    's21': ('W32', 'LPT coolant bleed'),
}
# Direction of degradation under HPC degradation (FD001): +1 rises toward failure, -1 falls.
DIRECTION = {'s2': 1, 's3': 1, 's4': 1, 's7': -1, 's8': 1, 's9': 1, 's11': 1, 's12': -1,
             's13': 1, 's14': 1, 's15': 1, 's17': 1, 's20': -1, 's21': -1}
# The sensors of the long file: the six that track HPC degradation most closely (|corr with RUL| >= 0.64).
LONG_SENSORS = ['s4', 's11', 's12', 's7', 's15', 's21']
# Sensors that track degradation in every engine (|corr with RUL| >= 0.5 in FD001).
HI_SENSORS = ['s2', 's3', 's4', 's7', 's8', 's11', 's12', 's13', 's15', 's17', 's20', 's21']
# In FD003 these move in opposite directions under the two fault modes, so they stay out of its HI.
MODE_DEPENDENT = ['s7', 's12', 's15', 's20', 's21']


def read(src, name):
    return pd.read_csv(src / name, sep=r'\s+', header=None, names=COLS)


def add_time(df):
    df['date'] = (BASE_DATE + pd.to_timedelta(df.cycle - 1, unit='D')).dt.strftime('%Y-%m-%d')
    return df


def add_condition(df):
    """Operating condition: altitude (kft), Mach and throttle resolver angle, rounded to their 6 set points."""
    key = (df.setting1.round(0).astype(int).astype(str) + ' kft · M' + df.setting2.round(2).map('{:.2f}'.format)
           + ' · TRA ' + df.setting3.round(0).astype(int).astype(str))
    df['condition'] = key
    return df


def zscores(df, sensors, by=('unit',)):
    """z-score of each sensor against its healthy baseline, signed so that up = degradation."""
    healthy = df[df.cycle <= BASELINE]
    stats = healthy.groupby(list(by))[sensors].agg(['mean', 'std'])
    z = pd.DataFrame(index=df.index)
    keys = pd.MultiIndex.from_frame(df[list(by)]) if len(by) > 1 else df[by[0]]
    for s in sensors:
        mean = stats[(s, 'mean')].reindex(keys).to_numpy()
        std = stats[(s, 'std')].reindex(keys).to_numpy()
        # fall back to the fleet's spread when a baseline is (nearly) constant
        fleet_std = healthy[s].std()
        std = np.where(np.isfinite(std) & (std > 1e-9), std, fleet_std)
        z[s] = DIRECTION[s] * (df[s].to_numpy() - mean) / std
    return z


def add_hi(df, z, sensors):
    df['hi'] = z[sensors].mean(axis=1).round(3)
    df['hi_smooth'] = (df.groupby('unit').hi.transform(lambda h: h.rolling(SMOOTH, min_periods=1).mean())
                       .round(3))
    return df


def add_life(df):
    life = df.groupby('unit').cycle.transform('max')
    df['life'] = life
    df['rul'] = life - df.cycle
    return df


def wide(df, extra=()):
    keep = ['unit', 'cycle', 'date', 'life', 'rul', *extra, 'hi', 'hi_smooth', *SENSORS]
    return df[[c for c in keep if c in df.columns]]


def long(df, z, sensors):
    out = []
    for s in sensors:
        out.append(pd.DataFrame({'unit': df.unit, 'date': df.date, 'sensor': SENSORS[s][0], 'z': z[s].round(2)}))
    return pd.concat(out, ignore_index=True)


def engines(df, failure):
    g = df.groupby('unit')
    return pd.DataFrame({
        'unit': g.cycle.size().index,
        'start_date': g.date.first().to_numpy(),
        'last_date': g.date.last().to_numpy(),
        'failure_date': failure.to_numpy(),
        'cycles_observed': g.cycle.max().to_numpy(),
    })


def main(src, out):
    out.mkdir(parents=True, exist_ok=True)

    # FD001: one condition, one fault mode (HPC degradation). The main example dataset.
    tr = add_life(add_time(read(src, 'train_FD001.txt')))
    z = zscores(tr, list(SENSORS))
    tr = add_hi(tr, z, HI_SENSORS)
    wide(tr).to_csv(out / 'fd001_train.csv', index=False)
    long(tr, z, LONG_SENSORS).to_csv(out / 'fd001_train_sensors_long.csv', index=False)
    eng = engines(tr, tr.groupby('unit').date.last())
    eng.rename(columns={'cycles_observed': 'life'}).drop(columns='last_date') \
        .to_csv(out / 'fd001_train_engines.csv', index=False)

    # FD001 test: series stop before failure; the true RUL at the last cycle is in RUL_FD001.txt.
    te = add_time(read(src, 'test_FD001.txt'))
    rul_end = pd.read_csv(src / 'RUL_FD001.txt', header=None, names=['rul_end']).rul_end
    rul_end.index = np.arange(1, len(rul_end) + 1)
    last = te.groupby('unit').cycle.transform('max')
    te['rul'] = te.unit.map(rul_end) + (last - te.cycle)
    te['life'] = last + te.unit.map(rul_end)
    te['failure_date'] = (BASE_DATE + pd.to_timedelta(te.life - 1, unit='D')).dt.strftime('%Y-%m-%d')
    # same baseline as training: each engine's own first BASELINE cycles (some test series are shorter)
    zt = zscores(te, list(SENSORS))
    te = add_hi(te, zt, HI_SENSORS)
    wide(te, extra=['failure_date']).to_csv(out / 'fd001_test.csv', index=False)
    failure = te.groupby('unit').failure_date.first()
    e = engines(te, failure)
    e['rul_end'] = rul_end.to_numpy()
    e.to_csv(out / 'fd001_test_engines.csv', index=False)

    # FD003: one condition, two fault modes. The mode is not labeled in the data: it is inferred from the
    # direction of phi (s12) near failure (falls under HPC degradation as in FD001, rises under fan degradation).
    t3 = add_life(add_time(read(src, 'train_FD003.txt')))
    g = t3.groupby('unit').s12
    rises = (g.apply(lambda s: s.tail(20).mean()) - g.apply(lambda s: s.head(BASELINE).mean())) > 0
    t3['fault_mode'] = t3.unit.map(rises.map({True: 'Fan (inferred)', False: 'HPC (inferred)'}))
    z3 = zscores(t3, list(SENSORS))
    t3 = add_hi(t3, z3, [s for s in HI_SENSORS if s not in MODE_DEPENDENT])
    wide(t3, extra=['fault_mode']).to_csv(out / 'fd003_train.csv', index=False)

    # FD002: six operating conditions, one fault mode. Raw sensors jump between condition set points;
    # z-scores against a per-condition baseline (pooled over the fleet's healthy cycles) remove that.
    t2 = add_condition(add_life(add_time(read(src, 'train_FD002.txt'))))
    z2 = zscores(t2, list(SENSORS), by=('condition',))
    t2 = add_hi(t2, z2, HI_SENSORS)
    t2['s11_normalized'] = z2['s11'].round(3)
    t2[['unit', 'cycle', 'date', 'life', 'rul', 'condition', 's11', 's11_normalized', 'hi', 'hi_smooth']] \
        .to_csv(out / 'fd002_train.csv', index=False)

    for f in sorted(out.glob('*.csv')):
        n = sum(1 for _ in open(f)) - 1
        print(f'{f.name:34s} {n:>7d} rows {f.stat().st_size / 1e6:6.2f} MB')


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
