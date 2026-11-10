"""Plot XGBoost (national, wachsender Trainingszeitraum ab 2015): gleiche Diagramme wie
plot_hist_expanding.py, nur CO2 und Gruenanteil (keine Quellen)."""
import plot_linear_expanding as plots

plots.RUN = plots.ROOT / 'reports/xgboost_expanding_v1'
plots.OUT = plots.ROOT / 'reports/xgboost_expanding_plots_v1'
plots.METHOD = 'XGBoost'

if __name__ == '__main__':
    plots.main(sources=False)
