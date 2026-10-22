"""Development-only weekday/hour means. Never opens 2025/2026 tables."""
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/stage0_v2_sunshine'
OUT = ROOT / 'reports/mean_baseline_v1'
TARGETS = {'target_co2_gco2eq_kwh': 'eligible_co2_nonestimated',
           'target_renewable_share_pct': 'eligible_renewable'}


def key(timestamp):
    t = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    local = t.astimezone(ZoneInfo('Europe/Berlin'))
    return local.weekday(), local.hour


def fit(rows, target):
    groups = defaultdict(list)
    for r in rows:
        if r[TARGETS[target]] == '1':
            value = float(r[target])
            if not math.isfinite(value):
                raise ValueError('Nonfinite eligible target')
            groups[key(r['target_time_utc'])].append(value)
    if len(groups) != 168:
        raise ValueError('Missing training groups: no validation-derived fallback allowed')
    return {k: (math.fsum(v) / len(v), len(v)) for k, v in groups.items()}


def metrics(actual, predicted):
    if len(actual) != len(predicted) or not actual:
        raise ValueError('Empty or mismatched evaluation')
    errors = [a - p for a, p in zip(actual, predicted)]
    sse = math.fsum(e * e for e in errors)
    mean = math.fsum(actual) / len(actual)
    sst = math.fsum((a - mean) ** 2 for a in actual)
    return dict(n=len(actual), mae=math.fsum(abs(e) for e in errors)/len(errors),
                rmse=math.sqrt(sse/len(errors)), r2=1-sse/sst if sst else None)


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    if OUT.exists():
        raise FileExistsError('Version already exists; do not overwrite experiments')
    splits = json.loads((DATA / 'splits.json').read_text())
    folds = splits['development_folds']
    years = sorted({y for f in folds for y in f['train_years'] + [f['validation_year']]})
    assert years == list(range(2015, 2025))
    for f in folds:
        assert f['train_years'] == list(range(f['validation_year']-3, f['validation_year']))
    selected = ['target_time_utc', *TARGETS, *TARGETS.values()]
    source_hashes, data = {}, {}
    for y in years:
        path = DATA / ('hourly_%s.csv' % y)
        source_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open() as f:
            data[y] = [{k: r[k] for k in selected} for r in csv.DictReader(f)]
        start = datetime.fromisoformat('%s-01-01T00:00:00+00:00' % y)
        end = start.replace(year=y+1)
        assert len(data[y]) == (end-start).total_seconds()/3600
        for i, r in enumerate(data[y]):
            assert datetime.fromisoformat(r['target_time_utc'].replace('Z', '+00:00')) == start+timedelta(hours=i)
            assert all(r[flag] in ('0', '1') for flag in TARGETS.values())
    OUT.mkdir(parents=True)
    summary = []
    pooled = {t: ([], []) for t in TARGETS}
    for fold in folds:
        y = fold['validation_year']
        train = [r for year in fold['train_years'] for r in data[year]]
        model_rows, predictions = [], []
        for target, flag in TARGETS.items():
            model = fit(train, target)
            for (weekday, hour), (mean, n) in sorted(model.items()):
                model_rows.append(dict(target=target, weekday=weekday, hour=hour, mean=mean, train_count=n))
            actual, predicted = [], []
            for r in data[y]:
                pred = model[key(r['target_time_utc'])][0]
                eligible = r[flag] == '1'
                predictions.append(dict(target_time_utc=r['target_time_utc'], target=target,
                                        prediction=pred, actual=r[target], scored=int(eligible)))
                if eligible:
                    actual.append(float(r[target]))
                    predicted.append(pred)
            stats = metrics(actual, predicted)
            summary.append(dict(validation_year=y, target=target,
                                train_years='-'.join(map(str, fold['train_years'])),
                                train_total=len(train), train_used=sum(n for _, n in model.values()),
                                validation_total=len(data[y]), excluded=len(data[y])-len(actual), **stats))
            pooled[target][0].extend(actual)
            pooled[target][1].extend(predicted)
            print(y, target, stats, flush=True)
        write_csv(OUT / ('model_%s.csv' % y), model_rows)
        write_csv(OUT / ('predictions_%s.csv' % y), predictions)
    write_csv(OUT / 'metrics.csv', summary)
    for relative, expected in source_hashes.items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == expected
    manifest = dict(method='weekday_hour_training_mean', timezone='Europe/Berlin',
                    folds=folds, targets=TARGETS, source_sha256=source_hashes,
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    pooled_metrics={t: metrics(a, p) for t, (a, p) in pooled.items()},
                    evaluation_policy='Prepared per-target eligibility masks used for fitting and scoring; all predictions retained',
                    caveats=['Retrospective revised targets, not as-issued availability',
                             'Yearly fixed models, not origin-specific 72h operational backtest',
                             '2025 and 2026 tables neither read nor evaluated',
                             'Both repeated autumn hours share same local weekday/hour mean'],
                    complete=True)
    (OUT / 'run.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print('Completed:', OUT)


if __name__ == '__main__':
    main()
