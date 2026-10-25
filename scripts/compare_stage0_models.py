"""Compare completed experiments; verify identical evaluation rows first."""
import json
import numpy as np
from plot_linear_results import ROOT, plt, pd


def main():
    methods = {'linear': 'linear_regression_v1',
               'hist_gradient_boosting': 'hist_gradient_boosting_v1',
               'xgboost': 'xgboost_v1'}
    labels = ['Lineare Regression', 'HistGradientBoosting', 'XGBoost']
    out = ROOT/'reports/model_comparison_v1'
    out.mkdir(exist_ok=True)
    rows = []
    for target in ('target_co2_gco2eq_kwh', 'target_renewable_share_pct'):
        reference = None
        for method, directory in methods.items():
            parts = []
            for year in range(2018, 2025):
                frame = pd.read_csv(ROOT/'reports'/directory/f'predictions_{year}_{target}.csv')
                parts.append(frame.loc[frame.common_scored == 1])
            frame = pd.concat(parts, ignore_index=True)
            identity = frame[['target_time_utc', 'actual']]
            if reference is None:
                reference = identity
            else:
                pd.testing.assert_frame_equal(reference, identity)
            actual, predicted = frame.actual.to_numpy(), frame[method].to_numpy()
            error = actual-predicted
            row = dict(target=target, method=method, n=len(frame),
                       mae=np.abs(error).mean(), rmse=np.sqrt((error**2).mean()),
                       r2=1-(error**2).sum()/((actual-actual.mean())**2).sum())
            manifest = json.loads((ROOT/'reports'/directory/'run.json').read_text())
            reported = next(r for r in manifest['pooled'] if r['target']==target and r['method']==method)
            for metric in ('n', 'mae', 'rmse', 'r2'):
                # XGBoost outputs float32; CSV serialization rounds predictions.
                np.testing.assert_allclose(row[metric], reported[metric], rtol=1e-7, atol=1e-8)
            rows.append(row)
        table = pd.DataFrame(rows).query('target == @target')
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        for ax, metric in zip(axes, ('mae', 'rmse', 'r2')):
            bars = ax.bar(labels, table[metric], color=['#1769aa', '#16846a', '#8c56b5'])
            ax.bar_label(bars, fmt='%.3f', padding=4)
            ax.set_title(metric.upper())
            ax.tick_params(axis='x', rotation=15, labelsize=9)
            ax.margins(y=.2)
            ax.set_ylabel('dimensionslos' if metric=='r2' else 'Prozentpunkte' if target.endswith('pct') else 'gCO₂eq/kWh')
        fig.suptitle('Grünanteil' if target.endswith('pct') else 'CO₂-Intensität')
        fig.text(.5, .02, 'Validierung 2018–2024 · identische Stunden · retrospektives ERA5, kein operativer 72h-Test', ha='center')
        fig.tight_layout(rect=(0,.07,1,.94))
        for extension in ('png', 'pdf'):
            fig.savefig(out/f'{target}.{extension}', dpi=180)
        plt.close(fig)
    pd.DataFrame(rows).to_csv(out/'metrics_verified.csv', index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == '__main__':
    main()
