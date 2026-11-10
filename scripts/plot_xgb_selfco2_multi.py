"""Plot XGBoost Mehrziel (selbst berechnetes CO2, wachsender Trainingszeitraum ab 2015): gleiche
Diagramme wie plot_xgb_selfco2_separate.py."""
import plot_linear_expanding as plots

plots.RUN = plots.ROOT / 'reports/xgboost_selfco2_multi_expanding_v1'
plots.OUT = plots.ROOT / 'reports/xgboost_selfco2_multi_expanding_plots_v1'
plots.METHOD = 'XGBoost Mehrziel'
plots.TARGETS['target_co2_gco2eq_kwh']['label'] = 'CO₂-Intensität (selbst berechnet)'

if __name__ == '__main__':
    plots.main()
