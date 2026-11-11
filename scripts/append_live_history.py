"""Append a new live prediction file to a cumulative history file (no training).

The daily workflow overwrites predictions.csv / predictions_bundesland.csv with
the newest 3-day forecast, so earlier days would disappear from the dashboard.
This keeps every forecast hour: history + new file, the newest value wins for
hours predicted more than once (keys: target_time_utc [+ bundesland]).
"""
import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new', type=Path, required=True)
    parser.add_argument('--history', type=Path, required=True)
    args = parser.parse_args()
    new = pd.read_csv(args.new)
    keys = ['target_time_utc', 'bundesland'] if 'bundesland' in new.columns else ['target_time_utc']
    frames = [pd.read_csv(args.history), new] if args.history.exists() else [new]
    combined = pd.concat(frames, ignore_index=True).drop_duplicates(keys, keep='last').sort_values(keys)
    combined.to_csv(args.history, index=False)
    print(args.history, 'Zeilen:', len(combined), 'von', combined.target_time_utc.min(), 'bis', combined.target_time_utc.max())


if __name__ == '__main__':
    main()
